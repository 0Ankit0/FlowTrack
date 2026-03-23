from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, field_serializer

from src.apps.iam.utils.hashid import encode_id

from ..models.enums import (
    MilestoneStatus,
    ProjectHealth,
    ProjectStatus,
    ReleaseStatus,
    ReleaseType,
    TaskStatus,
)


class ProjectCreate(BaseModel):
    tenant_id: str
    owner_id: Optional[str] = None
    name: str
    description: str = ""
    status: ProjectStatus = ProjectStatus.DRAFT
    health: ProjectHealth = ProjectHealth.GREEN
    start_date: Optional[date] = None
    target_end_date: Optional[date] = None
    budget_notes: str = ""


class ProjectRead(BaseModel):
    id: int
    tenant_id: int
    owner_id: Optional[int]
    name: str
    description: str
    status: ProjectStatus
    health: ProjectHealth
    start_date: Optional[date]
    target_end_date: Optional[date]
    budget_notes: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("id", "tenant_id")
    def serialize_ids(self, value: int) -> str:
        return encode_id(value)

    @field_serializer("owner_id")
    def serialize_owner_id(self, value: Optional[int]) -> Optional[str]:
        return encode_id(value) if value is not None else None


class MilestoneCreate(BaseModel):
    name: str
    owner_id: Optional[str] = None
    planned_date: date
    forecast_date: Optional[date] = None
    baseline_date: Optional[date] = None
    dependency_ids: list[str] = []
    completion_criteria: list[str] = []
    status: MilestoneStatus = MilestoneStatus.DRAFT


class MilestoneUpdate(BaseModel):
    name: Optional[str] = None
    owner_id: Optional[str] = None
    planned_date: Optional[date] = None
    forecast_date: Optional[date] = None
    baseline_date: Optional[date] = None
    dependency_ids: Optional[list[str]] = None
    completion_criteria: Optional[list[str]] = None
    status: Optional[MilestoneStatus] = None


class MilestoneRead(BaseModel):
    id: int
    project_id: int
    owner_id: Optional[int]
    name: str
    status: MilestoneStatus
    planned_date: date
    forecast_date: Optional[date]
    baseline_date: Optional[date]
    dependency_ids: list[int]
    completion_criteria: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("id", "project_id")
    def serialize_ids(self, value: int) -> str:
        return encode_id(value)

    @field_serializer("owner_id")
    def serialize_owner_id(self, value: Optional[int]) -> Optional[str]:
        return encode_id(value) if value is not None else None

    @field_serializer("dependency_ids")
    def serialize_dependency_ids(self, value: list[int]) -> list[str]:
        return [encode_id(item) for item in value]


class TaskCreate(BaseModel):
    title: str
    description: str = ""
    assignee_id: Optional[str] = None
    due_date: Optional[date] = None
    linked_ticket_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO


class TaskRead(BaseModel):
    id: int
    project_id: int
    milestone_id: Optional[int]
    parent_task_id: Optional[int]
    assignee_id: Optional[int]
    linked_ticket_id: Optional[int]
    title: str
    description: str
    status: TaskStatus
    due_date: Optional[date]
    extra_data: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("id", "project_id")
    def serialize_project_ids(self, value: int) -> str:
        return encode_id(value)

    @field_serializer("milestone_id", "parent_task_id", "assignee_id", "linked_ticket_id")
    def serialize_optional_ids(self, value: Optional[int]) -> Optional[str]:
        return encode_id(value) if value is not None else None


class ProjectDetailRead(ProjectRead):
    milestones: list[MilestoneRead] = []
    tasks: list[TaskRead] = []
    linked_ticket_count: int = 0
    releases: list["ReleaseRead"] = []


class ReleaseCreate(BaseModel):
    project_id: str
    milestone_id: Optional[str] = None
    owner_id: Optional[str] = None
    version: str
    status: ReleaseStatus = ReleaseStatus.PLANNED
    release_type: ReleaseType = ReleaseType.PLANNED
    planned_at: Optional[datetime] = None
    deployed_at: Optional[datetime] = None
    ticket_ids: list[str] = []
    task_ids: list[str] = []
    notes: str = ""


class ReleaseRead(BaseModel):
    id: int
    project_id: int
    milestone_id: Optional[int]
    owner_id: Optional[int]
    version: str
    status: ReleaseStatus
    release_type: ReleaseType
    planned_at: Optional[datetime]
    deployed_at: Optional[datetime]
    ticket_ids: list[int]
    task_ids: list[int]
    notes: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("id", "project_id")
    def serialize_ids(self, value: int) -> str:
        return encode_id(value)

    @field_serializer("milestone_id", "owner_id")
    def serialize_optional_ids(self, value: Optional[int]) -> Optional[str]:
        return encode_id(value) if value is not None else None

    @field_serializer("ticket_ids", "task_ids")
    def serialize_link_ids(self, values: list[int]) -> list[str]:
        return [encode_id(value) for value in values]
