from __future__ import annotations

from datetime import datetime, date
from typing import Optional, TYPE_CHECKING, List
from sqlalchemy import ForeignKey, String, Date, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.mixins import TimestampMixin
from src.db.base import Base
from src.core.enums import ProjectStatus, ProjectHealth

if TYPE_CHECKING:
    from src.apps.iam.models.user import User
    from .milestone import Milestone
    from ...ticket.models.ticket import Ticket
    from ...ticket.models.task import Task


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[Optional[int]] = mapped_column(primary_key=True, default=None, nullable=False)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenant.id", ondelete="CASCADE"), index=True)
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), default=None, index=True)
    
    name: Mapped[str] = mapped_column(String(150), index=True)
    description: Mapped[str] = mapped_column(String(2000))
    budget_notes: Mapped[str] = mapped_column(String(2000), default="")
    
    start_date: Mapped[Optional[date]] = mapped_column(Date, default=None)
    target_end_date: Mapped[Optional[date]] = mapped_column(Date, default=None)
    
    status: Mapped[ProjectStatus] = mapped_column(Enum(ProjectStatus, name="projectstatus", create_type=False), default=ProjectStatus.PLANNING)
    health: Mapped[ProjectHealth] = mapped_column(Enum(ProjectHealth, name="projecthealth", create_type=False), default=ProjectHealth.HEALTHY)

    # ORM Relationships
    owner: Mapped[Optional[User]] = relationship(back_populates="owned_projects", passive_deletes=True)
    milestones: Mapped[List[Milestone]] = relationship(back_populates="project", cascade="all, delete-orphan", passive_deletes=True)
    tickets: Mapped[List[Ticket]] = relationship(back_populates="project", cascade="all, delete-orphan", passive_deletes=True)
    tasks: Mapped[List[Task]] = relationship(back_populates="project", cascade="all, delete-orphan", passive_deletes=True)