from __future__ import annotations

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base

if TYPE_CHECKING:
    from src.apps.iam.models.user import User
    from .ticket import Ticket


class TicketComment(Base):
    """Discussion stream tied to individual execution tickets."""
    __tablename__ = "ticket_comments"

    id: Mapped[Optional[int]] = mapped_column(primary_key=True, default=None, nullable=False)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("flowtrack_tickets.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), default=None, index=True)
    parent_comment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ticket_comments.id", ondelete="CASCADE"), default=None, index=True)

    body: Mapped[str] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(default=None)

    # ORM Relationships
    ticket: Mapped[Ticket] = relationship(back_populates="comments")
    author: Mapped[Optional[User]] = relationship("User")
    parent_comment: Mapped[Optional["TicketComment"]] = relationship("TicketComment", remote_side=[id], back_populates="child_comments")
    replies: Mapped[list["TicketComment"]] = relationship("TicketComment", back_populates="parent_comment", cascade="all, delete-orphan")