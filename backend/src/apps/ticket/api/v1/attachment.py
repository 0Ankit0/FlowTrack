# src/apps/ticket/routers/attachment.py
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, Query, Request, Path, File, UploadFile, HTTPException, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.core.config import settings
from src.core.types import HashId
from src.apps.iam.models.user import User
from src.core.exceptions import NotFoundError, AuthorizationError
from src.apps.ticket.models.attachment import TicketAttachment
from src.apps.ticket.api.v1.ticket import CurrentTicket
from src.apps.ticket.schemas.attachment import (
    TicketAttachmentUpdate,
    TicketAttachmentPartialUpdate,
    TicketAttachmentResponse
)
from src.db.query import select
from src.core.utils import decode_cursor, encode_cursor
from src.core.dependencies import DB, get_current_active_superuser, require_module_permission
from src.core.schemas import CursorPage, CursorPagination, ApiSuccessResponse
from src.core.enums import RBACModule
from src.core.cache import RedisCache
from src.core.storage import save_media_bytes, delete_media 

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(
    prefix="/organizations/{org}/projects/{project_id}/tickets/{ticket_id}/attachments", 
    tags=["Ticket Attachments"],
    dependencies=[Depends(require_module_permission(RBACModule.PROJECTS))]
)
ATTACHMENT_RATE_LIMIT = limiter.limit("30/minute")

# --- Local Dependencies ---

async def get_current_attachment(
    db: DB,
    current_ticket: CurrentTicket,
    attachment_id: Annotated[HashId, Path(description="Attachment ID")],
) -> TicketAttachment:
    query = select(TicketAttachment).where(
        TicketAttachment.id == attachment_id,
        TicketAttachment.ticket_id == current_ticket.id
    )
    result = await db.execute(query)
    attachment = result.scalar_one_or_none()
    if not attachment:
        raise NotFoundError(message="Attachment not found")
    return attachment

CurrentAttachment = Annotated[TicketAttachment, Depends(get_current_attachment)]

# --- Cache Helpers ---

async def _invalidate_attachment_cache(ticket_id: int | None, attachment_id: int | None):
    """Invalidates attachment cache targets after making sure that the specific IDs exist."""
    if attachment_id:
        await RedisCache.delete(f"attachment:{attachment_id}")
    if ticket_id:
        await RedisCache.clear_pattern(f"attachment:list:{ticket_id}:*")

# --- Endpoints ---

@router.post("/", response_model=ApiSuccessResponse[TicketAttachmentResponse])
@ATTACHMENT_RATE_LIMIT
async def create_attachment(
    db: DB,
    current_ticket: CurrentTicket,
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_superuser),
):
    """Upload a reference document or asset directly to an execution ticket stream."""
    # Broaden allowed types beyond basic avatars to handle standard workflow documentation
    ALLOWED_TYPES = {
        "image/jpeg", "image/png", "image/gif", "image/webp",
        "application/pdf", "text/plain", "application/zip",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    }
    # Fallback to 10MB configuration boundary check if explicit app setting is missing
    max_size_mb = getattr(settings, "MAX_ATTACHMENT_SIZE_MB", 10)
    MAX_SIZE = max_size_mb * 1024 * 1024

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}.",
        )

    contents = await file.read()
    if len(contents) > MAX_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum allowed size is {max_size_mb} MB",
        )

    # Securely extract extension structures safely
    ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename and "." in file.filename else "dat"
    clean_uuid = uuid.uuid4().hex[:8]
    filename = f"{clean_uuid}_{file.filename}" if file.filename else f"{clean_uuid}.{ext}"
    
    # Store files partitioned logically by project ticket domains
    relative_path = f"tickets/{current_ticket.id}/attachments/{filename}"

    file_url = save_media_bytes(
        relative_path,
        contents,
        content_type=file.content_type,
    )

    new_attachment = TicketAttachment(
        ticket_id=current_ticket.id,
        user_id=current_user.id,
        file_name=file.filename or filename,
        file_path=file_url,
        file_size=len(contents),
        mime_type=file.content_type
    )
    db.add(new_attachment)
    await db.commit()
    await db.refresh(new_attachment)

    await _invalidate_attachment_cache(current_ticket.id, new_attachment.id)
    return ApiSuccessResponse[TicketAttachmentResponse](
        message="Attachment uploaded successfully", 
        data=TicketAttachmentResponse.model_validate(new_attachment)
    )


@router.get("/", response_model=CursorPage[TicketAttachmentResponse])
@ATTACHMENT_RATE_LIMIT
async def list_attachments(
    db: DB,
    current_ticket: CurrentTicket,
    request: Request,
    pagination: CursorPagination = Depends(),
    mime_type: str | None = Query(default=None, description="Filter attachments by mime type"),
):
    cache_key = f"attachment:list:{current_ticket.id}:{pagination.cursor}:{pagination.limit}:{mime_type}"
    cached_result = await RedisCache.get(cache_key)
    if cached_result:
        return cached_result

    query = select(TicketAttachment).where(TicketAttachment.ticket_id == current_ticket.id)

    if mime_type:
        query = query.where(TicketAttachment.mime_type.ilike(f"%{mime_type}%"))

    if pagination.cursor:
        _, cursor_id = decode_cursor(pagination.cursor)
        query = query.where(TicketAttachment.id > int(cursor_id))

    query = query.order_by(TicketAttachment.id).limit(pagination.limit + 1)
    result = await db.execute(query)
    attachments = result.scalars().all()

    has_next_page = len(attachments) > pagination.limit
    if has_next_page:
        attachments = attachments[:pagination.limit]

    items = [TicketAttachmentResponse.model_validate(a) for a in attachments]
    
    next_cursor = encode_cursor(str(attachments[-1].id)) if has_next_page and attachments else None
    response = CursorPage[TicketAttachmentResponse](items=items, next_cursor=next_cursor)

    await RedisCache.set(cache_key, response.model_dump_json(), ttl=60)
    return response


@router.get("/{attachment_id}", response_model=ApiSuccessResponse[TicketAttachmentResponse])
@ATTACHMENT_RATE_LIMIT
async def get_attachment(attachment: CurrentAttachment, request: Request):
    cache_key = f"attachment:{attachment.id}"
    cached_attachment = await RedisCache.get(cache_key)
    if cached_attachment:
        return ApiSuccessResponse[TicketAttachmentResponse](
            message="Attachment retrieved successfully",
            data=TicketAttachmentResponse.model_validate_json(cached_attachment)
        )

    attachment_response = TicketAttachmentResponse.model_validate(attachment)
    await RedisCache.set(cache_key, attachment_response.model_dump_json(), ttl=300)
    return ApiSuccessResponse[TicketAttachmentResponse](message="Attachment retrieved successfully", data=attachment_response)


@router.put("/{attachment_id}", response_model=ApiSuccessResponse[TicketAttachmentResponse])
@ATTACHMENT_RATE_LIMIT
async def update_attachment(
    attachment_data: TicketAttachmentUpdate, 
    attachment: CurrentAttachment, 
    db: DB, 
    request: Request
):
    # If file paths changed structurally, ensure cleanup of orphan storage configurations
    if attachment.file_path != attachment_data.file_path:
        delete_media(attachment.file_path)

    attachment.file_name = attachment_data.file_name
    attachment.file_path = attachment_data.file_path
    attachment.file_size = attachment_data.file_size
    attachment.mime_type = attachment_data.mime_type

    await db.commit()
    await db.refresh(attachment)
    await _invalidate_attachment_cache(attachment.ticket_id, attachment.id)

    return ApiSuccessResponse[TicketAttachmentResponse](
        message="Attachment updated successfully", 
        data=TicketAttachmentResponse.model_validate(attachment)
    )


@router.patch("/{attachment_id}", response_model=ApiSuccessResponse[TicketAttachmentResponse])
@ATTACHMENT_RATE_LIMIT
async def partial_update_attachment(
    attachment_data: TicketAttachmentPartialUpdate, 
    attachment: CurrentAttachment, 
    db: DB, 
    request: Request
):
    update_data = attachment_data.model_dump(exclude_unset=True)
    
    if "file_path" in update_data and attachment.file_path != update_data["file_path"]:
        delete_media(attachment.file_path)

    for key, value in update_data.items():
        setattr(attachment, key, value)

    await db.commit()
    await db.refresh(attachment)
    await _invalidate_attachment_cache(attachment.ticket_id, attachment.id)

    return ApiSuccessResponse[TicketAttachmentResponse](
        message="Attachment updated successfully", 
        data=TicketAttachmentResponse.model_validate(attachment)
    )


@router.delete("/{attachment_id}", response_model=ApiSuccessResponse[None])
@ATTACHMENT_RATE_LIMIT
async def delete_attachment(
    attachment: CurrentAttachment, 
    db: DB, 
    request: Request, 
    current_user: Annotated[User, Depends(get_current_active_superuser)]
):
    if attachment.user_id != current_user.id and not current_user.is_superuser:
        raise AuthorizationError(message="You lack permissions to delete this attachment reference")

    ticket_id = attachment.ticket_id
    attachment_id = attachment.id

    # Clean up storage binaries before dropping metadata rows
    if attachment.file_path:
        delete_media(attachment.file_path)

    await db.delete(attachment)
    await db.commit()
    
    await _invalidate_attachment_cache(ticket_id, attachment_id)
    return ApiSuccessResponse[None](message="Attachment deleted successfully", data=None)