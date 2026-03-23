from enum import Enum


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ProjectHealth(str, Enum):
    GREEN = "green"
    AMBER = "amber"
    RED = "red"


class MilestoneStatus(str, Enum):
    DRAFT = "draft"
    BASELINED = "baselined"
    IN_PROGRESS = "in_progress"
    AT_RISK = "at_risk"
    REPLANNING = "replanning"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"
    CANCELLED = "cancelled"


class ReleaseStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    DEPLOYED = "deployed"
    ROLLED_BACK = "rolled_back"


class ReleaseType(str, Enum):
    PLANNED = "planned"
    HOTFIX = "hotfix"


class TicketType(str, Enum):
    BUG = "bug"
    INCIDENT = "incident"
    SERVICE_REQUEST = "service_request"
    CHANGE_REQUEST = "change_request"


class Priority(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketStatus(str, Enum):
    NEW = "new"
    AWAITING_CLARIFICATION = "awaiting_clarification"
    TRIAGED = "triaged"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    READY_FOR_QA = "ready_for_qa"
    CLOSED = "closed"
    REOPENED = "reopened"


class CommentVisibility(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"


class AttachmentScanStatus(str, Enum):
    PENDING = "pending"
    CLEAN = "clean"
    QUARANTINED = "quarantined"
