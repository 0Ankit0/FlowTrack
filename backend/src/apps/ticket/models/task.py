from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.enums import TaskPriority, TaskStatus
from src.db.base import Base

if TYPE_CHECKING:
    from .ticket import Ticket
    from src.apps.iam.models.user import User
    from src.apps.project.models.milestone import Milestone
    from src.apps.project.models.project import Project
    

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)

    project_id: Mapped[int] = mapped_column(
        ForeignKey("flowtrack_projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    milestone_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("flowtrack_milestones.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    parent_task_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    owner_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    assignee_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)

    description: Mapped[Optional[str]] = mapped_column(Text)

    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="taskstatus", create_type=False),
        default=TaskStatus.TODO,
    )

    priority: Mapped[TaskPriority] = mapped_column(
        Enum(TaskPriority, name="taskpriority", create_type=False),
        default=TaskPriority.MEDIUM,
    )

    planned_start_date: Mapped[Optional[date]] = mapped_column(Date)

    due_date: Mapped[Optional[date]] = mapped_column(Date)

    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    estimated_hours: Mapped[Optional[int]] = mapped_column(Integer)

    actual_hours: Mapped[Optional[int]] = mapped_column(Integer)

    sort_order: Mapped[int] = mapped_column(default=0)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships

    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="tasks",
    )

    milestone: Mapped[Optional["Milestone"]] = relationship(
        "Milestone",
        back_populates="tasks",
    )

    owner: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[owner_id],
    )

    assignee: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[assignee_id],
    )

    parent_task: Mapped[Optional["Task"]] = relationship(
        "Task",
        remote_side=[id],
        back_populates="subtasks",
    )

    subtasks: Mapped[List["Task"]] = relationship(
        "Task",
        back_populates="parent_task",
        cascade="all, delete-orphan",
    )

    tickets: Mapped[List["Ticket"]] = relationship(
        "Ticket",
        back_populates="task",
    )