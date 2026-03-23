import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.iam.utils.hashid import encode_id

from .test_flowtrack_api import _add_member, _create_tenant, _create_user, _override_current_user


@pytest.mark.asyncio
async def test_doc_aligned_milestone_routes_and_release_creation(
    client: AsyncClient, db_session: AsyncSession
):
    pm_user = await _create_user(
        db_session, username="pm-release", email="pm-release@example.com", roles=["project_manager"]
    )
    tenant = await _create_tenant(db_session, owner=pm_user, slug="release-tenant")
    _override_current_user(pm_user)

    project_response = await client.post(
        "/api/v1/projects/",
        json={
            "tenant_id": encode_id(tenant.id),
            "name": "Portal refresh",
            "description": "Frontend refresh project",
            "status": "active",
        },
    )
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    milestone_response = await client.post(
        f"/api/v1/projects/{project_id}/milestones",
        json={
            "name": "Release 1",
            "planned_date": "2026-05-01",
            "status": "in_progress",
        },
    )
    assert milestone_response.status_code == 201
    milestone_id = milestone_response.json()["id"]

    task_response = await client.post(
        f"/api/v1/milestones/{milestone_id}/tasks",
        json={"title": "Regression testing", "description": "Run final checks"},
    )
    assert task_response.status_code == 201
    task_id = task_response.json()["id"]

    milestone_patch = await client.patch(
        f"/api/v1/milestones/{milestone_id}",
        json={"forecast_date": "2026-05-03"},
    )
    assert milestone_patch.status_code == 200

    release_response = await client.post(
        "/api/v1/releases/",
        json={
            "project_id": project_id,
            "milestone_id": milestone_id,
            "version": "v1.0.0",
            "release_type": "planned",
            "status": "planned",
            "task_ids": [task_id],
        },
    )
    assert release_response.status_code == 201
    assert release_response.json()["version"] == "v1.0.0"


@pytest.mark.asyncio
async def test_attachment_validation_and_admin_sla_listing(
    client: AsyncClient, db_session: AsyncSession
):
    client_user = await _create_user(
        db_session, username="client-attach", email="client-attach@example.com", roles=["client_requester"]
    )
    admin_user = await _create_user(
        db_session, username="admin-attach", email="admin-attach@example.com", roles=["admin"]
    )
    tenant = await _create_tenant(db_session, owner=admin_user, slug="attachment-tenant")
    await _add_member(db_session, tenant=tenant, user=client_user)

    _override_current_user(client_user)
    create_response = await client.post(
        "/api/v1/tickets/",
        json={
            "tenant_id": encode_id(tenant.id),
            "title": "Broken upload",
            "description": "Need to attach screenshot",
            "severity": "high",
            "type": "bug",
        },
    )
    assert create_response.status_code == 201
    ticket_id = create_response.json()["id"]

    bad_attachment = await client.post(
        f"/api/v1/tickets/{ticket_id}/attachments",
        json={
            "filename": "exploit.exe",
            "mime_type": "application/octet-stream",
            "size_bytes": 512,
            "storage_key": "tickets/exploit.exe",
        },
    )
    assert bad_attachment.status_code == 400

    _override_current_user(admin_user)
    policies_response = await client.get("/api/v1/admin/sla-policies")
    assert policies_response.status_code == 200
    assert len(policies_response.json()) >= 4
