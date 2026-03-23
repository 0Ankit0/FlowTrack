from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.apps.iam.models.role import Role

from ..models.enums import Priority
from ..models.ticket import SlaPolicy
from .authz import FLOWTRACK_ROLES


DEFAULT_SLA_POLICIES = {
    Priority.P1: ("Critical incidents", 15, 240),
    Priority.P2: ("High-priority issues", 60, 60 * 24),
    Priority.P3: ("Normal delivery work", 240, 60 * 24 * 5),
    Priority.P4: ("Backlog and low-priority work", 60 * 24, 60 * 24 * 10),
}


async def seed_flowtrack_defaults(db: AsyncSession) -> None:
    existing_roles = {
        role.name for role in (await db.execute(select(Role))).scalars().all()
    }

    for role_name in sorted(FLOWTRACK_ROLES):
        if role_name in existing_roles:
            continue
        db.add(Role(name=role_name, description=f"Flowtrack role: {role_name}"))

    existing_policies = {
        policy.priority
        for policy in (await db.execute(select(SlaPolicy))).scalars().all()
    }

    now = datetime.now(UTC)
    for priority, (name, first_response_minutes, resolution_minutes) in DEFAULT_SLA_POLICIES.items():
        if priority in existing_policies:
            continue
        db.add(
            SlaPolicy(
                name=name,
                priority=priority,
                first_response_minutes=first_response_minutes,
                resolution_minutes=resolution_minutes,
                created_at=now,
                updated_at=now,
            )
        )

    await db.commit()
