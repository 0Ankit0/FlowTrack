# src/apps/ticket/schemas/comment.py
from __future__ import annotations
from datetime import datetime
from src.core.schemas import BaseSchema
from src.core.types import HashId

class TicketCommentBase(BaseSchema):
    body: str


class TicketCommentCreate(TicketCommentBase):
    parent_comment_id: HashId | None = None


class TicketCommentUpdate(TicketCommentBase):
    pass


class TicketCommentPartialUpdate(BaseSchema):
    body: str | None = None


class TicketCommentResponse(TicketCommentBase):
    id: HashId
    ticket_id: HashId
    user_id: HashId | None = None
    parent_comment_id: HashId | None = None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None