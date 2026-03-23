from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from .enums import (
    AttachmentScanStatus,
    CommentVisibility,
    Priority,
    Severity,
    TicketStatus,
    TicketType,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


class SlaPolicy(SQLModel, table=True):
    __tablename__ = "flowtrack_sla_policies"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=120, unique=True, index=True)
    priority: Priority = Field(unique=True, index=True)
    first_response_minutes: int = Field(ge=1)
    resolution_minutes: int = Field(ge=1)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Ticket(SQLModel, table=True):
    __tablename__ = "flowtrack_tickets"

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenant.id", index=True)
    project_id: Optional[int] = Field(
        default=None, foreign_key="flowtrack_projects.id", index=True
    )
    milestone_id: Optional[int] = Field(
        default=None, foreign_key="flowtrack_milestones.id", index=True
    )
    reporter_id: int = Field(foreign_key="user.id", index=True)
    current_assignee_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    title: str = Field(max_length=180, index=True)
    description: str = Field(max_length=5000)
    category: str = Field(default="", max_length=120)
    environment: str = Field(default="", max_length=120)
    type: TicketType = Field(default=TicketType.BUG)
    severity: Severity = Field(default=Severity.MEDIUM)
    priority: Priority = Field(default=Priority.P3, index=True)
    status: TicketStatus = Field(default=TicketStatus.NEW, index=True)
    first_responded_at: Optional[datetime] = Field(default=None)
    resolved_at: Optional[datetime] = Field(default=None)
    closed_at: Optional[datetime] = Field(default=None)
    sla_first_response_due_at: Optional[datetime] = Field(default=None, index=True)
    sla_resolution_due_at: Optional[datetime] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class TicketComment(SQLModel, table=True):
    __tablename__ = "flowtrack_ticket_comments"

    id: Optional[int] = Field(default=None, primary_key=True)
    ticket_id: int = Field(foreign_key="flowtrack_tickets.id", index=True)
    author_id: int = Field(foreign_key="user.id", index=True)
    visibility: CommentVisibility = Field(default=CommentVisibility.PUBLIC)
    body: str = Field(max_length=5000)
    created_at: datetime = Field(default_factory=utc_now)


class TicketAttachment(SQLModel, table=True):
    __tablename__ = "flowtrack_ticket_attachments"

    id: Optional[int] = Field(default=None, primary_key=True)
    ticket_id: int = Field(foreign_key="flowtrack_tickets.id", index=True)
    uploaded_by_id: int = Field(foreign_key="user.id", index=True)
    filename: str = Field(max_length=255)
    mime_type: str = Field(max_length=120)
    size_bytes: int = Field(ge=0)
    storage_key: str = Field(max_length=255, unique=True, index=True)
    scan_status: AttachmentScanStatus = Field(default=AttachmentScanStatus.PENDING)
    extra_data: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utc_now)


class Assignment(SQLModel, table=True):
    __tablename__ = "flowtrack_assignments"

    id: Optional[int] = Field(default=None, primary_key=True)
    ticket_id: int = Field(foreign_key="flowtrack_tickets.id", index=True)
    assignee_id: int = Field(foreign_key="user.id", index=True)
    assigned_by_id: int = Field(foreign_key="user.id", index=True)
    note: str = Field(default="", max_length=2000)
    due_at: Optional[datetime] = Field(default=None)
    assigned_at: datetime = Field(default_factory=utc_now)
