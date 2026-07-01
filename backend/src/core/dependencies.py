from __future__ import annotations

from typing import Annotated, AsyncGenerator, Optional
from fastapi import status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, Path, Request
from src.apps.project.models.milestone import Milestone
from src.apps.project.models.project import Project
from src.core.types import HashId
from src.core.config import settings
from src.core.exceptions import AuthenticationError, AuthorizationError, NotFoundError, ValidationError
from src.core import security
from src.db.query import select, selectinload
from src.apps.iam.schemas.token import TokenPayload
from src.apps.organizations.models.organization import Organization
from src.apps.iam.models import TokenTracking
from src.apps.iam.models.user import User
from src.db.session import get_session 
from src.apps.iam.casbin import enforcer
from src.apps.iam.services.policy_service import PolicyService
from src.core.enums import RBACAction as Action, RBACModule as Module, UserStatus

DB = Annotated[AsyncSession, Depends(get_session)]


METHOD_ACTION_MAP = {
    "GET": Action.READ,
    "POST": Action.CREATE,
    "PUT": Action.UPDATE,
    "PATCH": Action.UPDATE,
    "DELETE": Action.DELETE,
}


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_session():
        yield session


# HTTPBearer with auto_error=False so cookie fallback still works,
# but FastAPI registers the BearerAuth security scheme on all
# routes that depend on get_current_user — enabling the Swagger
# "Authorize" button and lock icons on protected endpoints.
_bearer_scheme = HTTPBearer(auto_error=False)

async def authenticate_token(
    token: str,
    db: DB,
) -> User:
    payload = security.decode_token(token)
    token_data = TokenPayload(**payload)

    if not token_data.sub:
        raise AuthorizationError(
            message="Token payload missing subject"
        )

    jti = payload.get("jti")

    if jti:
        token_result = await db.execute(
            select(TokenTracking).where(
                TokenTracking.token_jti == jti,
                TokenTracking.is_active
            )
        )

        token_tracking = token_result.scalars().first()

        if not token_tracking:
            raise AuthenticationError(
                message="Token is invalid or has been revoked",
                headers={"WWW-Authenticate": "Bearer"}
            )

    result = await db.execute(
        select(User)
        .options(
            selectinload(User.profile)
        )
        .where(User.id == int(token_data.sub))
    )

    user = result.scalars().first()

    if not user:
        raise AuthenticationError(
            message="User not found"
        )

    if user.status != UserStatus.ACTIVE:
        raise AuthenticationError(
            message="User account is inactive"
        )

    return user

async def get_current_user(
    request: Request,
    credentials: Annotated[
        Optional[HTTPAuthorizationCredentials],
        Depends(_bearer_scheme)
    ],
    db: DB,
) -> User:

    token = credentials.credentials if credentials else None

    if not token:
        token = request.cookies.get(
            settings.ACCESS_TOKEN_COOKIE_NAME
        )

    if not token:
        raise AuthenticationError(
            message="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await authenticate_token(
        token=token,
        db=db,
    )

    request.state.current_user_id = user.id

    return user  
   

async def get_current_active_superuser(
current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    if not current_user.is_superuser and not current_user.status == UserStatus.ACTIVE:
        raise AuthorizationError(
            message="Insufficient permissions"
        )
    return current_user

CurrentUser = Annotated[User, Depends(get_current_user)]

async def get_current_org(
    db: DB,
    current_user: CurrentUser,
    org: Annotated[str, Path(description="Organization slug")],
) -> Organization | None:
    """Fetches and verifies the organization context, enforcing Casbin organization membership."""
    if not org:
        raise NotFoundError("Organization slug is required")
    
    # Handle global superuser context bypass
    if current_user.is_superuser and org == "global":
        return None

    result = await db.execute(
        select(Organization).where(Organization.slug == org)
    )
    organization = result.scalars().first()
    
    if not organization:
        raise NotFoundError("Organization not found")
    
    # Secure Enforcement Step: Verify the user holds an active role on this organization via Casbin
    if not current_user.is_superuser:
        is_member = PolicyService.is_org_member(current_user, str(org))
        if not is_member:
            raise AuthorizationError(message="Access denied to this organization")
            
    return organization

CurrentOrg = Annotated[Organization, Depends(get_current_org)]
 
async def get_current_project(
    db: DB,
    current_user: CurrentUser,
    current_org: CurrentOrg,
    project_id: Annotated[HashId, Path(description="Project ID")],
) -> Project:
    """Fetches, verifies organization containment, and enforces Casbin project access rules."""
    query = select(Project).where(Project.id == project_id)
    if current_org:
        query = query.where(Project.organization_id == current_org.id)
        
    result = await db.execute(query)
    project = result.scalar_one_or_none()
    if not project:
        raise NotFoundError(message="Project not found")
    
    # Secure Enforcement Step: Verify the user holds an active role on this specific project
    if not current_user.is_superuser:
        is_member = PolicyService.is_project_member(current_user, str(project_id))
        if not is_member:
            raise AuthorizationError(message="Access denied to this project")

    return project

CurrentProject = Annotated[Project, Depends(get_current_project)]

async def get_current_milestone(
    db: DB,
    current_project: CurrentProject,
    milestone_id: Annotated[HashId, Path(description="Milestone ID")],
) -> Milestone:
    """Fetches a milestone verifying it belongs exclusively to the resolved project context."""
    query = select(Milestone).where(
        Milestone.id == milestone_id,
        Milestone.project_id == current_project.id
    )
    result = await db.execute(query)
    milestone = result.scalar_one_or_none()
    if not milestone:
        raise NotFoundError(message="Milestone not found")
    return milestone

CurrentMilestone = Annotated[Milestone, Depends(get_current_milestone)]

def require_module_permission(module: Module):
    async def checker(
        request: Request,
        current_user: CurrentUser,
        org: CurrentOrg,
    ):
        if current_user.is_superuser:
            return

        action = METHOD_ACTION_MAP[request.method]

        # Automatically extract the project context from path parameters if available
        project_id = request.path_params.get("project_id")
        project_domain = f"proj_{project_id}" if project_id else "none"

        # Updated to perfectly evaluate against your unified 5-parameter model track
        allowed = enforcer.enforce(
            str(current_user.id),
            str(org.slug) if org else "none",
            project_domain,
            module.value,
            action.value,
        )

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

    return checker