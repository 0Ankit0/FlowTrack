from __future__ import annotations

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import ForeignKey, String, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base

if TYPE_CHECKING:
    from src.apps.iam.models.user import User
    from .ticket import Ticket


class TicketAttachment(Base):
    """Tracks reference files, documents, or screenshots uploaded to a ticket."""
    __tablename__ = "flowtrack_ticket_attachments"

    id: Mapped[Optional[int]] = mapped_column(primary_key=True, default=None, nullable=False)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("flowtrack_tickets.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), default=None, index=True)
    
    file_name: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(512))  # S3 bucket URI or localized path string
    file_size: Mapped[int] = mapped_column(Integer)  # Saved in Bytes
    mime_type: Mapped[str] = mapped_column(String(100))
    
    uploaded_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # ORM Relationships
    ticket: Mapped[Ticket] = relationship(back_populates="attachments")
    uploader: Mapped[Optional[User]] = relationship("User")