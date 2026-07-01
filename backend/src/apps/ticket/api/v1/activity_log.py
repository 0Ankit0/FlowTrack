# src/apps/ticket/routers/activity_log.py
from typing import Annotated
from fastapi import APIRouter, Depends, Query, Request, Path
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.core.types import HashId
from src.core.exceptions import NotFoundError
from src.apps.ticket.models.activity_log import TicketActivityLog
from src.apps.ticket.api.v1.ticket import CurrentTicket
from src.apps.ticket.schemas.activity_log import TicketActivityLogResponse
from src.db.query import select
from src.core.utils import decode_cursor, encode_cursor
from src.core.dependencies import DB, require_module_permission
from src.core.schemas import CursorPage, CursorPagination, ApiSuccessResponse
from src.core.enums import RBACModule, TicketActivityType
from src.core.cache import RedisCache

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(
    prefix="/organizations/{org}/projects/{project_id}/tickets/{ticket_id}/activities", 
    tags=["Ticket Activity Logs"],
    dependencies=[Depends(require_module_permission(RBACModule.PROJECTS))]
)
ACTIVITY_RATE_LIMIT = limiter.limit("30/minute")

@router.get("/", response_model=CursorPage[TicketActivityLogResponse])
@ACTIVITY_RATE_LIMIT
async def list_activity_logs(
    db: DB,
    current_ticket: CurrentTicket,
    request: Request,
    pagination: CursorPagination = Depends(),
    activity_type: TicketActivityType | None = Query(default=None),
    field_changed: str | None = Query(default=None),
):
    cache_key = f"activity_log:list:{current_ticket.id}:{pagination.cursor}:{pagination.limit}:{activity_type}:{field_changed}"
    cached_result = await RedisCache.get(cache_key)
    if cached_result:
        return cached_result

    query = select(TicketActivityLog).where(TicketActivityLog.ticket_id == current_ticket.id)

    if activity_type:
        query = query.where(TicketActivityLog.activity_type == activity_type)
    if field_changed:
        query = query.where(TicketActivityLog.field_changed == field_changed)

    if pagination.cursor:
        _, cursor_id = decode_cursor(pagination.cursor)
        query = query.where(TicketActivityLog.id > int(cursor_id))

    query = query.order_by(TicketActivityLog.id).limit(pagination.limit + 1)
    result = await db.execute(query)
    logs = result.scalars().all()

    has_next_page = len(logs) > pagination.limit
    if has_next_page:
        logs = logs[:pagination.limit]

    items = [TicketActivityLogResponse.model_validate(l) for l in logs]
    next_cursor = encode_cursor(str(logs[-1].id)) if has_next_page and logs else None
    response = CursorPage[TicketActivityLogResponse](items=items, next_cursor=next_cursor)

    await RedisCache.set(cache_key, response.model_dump_json(), ttl=30)
    return response


@router.get("/{activity_log_id}", response_model=ApiSuccessResponse[TicketActivityLogResponse])
@ACTIVITY_RATE_LIMIT
async def get_activity_log(
    db: DB,
    current_ticket: CurrentTicket,
    activity_log_id: Annotated[HashId, Path()],
    request: Request
):
    query = select(TicketActivityLog).where(
        TicketActivityLog.id == activity_log_id,
        TicketActivityLog.ticket_id == current_ticket.id
    )
    result = await db.execute(query)
    activity_log = result.scalar_one_or_none()
    if not activity_log:
        raise NotFoundError(message="Activity log entry not found")

    return ApiSuccessResponse[TicketActivityLogResponse](
        message="Activity log entry retrieved successfully", 
        data=TicketActivityLogResponse.model_validate(activity_log)
    )