from __future__ import annotations

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.enums import TicketActivityType
from src.db.base import Base

if TYPE_CHECKING:
    from src.apps.iam.models.user import User
    from .ticket import Ticket


class TicketActivityLog(Base):
    """Audit logs tracking status hops, re-assignments, or title modifications."""
    __tablename__ = "flowtrack_ticket_activity_logs"

    id: Mapped[Optional[int]] = mapped_column(primary_key=True, default=None, nullable=False)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("flowtrack_tickets.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), default=None, index=True)
    
    activity_type: Mapped[TicketActivityType] = mapped_column(
        Enum(
            TicketActivityType, 
            name="ticketactivitytype", 
            create_type=False
        )
    ) 
    field_changed: Mapped[str] = mapped_column(String(100)) 
    old_value: Mapped[Optional[str]] = mapped_column(Text, default=None)
    new_value: Mapped[Optional[str]] = mapped_column(Text, default=None)
    
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # ORM Relationships
    ticket: Mapped[Ticket] = relationship(back_populates="activities")
    actor: Mapped[Optional[User]] = relationship("User")