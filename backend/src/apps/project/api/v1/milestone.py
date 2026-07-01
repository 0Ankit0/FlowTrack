# src/apps/projects/routers/milestone.py
from typing import Annotated
from fastapi import APIRouter, Depends, Query, Request, Path
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.core.types import HashId
from src.apps.iam.models.user import User
from src.core.exceptions import NotFoundError
from src.apps.project.models.milestone import Milestone
from src.core.dependencies import CurrentProject, CurrentMilestone 
from src.apps.project.schemas.milestone import (
    MilestoneCreate,
    MilestoneUpdate,
    MilestonePartialUpdate,
    MilestoneResponse
)
from src.db.query import select, or_
from src.core.utils import decode_cursor, encode_cursor
from src.core.dependencies import DB, get_current_active_superuser, require_module_permission
from src.core.schemas import CursorPage, CursorPagination, ApiSuccessResponse
from src.core.enums import MilestoneStatus, RBACModule
from src.core.cache import RedisCache

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(
    prefix="/organizations/{org}/projects/{project_id}/milestones", 
    tags=["Milestones"],
    dependencies=[Depends(require_module_permission(RBACModule.PROJECTS))]
)
MILESTONE_RATE_LIMIT = limiter.limit("10/minute")


# --- Cache Helpers ---

async def _invalidate_milestone_cache(milestone_id: int):
    await RedisCache.delete(f"milestone:{milestone_id}")
    await RedisCache.clear_pattern(f"milestone:{milestone_id}:*")

# --- Endpoints ---

@router.get("/", response_model=CursorPage[MilestoneResponse])
@MILESTONE_RATE_LIMIT
async def list_milestones(
    db: DB,
    current_project: CurrentProject,
    request: Request,
    pagination: CursorPagination = Depends(),
    search: str | None = Query(default=None, description="Search by title or description"),
    milestone_status: MilestoneStatus | None = Query(default=None, description="Filter milestones by status"),
):
    cache_key = f"milestone:list:{current_project.id}:{pagination.cursor}:{pagination.limit}:{search}:{milestone_status}"
    cached_result = await RedisCache.get(cache_key)
    if cached_result:
        return cached_result

    query = select(Milestone).where(Milestone.project_id == current_project.id)

    if search:
        search_term = f"%{search}%"
        query = query.where(or_(Milestone.title.ilike(search_term), Milestone.description.ilike(search_term)))
        
    if milestone_status is not None:
        query = query.where(Milestone.status == milestone_status)

    if pagination.cursor:
        _, cursor_id = decode_cursor(pagination.cursor)
        query = query.where(Milestone.id > int(cursor_id))

    query = query.order_by(Milestone.sorted_order, Milestone.id).limit(pagination.limit + 1)
    result = await db.execute(query)
    milestones = result.scalars().all()

    has_next_page = len(milestones) > pagination.limit
    if has_next_page:
        milestones = milestones[:pagination.limit]

    items = [MilestoneResponse.model_validate(m) for m in milestones]
    next_cursor = encode_cursor(str(milestones[-1].id)) if has_next_page and milestones else None
    response = CursorPage[MilestoneResponse](items=items, next_cursor=next_cursor)

    await RedisCache.set(cache_key, response.model_dump_json(), ttl=120)
    return response


@router.get("/{milestone_id}", response_model=ApiSuccessResponse[MilestoneResponse])
@MILESTONE_RATE_LIMIT
async def get_milestone(milestone: CurrentMilestone, request: Request):
    cache_key = f"milestone:{milestone.id}"
    cached_m = await RedisCache.get(cache_key)
    if cached_m:
        return ApiSuccessResponse[MilestoneResponse](
            message="Milestone retrieved successfully",
            data=MilestoneResponse.model_validate_json(cached_m)
        )

    m_response = MilestoneResponse.model_validate(milestone)
    await RedisCache.set(cache_key, m_response.model_dump_json(), ttl=300)
    return ApiSuccessResponse[MilestoneResponse](message="Milestone retrieved successfully", data=m_response)


@router.post("/", response_model=ApiSuccessResponse[MilestoneResponse])
@MILESTONE_RATE_LIMIT
async def create_milestone(
    milestone_data: MilestoneCreate,
    db: DB,
    current_project: CurrentProject,
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_superuser)],
):
    new_milestone = Milestone(
        project_id=current_project.id,
        owner_id=milestone_data.owner_id or current_user.id,
        title=milestone_data.title,
        description=milestone_data.description,
        status=milestone_data.status,
        planned_date=milestone_data.planned_date,
        due_date=milestone_data.due_date,
        sorted_order=milestone_data.sorted_order,
        progress=0.0
    )
    db.add(new_milestone)
    await db.commit()
    await db.refresh(new_milestone)

    if new_milestone.id:
        await _invalidate_milestone_cache(new_milestone.id)
    return ApiSuccessResponse[MilestoneResponse](message="Milestone created successfully", data=MilestoneResponse.model_validate(new_milestone))


@router.put("/{milestone_id}", response_model=ApiSuccessResponse[MilestoneResponse])
@MILESTONE_RATE_LIMIT
async def update_milestone(milestone_data: MilestoneUpdate, milestone: CurrentMilestone, db: DB, request: Request):
    milestone.title = milestone_data.title
    milestone.description = milestone_data.description
    milestone.planned_date = milestone_data.planned_date
    milestone.due_date = milestone_data.due_date
    
    if milestone_data.status is not None:
        milestone.status = milestone_data.status
    if milestone_data.owner_id is not None:
        milestone.owner_id = milestone_data.owner_id
    if milestone_data.progress is not None:
        milestone.progress = milestone_data.progress
    if milestone_data.sorted_order is not None:
        milestone.sorted_order = milestone_data.sorted_order
    if milestone_data.completed_at is not None:
        milestone.completed_at = milestone_data.completed_at

    await db.commit()
    await db.refresh(milestone)
    if milestone.id:
        await _invalidate_milestone_cache(milestone.id)

    return ApiSuccessResponse[MilestoneResponse](message="Milestone updated successfully", data=MilestoneResponse.model_validate(milestone))


@router.patch("/{milestone_id}", response_model=ApiSuccessResponse[MilestoneResponse])
@MILESTONE_RATE_LIMIT
async def partial_update_milestone(milestone_data: MilestonePartialUpdate, milestone: CurrentMilestone, db: DB, request: Request):
    update_data = milestone_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(milestone, key, value)

    await db.commit()
    await db.refresh(milestone)
    if milestone.id:
        await _invalidate_milestone_cache(milestone.id)

    return ApiSuccessResponse[MilestoneResponse](message="Milestone updated successfully", data=MilestoneResponse.model_validate(milestone))


@router.delete("/{milestone_id}", response_model=ApiSuccessResponse[None])
@MILESTONE_RATE_LIMIT
async def delete_milestone(milestone: CurrentMilestone, db: DB, request: Request, _ = Depends(get_current_active_superuser)):
    await db.delete(milestone)
    await db.commit()
    if milestone.id:
        await _invalidate_milestone_cache(milestone.id)
    return ApiSuccessResponse[None](message="Milestone deleted successfully", data=None)