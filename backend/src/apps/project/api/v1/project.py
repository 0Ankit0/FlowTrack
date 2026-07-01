# src/apps/projects/routers/project.py
from typing import Annotated
from fastapi import APIRouter, Depends, Query, Request, Path
from slugify import slugify
from slowapi import Limiter
from slowapi.util import get_remote_address
from src.core.dependencies import CurrentProject
from src.core.types import HashId
from src.apps.iam.models.user import User
from src.core.exceptions import NotFoundError
from src.apps.project.models.project import Project
from src.core.dependencies import CurrentOrg 
from src.apps.project.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectPartialUpdate,
    ProjectResponse
)
from src.db.query import select, or_
from src.core.utils import decode_cursor, encode_cursor
from src.core.dependencies import DB, get_current_active_superuser, require_module_permission
from src.core.schemas import CursorPage, CursorPagination, ApiSuccessResponse
from src.core.enums import ProjectStatus, RBACModule
from src.core.cache import RedisCache

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(
    prefix="/organizations/{org}/projects", 
    tags=["Projects"],
    dependencies=[Depends(require_module_permission(RBACModule.PROJECTS))]
)
PROJECT_RATE_LIMIT = limiter.limit("10/minute")

# --- Cache Helpers ---

async def _invalidate_project_cache(project_id: int):
    await RedisCache.delete(f"project:{project_id}")
    await RedisCache.clear_pattern(f"project:{project_id}:*")

# --- Endpoints ---

@router.get("/", response_model=CursorPage[ProjectResponse])
@PROJECT_RATE_LIMIT
async def list_projects(
    db: DB,
    current_org: CurrentOrg,
    request: Request,
    pagination: CursorPagination = Depends(),
    search: str | None = Query(default=None, description="Search term to filter projects by name or description"),
    project_status: ProjectStatus | None = Query(default=None, description="Filter projects by status"),
):
    cache_key = f"project:list:{current_org.id if current_org else 'global'}:{pagination.cursor}:{pagination.limit}:{search}"
    cached_result = await RedisCache.get(cache_key)
    if cached_result:
        return cached_result
   
    query = select(Project)
    if current_org:
        query = query.where(Project.organization_id == current_org.id)

    if search:
        search_term = f"%{search}%"
        query = query.where(or_(Project.name.ilike(search_term), Project.description.ilike(search_term)))
        
    if project_status is not None:
        query = query.where(Project.status == project_status)

    if pagination.cursor:
        _, cursor_id = decode_cursor(pagination.cursor)
        query = query.where(Project.id > int(cursor_id))

    query = query.order_by(Project.id).limit(pagination.limit + 1)
    result = await db.execute(query)
    projects = result.scalars().all()

    has_next_page = len(projects) > pagination.limit
    if has_next_page:
        projects = projects[:pagination.limit]

    items = [ProjectResponse.model_validate(proj) for proj in projects]
    next_cursor = encode_cursor(str(projects[-1].id)) if has_next_page and projects else None
    response = CursorPage[ProjectResponse](items=items, next_cursor=next_cursor)

    await RedisCache.set(cache_key, response.model_dump_json(), ttl=120)
    return response


@router.get("/{project_id}", response_model=ApiSuccessResponse[ProjectResponse])
@PROJECT_RATE_LIMIT
async def get_project(project: CurrentProject, request: Request):
    cache_key = f"project:{project.id}"
    cached_proj = await RedisCache.get(cache_key)
    if cached_proj:
        return ApiSuccessResponse[ProjectResponse](
            message="Project retrieved successfully",
            data=ProjectResponse.model_validate_json(cached_proj)
        )

    proj_response = ProjectResponse.model_validate(project)
    await RedisCache.set(cache_key, proj_response.model_dump_json(), ttl=300)
    return ApiSuccessResponse[ProjectResponse](message="Project retrieved successfully", data=proj_response)


@router.post("/", response_model=ApiSuccessResponse[ProjectResponse])
@PROJECT_RATE_LIMIT
async def create_project(
    project_data: ProjectCreate,
    db: DB,
    current_org: CurrentOrg,
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_superuser)],
):
    new_project = Project(
        name=project_data.name,
        slug=slugify(project_data.name),
        description=project_data.description,
        budget_notes=project_data.budget_notes,
        start_date=project_data.start_date,
        target_end_date=project_data.target_end_date,
        status=project_data.status,
        health=project_data.health,
        organization_id=current_org.id if current_org else None,
        owner_id=project_data.owner_id or current_user.id,
        created_by=current_user.id,
    )
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)

    if new_project.id:
        await _invalidate_project_cache(new_project.id)
    return ApiSuccessResponse[ProjectResponse](message="Project created successfully", data=ProjectResponse.model_validate(new_project))


@router.put("/{project_id}", response_model=ApiSuccessResponse[ProjectResponse])
@PROJECT_RATE_LIMIT
async def update_project(
    project_data: ProjectUpdate, 
    project: CurrentProject, 
    db: DB, 
    request: Request
    ):
    project.name = project_data.name
    project.description = project_data.description
    project.budget_notes = project_data.budget_notes
    project.start_date = project_data.start_date
    project.target_end_date = project_data.target_end_date
    
    if project_data.status is not None:
        project.status = project_data.status
    if project_data.health is not None:
        project.health = project_data.health
    if project_data.owner_id is not None:
        project.owner_id = project_data.owner_id

    await db.commit()
    await db.refresh(project)
    if project.id:
        await _invalidate_project_cache(project.id)

    return ApiSuccessResponse[ProjectResponse](message="Project updated successfully", data=ProjectResponse.model_validate(project))


@router.patch("/{project_id}", response_model=ApiSuccessResponse[ProjectResponse])
@PROJECT_RATE_LIMIT
async def partial_update_project(project_data: ProjectPartialUpdate, project: CurrentProject, db: DB, request: Request):
    update_data = project_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)

    await db.commit()
    await db.refresh(project)
    if project.id:
        await _invalidate_project_cache(project.id)

    return ApiSuccessResponse[ProjectResponse](message="Project updated successfully", data=ProjectResponse.model_validate(project))


@router.delete("/{project_id}", response_model=ApiSuccessResponse[None])
@PROJECT_RATE_LIMIT
async def delete_project(project: CurrentProject, db: DB, request: Request, _ = Depends(get_current_active_superuser)):
    await db.delete(project)
    await db.commit()
    if project.id:
        await _invalidate_project_cache(project.id)
    return ApiSuccessResponse[None](message="Project deleted successfully", data=None)