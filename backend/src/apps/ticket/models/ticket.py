from __future__ import annotations

from datetime import datetime
from typing import Optional, TYPE_CHECKING, List
from sqlalchemy import ForeignKey, String, Text, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.core.enums import TicketStatus, Priority

if TYPE_CHECKING:
    from src.apps.iam.models.user import User
    from src.apps.project.models.project import Project
    from src.apps.project.models.milestone import Milestone
    from .task import Task
    from .comment import TicketComment
    from .attachment import TicketAttachment
    from .activity import TicketActivityLog

class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)

    project_id: Mapped[int] = mapped_column(
        ForeignKey("flowtrack_projects.id", ondelete="CASCADE"),
        index=True,
    )

    milestone_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("flowtrack_milestones.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    task_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    reporter_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    assignee_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        index=True,
    )

    description: Mapped[Optional[str]] = mapped_column(Text)

    status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus, name="ticketstatus", create_type=False),
        default=TicketStatus.TODO,
    )

    priority: Mapped[Priority] = mapped_column(
        Enum(Priority, name="priority", create_type=False),
        default=Priority.MEDIUM,
    )

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships

    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="tickets",
    )

    milestone: Mapped[Optional["Milestone"]] = relationship(
        "Milestone",
        back_populates="tickets",
    )

    task: Mapped[Optional["Task"]] = relationship(
        "Task",
        back_populates="tickets",
    )

    reporter: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[reporter_id],
    )

    assignee: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[assignee_id],
    )

    comments: Mapped[List["TicketComment"]] = relationship(
        back_populates="ticket",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    attachments: Mapped[List["TicketAttachment"]] = relationship(
        back_populates="ticket",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    activities: Mapped[List["TicketActivityLog"]] = relationship(
        back_populates="ticket",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

