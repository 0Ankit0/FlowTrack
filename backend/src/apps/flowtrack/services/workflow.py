from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.apps.iam.models.user import User

from ..models.enums import MilestoneStatus, Priority, Severity, TicketStatus
from ..models.project import Milestone
from ..models.ticket import SlaPolicy, Ticket
from .authz import require_roles


TICKET_TRANSITIONS: dict[TicketStatus, set[TicketStatus]] = {
    TicketStatus.NEW: {TicketStatus.AWAITING_CLARIFICATION, TicketStatus.TRIAGED},
    TicketStatus.AWAITING_CLARIFICATION: {TicketStatus.TRIAGED},
    TicketStatus.TRIAGED: {TicketStatus.ASSIGNED},
    TicketStatus.ASSIGNED: {TicketStatus.IN_PROGRESS},
    TicketStatus.IN_PROGRESS: {TicketStatus.BLOCKED, TicketStatus.READY_FOR_QA},
    TicketStatus.BLOCKED: {TicketStatus.IN_PROGRESS},
    TicketStatus.READY_FOR_QA: {TicketStatus.REOPENED, TicketStatus.CLOSED},
    TicketStatus.REOPENED: {TicketStatus.IN_PROGRESS},
    TicketStatus.CLOSED: {TicketStatus.REOPENED},
}

MILESTONE_TRANSITIONS: dict[MilestoneStatus, set[MilestoneStatus]] = {
    MilestoneStatus.DRAFT: {MilestoneStatus.BASELINED, MilestoneStatus.CANCELLED},
    MilestoneStatus.BASELINED: {MilestoneStatus.IN_PROGRESS, MilestoneStatus.CANCELLED},
    MilestoneStatus.IN_PROGRESS: {
        MilestoneStatus.AT_RISK,
        MilestoneStatus.COMPLETED,
    },
    MilestoneStatus.AT_RISK: {MilestoneStatus.IN_PROGRESS, MilestoneStatus.REPLANNING},
    MilestoneStatus.REPLANNING: {MilestoneStatus.BASELINED},
}

DEFAULT_SLA_MINUTES: dict[Priority, tuple[int, int]] = {
    Priority.P1: (15, 240),
    Priority.P2: (60, 60 * 24),
    Priority.P3: (240, 60 * 24 * 5),
    Priority.P4: (60 * 24, 60 * 24 * 10),
}

SEVERITY_TO_PRIORITY = {
    Severity.CRITICAL: Priority.P1,
    Severity.HIGH: Priority.P2,
    Severity.MEDIUM: Priority.P3,
    Severity.LOW: Priority.P4,
}


async def resolve_priority(
    db: AsyncSession,
    *,
    explicit_priority: Priority | None,
    severity: Severity,
) -> Priority:
    if explicit_priority is not None:
        return explicit_priority

    return SEVERITY_TO_PRIORITY[severity]


async def calculate_sla_targets(
    db: AsyncSession, *, priority: Priority, created_at: datetime | None = None
) -> tuple[datetime, datetime]:
    created_at = created_at or datetime.now(UTC)
    policy = (
        await db.execute(
            select(SlaPolicy).where(SlaPolicy.priority == priority, SlaPolicy.is_active == True)
        )
    ).scalars().first()

    first_response_minutes, resolution_minutes = DEFAULT_SLA_MINUTES[priority]
    if policy:
        first_response_minutes = policy.first_response_minutes
        resolution_minutes = policy.resolution_minutes

    return (
        created_at + timedelta(minutes=first_response_minutes),
        created_at + timedelta(minutes=resolution_minutes),
    )


def ensure_ticket_transition(
    *,
    ticket: Ticket,
    next_status: TicketStatus,
    actor: User,
) -> None:
    current_status = ticket.status
    if next_status == current_status:
        return

    allowed = TICKET_TRANSITIONS.get(current_status, set())
    if next_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ticket transition from {current_status} to {next_status}",
        )

    if next_status == TicketStatus.CLOSED:
        require_roles(actor, "support", "project_manager", "qa_reviewer", "admin")


def ensure_milestone_transition(
    *,
    milestone: Milestone,
    next_status: MilestoneStatus,
) -> None:
    current_status = milestone.status
    if next_status == current_status:
        return

    allowed = MILESTONE_TRANSITIONS.get(current_status, set())
    if next_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid milestone transition from {current_status} to {next_status}",
        )
