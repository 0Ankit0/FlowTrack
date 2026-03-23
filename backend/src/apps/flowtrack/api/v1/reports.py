from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, func, select

from src.apps.iam.api.deps import get_current_user, get_db
from src.apps.iam.models.user import User
from src.apps.iam.utils.hashid import decode_id_or_404, encode_id

from ...models.enums import MilestoneStatus, ProjectStatus, TicketStatus
from ...models.project import Milestone, Project
from ...models.ticket import Ticket
from ...schemas.admin import OperationalSummaryRead
from ...services.authz import ensure_tenant_access, require_roles

router = APIRouter(prefix="/reports")


@router.get("/operational-summary", response_model=OperationalSummaryRead)
async def get_operational_summary(
    tenant_id: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OperationalSummaryRead:
    require_roles(current_user, "support", "project_manager", "developer", "qa_reviewer", "admin")

    tenant_db_id = decode_id_or_404(tenant_id)
    await ensure_tenant_access(db, current_user, tenant_db_id)

    now = datetime.now(UTC)
    open_ticket_count = (
        await db.execute(
            select(func.count(col(Ticket.id))).where(
                Ticket.tenant_id == tenant_db_id,
                Ticket.status != TicketStatus.CLOSED,
            )
        )
    ).one()[0]
    breached_ticket_count = (
        await db.execute(
            select(func.count(col(Ticket.id))).where(
                Ticket.tenant_id == tenant_db_id,
                Ticket.status != TicketStatus.CLOSED,
                Ticket.sla_resolution_due_at < now,
            )
        )
    ).one()[0]
    project_count = (
        await db.execute(select(func.count(col(Project.id))).where(Project.tenant_id == tenant_db_id))
    ).one()[0]
    active_project_count = (
        await db.execute(
            select(func.count(col(Project.id))).where(
                Project.tenant_id == tenant_db_id,
                Project.status == ProjectStatus.ACTIVE,
            )
        )
    ).one()[0]

    total_milestones = (
        await db.execute(
            select(func.count(col(Milestone.id)))
            .join(Project, Project.id == Milestone.project_id)
            .where(Project.tenant_id == tenant_db_id)
        )
    ).one()[0]
    completed_milestones = (
        await db.execute(
            select(func.count(col(Milestone.id)))
            .join(Project, Project.id == Milestone.project_id)
            .where(
                Project.tenant_id == tenant_db_id,
                Milestone.status == MilestoneStatus.COMPLETED,
            )
        )
    ).one()[0]
    milestone_completion_rate = (
        round(completed_milestones / total_milestones, 2) if total_milestones else 0.0
    )

    workload_rows = (
        await db.execute(
            select(Ticket.current_assignee_id, func.count(col(Ticket.id)))
            .where(
                Ticket.tenant_id == tenant_db_id,
                Ticket.status != TicketStatus.CLOSED,
                Ticket.current_assignee_id != None,
            )
            .group_by(Ticket.current_assignee_id)
        )
    ).all()
    workload_by_assignee = {
        encode_id(assignee_id): count for assignee_id, count in workload_rows if assignee_id is not None
    }

    return OperationalSummaryRead(
        tenant_id=encode_id(tenant_db_id),
        open_ticket_count=open_ticket_count,
        breached_ticket_count=breached_ticket_count,
        project_count=project_count,
        active_project_count=active_project_count,
        milestone_completion_rate=milestone_completion_rate,
        workload_by_assignee=workload_by_assignee,
    )
