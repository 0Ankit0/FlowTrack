export type TicketType = 'bug' | 'incident' | 'service_request' | 'change_request';
export type TicketSeverity = 'low' | 'medium' | 'high' | 'critical';
export type TicketPriority = 'P1' | 'P2' | 'P3' | 'P4';
export type TicketStatus =
  | 'new'
  | 'awaiting_clarification'
  | 'triaged'
  | 'assigned'
  | 'in_progress'
  | 'blocked'
  | 'ready_for_qa'
  | 'closed'
  | 'reopened';

export type CommentVisibility = 'public' | 'internal';
export type AttachmentScanStatus = 'pending' | 'clean' | 'quarantined';
export type MilestoneStatus =
  | 'draft'
  | 'baselined'
  | 'in_progress'
  | 'at_risk'
  | 'replanning'
  | 'completed'
  | 'cancelled';
export type TaskStatus = 'todo' | 'in_progress' | 'blocked' | 'done' | 'cancelled';
export type ProjectStatus = 'draft' | 'active' | 'on_hold' | 'completed' | 'cancelled';
export type ProjectHealth = 'green' | 'amber' | 'red';
export type ReleaseStatus = 'planned' | 'in_progress' | 'deployed' | 'rolled_back';
export type ReleaseType = 'planned' | 'hotfix';

export interface TicketComment {
  id: string;
  ticket_id: string;
  author_id: string;
  visibility: CommentVisibility;
  body: string;
  created_at: string;
}

export interface TicketAttachment {
  id: string;
  ticket_id: string;
  uploaded_by_id: string;
  filename: string;
  mime_type: string;
  size_bytes: number;
  storage_key: string;
  scan_status: AttachmentScanStatus;
  extra_data: Record<string, unknown>;
  created_at: string;
}

export interface TicketAssignment {
  id: string;
  ticket_id: string;
  assignee_id: string;
  assigned_by_id: string;
  note: string;
  due_at?: string | null;
  assigned_at: string;
}

export interface Ticket {
  id: string;
  tenant_id: string;
  project_id?: string | null;
  milestone_id?: string | null;
  reporter_id: string;
  current_assignee_id?: string | null;
  title: string;
  description: string;
  category: string;
  environment: string;
  type: TicketType;
  severity: TicketSeverity;
  priority: TicketPriority;
  status: TicketStatus;
  first_responded_at?: string | null;
  resolved_at?: string | null;
  closed_at?: string | null;
  sla_first_response_due_at?: string | null;
  sla_resolution_due_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface TicketDetail extends Ticket {
  comments: TicketComment[];
  attachments: TicketAttachment[];
  assignments: TicketAssignment[];
}

export interface Project {
  id: string;
  tenant_id: string;
  owner_id?: string | null;
  name: string;
  description: string;
  status: ProjectStatus;
  health: ProjectHealth;
  start_date?: string | null;
  target_end_date?: string | null;
  budget_notes: string;
  created_at: string;
  updated_at: string;
}

export interface Milestone {
  id: string;
  project_id: string;
  owner_id?: string | null;
  name: string;
  status: MilestoneStatus;
  planned_date: string;
  forecast_date?: string | null;
  baseline_date?: string | null;
  dependency_ids: string[];
  completion_criteria: string[];
  created_at: string;
  updated_at: string;
}

export interface Task {
  id: string;
  project_id: string;
  milestone_id?: string | null;
  parent_task_id?: string | null;
  assignee_id?: string | null;
  linked_ticket_id?: string | null;
  title: string;
  description: string;
  status: TaskStatus;
  due_date?: string | null;
  extra_data: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface Release {
  id: string;
  project_id: string;
  milestone_id?: string | null;
  owner_id?: string | null;
  version: string;
  status: ReleaseStatus;
  release_type: ReleaseType;
  planned_at?: string | null;
  deployed_at?: string | null;
  ticket_ids: string[];
  task_ids: string[];
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectDetail extends Project {
  milestones: Milestone[];
  tasks: Task[];
  linked_ticket_count: number;
  releases: Release[];
}

export interface OperationalSummary {
  tenant_id: string;
  open_ticket_count: number;
  breached_ticket_count: number;
  project_count: number;
  active_project_count: number;
  milestone_completion_rate: number;
  workload_by_assignee: Record<string, number>;
}

export interface SlaPolicy {
  id: string;
  name: string;
  priority: TicketPriority;
  first_response_minutes: number;
  resolution_minutes: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TicketCreatePayload {
  tenant_id: string;
  project_id?: string;
  milestone_id?: string;
  title: string;
  description: string;
  category?: string;
  environment?: string;
  type: TicketType;
  severity: TicketSeverity;
  priority?: TicketPriority;
}

export interface TicketUpdatePayload {
  status?: TicketStatus;
  priority?: TicketPriority;
  project_id?: string;
  milestone_id?: string;
  category?: string;
  environment?: string;
}

export interface TicketCommentPayload {
  body: string;
  visibility: CommentVisibility;
}

export interface TicketAttachmentPayload {
  filename: string;
  mime_type: string;
  size_bytes: number;
  storage_key: string;
}

export interface TicketAssignmentPayload {
  assignee_id: string;
  note?: string;
  due_at?: string;
}

export interface ProjectCreatePayload {
  tenant_id: string;
  owner_id?: string;
  name: string;
  description?: string;
  status?: ProjectStatus;
  health?: ProjectHealth;
  start_date?: string;
  target_end_date?: string;
  budget_notes?: string;
}

export interface MilestoneCreatePayload {
  name: string;
  owner_id?: string;
  planned_date: string;
  forecast_date?: string;
  baseline_date?: string;
  dependency_ids?: string[];
  completion_criteria?: string[];
  status?: MilestoneStatus;
}

export interface TaskCreatePayload {
  title: string;
  description?: string;
  assignee_id?: string;
  due_date?: string;
  linked_ticket_id?: string;
  parent_task_id?: string;
  status?: TaskStatus;
}

export interface ReleaseCreatePayload {
  project_id: string;
  milestone_id?: string;
  owner_id?: string;
  version: string;
  status?: ReleaseStatus;
  release_type?: ReleaseType;
  planned_at?: string;
  deployed_at?: string;
  ticket_ids?: string[];
  task_ids?: string[];
  notes?: string;
}
