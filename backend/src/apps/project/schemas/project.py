from __future__ import annotations

from datetime import date

from src.core.enums import ProjectHealth, ProjectStatus
from src.core.schemas import BaseSchema
from src.core.types import HashId


class ProjectBase(BaseSchema):
    name: str
    description: str | None = None
    budget_notes: str | None = None

    start_date: date | None = None
    target_end_date: date | None = None


class ProjectCreate(ProjectBase):
    owner_id: HashId | None = None
    status: ProjectStatus = ProjectStatus.PLANNING
    health: ProjectHealth = ProjectHealth.HEALTHY


class ProjectUpdate(ProjectBase):
    owner_id: HashId | None = None
    status: ProjectStatus | None = None
    health: ProjectHealth | None = None


class ProjectPartialUpdate(BaseSchema):
    name: str | None = None
    description: str | None = None
    budget_notes: str | None = None

    owner_id: HashId | None = None

    start_date: date | None = None
    target_end_date: date | None = None

    status: ProjectStatus | None = None
    health: ProjectHealth | None = None


class ProjectStatusUpdate(BaseSchema):
    status: ProjectStatus


class ProjectHealthUpdate(BaseSchema):
    health: ProjectHealth


class ProjectOwnerUpdate(BaseSchema):
    owner_id: HashId | None = None


class ProjectResponse(ProjectBase):
    id: HashId
    owner_id: HashId | None = None

    status: ProjectStatus
    health: ProjectHealth