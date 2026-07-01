from __future__ import annotations

from typing import Optional, TYPE_CHECKING, List
from sqlalchemy import  Index, String, Date, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.mixins import TimestampMixin
from src.db.base import Base
from src.core.enums import Priority

if TYPE_CHECKING:
    from backend.src.apps.ticket.models.ticket import Ticket

class SLAPolicy(Base, TimestampMixin):
    __tablename__ = "sla_policies"

    id: Mapped[Optional[int]] = mapped_column(primary_key=True, default=None, nullable=False)
    
    name: Mapped[str] = mapped_column(String(150), index=True)
    priority: Mapped[Priority] = mapped_column(Enum(Priority, name="priority", create_type=False))
    first_response_minutes: Mapped[int] = mapped_column(nullable=False)
    resolution_minutes: Mapped[int] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)

    # Relationships
    tickets: Mapped[List["Ticket"]] = relationship("Ticket", back_populates="sla_policy")

    __table_args__ = (
        Index(
            "uq_active_sla_policy_per_priority",
            "priority",
            unique=True,
            postgresql_where=(is_active.is_(True)),
        ),
    )

    
   