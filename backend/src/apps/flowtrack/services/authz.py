from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.apps.iam.models.role import UserRole
from src.apps.iam.models.user import User
from src.apps.multitenancy.models.tenant import TenantMember


INTERNAL_ROLES = {"support", "project_manager", "developer", "qa_reviewer", "admin"}
FLOWTRACK_ROLES = INTERNAL_ROLES | {"client_requester"}


def get_user_role_names(user: User) -> set[str]:
    return {
        user_role.role.name
        for user_role in getattr(user, "user_roles", []) or []
        if isinstance(user_role, UserRole) and user_role.role
    }


def require_roles(user: User, *allowed_roles: str) -> None:
    if user.is_superuser:
        return

    user_roles = get_user_role_names(user)
    if not user_roles.intersection(allowed_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action",
        )


def is_internal_user(user: User) -> bool:
    return user.is_superuser or bool(get_user_role_names(user).intersection(INTERNAL_ROLES))


async def ensure_tenant_access(db: AsyncSession, user: User, tenant_id: int) -> TenantMember | None:
    if user.is_superuser:
        return None

    membership = (
        await db.execute(
            select(TenantMember).where(
                TenantMember.tenant_id == tenant_id,
                TenantMember.user_id == user.id,
                TenantMember.is_active == True,
            )
        )
    ).scalars().first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this organization",
        )

    return membership
