from datetime import UTC, datetime

import pytest

from src.apps.flowtrack.models.enums import Priority, Severity, TicketStatus
from src.apps.flowtrack.models.ticket import Ticket
from src.apps.flowtrack.services.workflow import (
    DEFAULT_SLA_MINUTES,
    SEVERITY_TO_PRIORITY,
    ensure_ticket_transition,
)
from src.apps.iam.models.user import User
from src.apps.iam.models.role import Role, UserRole


def _user_with_roles(*role_names: str) -> User:
    user = User(id=1, username="tester", email="tester@example.com", is_active=True)
    roles = []
    for index, role_name in enumerate(role_names, start=1):
        roles.append(
            UserRole(
                id=index,
                user_id=1,
                role_id=index,
                role=Role(id=index, name=role_name, description=role_name),
            )
        )
    user.user_roles = roles
    return user


def test_severity_maps_to_expected_priority():
    assert SEVERITY_TO_PRIORITY[Severity.CRITICAL] == Priority.P1
    assert SEVERITY_TO_PRIORITY[Severity.HIGH] == Priority.P2
    assert SEVERITY_TO_PRIORITY[Severity.MEDIUM] == Priority.P3
    assert SEVERITY_TO_PRIORITY[Severity.LOW] == Priority.P4
    assert DEFAULT_SLA_MINUTES[Priority.P1] == (15, 240)


def test_only_authorized_roles_can_close_ticket():
    ticket = Ticket(
        id=1,
        tenant_id=1,
        reporter_id=1,
        title="Broken export",
        description="Export is empty",
        status=TicketStatus.READY_FOR_QA,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    qa_user = _user_with_roles("qa_reviewer")
    ensure_ticket_transition(ticket=ticket, next_status=TicketStatus.CLOSED, actor=qa_user)

    developer_user = _user_with_roles("developer")
    with pytest.raises(Exception):
        ensure_ticket_transition(ticket=ticket, next_status=TicketStatus.CLOSED, actor=developer_user)
