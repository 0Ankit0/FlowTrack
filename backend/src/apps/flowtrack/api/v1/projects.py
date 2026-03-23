from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, func, select

from src.apps.core.schemas import PaginatedResponse
from src.apps.iam.api.deps import get_current_user, get_db
from src.apps.iam.models.user import User
from src.apps.iam.utils.hashid import decode_id_or_404
from src.apps.multitenancy.models.tenant import Tenant

from ...models.enums import MilestoneStatus, TicketStatus
from ...models.project import Milestone, Project, Release, Task
from ...models.ticket import Ticket
from ...schemas.project import (
    MilestoneCreate,
    MilestoneRead,
    MilestoneUpdate,
    ProjectCreate,
    ProjectDetailRead,
    ProjectRead,
    ReleaseRead,
    TaskCreate,
    TaskRead,
)
from ...services.audit import record_audit_log
from ...services.authz import ensure_tenant_access, require_roles
from ...services.workflow import ensure_milestone_transition

router = APIRouter(prefix="/projects")


async def _get_project_or_404(project_id: str, db: AsyncSession) -> Project:
    db_id = decode_id_or_404(project_id)
    project = await db.get(Project, db_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


async def _get_milestone_or_404(milestone_id: str, db: AsyncSession) -> Milestone:
    db_id = decode_id_or_404(milestone_id)
    milestone = await db.get(Milestone, db_id)
    if not milestone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Milestone not found")
    return milestone


@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Project:
    require_roles(current_user, "project_manager", "admin", "support")

    tenant_id = decode_id_or_404(payload.tenant_id)
    await ensure_tenant_access(db, current_user, tenant_id)
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    owner_id = decode_id_or_404(payload.owner_id) if payload.owner_id else current_user.id
    project = Project(
        tenant_id=tenant_id,
        owner_id=owner_id,
        name=payload.name,
        description=payload.description,
        status=payload.status,
        health=payload.health,
        start_date=payload.start_date,
        target_end_date=payload.target_end_date,
        budget_notes=payload.budget_notes,
    )
    db.add(project)
    await db.flush()

    await record_audit_log(
        db,
        actor_id=current_user.id,
        tenant_id=tenant_id,
        action="project.created",
        entity_type="project",
        entity_id=project.id,
        payload={"name": project.name, "status": project.status},
    )
    await db.commit()
    await db.refresh(project)
    return project


@router.get("/", response_model=PaginatedResponse[ProjectRead])
async def list_projects(
    tenant_id: str = Query(...),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[ProjectRead]:
    tenant_db_id = decode_id_or_404(tenant_id)
    await ensure_tenant_access(db, current_user, tenant_db_id)

    total = (
        await db.execute(select(func.count(col(Project.id))).where(Project.tenant_id == tenant_db_id))
    ).one()[0]
    items = (
        await db.execute(
            select(Project)
            .where(Project.tenant_id == tenant_db_id)
            .order_by(Project.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
    ).scalars().all()
    response_items = [ProjectRead.model_validate(item) for item in items]
    return PaginatedResponse[ProjectRead].create(
        items=response_items,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{project_id}", response_model=ProjectDetailRead)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectDetailRead:
    project = await _get_project_or_404(project_id, db)
    await ensure_tenant_access(db, current_user, project.tenant_id)

    milestones = (
        await db.execute(
            select(Milestone)
            .where(Milestone.project_id == project.id)
            .order_by(Milestone.planned_date.asc())
        )
    ).scalars().all()
    tasks = (
        await db.execute(
            select(Task)
            .where(Task.project_id == project.id)
            .order_by(Task.created_at.asc())
        )
    ).scalars().all()
    linked_ticket_count = (
        await db.execute(
            select(func.count(col(Ticket.id))).where(Ticket.project_id == project.id)
        )
    ).one()[0]
    releases = (
        await db.execute(
            select(Release)
            .where(Release.project_id == project.id)
            .order_by(Release.created_at.desc())
        )
    ).scalars().all()

    return ProjectDetailRead.model_validate(
        {
            **project.model_dump(),
            "milestones": [MilestoneRead.model_validate(item) for item in milestones],
            "tasks": [TaskRead.model_validate(item) for item in tasks],
            "linked_ticket_count": linked_ticket_count,
            "releases": [ReleaseRead.model_validate(item) for item in releases],
        }
    )


@router.post(
    "/{project_id}/milestones",
    response_model=MilestoneRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_milestone(
    project_id: str,
    payload: MilestoneCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Milestone:
    require_roles(current_user, "project_manager", "admin", "support")

    project = await _get_project_or_404(project_id, db)
    await ensure_tenant_access(db, current_user, project.tenant_id)

    owner_id = decode_id_or_404(payload.owner_id) if payload.owner_id else None
    dependency_ids = [decode_id_or_404(item) for item in payload.dependency_ids]
    milestone = Milestone(
        project_id=project.id,
        owner_id=owner_id,
        name=payload.name,
        status=payload.status,
        planned_date=payload.planned_date,
        forecast_date=payload.forecast_date,
        baseline_date=payload.baseline_date,
        dependency_ids=dependency_ids,
        completion_criteria=payload.completion_criteria,
    )
    db.add(milestone)
    await db.flush()

    await record_audit_log(
        db,
        actor_id=current_user.id,
        tenant_id=project.tenant_id,
        action="milestone.created",
        entity_type="milestone",
        entity_id=milestone.id,
        payload={"project_id": project.id, "name": milestone.name},
    )
    await db.commit()
    await db.refresh(milestone)
    return milestone


@router.patch("/milestones/{milestone_id}", response_model=MilestoneRead)
async def update_milestone_legacy(
    milestone_id: str,
    payload: MilestoneUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Milestone:
    require_roles(current_user, "project_manager", "admin", "support")

    milestone = await _get_milestone_or_404(milestone_id, db)
    project = await db.get(Project, milestone.project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    await ensure_tenant_access(db, current_user, project.tenant_id)

    update_data = payload.model_dump(exclude_unset=True)
    if "owner_id" in update_data and update_data["owner_id"] is not None:
        update_data["owner_id"] = decode_id_or_404(update_data["owner_id"])
    if "dependency_ids" in update_data and update_data["dependency_ids"] is not None:
        update_data["dependency_ids"] = [
            decode_id_or_404(item) for item in update_data["dependency_ids"]
        ]
    if "status" in update_data and update_data["status"] is not None:
        ensure_milestone_transition(milestone=milestone, next_status=update_data["status"])
        if update_data["status"] == MilestoneStatus.COMPLETED:
            open_tickets = (
                await db.execute(
                    select(Ticket).where(
                        Ticket.milestone_id == milestone.id,
                        Ticket.status != TicketStatus.CLOSED,
                    )
                )
            ).scalars().all()
            if open_tickets:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Milestone cannot be completed while linked tickets remain open",
                )

    for field, value in update_data.items():
        setattr(milestone, field, value)
    milestone.updated_at = datetime.now(UTC)

    await record_audit_log(
        db,
        actor_id=current_user.id,
        tenant_id=project.tenant_id,
        action="milestone.updated",
        entity_type="milestone",
        entity_id=milestone.id,
        payload={"changes": payload.model_dump(exclude_unset=True, mode="json")},
    )
    await db.commit()
    await db.refresh(milestone)
    return milestone


@router.post(
    "/milestones/{milestone_id}/tasks",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_task_legacy(
    milestone_id: str,
    payload: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Task:
    require_roles(current_user, "project_manager", "developer", "admin", "support")

    milestone = await _get_milestone_or_404(milestone_id, db)
    project = await db.get(Project, milestone.project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    await ensure_tenant_access(db, current_user, project.tenant_id)

    assignee_id = decode_id_or_404(payload.assignee_id) if payload.assignee_id else None
    linked_ticket_id = (
        decode_id_or_404(payload.linked_ticket_id) if payload.linked_ticket_id else None
    )
    parent_task_id = decode_id_or_404(payload.parent_task_id) if payload.parent_task_id else None

    task = Task(
        project_id=project.id,
        milestone_id=milestone.id,
        parent_task_id=parent_task_id,
        assignee_id=assignee_id,
        linked_ticket_id=linked_ticket_id,
        title=payload.title,
        description=payload.description,
        status=payload.status,
        due_date=payload.due_date,
    )
    db.add(task)
    await db.flush()

    await record_audit_log(
        db,
        actor_id=current_user.id,
        tenant_id=project.tenant_id,
        action="task.created",
        entity_type="task",
        entity_id=task.id,
        payload={"project_id": project.id, "milestone_id": milestone.id},
    )
    await db.commit()
    await db.refresh(task)
    return task
