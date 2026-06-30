"""Shared application enums used by models and schemas."""

from __future__ import annotations

from enum import Enum

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class ProjectStatus(str, Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"

class MilestoneStatus(str, Enum):
    DRAFT = "draft"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELED = "canceled"

class ProjectHealth(str, Enum):
    HEALTHY = "healthy"
    STABLE = "stable"
    AT_RISK = "at_risk"
    CRITICAL = "critical"

class TaskStatus(str, Enum):
    PLANNED = "planned"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    IN_REVIEW = "in_review"
    COMPLETED = "completed"
    CANCELED = "canceled"

class TicketStatus(str, Enum):
    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"

class TicketActivityType(str, Enum):
    STATUS_CHANGED = "status_changed"
    ASSIGNED = "assigned"
    UNASSIGNED = "unassigned"
    COMMENT_ADDED = "comment_added"
    CREATED = "created"
    CLOSED = "closed"
    REOPENED = "reopened"

class UserStatus(str, Enum):
    ACTIVE = "active"
    INVITED = "invited"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"

class OrganizationStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"

class OrganizationMemberStatus(str, Enum):
    ACTIVE = "active"
    INVITED = "invited"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"

class RBACAction(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"

class RBACRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"

class RBACModule(str, Enum):
    USERS = "users"
    RBAC = "rbac"
    ORGANIZATIONS = "organizations"
    ORGANIZATION_MEMBERS = "organization_members"

class EmailProvider(str, Enum):
    SMTP = "smtp"

class PushProvider(str, Enum):
    FCM = "fcm"


def enum_values(enum_cls: type[Enum]) -> list[str]:
    """Return the string values for a Python enum."""

    return [member.value for member in enum_cls]
