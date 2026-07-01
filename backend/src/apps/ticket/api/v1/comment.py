# src/apps/ticket/routers/comment.py
from typing import Annotated
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query, Request, Path
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.apps.ticket.models.activity_log import TicketActivityLog
from src.core.types import HashId
from src.apps.iam.models.user import User
from src.core.exceptions import NotFoundError, AuthorizationError
from src.apps.ticket.models.comment import TicketComment
from src.apps.ticket.dependencies import CurrentTicket  
from src.apps.ticket.schemas.comment import (
    TicketCommentCreate,
    TicketCommentUpdate,
    TicketCommentPartialUpdate,
    TicketCommentResponse
)
from src.db.query import select
from src.core.utils import decode_cursor, encode_cursor
from src.core.dependencies import DB, get_current_active_superuser, require_module_permission
from src.core.schemas import CursorPage, CursorPagination, ApiSuccessResponse
from src.core.enums import RBACModule, TicketActivityType
from src.core.cache import RedisCache

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(
    prefix="/organizations/{org}/projects/{project_id}/tickets/{ticket_id}/comments", 
    tags=["Ticket Comments"],
    dependencies=[Depends(require_module_permission(RBACModule.PROJECTS))]
)
COMMENT_RATE_LIMIT = limiter.limit("20/minute")

# --- Local Dependencies ---

async def get_current_comment(
    db: DB,
    current_ticket: CurrentTicket,
    comment_id: Annotated[HashId, Path(description="Comment ID")],
) -> TicketComment:
    """Fetches an active comment, ensuring it belongs completely to the resolved ticket scope."""
    query = select(TicketComment).where(
        TicketComment.id == comment_id,
        TicketComment.ticket_id == current_ticket.id,
        TicketComment.deleted_at.is_(None) # Exclude soft-deleted comments
    )
    result = await db.execute(query)
    comment = result.scalar_one_or_none()
    if not comment:
        raise NotFoundError(message="Comment not found")
    return comment

CurrentComment = Annotated[TicketComment, Depends(get_current_comment)]

# --- Cache Helpers ---

async def _invalidate_comment_cache(ticket_id: int, comment_id: int):
    await RedisCache.delete(f"comment:{comment_id}")
    await RedisCache.clear_pattern(f"comment:list:{ticket_id}:*")

# --- Endpoints ---

@router.get("/", response_model=CursorPage[TicketCommentResponse])
@COMMENT_RATE_LIMIT
async def list_comments(
    db: DB,
    current_ticket: CurrentTicket,
    request: Request,
    pagination: CursorPagination = Depends(),
    parent_comment_id: HashId | None = Query(default=None, description="Filter to fetch specific reply threads"),
):
    cache_key = f"comment:list:{current_ticket.id}:{pagination.cursor}:{pagination.limit}:{parent_comment_id}"
    cached_result = await RedisCache.get(cache_key)
    if cached_result:
        return cached_result

    query = select(TicketComment).where(
        TicketComment.ticket_id == current_ticket.id,
        TicketComment.deleted_at.is_(None)
    )

    # Filter by parent_comment_id (helps separate top-level comments from nested replies)
    if parent_comment_id is not None:
        query = query.where(TicketComment.parent_comment_id == parent_comment_id)
    else:
        query = query.where(TicketComment.parent_comment_id.is_(None))

    if pagination.cursor:
        _, cursor_id = decode_cursor(pagination.cursor)
        query = query.where(TicketComment.id > int(cursor_id))

    query = query.order_by(TicketComment.id).limit(pagination.limit + 1)
    result = await db.execute(query)
    comments = result.scalars().all()

    has_next_page = len(comments) > pagination.limit
    if has_next_page:
        comments = comments[:pagination.limit]

    items = [TicketCommentResponse.model_validate(c) for c in comments]
    next_cursor = encode_cursor(str(comments[-1].id)) if has_next_page and comments else None
    response = CursorPage[TicketCommentResponse](items=items, next_cursor=next_cursor)

    await RedisCache.set(cache_key, response.model_dump_json(), ttl=60)
    return response


@router.get("/{comment_id}", response_model=ApiSuccessResponse[TicketCommentResponse])
@COMMENT_RATE_LIMIT
async def get_comment(comment: CurrentComment, request: Request):
    cache_key = f"comment:{comment.id}"
    cached_comment = await RedisCache.get(cache_key)
    if cached_comment:
        return ApiSuccessResponse[TicketCommentResponse](
            message="Comment retrieved successfully",
            data=TicketCommentResponse.model_validate_json(cached_comment)
        )

    comment_response = TicketCommentResponse.model_validate(comment)
    await RedisCache.set(cache_key, comment_response.model_dump_json(), ttl=300)
    return ApiSuccessResponse[TicketCommentResponse](message="Comment retrieved successfully", data=comment_response)


@router.post("/", response_model=ApiSuccessResponse[TicketCommentResponse])
@COMMENT_RATE_LIMIT
async def create_comment(
    comment_data: TicketCommentCreate,
    db: DB,
    current_ticket: CurrentTicket,
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_superuser)],
):
    # Verify parent comment exists within the same ticket scope if it's a reply
    if comment_data.parent_comment_id:
        parent_check = await db.execute(
            select(TicketComment).where(
                TicketComment.id == comment_data.parent_comment_id,
                TicketComment.ticket_id == current_ticket.id,
                TicketComment.deleted_at.is_(None)
            )
        )
        if not parent_check.scalar_one_or_none():
            raise NotFoundError(message="Parent comment thread not found within this ticket scope")

    # 1. Instantiate the new ticket comment
    new_comment = TicketComment(
        ticket_id=current_ticket.id,
        user_id=current_user.id,
        parent_comment_id=comment_data.parent_comment_id,
        body=comment_data.body
    )
    db.add(new_comment)

    # 2. Automatically seed the immutable audit log trail side effect
    new_activity_log = TicketActivityLog(
        ticket_id=current_ticket.id,
        user_id=current_user.id,
        activity_type=TicketActivityType.COMMENT_ADDED,
        field_changed="comment",
        old_value=None,
        new_value=comment_data.body  # Stores comment body securely inside history dump
    )
    db.add(new_activity_log)

    # Commit both entries atomically in a single transaction unit
    await db.commit()
    await db.refresh(new_comment)

    # 3. Synchronize Redis caching bounds across both modules
    if new_comment.id:
        await _invalidate_comment_cache(current_ticket.id, new_comment.id)
    await RedisCache.clear_pattern(f"activity_log:list:{current_ticket.id}:*")

    return ApiSuccessResponse[TicketCommentResponse](
        message="Comment added successfully", 
        data=TicketCommentResponse.model_validate(new_comment)
    )

@router.put("/{comment_id}", response_model=ApiSuccessResponse[TicketCommentResponse])
@COMMENT_RATE_LIMIT
async def update_comment(
    comment_data: TicketCommentUpdate, 
    comment: CurrentComment, 
    db: DB, 
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_superuser)]
):
    # Ownership verification guard (Admins or Authors only)
    if comment.user_id != current_user.id and not current_user.is_superuser:
        raise AuthorizationError(message="You lack permissions to modify this comment")

    comment.body = comment_data.body

    await db.commit()
    await db.refresh(comment)
    if comment.id:
        await _invalidate_comment_cache(comment.ticket_id, comment.id)

    return ApiSuccessResponse[TicketCommentResponse](
        message="Comment updated successfully", 
        data=TicketCommentResponse.model_validate(comment)
    )


@router.patch("/{comment_id}", response_model=ApiSuccessResponse[TicketCommentResponse])
@COMMENT_RATE_LIMIT
async def partial_update_comment(
    comment_data: TicketCommentPartialUpdate, 
    comment: CurrentComment, 
    db: DB, 
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_superuser)]
):
    if comment.user_id != current_user.id and not current_user.is_superuser:
        raise AuthorizationError(message="You lack permissions to modify this comment")

    update_data = comment_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(comment, key, value)

    await db.commit()
    await db.refresh(comment)
    if comment.id:
        await _invalidate_comment_cache(comment.ticket_id, comment.id)

    return ApiSuccessResponse[TicketCommentResponse](
        message="Comment updated successfully", 
        data=TicketCommentResponse.model_validate(comment)
    )


@router.delete("/{comment_id}", response_model=ApiSuccessResponse[None])
@COMMENT_RATE_LIMIT
async def delete_comment(
    comment: CurrentComment, 
    db: DB, 
    request: Request, 
    current_user: Annotated[User, Depends(get_current_active_superuser)]
):
    if comment.user_id != current_user.id and not current_user.is_superuser:
        raise AuthorizationError(message="You lack permissions to delete this comment")

    # Executing safe soft-delete process using your model's deleted_at timestamp field
    comment.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    
    await db.commit()
    if comment.id:
        await _invalidate_comment_cache(comment.ticket_id, comment.id)
    return ApiSuccessResponse[None](message="Comment deleted successfully", data=None)