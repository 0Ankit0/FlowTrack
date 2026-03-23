from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_serializer

from src.apps.iam.utils.hashid import encode_id

from ..models.enums import (
    AttachmentScanStatus,
    CommentVisibility,
    Priority,
    Severity,
    TicketStatus,
    TicketType,
)


class TicketCreate(BaseModel):
    tenant_id: str
    project_id: Optional[str] = None
    milestone_id: Optional[str] = None
    title: str
    description: str
    category: str = ""
    environment: str = ""
    type: TicketType = TicketType.BUG
    severity: Severity = Severity.MEDIUM
    priority: Optional[Priority] = None


class TicketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    environment: Optional[str] = None
    type: Optional[TicketType] = None
    severity: Optional[Severity] = None
    priority: Optional[Priority] = None
    status: Optional[TicketStatus] = None
    project_id: Optional[str] = None
    milestone_id: Optional[str] = None


class CommentCreate(BaseModel):
    body: str
    visibility: CommentVisibility = CommentVisibility.PUBLIC


class AttachmentCreate(BaseModel):
    filename: str
    mime_type: str
    size_bytes: int
    storage_key: str


class AssignmentCreate(BaseModel):
    assignee_id: str
    note: str = ""
    due_at: Optional[datetime] = None


class TicketCommentRead(BaseModel):
    id: int
    ticket_id: int
    author_id: int
    visibility: CommentVisibility
    body: str
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("id", "ticket_id", "author_id")
    def serialize_ids(self, value: int) -> str:
        return encode_id(value)


class TicketAttachmentRead(BaseModel):
    id: int
    ticket_id: int
    uploaded_by_id: int
    filename: str
    mime_type: str
    size_bytes: int
    storage_key: str
    scan_status: AttachmentScanStatus
    extra_data: dict
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("id", "ticket_id", "uploaded_by_id")
    def serialize_ids(self, value: int) -> str:
        return encode_id(value)


class AssignmentRead(BaseModel):
    id: int
    ticket_id: int
    assignee_id: int
    assigned_by_id: int
    note: str
    due_at: Optional[datetime]
    assigned_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("id", "ticket_id", "assignee_id", "assigned_by_id")
    def serialize_ids(self, value: int) -> str:
        return encode_id(value)


class TicketRead(BaseModel):
    id: int
    tenant_id: int
    project_id: Optional[int]
    milestone_id: Optional[int]
    reporter_id: int
    current_assignee_id: Optional[int]
    title: str
    description: str
    category: str
    environment: str
    type: TicketType
    severity: Severity
    priority: Priority
    status: TicketStatus
    first_responded_at: Optional[datetime]
    resolved_at: Optional[datetime]
    closed_at: Optional[datetime]
    sla_first_response_due_at: Optional[datetime]
    sla_resolution_due_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("id", "tenant_id", "reporter_id")
    def serialize_ids(self, value: int) -> str:
        return encode_id(value)

    @field_serializer("project_id", "milestone_id", "current_assignee_id")
    def serialize_optional_ids(self, value: Optional[int]) -> Optional[str]:
        return encode_id(value) if value is not None else None


class TicketDetailRead(TicketRead):
    comments: list[TicketCommentRead] = []
    attachments: list[TicketAttachmentRead] = []
    assignments: list[AssignmentRead] = []
