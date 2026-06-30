from __future__ import annotations

from datetime import datetime, date
from typing import Optional, TYPE_CHECKING, List
from sqlalchemy import ForeignKey, String, Text, Date, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.enums import MilestoneStatus
from src.db.base import Base

if TYPE_CHECKING:
    from .project import Project
    from ...ticket.models.ticket import Ticket
    from src.apps.iam.models.user import User


class Milestone(Base):
    __tablename__ = "project_milestones"

    id: Mapped[Optional[int]] = mapped_column(primary_key=True, default=None, nullable=False)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), default=None, index=True)

    title: Mapped[str] = mapped_column(String(150))
    description: Mapped[Optional[str]] = mapped_column(Text, default=None)
    status: Mapped[MilestoneStatus] = mapped_column()
    planned_date: Mapped[Optional[date]] = mapped_column(Date, default=None)
    due_date: Mapped[Optional[date]] = mapped_column(Date, default=None)
    completed_at: Mapped[Optional[datetime]] = mapped_column(Date, default=None)

    progress: Mapped[Optional[float]] = mapped_column(default=0.0)
    sorted_order: Mapped[Optional[int]] = mapped_column(default=0)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    # ORM Relationships
    project: Mapped[Project] = relationship(back_populates="milestones")
    owner: Mapped[Optional["User"]] = relationship("User", back_populates="owned_milestones")
    tickets: Mapped[List[Ticket]] = relationship(back_populates="milestone", passive_deletes=True)
