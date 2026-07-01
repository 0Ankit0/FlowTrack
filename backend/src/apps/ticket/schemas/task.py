# src/apps/projects/schemas/task.py
from __future__ import annotations
from datetime import date, datetime
from src.core.enums import TaskStatus, Priority
from src.core.schemas import BaseSchema
from src.core.types import HashId

class TaskBase(BaseSchema):
    title: str
    description: str | None = None
    status: TaskStatus = TaskStatus.TODO
    priority: Priority = Priority.MEDIUM
    planned_start_date: date | None = None
    due_date: date | None = None
    estimated_hours: int | None = None
    actual_hours: int | None = None
    sort_order: int = 0


class TaskCreate(TaskBase):
    milestone_id: HashId | None = None
    parent_task_id: HashId | None = None
    assignee_id: HashId | None = None
    owner_id: HashId | None = None


class TaskUpdate(TaskBase):
    milestone_id: HashId | None = None
    parent_task_id: HashId | None = None
    assignee_id: HashId | None = None
    owner_id: HashId | None = None
    completed_at: datetime | None = None


class TaskPartialUpdate(BaseSchema):
    title: str | None = None
    description: str | None = None
    status: TaskStatus | None = None
    priority: Priority | None = None
    planned_start_date: date | None = None
    due_date: date | None = None
    estimated_hours: int | None = None
    actual_hours: int | None = None
    sort_order: int | None = None
    milestone_id: HashId | None = None
    parent_task_id: HashId | None = None
    assignee_id: HashId | None = None
    owner_id: HashId | None = None
    completed_at: datetime | None = None


class TaskResponse(TaskBase):
    id: HashId
    project_id: HashId
    milestone_id: HashId | None = None
    parent_task_id: HashId | None = None
    owner_id: HashId | None = None
    assignee_id: HashId | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime