# src/apps/projects/schemas/milestone.py
from __future__ import annotations
from datetime import date, datetime
from src.core.enums import MilestoneStatus
from src.core.schemas import BaseSchema
from src.core.types import HashId

class MilestoneBase(BaseSchema):
    title: str
    description: str | None = None
    planned_date: date | None = None
    due_date: date | None = None


class MilestoneCreate(MilestoneBase):
    owner_id: HashId | None = None
    status: MilestoneStatus = MilestoneStatus.DRAFT
    sorted_order: int | None = 0


class MilestoneUpdate(MilestoneBase):
    owner_id: HashId | None = None
    status: MilestoneStatus | None = None
    progress: float | None = None
    sorted_order: int | None = None
    completed_at: datetime | None = None


class MilestonePartialUpdate(BaseSchema):
    title: str | None = None
    description: str | None = None
    planned_date: date | None = None
    due_date: date | None = None
    owner_id: HashId | None = None
    status: MilestoneStatus | None = None
    progress: float | None = None
    sorted_order: int | None = None
    completed_at: datetime | None = None


class MilestoneResponse(MilestoneBase):
    id: HashId
    project_id: HashId
    owner_id: HashId | None = None
    status: MilestoneStatus
    progress: float
    sorted_order: int
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime