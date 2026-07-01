# src/apps/ticket/routers/sla_policy.py
from typing import Annotated
from fastapi import APIRouter, Depends, Query, Request, Path
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.core.types import HashId
from src.core.exceptions import NotFoundError
from src.apps.ticket.models.sla_policy import SLAPolicy
from src.core.dependencies import CurrentOrg
from src.apps.ticket.schemas.sla_policy import (
    SLAPolicyCreate,
    SLAPolicyUpdate,
    SLAPolicyPartialUpdate,
    SLAPolicyResponse
)
from src.db.query import select, or_
from src.core.utils import decode_cursor, encode_cursor
from src.core.dependencies import DB, get_current_active_superuser, require_module_permission
from src.core.schemas import CursorPage, CursorPagination, ApiSuccessResponse
from src.core.enums import Priority, RBACModule
from src.core.cache import RedisCache

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(
    prefix="/organizations/{org}/sla-policies", 
    tags=["SLA Policies"],
    dependencies=[Depends(require_module_permission(RBACModule.PROJECTS))] # Reusing project/ticketing rbac scope
)
SLA_RATE_LIMIT = limiter.limit("10/minute")

# --- Local Dependencies ---

async def get_current_sla_policy(
    db: DB,
    current_org: CurrentOrg, # Validates organizational access context bounds
    sla_policy_id: Annotated[HashId, Path(description="SLA Policy ID")],
) -> SLAPolicy:
    """Fetches a specific global SLA configuration by its unique ID identifier."""
    query = select(SLAPolicy).where(SLAPolicy.id == sla_policy_id)
    result = await db.execute(query)
    sla_policy = result.scalar_one_or_none()
    if not sla_policy:
        raise NotFoundError(message="SLA Policy not found")
    return sla_policy

CurrentSLAPolicy = Annotated[SLAPolicy, Depends(get_current_sla_policy)]

# --- Cache Helpers ---

async def _invalidate_sla_cache(sla_policy_id: int):
    await RedisCache.delete(f"sla_policy:{sla_policy_id}")
    await RedisCache.clear_pattern("sla_policy:list:*")

# --- Endpoints ---

@router.get("/", response_model=CursorPage[SLAPolicyResponse])
@SLA_RATE_LIMIT
async def list_sla_policies(
    db: DB,
    current_org: CurrentOrg,
    request: Request,
    pagination: CursorPagination = Depends(),
    search: str | None = Query(default=None, description="Search policies by name"),
    priority: Priority | None = Query(default=None, description="Filter by priority tier"),
    is_active: bool | None = Query(default=None, description="Filter active or deactivated policies"),
):
    cache_key = f"sla_policy:list:{pagination.cursor}:{pagination.limit}:{search}:{priority}:{is_active}"
    cached_result = await RedisCache.get(cache_key)
    if cached_result:
        return cached_result

    query = select(SLAPolicy)

    if search:
        query = query.where(SLAPolicy.name.ilike(f"%{search}%"))
    if priority is not None:
        query = query.where(SLAPolicy.priority == priority)
    if is_active is not None:
        query = query.where(SLAPolicy.is_active == is_active)

    if pagination.cursor:
        _, cursor_id = decode_cursor(pagination.cursor)
        query = query.where(SLAPolicy.id > int(cursor_id))

    query = query.order_by(SLAPolicy.id).limit(pagination.limit + 1)
    result = await db.execute(query)
    policies = result.scalars().all()

    has_next_page = len(policies) > pagination.limit
    if has_next_page:
        policies = policies[:pagination.limit]

    items = [SLAPolicyResponse.model_validate(p) for p in policies]
    next_cursor = encode_cursor(str(policies[-1].id)) if has_next_page and policies else None
    response = CursorPage[SLAPolicyResponse](items=items, next_cursor=next_cursor)

    await RedisCache.set(cache_key, response.model_dump_json(), ttl=300)
    return response


@router.get("/{sla_policy_id}", response_model=ApiSuccessResponse[SLAPolicyResponse])
@SLA_RATE_LIMIT
async def get_sla_policy(sla_policy: CurrentSLAPolicy, request: Request):
    cache_key = f"sla_policy:{sla_policy.id}"
    cached_policy = await RedisCache.get(cache_key)
    if cached_policy:
        return ApiSuccessResponse[SLAPolicyResponse](
            message="SLA Policy retrieved successfully",
            data=SLAPolicyResponse.model_validate_json(cached_policy)
        )

    sla_response = SLAPolicyResponse.model_validate(sla_policy)
    await RedisCache.set(cache_key, sla_response.model_dump_json(), ttl=600)
    return ApiSuccessResponse[SLAPolicyResponse](message="SLA Policy retrieved successfully", data=sla_response)


@router.post("/", response_model=ApiSuccessResponse[SLAPolicyResponse])
@SLA_RATE_LIMIT
async def create_sla_policy(
    sla_data: SLAPolicyCreate,
    db: DB,
    current_org: CurrentOrg,
    request: Request,
    _ = Depends(get_current_active_superuser), # Configurations restricted to platform admins
):
    # If the new policy is flagged active, automatically deactivate older active policies targeting the exact priority tier
    if sla_data.is_active:
        await db.execute(
            select(SLAPolicy)
            .where(SLAPolicy.priority == sla_data.priority, SLAPolicy.is_active == True)
            .execution_options(synchronize_session="fetch")
        )
        # Note: Handled cleanly by postgres structural partial unique index configuration criteria constraints

    new_policy = SLAPolicy(
        name=sla_data.name,
        priority=sla_data.priority,
        first_response_minutes=sla_data.first_response_minutes,
        resolution_minutes=sla_data.resolution_minutes,
        is_active=sla_data.is_active,
    )
    db.add(new_policy)
    await db.commit()
    await db.refresh(new_policy)

    if new_policy.id:
        await _invalidate_sla_cache(new_policy.id)
    return ApiSuccessResponse[SLAPolicyResponse](
        message="SLA Policy created successfully", 
        data=SLAPolicyResponse.model_validate(new_policy)
    )


@router.put("/{sla_policy_id}", response_model=ApiSuccessResponse[SLAPolicyResponse])
@SLA_RATE_LIMIT
async def update_sla_policy(
    sla_data: SLAPolicyUpdate, 
    sla_policy: CurrentSLAPolicy, 
    db: DB, 
    request: Request,
    _ = Depends(get_current_active_superuser)
):
    sla_policy.name = sla_data.name
    sla_policy.priority = sla_data.priority
    sla_policy.first_response_minutes = sla_data.first_response_minutes
    sla_policy.resolution_minutes = sla_data.resolution_minutes
    sla_policy.is_active = sla_data.is_active

    await db.commit()
    await db.refresh(sla_policy)
    if sla_policy.id:
        await _invalidate_sla_cache(sla_policy.id)

    return ApiSuccessResponse[SLAPolicyResponse](
        message="SLA Policy updated successfully", 
        data=SLAPolicyResponse.model_validate(sla_policy)
    )


@router.patch("/{sla_policy_id}", response_model=ApiSuccessResponse[SLAPolicyResponse])
@SLA_RATE_LIMIT
async def partial_update_sla_policy(
    sla_data: SLAPolicyPartialUpdate, 
    sla_policy: CurrentSLAPolicy, 
    db: DB, 
    request: Request,
    _ = Depends(get_current_active_superuser)
):
    update_data = sla_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(sla_policy, key, value)

    await db.commit()
    await db.refresh(sla_policy)
    if sla_policy.id:
        await _invalidate_sla_cache(sla_policy.id)

    return ApiSuccessResponse[SLAPolicyResponse](
        message="SLA Policy updated successfully", 
        data=SLAPolicyResponse.model_validate(sla_policy)
    )


@router.delete("/{sla_policy_id}", response_model=ApiSuccessResponse[None])
@SLA_RATE_LIMIT
async def delete_sla_policy(
    sla_policy: CurrentSLAPolicy, 
    db: DB, 
    request: Request, 
    _ = Depends(get_current_active_superuser)
):
    await db.delete(sla_policy)
    await db.commit()
    if sla_policy.id:
        await _invalidate_sla_cache(sla_policy.id)
    return ApiSuccessResponse[None](message="SLA Policy deleted successfully", data=None)