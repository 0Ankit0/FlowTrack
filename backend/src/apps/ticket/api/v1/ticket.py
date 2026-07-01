# src/apps/ticket/routers/ticket.py
from datetime import datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, Query, Request, Path
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.apps.ticket.models.activity_log import TicketActivityLog
from src.core.types import HashId
from src.apps.iam.models.user import User
from src.apps.ticket.dependencies import CurrentTicket
from src.apps.ticket.models.ticket import Ticket
from src.core.dependencies import CurrentProject, CurrentUser  
from src.apps.ticket.schemas.ticket import (
    TicketCreate,
    TicketUpdate,
    TicketPartialUpdate,
    TicketResponse
)
from src.db.query import select, or_
from src.core.utils import decode_cursor, encode_cursor
from src.core.dependencies import DB, get_current_active_superuser, require_module_permission
from src.core.schemas import CursorPage, CursorPagination, ApiSuccessResponse
from src.core.enums import TicketActivityType, TicketStatus, Priority, RBACModule
from src.core.cache import RedisCache

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(
    prefix="/organizations/{org}/projects/{project_id}/tickets", 
    tags=["Tickets"],
    dependencies=[Depends(require_module_permission(RBACModule.PROJECTS))] # Reusing project level access control
)
TICKET_RATE_LIMIT = limiter.limit("15/minute")

# --- Cache Helpers ---

async def _invalidate_ticket_cache(ticket_id: int):
    await RedisCache.delete(f"ticket:{ticket_id}")
    await RedisCache.clear_pattern(f"ticket:{ticket_id}:*")

# --- Endpoints ---

@router.get("/", response_model=CursorPage[TicketResponse])
@TICKET_RATE_LIMIT
async def list_tickets(
    db: DB,
    current_project: CurrentProject,
    request: Request,
    pagination: CursorPagination = Depends(),
    search: str | None = Query(default=None, description="Search by title or description"),
    status: TicketStatus | None = Query(default=None, description="Filter by ticket status"),
    priority: Priority | None = Query(default=None, description="Filter by ticket priority"),
    assignee_id: HashId | None = Query(default=None, description="Filter by assigned user ID"),
):
    cache_key = (
        f"ticket:list:{current_project.id}:{pagination.cursor}:{pagination.limit}:"
        f"{search}:{status}:{priority}:{assignee_id}"
    )
    cached_result = await RedisCache.get(cache_key)
    if cached_result:
        return cached_result

    query = select(Ticket).where(Ticket.project_id == current_project.id)

    if search:
        search_term = f"%{search}%"
        query = query.where(or_(Ticket.title.ilike(search_term), Ticket.description.ilike(search_term)))
    if status is not None:
        query = query.where(Ticket.status == status)
    if priority is not None:
        query = query.where(Ticket.priority == priority)
    if assignee_id is not None:
        query = query.where(Ticket.assignee_id == assignee_id)

    if pagination.cursor:
        _, cursor_id = decode_cursor(pagination.cursor)
        query = query.where(Ticket.id > int(cursor_id))

    query = query.order_by(Ticket.id).limit(pagination.limit + 1)
    result = await db.execute(query)
    tickets = result.scalars().all()

    has_next_page = len(tickets) > pagination.limit
    if has_next_page:
        tickets = tickets[:pagination.limit]

    items = [TicketResponse.model_validate(t) for t in tickets]
    next_cursor = encode_cursor(tickets[-1].id) if has_next_page and tickets else None
    response = CursorPage[TicketResponse](items=items, next_cursor=next_cursor)

    await RedisCache.set(cache_key, response.model_dump_json(), ttl=60)
    return response


@router.get("/{ticket_id}", response_model=ApiSuccessResponse[TicketResponse])
@TICKET_RATE_LIMIT
async def get_ticket(ticket: CurrentTicket, request: Request):
    cache_key = f"ticket:{ticket.id}"
    cached_ticket = await RedisCache.get(cache_key)
    if cached_ticket:
        return ApiSuccessResponse[TicketResponse](
            message="Ticket retrieved successfully",
            data=TicketResponse.model_validate_json(cached_ticket)
        )

    ticket_response = TicketResponse.model_validate(ticket)
    await RedisCache.set(cache_key, ticket_response.model_dump_json(), ttl=300)
    return ApiSuccessResponse[TicketResponse](message="Ticket retrieved successfully", data=ticket_response)


@router.post("/", response_model=ApiSuccessResponse[TicketResponse])
@TICKET_RATE_LIMIT
async def create_ticket(
    ticket_data: TicketCreate,
    db: DB,
    current_project: CurrentProject,
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_superuser)],
):
    new_ticket = Ticket(
        project_id=current_project.id,
        milestone_id=ticket_data.milestone_id,
        task_id=ticket_data.task_id,
        reporter_id=current_user.id,
        assignee_id=ticket_data.assignee_id,
        title=ticket_data.title,
        description=ticket_data.description,
        status=ticket_data.status,
        priority=ticket_data.priority,
        sla_policy_id=ticket_data.sla_policy_id,
    )
    db.add(new_ticket)
    await db.commit()
    await db.refresh(new_ticket)

    await _invalidate_ticket_cache(new_ticket.id)
    return ApiSuccessResponse[TicketResponse](message="Ticket created successfully", data=TicketResponse.model_validate(new_ticket))


@router.put("/{ticket_id}", response_model=ApiSuccessResponse[TicketResponse])
@TICKET_RATE_LIMIT
async def update_ticket(ticket_data: TicketUpdate, ticket: CurrentTicket, db: DB, request: Request):
    ticket.title = ticket_data.title
    ticket.description = ticket_data.description
    ticket.status = ticket_data.status
    ticket.priority = ticket_data.priority
    ticket.milestone_id = ticket_data.milestone_id
    ticket.task_id = ticket_data.task_id
    ticket.assignee_id = ticket_data.assignee_id
    ticket.sla_policy_id = ticket_data.sla_policy_id
    ticket.first_response_due_at = ticket_data.first_response_due_at
    ticket.resolution_due_at = ticket_data.resolution_due_at
    ticket.first_response_at = ticket_data.first_response_at
    ticket.resolved_at = ticket_data.resolved_at
    
    if ticket_data.sla_breached is not None:
        ticket.sla_breached = ticket_data.sla_breached

    await db.commit()
    await db.refresh(ticket)
    await _invalidate_ticket_cache(ticket.id)

    return ApiSuccessResponse[TicketResponse](message="Ticket updated successfully", data=TicketResponse.model_validate(ticket))


@router.patch("/{ticket_id}", response_model=ApiSuccessResponse[TicketResponse])
@TICKET_RATE_LIMIT
async def partial_update_ticket(
    ticket_data: TicketPartialUpdate, 
    ticket: CurrentTicket, 
    db: DB, 
    request: Request,
    current_user: CurrentUser
):
    update_data = ticket_data.model_dump(exclude_unset=True)
    logs_to_add = []

    # Intercept changes to track history automatically
    for key, new_value in update_data.items():
        old_value = getattr(ticket, key, None)
        
        # Format enums or complex types cleanly to strings for text storage
        old_str = str(old_value.value if hasattr(old_value, "value") else old_value) if old_value is not None else None
        new_str = str(new_value.value if hasattr(new_value, "value") else new_value) if new_value is not None else None

        if old_str != new_str:
            # Determine activity type mapping based on the field
            activity_type = TicketActivityType.UPDATED
            if key == "status" and ticket_data.status == TicketStatus.DONE:
                activity_type = TicketActivityType.CLOSED
            elif key == "status" and ticket_data.status == TicketStatus.REOPENED:
                activity_type = TicketActivityType.REOPENED
            elif key == "assignee_id":
                activity_type = TicketActivityType.ASSIGNED

            logs_to_add.append(
                TicketActivityLog(
                    ticket_id=ticket.id,
                    user_id=current_user.id,
                    activity_type=activity_type,
                    field_changed=key,
                    old_value=old_str,
                    new_value=new_str
                )
            )
        
        # Apply the mutation to the model instance
        setattr(ticket, key, new_value)

    # Automatically handle completion timestamp if status switched to DONE
    if "status" in update_data and update_data["status"] == TicketStatus.DONE:
        ticket.resolved_at = datetime.now(timezone.utc).replace(tzinfo=None)

    # If any fields changed, stage the audit logs to the transaction session
    if logs_to_add:
        db.add_all(logs_to_add)

    await db.commit()
    await db.refresh(ticket)
    
    # Clean up both ticket cache and the read list of its activities
    await _invalidate_ticket_cache(ticket.id)
    await RedisCache.clear_pattern(f"activity_log:list:{ticket.id}:*")

    return ApiSuccessResponse[TicketResponse](
        message="Ticket updated successfully", 
        data=TicketResponse.model_validate(ticket)
    )
@router.delete("/{ticket_id}", response_model=ApiSuccessResponse[None])
@TICKET_RATE_LIMIT
async def delete_ticket(ticket: CurrentTicket, db: DB, request: Request, _ = Depends(get_current_active_superuser)):
    await db.delete(ticket)
    await db.commit()
    await _invalidate_ticket_cache(ticket.id)
    return ApiSuccessResponse[None](message="Ticket deleted successfully", data=None)