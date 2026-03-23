from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.audit import AuditLog


async def record_audit_log(
    db: AsyncSession,
    *,
    actor_id: int | None,
    tenant_id: int | None,
    action: str,
    entity_type: str,
    entity_id: int,
    payload: dict | None = None,
) -> AuditLog:
    log = AuditLog(
        actor_id=actor_id,
        tenant_id=tenant_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        payload=payload or {},
    )
    db.add(log)
    await db.flush()
    return log
