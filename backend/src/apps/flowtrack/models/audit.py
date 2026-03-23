from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


class AuditLog(SQLModel, table=True):
    __tablename__ = "flowtrack_audit_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: Optional[int] = Field(default=None, foreign_key="tenant.id", index=True)
    actor_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    action: str = Field(max_length=120, index=True)
    entity_type: str = Field(max_length=120, index=True)
    entity_id: int = Field(index=True)
    payload: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utc_now)
