from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.apps.iam.api.deps import get_current_user, get_db
from src.apps.iam.models.user import User
from src.apps.iam.utils.hashid import decode_id_or_404

from ...models.audit import AuditLog
from ...models.ticket import SlaPolicy
from ...schemas.admin import AuditLogRead, SlaPolicyRead, SlaPolicyUpdate
from ...services.audit import record_audit_log
from ...services.authz import ensure_tenant_access, require_roles

router = APIRouter()


@router.get("/audit-logs", response_model=list[AuditLogRead])
async def list_audit_logs(
    tenant_id: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AuditLogRead]:
    require_roles(current_user, "admin")

    query = select(AuditLog).order_by(AuditLog.created_at.desc())
    if tenant_id is not None:
        tenant_db_id = decode_id_or_404(tenant_id)
        await ensure_tenant_access(db, current_user, tenant_db_id)
        query = query.where(AuditLog.tenant_id == tenant_db_id)

    logs = (await db.execute(query.limit(200))).scalars().all()
    return [AuditLogRead.model_validate(item) for item in logs]


@router.get("/admin/sla-policies", response_model=list[SlaPolicyRead])
async def list_sla_policies(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SlaPolicyRead]:
    require_roles(current_user, "admin", "support", "project_manager")
    policies = (await db.execute(select(SlaPolicy).order_by(SlaPolicy.priority.asc()))).scalars().all()
    return [SlaPolicyRead.model_validate(item) for item in policies]


@router.patch("/admin/sla-policies/{policy_id}", response_model=SlaPolicyRead)
async def update_sla_policy(
    policy_id: str,
    payload: SlaPolicyUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SlaPolicy:
    require_roles(current_user, "admin")

    policy_db_id = decode_id_or_404(policy_id)
    policy = await db.get(SlaPolicy, policy_db_id)
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SLA policy not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(policy, field, value)
    policy.updated_at = datetime.now(UTC)

    await record_audit_log(
        db,
        actor_id=current_user.id,
        tenant_id=None,
        action="sla_policy.updated",
        entity_type="sla_policy",
        entity_id=policy.id,
        payload={"changes": payload.model_dump(exclude_unset=True, mode="json")},
    )
    await db.commit()
    await db.refresh(policy)
    return policy
