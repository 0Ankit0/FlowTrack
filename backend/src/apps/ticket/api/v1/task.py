# src/apps/projects/routers/task.py
from typing import Annotated
from fastapi import APIRouter, Depends, Query, Request, Path
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.core.types import HashId
from src.apps.iam.models.user import User
from src.core.exceptions import NotFoundError
from src.apps.ticket.models.task import Task
from src.core.dependencies import CurrentProject
from src.apps.ticket.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskPartialUpdate,
    TaskResponse
)
from src.db.query import select, or_
from src.core.utils import decode_cursor, encode_cursor
from src.core.dependencies import DB, get_current_active_superuser, require_module_permission
from src.core.schemas import CursorPage, CursorPagination, ApiSuccessResponse
from src.core.enums import TaskStatus, Priority, RBACModule
from src.core.cache import RedisCache

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(
    prefix="/organizations/{org}/projects/{project_id}/tasks", 
    tags=["Tasks"],
    dependencies=[Depends(require_module_permission(RBACModule.PROJECTS))]
)
TASK_RATE_LIMIT = limiter.limit("15/minute")

# --- Local Dependencies ---

async def get_current_task(
    db: DB,
    current_project: CurrentProject,
    task_id: Annotated[HashId, Path(description="Task ID")],
) -> Task:
    """Fetches a specific task, confirming validation down through the active project context."""
    query = select(Task).where(
        Task.id == task_id,
        Task.project_id == current_project.id
    )
    result = await db.execute(query)
    task = result.scalar_one_or_none()
    if not task:
        raise NotFoundError(message="Task not found")
    return task

CurrentTask = Annotated[Task, Depends(get_current_task)]

# --- Cache Helpers ---

async def _invalidate_task_cache(task_id: int):
    await RedisCache.delete(f"task:{task_id}")
    await RedisCache.clear_pattern(f"task:{task_id}:*")

# --- Endpoints ---

@router.get("/", response_model=CursorPage[TaskResponse])
@TASK_RATE_LIMIT
async def list_tasks(
    db: DB,
    current_project: CurrentProject,
    request: Request,
    pagination: CursorPagination = Depends(),
    search: str | None = Query(default=None, description="Search by title or description"),
    status: TaskStatus | None = Query(default=None, description="Filter by task status"),
    priority: Priority | None = Query(default=None, description="Filter by task priority"),
    assignee_id: HashId | None = Query(default=None, description="Filter by assigned user"),
    milestone_id: HashId | None = Query(default=None, description="Filter by specific milestone resource"),
    parent_task_id: HashId | None = Query(default=None, description="Filter subtasks belonging to a parent task id"),
):
    cache_key = (
        f"task:list:{current_project.id}:{pagination.cursor}:{pagination.limit}:"
        f"{search}:{status}:{priority}:{assignee_id}:{milestone_id}:{parent_task_id}"
    )
    cached_result = await RedisCache.get(cache_key)
    if cached_result:
        return cached_result

    query = select(Task).where(Task.project_id == current_project.id)

    if search:
        search_term = f"%{search}%"
        query = query.where(or_(Task.title.ilike(search_term), Task.description.ilike(search_term)))
    if status is not None:
        query = query.where(Task.status == status)
    if priority is not None:
        query = query.where(Task.priority == priority)
    if assignee_id is not None:
        query = query.where(Task.assignee_id == assignee_id)
    if milestone_id is not None:
        query = query.where(Task.milestone_id == milestone_id)
    if parent_task_id is not None:
        query = query.where(Task.parent_task_id == parent_task_id)

    if pagination.cursor:
        _, cursor_id = decode_cursor(pagination.cursor)
        query = query.where(Task.id > int(cursor_id))

    query = query.order_by(Task.sort_order, Task.id).limit(pagination.limit + 1)
    result = await db.execute(query)
    tasks = result.scalars().all()

    has_next_page = len(tasks) > pagination.limit
    if has_next_page:
        tasks = tasks[:pagination.limit]

    items = [TaskResponse.model_validate(t) for t in tasks]
    next_cursor = encode_cursor(tasks[-1].id) if has_next_page and tasks else None
    response = CursorPage[TaskResponse](items=items, next_cursor=next_cursor)

    await RedisCache.set(cache_key, response.model_dump_json(), ttl=60)
    return response


@router.get("/{task_id}", response_model=ApiSuccessResponse[TaskResponse])
@TASK_RATE_LIMIT
async def get_task(task: CurrentTask, request: Request):
    cache_key = f"task:{task.id}"
    cached_task = await RedisCache.get(cache_key)
    if cached_task:
        return ApiSuccessResponse[TaskResponse](
            message="Task retrieved successfully",
            data=TaskResponse.model_validate_json(cached_task)
        )

    task_response = TaskResponse.model_validate(task)
    await RedisCache.set(cache_key, task_response.model_dump_json(), ttl=300)
    return ApiSuccessResponse[TaskResponse](message="Task retrieved successfully", data=task_response)


@router.post("/", response_model=ApiSuccessResponse[TaskResponse])
@TASK_RATE_LIMIT
async def create_task(
    task_data: TaskCreate,
    db: DB,
    current_project: CurrentProject,
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_superuser)],
):
    new_task = Task(
        project_id=current_project.id,
        milestone_id=task_data.milestone_id,
        parent_task_id=task_data.parent_task_id,
        owner_id=task_data.owner_id or current_user.id,
        assignee_id=task_data.assignee_id,
        title=task_data.title,
        description=task_data.description,
        status=task_data.status,
        priority=task_data.priority,
        planned_start_date=task_data.planned_start_date,
        due_date=task_data.due_date,
        estimated_hours=task_data.estimated_hours,
        actual_hours=task_data.actual_hours,
        sort_order=task_data.sort_order,
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    await _invalidate_task_cache(new_task.id)
    return ApiSuccessResponse[TaskResponse](message="Task created successfully", data=TaskResponse.model_validate(new_task))


@router.put("/{task_id}", response_model=ApiSuccessResponse[TaskResponse])
@TASK_RATE_LIMIT
async def update_task(task_data: TaskUpdate, task: CurrentTask, db: DB, request: Request):
    task.title = task_data.title
    task.description = task_data.description
    task.status = task_data.status
    task.priority = task_data.priority
    task.planned_start_date = task_data.planned_start_date
    task.due_date = task_data.due_date
    task.estimated_hours = task_data.estimated_hours
    task.actual_hours = task_data.actual_hours
    task.sort_order = task_data.sort_order
    task.milestone_id = task_data.milestone_id
    task.parent_task_id = task_data.parent_task_id
    task.assignee_id = task_data.assignee_id
    task.owner_id = task_data.owner_id
    task.completed_at = task_data.completed_at

    await db.commit()
    await db.refresh(task)
    await _invalidate_task_cache(task.id)

    return ApiSuccessResponse[TaskResponse](message="Task updated successfully", data=TaskResponse.model_validate(task))


@router.patch("/{task_id}", response_model=ApiSuccessResponse[TaskResponse])
@TASK_RATE_LIMIT
async def partial_update_task(task_data: TaskPartialUpdate, task: CurrentTask, db: DB, request: Request):
    update_data = task_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)

    # Automatically handle fallback systems if task updates to a terminal 'DONE' metadata type status
    if "status" in update_data and getattr(update_data["status"], "value", None) in ("done", "completed"):
        from datetime import datetime, timezone
        task.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)

    await db.commit()
    await db.refresh(task)
    await _invalidate_task_cache(task.id)

    return ApiSuccessResponse[TaskResponse](message="Task updated successfully", data=TaskResponse.model_validate(task))


@router.delete("/{task_id}", response_model=ApiSuccessResponse[None])
@TASK_RATE_LIMIT
async def delete_task(task: CurrentTask, db: DB, request: Request, _ = Depends(get_current_active_superuser)):
    await db.delete(task)
    await db.commit()
    await _invalidate_task_cache(task.id)
    return ApiSuccessResponse[None](message="Task deleted successfully", data=None)