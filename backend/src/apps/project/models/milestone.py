from __future__ import annotations

from datetime import datetime, date
from typing import Optional, TYPE_CHECKING, List
from sqlalchemy import ForeignKey, String, Text, Date, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.mixins import TimestampMixin
from src.core.enums import MilestoneStatus
from src.db.base import Base

if TYPE_CHECKING:
    from .project import Project
    from ...ticket.models.ticket import Ticket
    from ...ticket.models.task import Task


class Milestone(Base, TimestampMixin):
    __tablename__ = "project_milestones"

    id: Mapped[Optional[int]] = mapped_column(primary_key=True, default=None, nullable=False)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), default=None, index=True)
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), default=None, index=True)

    title: Mapped[str] = mapped_column(String(150))
    description: Mapped[Optional[str]] = mapped_column(Text, default=None)
    status: Mapped[MilestoneStatus] = mapped_column()
    planned_date: Mapped[Optional[date]] = mapped_column(Date, default=None)
    due_date: Mapped[Optional[date]] = mapped_column(Date, default=None)
    completed_at: Mapped[Optional[datetime]] = mapped_column(Date, default=None)

    progress: Mapped[Optional[float]] = mapped_column(default=0.0)
    sorted_order: Mapped[Optional[int]] = mapped_column(default=0)

    # ORM Relationships
    project: Mapped[Project] = relationship(back_populates="milestones")
    tickets: Mapped[List[Ticket]] = relationship(back_populates="milestone", passive_deletes=True)
    tasks: Mapped[List[Task]] = relationship(back_populates="milestone", passive_deletes=True)
