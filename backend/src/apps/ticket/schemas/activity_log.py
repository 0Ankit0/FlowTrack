# src/apps/ticket/schemas/activity_log.py
from __future__ import annotations
from datetime import datetime
from src.core.enums import TicketActivityType
from src.core.schemas import BaseSchema
from src.core.types import HashId

class TicketActivityLogBase(BaseSchema):
    activity_type: TicketActivityType
    field_changed: str
    old_value: str | None = None
    new_value: str | None = None


class TicketActivityLogCreate(TicketActivityLogBase):
    pass


class TicketActivityLogUpdate(TicketActivityLogBase):
    pass


class TicketActivityLogPartialUpdate(BaseSchema):
    activity_type: TicketActivityType | None = None
    field_changed: str | None = None
    old_value: str | None = None
    new_value: str | None = None


class TicketActivityLogResponse(TicketActivityLogBase):
    id: HashId
    ticket_id: HashId
    user_id: HashId | None = None
    created_at: datetime