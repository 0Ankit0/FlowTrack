from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any, Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from .enums import (
    MilestoneStatus,
    ProjectHealth,
    ProjectStatus,
    ReleaseStatus,
    ReleaseType,
    TaskStatus,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


class Project(SQLModel, table=True):
    __tablename__ = "flowtrack_projects"

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenant.id", index=True)
    owner_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    name: str = Field(max_length=150, index=True)
    description: str = Field(default="", max_length=2000)
    status: ProjectStatus = Field(default=ProjectStatus.DRAFT)
    health: ProjectHealth = Field(default=ProjectHealth.GREEN)
    start_date: Optional[date] = Field(default=None)
    target_end_date: Optional[date] = Field(default=None)
    budget_notes: str = Field(default="", max_length=2000)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Milestone(SQLModel, table=True):
    __tablename__ = "flowtrack_milestones"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="flowtrack_projects.id", index=True)
    owner_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    name: str = Field(max_length=150, index=True)
    status: MilestoneStatus = Field(default=MilestoneStatus.DRAFT)
    planned_date: date
    forecast_date: Optional[date] = Field(default=None)
    baseline_date: Optional[date] = Field(default=None)
    dependency_ids: list[int] = Field(default_factory=list, sa_column=Column(JSON))
    completion_criteria: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Task(SQLModel, table=True):
    __tablename__ = "flowtrack_tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="flowtrack_projects.id", index=True)
    milestone_id: Optional[int] = Field(
        default=None, foreign_key="flowtrack_milestones.id", index=True
    )
    parent_task_id: Optional[int] = Field(default=None, foreign_key="flowtrack_tasks.id")
    assignee_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    linked_ticket_id: Optional[int] = Field(
        default=None, foreign_key="flowtrack_tickets.id", index=True
    )
    title: str = Field(max_length=150, index=True)
    description: str = Field(default="", max_length=2000)
    status: TaskStatus = Field(default=TaskStatus.TODO)
    due_date: Optional[date] = Field(default=None)
    extra_data: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Release(SQLModel, table=True):
    __tablename__ = "flowtrack_releases"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="flowtrack_projects.id", index=True)
    milestone_id: Optional[int] = Field(
        default=None, foreign_key="flowtrack_milestones.id", index=True
    )
    owner_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    version: str = Field(max_length=80, index=True)
    status: ReleaseStatus = Field(default=ReleaseStatus.PLANNED)
    release_type: ReleaseType = Field(default=ReleaseType.PLANNED)
    planned_at: Optional[datetime] = Field(default=None)
    deployed_at: Optional[datetime] = Field(default=None)
    ticket_ids: list[int] = Field(default_factory=list, sa_column=Column(JSON))
    task_ids: list[int] = Field(default_factory=list, sa_column=Column(JSON))
    notes: str = Field(default="", max_length=4000)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
