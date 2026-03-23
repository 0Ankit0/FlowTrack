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

from ...models.enums import AttachmentScanStatus, CommentVisibility, Priority, Severity, TicketStatus
from ...models.project import Milestone, Project
from ...models.ticket import Assignment, Ticket, TicketAttachment, TicketComment
from ...schemas.ticket import (
    AssignmentCreate,
    AssignmentRead,
    AttachmentCreate,
    CommentCreate,
    TicketAttachmentRead,
    TicketCommentRead,
    TicketCreate,
    TicketDetailRead,
    TicketRead,
    TicketUpdate,
)
from ...services.audit import record_audit_log
from ...services.authz import ensure_tenant_access, is_internal_user, require_roles
from ...services.workflow import calculate_sla_targets, ensure_ticket_transition, resolve_priority

router = APIRouter(prefix="/tickets")

ALLOWED_ATTACHMENT_MIME_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}
MAX_ATTACHMENT_SIZE_BYTES = 10 * 1024 * 1024


async def _get_ticket_or_404(ticket_id: str, db: AsyncSession) -> Ticket:
    db_id = decode_id_or_404(ticket_id)
    ticket = await db.get(Ticket, db_id)
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return ticket


async def _validate_project_scope(
    db: AsyncSession,
    *,
    tenant_id: int,
    project_id: int | None,
    milestone_id: int | None,
) -> tuple[Project | None, Milestone | None]:
    project = None
    milestone = None
    if project_id is not None:
        project = await db.get(Project, project_id)
        if not project or project.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project does not belong to the selected organization",
            )
    if milestone_id is not None:
        milestone = await db.get(Milestone, milestone_id)
        if not milestone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Milestone does not exist",
            )
        if project is not None and milestone.project_id != project.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Milestone does not belong to the selected project",
            )
    return project, milestone


@router.post("/", response_model=TicketRead, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    payload: TicketCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Ticket:
    tenant_id = decode_id_or_404(payload.tenant_id)
    await ensure_tenant_access(db, current_user, tenant_id)

    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    project_id = decode_id_or_404(payload.project_id) if payload.project_id else None
    milestone_id = decode_id_or_404(payload.milestone_id) if payload.milestone_id else None
    await _validate_project_scope(
        db, tenant_id=tenant_id, project_id=project_id, milestone_id=milestone_id
    )

    priority = await resolve_priority(
        db, explicit_priority=payload.priority, severity=payload.severity
    )
    first_response_due_at, resolution_due_at = await calculate_sla_targets(
        db, priority=priority
    )

    ticket = Ticket(
        tenant_id=tenant_id,
        project_id=project_id,
        milestone_id=milestone_id,
        reporter_id=current_user.id,
        title=payload.title,
        description=payload.description,
        category=payload.category,
        environment=payload.environment,
        type=payload.type,
        severity=payload.severity,
        priority=priority,
        sla_first_response_due_at=first_response_due_at,
        sla_resolution_due_at=resolution_due_at,
    )
    db.add(ticket)
    await db.flush()

    await record_audit_log(
        db,
        actor_id=current_user.id,
        tenant_id=ticket.tenant_id,
        action="ticket.created",
        entity_type="ticket",
        entity_id=ticket.id,
        payload={"title": ticket.title, "priority": ticket.priority},
    )
    await db.commit()
    await db.refresh(ticket)
    return ticket


@router.get("/", response_model=PaginatedResponse[TicketRead])
async def list_tickets(
    tenant_id: str = Query(...),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    status_filter: TicketStatus | None = Query(default=None, alias="status"),
    project_id: str | None = Query(default=None),
    assignee_id: str | None = Query(default=None),
    priority: Priority | None = Query(default=None),
    severity: Severity | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[TicketRead]:
    tenant_db_id = decode_id_or_404(tenant_id)
    await ensure_tenant_access(db, current_user, tenant_db_id)

    base_query = select(Ticket).where(Ticket.tenant_id == tenant_db_id)
    count_query = select(func.count(col(Ticket.id))).where(Ticket.tenant_id == tenant_db_id)

    if status_filter is not None:
        base_query = base_query.where(Ticket.status == status_filter)
        count_query = count_query.where(Ticket.status == status_filter)
    if project_id is not None:
        project_db_id = decode_id_or_404(project_id)
        base_query = base_query.where(Ticket.project_id == project_db_id)
        count_query = count_query.where(Ticket.project_id == project_db_id)
    if assignee_id is not None:
        assignee_db_id = decode_id_or_404(assignee_id)
        base_query = base_query.where(Ticket.current_assignee_id == assignee_db_id)
        count_query = count_query.where(Ticket.current_assignee_id == assignee_db_id)
    if priority is not None:
        base_query = base_query.where(Ticket.priority == priority)
        count_query = count_query.where(Ticket.priority == priority)
    if severity is not None:
        base_query = base_query.where(Ticket.severity == severity)
        count_query = count_query.where(Ticket.severity == severity)

    total = (await db.execute(count_query)).one()[0]
    items = (
        await db.execute(base_query.order_by(Ticket.created_at.desc()).offset(skip).limit(limit))
    ).scalars().all()
    response_items = [TicketRead.model_validate(item) for item in items]
    return PaginatedResponse[TicketRead].create(
        items=response_items,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{ticket_id}", response_model=TicketDetailRead)
async def get_ticket(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TicketDetailRead:
    ticket = await _get_ticket_or_404(ticket_id, db)
    await ensure_tenant_access(db, current_user, ticket.tenant_id)

    comments_query = select(TicketComment).where(TicketComment.ticket_id == ticket.id)
    if not is_internal_user(current_user):
        comments_query = comments_query.where(
            TicketComment.visibility == CommentVisibility.PUBLIC
        )

    comments = (
        await db.execute(comments_query.order_by(TicketComment.created_at.asc()))
    ).scalars().all()
    attachments = (
        await db.execute(
            select(TicketAttachment)
            .where(TicketAttachment.ticket_id == ticket.id)
            .order_by(TicketAttachment.created_at.asc())
        )
    ).scalars().all()
    assignments = (
        await db.execute(
            select(Assignment)
            .where(Assignment.ticket_id == ticket.id)
            .order_by(Assignment.assigned_at.asc())
        )
    ).scalars().all()

    return TicketDetailRead.model_validate(
        {
            **ticket.model_dump(),
            "comments": [TicketCommentRead.model_validate(item) for item in comments],
            "attachments": [
                TicketAttachmentRead.model_validate(item) for item in attachments
            ],
            "assignments": [AssignmentRead.model_validate(item) for item in assignments],
        }
    )


@router.patch("/{ticket_id}", response_model=TicketRead)
async def update_ticket(
    ticket_id: str,
    payload: TicketUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Ticket:
    ticket = await _get_ticket_or_404(ticket_id, db)
    await ensure_tenant_access(db, current_user, ticket.tenant_id)

    update_data = payload.model_dump(exclude_unset=True)

    if "project_id" in update_data:
        update_data["project_id"] = (
            decode_id_or_404(update_data["project_id"]) if update_data["project_id"] else None
        )
    if "milestone_id" in update_data:
        update_data["milestone_id"] = (
            decode_id_or_404(update_data["milestone_id"]) if update_data["milestone_id"] else None
        )

    project_id = update_data.get("project_id", ticket.project_id)
    milestone_id = update_data.get("milestone_id", ticket.milestone_id)
    await _validate_project_scope(
        db, tenant_id=ticket.tenant_id, project_id=project_id, milestone_id=milestone_id
    )

    if "status" in update_data and update_data["status"] is not None:
        ensure_ticket_transition(
            ticket=ticket,
            next_status=update_data["status"],
            actor=current_user,
        )
        if update_data["status"] == TicketStatus.CLOSED:
            ticket.closed_at = datetime.now(UTC)
        elif update_data["status"] == TicketStatus.READY_FOR_QA:
            ticket.resolved_at = datetime.now(UTC)
        elif update_data["status"] == TicketStatus.REOPENED:
            ticket.closed_at = None

    if "priority" in update_data or "severity" in update_data:
        priority = await resolve_priority(
            db,
            explicit_priority=update_data.get("priority", ticket.priority),
            severity=update_data.get("severity", ticket.severity),
        )
        first_response_due_at, resolution_due_at = await calculate_sla_targets(
            db, priority=priority, created_at=ticket.created_at
        )
        ticket.priority = priority
        ticket.sla_first_response_due_at = first_response_due_at
        ticket.sla_resolution_due_at = resolution_due_at
        update_data.pop("priority", None)

    for field, value in update_data.items():
        setattr(ticket, field, value)

    if is_internal_user(current_user) and ticket.first_responded_at is None:
        ticket.first_responded_at = datetime.now(UTC)

    ticket.updated_at = datetime.now(UTC)
    await record_audit_log(
        db,
        actor_id=current_user.id,
        tenant_id=ticket.tenant_id,
        action="ticket.updated",
        entity_type="ticket",
        entity_id=ticket.id,
        payload={"changes": payload.model_dump(exclude_unset=True, mode="json")},
    )
    await db.commit()
    await db.refresh(ticket)
    return ticket


@router.post("/{ticket_id}/comments", response_model=TicketCommentRead, status_code=status.HTTP_201_CREATED)
async def add_comment(
    ticket_id: str,
    payload: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TicketComment:
    ticket = await _get_ticket_or_404(ticket_id, db)
    await ensure_tenant_access(db, current_user, ticket.tenant_id)

    if payload.visibility == CommentVisibility.INTERNAL and not is_internal_user(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Client users cannot create internal comments",
        )

    comment = TicketComment(
        ticket_id=ticket.id,
        author_id=current_user.id,
        visibility=payload.visibility,
        body=payload.body,
    )
    db.add(comment)

    if ticket.status == TicketStatus.AWAITING_CLARIFICATION and payload.visibility == CommentVisibility.PUBLIC:
        ticket.status = TicketStatus.TRIAGED
        ticket.updated_at = datetime.now(UTC)

    await db.flush()
    await record_audit_log(
        db,
        actor_id=current_user.id,
        tenant_id=ticket.tenant_id,
        action="ticket.comment_added",
        entity_type="ticket_comment",
        entity_id=comment.id,
        payload={"ticket_id": ticket.id, "visibility": comment.visibility},
    )
    await db.commit()
    await db.refresh(comment)
    return comment


@router.post(
    "/{ticket_id}/attachments",
    response_model=TicketAttachmentRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_attachment(
    ticket_id: str,
    payload: AttachmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TicketAttachment:
    ticket = await _get_ticket_or_404(ticket_id, db)
    await ensure_tenant_access(db, current_user, ticket.tenant_id)
    if payload.mime_type not in ALLOWED_ATTACHMENT_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported attachment type. Only standard image formats are allowed.",
        )
    if payload.size_bytes > MAX_ATTACHMENT_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attachment exceeds the 10 MB size limit.",
        )

    attachment = TicketAttachment(
        ticket_id=ticket.id,
        uploaded_by_id=current_user.id,
        filename=payload.filename,
        mime_type=payload.mime_type,
        size_bytes=payload.size_bytes,
        storage_key=payload.storage_key,
        scan_status=AttachmentScanStatus.PENDING,
    )
    db.add(attachment)
    await db.flush()

    await record_audit_log(
        db,
        actor_id=current_user.id,
        tenant_id=ticket.tenant_id,
        action="ticket.attachment_registered",
        entity_type="ticket_attachment",
        entity_id=attachment.id,
        payload={"ticket_id": ticket.id, "filename": attachment.filename},
    )
    await db.commit()
    await db.refresh(attachment)
    return attachment


@router.post(
    "/{ticket_id}/assignments",
    response_model=AssignmentRead,
    status_code=status.HTTP_201_CREATED,
)
async def assign_ticket(
    ticket_id: str,
    payload: AssignmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Assignment:
    require_roles(current_user, "support", "project_manager", "admin")

    ticket = await _get_ticket_or_404(ticket_id, db)
    await ensure_tenant_access(db, current_user, ticket.tenant_id)
    assignee_id = decode_id_or_404(payload.assignee_id)

    assignee = await db.get(User, assignee_id)
    if not assignee or not assignee.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignee not found")

    assignment = Assignment(
        ticket_id=ticket.id,
        assignee_id=assignee_id,
        assigned_by_id=current_user.id,
        note=payload.note,
        due_at=payload.due_at,
    )
    db.add(assignment)
    ticket.current_assignee_id = assignee_id
    if ticket.status in {
        TicketStatus.NEW,
        TicketStatus.TRIAGED,
        TicketStatus.AWAITING_CLARIFICATION,
    }:
        ticket.status = TicketStatus.ASSIGNED
    if ticket.first_responded_at is None:
        ticket.first_responded_at = datetime.now(UTC)
    ticket.updated_at = datetime.now(UTC)
    await db.flush()

    await record_audit_log(
        db,
        actor_id=current_user.id,
        tenant_id=ticket.tenant_id,
        action="ticket.assigned",
        entity_type="assignment",
        entity_id=assignment.id,
        payload={"ticket_id": ticket.id, "assignee_id": assignee_id},
    )
    await db.commit()
    await db.refresh(assignment)
    return assignment
