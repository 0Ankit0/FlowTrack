from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_serializer

from src.apps.iam.utils.hashid import encode_id

from ..models.enums import Priority


class AuditLogRead(BaseModel):
    id: int
    tenant_id: Optional[int]
    actor_id: Optional[int]
    action: str
    entity_type: str
    entity_id: int
    payload: dict
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("id", "entity_id")
    def serialize_ids(self, value: int) -> str:
        return encode_id(value)

    @field_serializer("tenant_id", "actor_id")
    def serialize_optional_ids(self, value: Optional[int]) -> Optional[str]:
        return encode_id(value) if value is not None else None


class SlaPolicyUpdate(BaseModel):
    name: Optional[str] = None
    priority: Optional[Priority] = None
    first_response_minutes: Optional[int] = None
    resolution_minutes: Optional[int] = None
    is_active: Optional[bool] = None


class SlaPolicyRead(BaseModel):
    id: int
    name: str
    priority: Priority
    first_response_minutes: int
    resolution_minutes: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("id")
    def serialize_id(self, value: int) -> str:
        return encode_id(value)


class OperationalSummaryRead(BaseModel):
    tenant_id: str
    open_ticket_count: int
    breached_ticket_count: int
    project_count: int
    active_project_count: int
    milestone_completion_rate: float
    workload_by_assignee: dict[str, int]
