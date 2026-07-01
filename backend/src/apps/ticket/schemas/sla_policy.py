# src/apps/ticket/schemas/sla_policy.py
from __future__ import annotations
from datetime import datetime
from src.core.enums import Priority
from src.core.schemas import BaseSchema
from src.core.types import HashId

class SLAPolicyBase(BaseSchema):
    name: str
    priority: Priority
    first_response_minutes: int
    resolution_minutes: int
    is_active: bool = True


class SLAPolicyCreate(SLAPolicyBase):
    pass


class SLAPolicyUpdate(SLAPolicyBase):
    pass


class SLAPolicyPartialUpdate(BaseSchema):
    name: str | None = None
    priority: Priority | None = None
    first_response_minutes: int | None = None
    resolution_minutes: int | None = None
    is_active: bool | None = None


class SLAPolicyResponse(SLAPolicyBase):
    id: HashId
    created_at: datetime
    updated_at: datetime