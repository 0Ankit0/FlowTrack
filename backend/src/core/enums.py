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
    REOPENED = "reopened"

class TicketActivityType(str, Enum):
    ASSIGNED = "assigned"
    UNASSIGNED = "unassigned"
    COMMENT_ADDED = "comment_added"
    CREATED = "created"
    UPDATED = "updated"
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
    ORG_ADMIN = "org_admin"
    ORG_MANAGER = "org_manager"
    ORG_MEMBER = "org_member"

class ProjectRole(str, Enum):
    PROJECT_ADMIN = "project_admin"
    PROJECT_MANAGER = "project_manager"
    PROJECT_MEMBER = "project_member"
    PROJECT_VIEWER = "project_viewer"

class RBACModule(str, Enum):
    USERS = "users"
    RBAC = "rbac"
    ORGANIZATIONS = "organizations"
    ORGANIZATION_MEMBERS = "organization_members"
    PROJECTS = "projects"

class EmailProvider(str, Enum):
    SMTP = "smtp"

class PushProvider(str, Enum):
    FCM = "fcm"


def enum_values(enum_cls: type[Enum]) -> list[str]:
    """Return the string values for a Python enum."""

    return [member.value for member in enum_cls]
