# src/apps/ticket/schemas/attachment.py
from __future__ import annotations
from datetime import datetime
from src.core.schemas import BaseSchema
from src.core.types import HashId

class TicketAttachmentBase(BaseSchema):
    file_name: str
    file_path: str  
    file_size: int  
    mime_type: str


class TicketAttachmentUpdate(TicketAttachmentBase):
    pass


class TicketAttachmentPartialUpdate(BaseSchema):
    file_name: str | None = None
    file_path: str | None = None
    file_size: int | None = None
    mime_type: str | None = None


class TicketAttachmentResponse(TicketAttachmentBase):
    id: HashId
    ticket_id: HashId
    user_id: HashId | None = None
    uploaded_at: datetime