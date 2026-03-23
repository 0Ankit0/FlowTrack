from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.apps.iam.api.deps import get_current_user, get_db
from src.apps.iam.models.user import User
from src.apps.iam.utils.hashid import decode_id_or_404

from ...models.enums import MilestoneStatus, TicketStatus
from ...models.project import Milestone, Project, Task
from ...models.ticket import Ticket
from ...schemas.project import MilestoneRead, MilestoneUpdate, TaskCreate, TaskRead
from ...services.audit import record_audit_log
from ...services.authz import ensure_tenant_access, require_roles
from ...services.workflow import ensure_milestone_transition

router = APIRouter(prefix="/milestones")


async def _get_milestone_or_404(milestone_id: str, db: AsyncSession) -> Milestone:
    db_id = decode_id_or_404(milestone_id)
    milestone = await db.get(Milestone, db_id)
    if not milestone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Milestone not found")
    return milestone


@router.patch("/{milestone_id}", response_model=MilestoneRead)
async def update_milestone(
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


@router.post("/{milestone_id}/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
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
