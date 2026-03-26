from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.apps.iam.api.deps import get_current_user, get_db
from src.apps.iam.models.user import User
from src.apps.iam.utils.hashid import decode_id_or_404

from ...models.project import Milestone, Project, Release, Task
from ...models.ticket import Ticket
from ...schemas.project import ReleaseCreate, ReleaseRead
from ...services.audit import record_audit_log
from ...services.authz import ensure_tenant_access, require_roles

router = APIRouter(prefix="/releases")


@router.post("/", response_model=ReleaseRead, status_code=status.HTTP_201_CREATED)
async def create_release(
    payload: ReleaseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Release:
    require_roles(current_user, "project_manager", "qa_reviewer", "admin", "support")

    project_id = decode_id_or_404(payload.project_id)
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    await ensure_tenant_access(db, current_user, project.tenant_id)

    milestone_id = decode_id_or_404(payload.milestone_id) if payload.milestone_id else None
    if milestone_id is not None:
        milestone = await db.get(Milestone, milestone_id)
        if not milestone or milestone.project_id != project.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Milestone does not belong to the selected project",
            )

    ticket_ids = [decode_id_or_404(item) for item in payload.ticket_ids]
    for ticket_id in ticket_ids:
        ticket = await db.get(Ticket, ticket_id)
        if not ticket or ticket.project_id != project.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A linked ticket does not belong to the selected project",
            )

    task_ids = [decode_id_or_404(item) for item in payload.task_ids]
    for task_id in task_ids:
        task = await db.get(Task, task_id)
        if not task or task.project_id != project.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A linked task does not belong to the selected project",
            )

    owner_id = decode_id_or_404(payload.owner_id) if payload.owner_id else current_user.id
    release = Release(
        project_id=project.id,
        milestone_id=milestone_id,
        owner_id=owner_id,
        version=payload.version,
        status=payload.status,
        release_type=payload.release_type,
        planned_at=payload.planned_at,
        deployed_at=payload.deployed_at,
        ticket_ids=ticket_ids,
        task_ids=task_ids,
        notes=payload.notes,
    )
    db.add(release)
    await db.flush()

    await record_audit_log(
        db,
        actor_id=current_user.id,
        tenant_id=project.tenant_id,
        action="release.created",
        entity_type="release",
        entity_id=release.id,
        payload={"project_id": project.id, "version": release.version},
    )
    await db.commit()
    await db.refresh(release)
    return release


@router.get("/", response_model=list[ReleaseRead])
async def list_releases(
    tenant_id: str = Query(...),
    project_id: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ReleaseRead]:
    tenant_db_id = decode_id_or_404(tenant_id)
    await ensure_tenant_access(db, current_user, tenant_db_id)

    query = (
        select(Release)
        .join(Project, Project.id == Release.project_id)
        .where(Project.tenant_id == tenant_db_id)
        .order_by(Release.created_at.desc())
    )
    if project_id:
        query = query.where(Release.project_id == decode_id_or_404(project_id))

    releases = (await db.execute(query)).scalars().all()
    return [ReleaseRead.model_validate(item) for item in releases]
