import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from src.main import app
from src.apps.iam.api.deps import get_current_user
from src.apps.iam.models.role import Role, UserRole
from src.apps.iam.models.user import User
from src.apps.iam.utils.hashid import encode_id
from src.apps.multitenancy.models.tenant import Tenant, TenantMember, TenantRole
from src.apps.flowtrack.models.ticket import Ticket


FLOWTRACK_ROLES = [
    "client_requester",
    "support",
    "project_manager",
    "developer",
    "qa_reviewer",
    "admin",
]


async def _create_user(
    db_session: AsyncSession,
    *,
    username: str,
    email: str,
    roles: list[str],
) -> User:
    user = User(
        username=username,
        email=email,
        hashed_password="hashed",
        is_active=True,
        is_confirmed=True,
    )
    db_session.add(user)
    await db_session.flush()

    for role_name in roles:
        role = (
            await db_session.execute(select(Role).where(Role.name == role_name))
        ).scalars().first()
        if not role:
            role = Role(name=role_name, description=f"Role {role_name}")
            db_session.add(role)
            await db_session.flush()
        db_session.add(UserRole(user_id=user.id, role_id=role.id))

    await db_session.commit()
    result = await db_session.execute(
        select(User)
        .options(selectinload(User.user_roles).selectinload(UserRole.role))
        .where(User.id == user.id)
    )
    return result.scalars().one()


async def _create_tenant(
    db_session: AsyncSession, *, owner: User, name: str = "Acme Corp", slug: str = "acme-corp"
) -> Tenant:
    tenant = Tenant(name=name, slug=slug, description="Test tenant", owner_id=owner.id)
    db_session.add(tenant)
    await db_session.flush()
    db_session.add(
        TenantMember(tenant_id=tenant.id, user_id=owner.id, role=TenantRole.OWNER, is_active=True)
    )
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


async def _add_member(
    db_session: AsyncSession, *, tenant: Tenant, user: User, role: TenantRole = TenantRole.MEMBER
) -> None:
    db_session.add(
        TenantMember(tenant_id=tenant.id, user_id=user.id, role=role, is_active=True)
    )
    await db_session.commit()


def _override_current_user(user: User) -> None:
    async def _dependency_override() -> User:
        return user

    app.dependency_overrides[get_current_user] = _dependency_override


@pytest.mark.asyncio
async def test_ticket_assignment_and_closure_flow(client: AsyncClient, db_session: AsyncSession):
    client_user = await _create_user(
        db_session, username="client1", email="client1@example.com", roles=["client_requester"]
    )
    support_user = await _create_user(
        db_session, username="support1", email="support1@example.com", roles=["support"]
    )
    developer_user = await _create_user(
        db_session, username="dev1", email="dev1@example.com", roles=["developer"]
    )
    qa_user = await _create_user(
        db_session, username="qa1", email="qa1@example.com", roles=["qa_reviewer"]
    )
    tenant = await _create_tenant(db_session, owner=support_user)
    await _add_member(db_session, tenant=tenant, user=client_user)
    await _add_member(db_session, tenant=tenant, user=developer_user)
    await _add_member(db_session, tenant=tenant, user=qa_user)

    _override_current_user(client_user)
    create_response = await client.post(
        "/api/v1/tickets/",
        json={
            "tenant_id": encode_id(tenant.id),
            "title": "Client cannot download report",
            "description": "The report export ends with a blank file.",
            "severity": "high",
            "type": "bug",
        },
    )
    assert create_response.status_code == 201
    ticket_payload = create_response.json()
    assert ticket_payload["status"] == "new"
    ticket_id = ticket_payload["id"]

    _override_current_user(support_user)
    assign_response = await client.post(
        f"/api/v1/tickets/{ticket_id}/assignments",
        json={"assignee_id": encode_id(developer_user.id), "note": "Please investigate today"},
    )
    assert assign_response.status_code == 201

    progress_response = await client.patch(
        f"/api/v1/tickets/{ticket_id}",
        json={"status": "in_progress"},
    )
    assert progress_response.status_code == 200
    assert progress_response.json()["status"] == "in_progress"

    ready_for_qa_response = await client.patch(
        f"/api/v1/tickets/{ticket_id}",
        json={"status": "ready_for_qa"},
    )
    assert ready_for_qa_response.status_code == 200
    assert ready_for_qa_response.json()["status"] == "ready_for_qa"

    _override_current_user(qa_user)
    close_response = await client.patch(
        f"/api/v1/tickets/{ticket_id}",
        json={"status": "closed"},
    )
    assert close_response.status_code == 200
    assert close_response.json()["status"] == "closed"


@pytest.mark.asyncio
async def test_clarification_comment_moves_ticket_back_to_triaged(
    client: AsyncClient, db_session: AsyncSession
):
    client_user = await _create_user(
        db_session, username="client2", email="client2@example.com", roles=["client_requester"]
    )
    support_user = await _create_user(
        db_session, username="support2", email="support2@example.com", roles=["support"]
    )
    tenant = await _create_tenant(db_session, owner=support_user, slug="clarify-tenant")
    await _add_member(db_session, tenant=tenant, user=client_user)

    _override_current_user(client_user)
    create_response = await client.post(
        "/api/v1/tickets/",
        json={
            "tenant_id": encode_id(tenant.id),
            "title": "Need help with login issue",
            "description": "I cannot reproduce consistently.",
            "severity": "medium",
            "type": "incident",
        },
    )
    ticket_id = create_response.json()["id"]

    _override_current_user(support_user)
    await client.patch(
        f"/api/v1/tickets/{ticket_id}",
        json={"status": "awaiting_clarification"},
    )

    _override_current_user(client_user)
    comment_response = await client.post(
        f"/api/v1/tickets/{ticket_id}/comments",
        json={"body": "I reproduced it again on Safari and attached the steps.", "visibility": "public"},
    )
    assert comment_response.status_code == 201

    detail_response = await client.get(f"/api/v1/tickets/{ticket_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["status"] == "triaged"


@pytest.mark.asyncio
async def test_milestone_completion_is_blocked_until_tickets_close(
    client: AsyncClient, db_session: AsyncSession
):
    pm_user = await _create_user(
        db_session, username="pm1", email="pm1@example.com", roles=["project_manager"]
    )
    tenant = await _create_tenant(db_session, owner=pm_user, slug="project-tenant")

    _override_current_user(pm_user)
    project_response = await client.post(
        "/api/v1/projects/",
        json={
            "tenant_id": encode_id(tenant.id),
            "name": "Flowtrack rollout",
            "description": "Internal rollout plan",
            "status": "active",
        },
    )
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    milestone_response = await client.post(
        f"/api/v1/projects/{project_id}/milestones",
        json={
            "name": "Stabilization",
            "planned_date": "2026-04-15",
            "status": "in_progress",
            "completion_criteria": ["All linked tickets closed"],
        },
    )
    assert milestone_response.status_code == 201
    milestone_id = milestone_response.json()["id"]

    ticket_response = await client.post(
        "/api/v1/tickets/",
        json={
            "tenant_id": encode_id(tenant.id),
            "project_id": project_id,
            "milestone_id": milestone_id,
            "title": "Regression in reporting",
            "description": "Charts fail to load after deploy.",
            "severity": "critical",
            "type": "bug",
        },
    )
    assert ticket_response.status_code == 201
    ticket_id = ticket_response.json()["id"]

    blocked_completion_response = await client.patch(
        f"/api/v1/projects/milestones/{milestone_id}",
        json={"status": "completed"},
    )
    assert blocked_completion_response.status_code == 400

    await client.patch(f"/api/v1/tickets/{ticket_id}", json={"status": "triaged"})
    await client.patch(f"/api/v1/tickets/{ticket_id}", json={"status": "assigned"})
    await client.patch(f"/api/v1/tickets/{ticket_id}", json={"status": "in_progress"})
    await client.patch(f"/api/v1/tickets/{ticket_id}", json={"status": "ready_for_qa"})
    await client.patch(f"/api/v1/tickets/{ticket_id}", json={"status": "closed"})

    complete_response = await client.patch(
        f"/api/v1/projects/milestones/{milestone_id}",
        json={"status": "completed"},
    )
    assert complete_response.status_code == 200
    assert complete_response.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_tenant_isolation_blocks_other_organizations(
    client: AsyncClient, db_session: AsyncSession
):
    support_user = await _create_user(
        db_session, username="support3", email="support3@example.com", roles=["support"]
    )
    outsider_user = await _create_user(
        db_session, username="outsider1", email="outsider1@example.com", roles=["client_requester"]
    )
    tenant = await _create_tenant(db_session, owner=support_user, slug="isolation-tenant")

    _override_current_user(support_user)
    create_response = await client.post(
        "/api/v1/tickets/",
        json={
            "tenant_id": encode_id(tenant.id),
            "title": "Missing data export",
            "description": "CSV export drops rows.",
            "severity": "low",
            "type": "service_request",
        },
    )
    assert create_response.status_code == 201
    ticket_id = create_response.json()["id"]

    _override_current_user(outsider_user)
    detail_response = await client.get(f"/api/v1/tickets/{ticket_id}")
    assert detail_response.status_code == 403

    list_response = await client.get(f"/api/v1/tickets/?tenant_id={encode_id(tenant.id)}")
    assert list_response.status_code == 403

    result = await db_session.execute(select(Ticket).where(Ticket.id.is_not(None)))
    assert result.scalars().first() is not None
