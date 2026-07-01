# src/apps/ticket/schemas/ticket.py
from __future__ import annotations
from datetime import datetime
from src.core.enums import TicketStatus, Priority
from src.core.schemas import BaseSchema
from src.core.types import HashId

class TicketBase(BaseSchema):
    title: str
    description: str | None = None
    status: TicketStatus = TicketStatus.TODO
    priority: Priority = Priority.MEDIUM


class TicketCreate(TicketBase):
    milestone_id: HashId | None = None
    task_id: HashId | None = None
    assignee_id: HashId | None = None
    sla_policy_id: HashId | None = None


class TicketUpdate(TicketBase):
    milestone_id: HashId | None = None
    task_id: HashId | None = None
    assignee_id: HashId | None = None
    sla_policy_id: HashId | None = None
    first_response_due_at: datetime | None = None
    resolution_due_at: datetime | None = None
    first_response_at: datetime | None = None
    resolved_at: datetime | None = None
    sla_breached: bool | None = False


class TicketPartialUpdate(BaseSchema):
    title: str | None = None
    description: str | None = None
    status: TicketStatus | None = None
    priority: Priority | None = None
    milestone_id: HashId | None = None
    task_id: HashId | None = None
    assignee_id: HashId | None = None
    sla_policy_id: HashId | None = None
    first_response_due_at: datetime | None = None
    resolution_due_at: datetime | None = None
    first_response_at: datetime | None = None
    resolved_at: datetime | None = None
    sla_breached: bool | None = None


class TicketResponse(TicketBase):
    id: HashId
    project_id: HashId
    milestone_id: HashId | None = None
    task_id: HashId | None = None
    reporter_id: HashId | None = None
    assignee_id: HashId | None = None
    sla_policy_id: HashId | None = None
    first_response_due_at: datetime | None = None
    resolution_due_at: datetime | None = None
    first_response_at: datetime | None = None
    resolved_at: datetime | None = None
    sla_breached: bool
    created_at: datetime
    updated_at: datetime