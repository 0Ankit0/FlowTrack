import '../../../../core/models/paginated_response.dart';

List<String> _asStringList(dynamic value) {
  final items = value as List<dynamic>? ?? <dynamic>[];
  return items.map((item) => item.toString()).toList();
}

Map<String, int> _asIntMap(dynamic value) {
  final map = value as Map<String, dynamic>? ?? <String, dynamic>{};
  return map.map((key, entry) => MapEntry(key, (entry as num).toInt()));
}

String? _stringOrNull(dynamic value) {
  final text = value?.toString();
  if (text == null || text.isEmpty) return null;
  return text;
}

class WorkspaceTenant {
  final String id;
  final String name;
  final String slug;
  final String description;

  const WorkspaceTenant({
    required this.id,
    required this.name,
    required this.slug,
    required this.description,
  });

  factory WorkspaceTenant.fromJson(Map<String, dynamic> json) {
    return WorkspaceTenant(
      id: json['id'].toString(),
      name: json['name'] as String? ?? 'Workspace',
      slug: json['slug'] as String? ?? '',
      description: json['description'] as String? ?? '',
    );
  }
}

class FlowtrackOperationalSummary {
  final String tenantId;
  final int openTicketCount;
  final int breachedTicketCount;
  final int projectCount;
  final int activeProjectCount;
  final double milestoneCompletionRate;
  final Map<String, int> workloadByAssignee;

  const FlowtrackOperationalSummary({
    required this.tenantId,
    required this.openTicketCount,
    required this.breachedTicketCount,
    required this.projectCount,
    required this.activeProjectCount,
    required this.milestoneCompletionRate,
    required this.workloadByAssignee,
  });

  factory FlowtrackOperationalSummary.fromJson(Map<String, dynamic> json) {
    return FlowtrackOperationalSummary(
      tenantId: json['tenant_id'].toString(),
      openTicketCount: (json['open_ticket_count'] as num? ?? 0).toInt(),
      breachedTicketCount: (json['breached_ticket_count'] as num? ?? 0).toInt(),
      projectCount: (json['project_count'] as num? ?? 0).toInt(),
      activeProjectCount: (json['active_project_count'] as num? ?? 0).toInt(),
      milestoneCompletionRate: (json['milestone_completion_rate'] as num? ?? 0)
          .toDouble(),
      workloadByAssignee: _asIntMap(json['workload_by_assignee']),
    );
  }
}

class FlowtrackTicket {
  final String id;
  final String tenantId;
  final String? projectId;
  final String? milestoneId;
  final String reporterId;
  final String? currentAssigneeId;
  final String title;
  final String description;
  final String category;
  final String environment;
  final String type;
  final String severity;
  final String priority;
  final String status;
  final String? firstRespondedAt;
  final String? resolvedAt;
  final String? closedAt;
  final String? slaFirstResponseDueAt;
  final String? slaResolutionDueAt;
  final String createdAt;
  final String updatedAt;

  const FlowtrackTicket({
    required this.id,
    required this.tenantId,
    required this.projectId,
    required this.milestoneId,
    required this.reporterId,
    required this.currentAssigneeId,
    required this.title,
    required this.description,
    required this.category,
    required this.environment,
    required this.type,
    required this.severity,
    required this.priority,
    required this.status,
    required this.firstRespondedAt,
    required this.resolvedAt,
    required this.closedAt,
    required this.slaFirstResponseDueAt,
    required this.slaResolutionDueAt,
    required this.createdAt,
    required this.updatedAt,
  });

  factory FlowtrackTicket.fromJson(Map<String, dynamic> json) {
    return FlowtrackTicket(
      id: json['id'].toString(),
      tenantId: json['tenant_id'].toString(),
      projectId: _stringOrNull(json['project_id']),
      milestoneId: _stringOrNull(json['milestone_id']),
      reporterId: json['reporter_id'].toString(),
      currentAssigneeId: _stringOrNull(json['current_assignee_id']),
      title: json['title'] as String? ?? '',
      description: json['description'] as String? ?? '',
      category: json['category'] as String? ?? '',
      environment: json['environment'] as String? ?? '',
      type: json['type'] as String? ?? 'bug',
      severity: json['severity'] as String? ?? 'medium',
      priority: json['priority'] as String? ?? 'P3',
      status: json['status'] as String? ?? 'new',
      firstRespondedAt: _stringOrNull(json['first_responded_at']),
      resolvedAt: _stringOrNull(json['resolved_at']),
      closedAt: _stringOrNull(json['closed_at']),
      slaFirstResponseDueAt: _stringOrNull(json['sla_first_response_due_at']),
      slaResolutionDueAt: _stringOrNull(json['sla_resolution_due_at']),
      createdAt: json['created_at'] as String? ?? '',
      updatedAt: json['updated_at'] as String? ?? '',
    );
  }
}

class FlowtrackTicketComment {
  final String id;
  final String ticketId;
  final String authorId;
  final String visibility;
  final String body;
  final String createdAt;

  const FlowtrackTicketComment({
    required this.id,
    required this.ticketId,
    required this.authorId,
    required this.visibility,
    required this.body,
    required this.createdAt,
  });

  factory FlowtrackTicketComment.fromJson(Map<String, dynamic> json) {
    return FlowtrackTicketComment(
      id: json['id'].toString(),
      ticketId: json['ticket_id'].toString(),
      authorId: json['author_id'].toString(),
      visibility: json['visibility'] as String? ?? 'public',
      body: json['body'] as String? ?? '',
      createdAt: json['created_at'] as String? ?? '',
    );
  }
}

class FlowtrackTicketAttachment {
  final String id;
  final String filename;
  final String mimeType;
  final int sizeBytes;
  final String scanStatus;
  final String createdAt;

  const FlowtrackTicketAttachment({
    required this.id,
    required this.filename,
    required this.mimeType,
    required this.sizeBytes,
    required this.scanStatus,
    required this.createdAt,
  });

  factory FlowtrackTicketAttachment.fromJson(Map<String, dynamic> json) {
    return FlowtrackTicketAttachment(
      id: json['id'].toString(),
      filename: json['filename'] as String? ?? '',
      mimeType: json['mime_type'] as String? ?? '',
      sizeBytes: (json['size_bytes'] as num? ?? 0).toInt(),
      scanStatus: json['scan_status'] as String? ?? 'pending',
      createdAt: json['created_at'] as String? ?? '',
    );
  }
}

class FlowtrackTicketAssignment {
  final String id;
  final String assigneeId;
  final String assignedById;
  final String note;
  final String? dueAt;
  final String assignedAt;

  const FlowtrackTicketAssignment({
    required this.id,
    required this.assigneeId,
    required this.assignedById,
    required this.note,
    required this.dueAt,
    required this.assignedAt,
  });

  factory FlowtrackTicketAssignment.fromJson(Map<String, dynamic> json) {
    return FlowtrackTicketAssignment(
      id: json['id'].toString(),
      assigneeId: json['assignee_id'].toString(),
      assignedById: json['assigned_by_id'].toString(),
      note: json['note'] as String? ?? '',
      dueAt: _stringOrNull(json['due_at']),
      assignedAt: json['assigned_at'] as String? ?? '',
    );
  }
}

class FlowtrackTicketDetail extends FlowtrackTicket {
  final List<FlowtrackTicketComment> comments;
  final List<FlowtrackTicketAttachment> attachments;
  final List<FlowtrackTicketAssignment> assignments;

  const FlowtrackTicketDetail({
    required super.id,
    required super.tenantId,
    required super.projectId,
    required super.milestoneId,
    required super.reporterId,
    required super.currentAssigneeId,
    required super.title,
    required super.description,
    required super.category,
    required super.environment,
    required super.type,
    required super.severity,
    required super.priority,
    required super.status,
    required super.firstRespondedAt,
    required super.resolvedAt,
    required super.closedAt,
    required super.slaFirstResponseDueAt,
    required super.slaResolutionDueAt,
    required super.createdAt,
    required super.updatedAt,
    required this.comments,
    required this.attachments,
    required this.assignments,
  });

  factory FlowtrackTicketDetail.fromJson(Map<String, dynamic> json) {
    final ticket = FlowtrackTicket.fromJson(json);
    final comments = json['comments'] as List<dynamic>? ?? <dynamic>[];
    final attachments = json['attachments'] as List<dynamic>? ?? <dynamic>[];
    final assignments = json['assignments'] as List<dynamic>? ?? <dynamic>[];

    return FlowtrackTicketDetail(
      id: ticket.id,
      tenantId: ticket.tenantId,
      projectId: ticket.projectId,
      milestoneId: ticket.milestoneId,
      reporterId: ticket.reporterId,
      currentAssigneeId: ticket.currentAssigneeId,
      title: ticket.title,
      description: ticket.description,
      category: ticket.category,
      environment: ticket.environment,
      type: ticket.type,
      severity: ticket.severity,
      priority: ticket.priority,
      status: ticket.status,
      firstRespondedAt: ticket.firstRespondedAt,
      resolvedAt: ticket.resolvedAt,
      closedAt: ticket.closedAt,
      slaFirstResponseDueAt: ticket.slaFirstResponseDueAt,
      slaResolutionDueAt: ticket.slaResolutionDueAt,
      createdAt: ticket.createdAt,
      updatedAt: ticket.updatedAt,
      comments: comments
          .map(
            (item) =>
                FlowtrackTicketComment.fromJson(item as Map<String, dynamic>),
          )
          .toList(),
      attachments: attachments
          .map(
            (item) => FlowtrackTicketAttachment.fromJson(
              item as Map<String, dynamic>,
            ),
          )
          .toList(),
      assignments: assignments
          .map(
            (item) => FlowtrackTicketAssignment.fromJson(
              item as Map<String, dynamic>,
            ),
          )
          .toList(),
    );
  }
}

class FlowtrackMilestone {
  final String id;
  final String projectId;
  final String? ownerId;
  final String name;
  final String status;
  final String plannedDate;
  final String? forecastDate;
  final String? baselineDate;
  final List<String> dependencyIds;
  final List<String> completionCriteria;
  final String createdAt;
  final String updatedAt;

  const FlowtrackMilestone({
    required this.id,
    required this.projectId,
    required this.ownerId,
    required this.name,
    required this.status,
    required this.plannedDate,
    required this.forecastDate,
    required this.baselineDate,
    required this.dependencyIds,
    required this.completionCriteria,
    required this.createdAt,
    required this.updatedAt,
  });

  factory FlowtrackMilestone.fromJson(Map<String, dynamic> json) {
    return FlowtrackMilestone(
      id: json['id'].toString(),
      projectId: json['project_id'].toString(),
      ownerId: _stringOrNull(json['owner_id']),
      name: json['name'] as String? ?? '',
      status: json['status'] as String? ?? 'draft',
      plannedDate: json['planned_date'] as String? ?? '',
      forecastDate: _stringOrNull(json['forecast_date']),
      baselineDate: _stringOrNull(json['baseline_date']),
      dependencyIds: _asStringList(json['dependency_ids']),
      completionCriteria: _asStringList(json['completion_criteria']),
      createdAt: json['created_at'] as String? ?? '',
      updatedAt: json['updated_at'] as String? ?? '',
    );
  }
}

class FlowtrackTask {
  final String id;
  final String projectId;
  final String? milestoneId;
  final String? parentTaskId;
  final String? assigneeId;
  final String? linkedTicketId;
  final String title;
  final String description;
  final String status;
  final String? dueDate;
  final String createdAt;
  final String updatedAt;

  const FlowtrackTask({
    required this.id,
    required this.projectId,
    required this.milestoneId,
    required this.parentTaskId,
    required this.assigneeId,
    required this.linkedTicketId,
    required this.title,
    required this.description,
    required this.status,
    required this.dueDate,
    required this.createdAt,
    required this.updatedAt,
  });

  factory FlowtrackTask.fromJson(Map<String, dynamic> json) {
    return FlowtrackTask(
      id: json['id'].toString(),
      projectId: json['project_id'].toString(),
      milestoneId: _stringOrNull(json['milestone_id']),
      parentTaskId: _stringOrNull(json['parent_task_id']),
      assigneeId: _stringOrNull(json['assignee_id']),
      linkedTicketId: _stringOrNull(json['linked_ticket_id']),
      title: json['title'] as String? ?? '',
      description: json['description'] as String? ?? '',
      status: json['status'] as String? ?? 'todo',
      dueDate: _stringOrNull(json['due_date']),
      createdAt: json['created_at'] as String? ?? '',
      updatedAt: json['updated_at'] as String? ?? '',
    );
  }
}

class FlowtrackRelease {
  final String id;
  final String projectId;
  final String? milestoneId;
  final String? ownerId;
  final String version;
  final String status;
  final String releaseType;
  final String? plannedAt;
  final String? deployedAt;
  final List<String> ticketIds;
  final List<String> taskIds;
  final String notes;
  final String createdAt;
  final String updatedAt;

  const FlowtrackRelease({
    required this.id,
    required this.projectId,
    required this.milestoneId,
    required this.ownerId,
    required this.version,
    required this.status,
    required this.releaseType,
    required this.plannedAt,
    required this.deployedAt,
    required this.ticketIds,
    required this.taskIds,
    required this.notes,
    required this.createdAt,
    required this.updatedAt,
  });

  factory FlowtrackRelease.fromJson(Map<String, dynamic> json) {
    return FlowtrackRelease(
      id: json['id'].toString(),
      projectId: json['project_id'].toString(),
      milestoneId: _stringOrNull(json['milestone_id']),
      ownerId: _stringOrNull(json['owner_id']),
      version: json['version'] as String? ?? '',
      status: json['status'] as String? ?? 'planned',
      releaseType: json['release_type'] as String? ?? 'planned',
      plannedAt: _stringOrNull(json['planned_at']),
      deployedAt: _stringOrNull(json['deployed_at']),
      ticketIds: _asStringList(json['ticket_ids']),
      taskIds: _asStringList(json['task_ids']),
      notes: json['notes'] as String? ?? '',
      createdAt: json['created_at'] as String? ?? '',
      updatedAt: json['updated_at'] as String? ?? '',
    );
  }
}

class FlowtrackProject {
  final String id;
  final String tenantId;
  final String? ownerId;
  final String name;
  final String description;
  final String status;
  final String health;
  final String? startDate;
  final String? targetEndDate;
  final String budgetNotes;
  final String createdAt;
  final String updatedAt;

  const FlowtrackProject({
    required this.id,
    required this.tenantId,
    required this.ownerId,
    required this.name,
    required this.description,
    required this.status,
    required this.health,
    required this.startDate,
    required this.targetEndDate,
    required this.budgetNotes,
    required this.createdAt,
    required this.updatedAt,
  });

  factory FlowtrackProject.fromJson(Map<String, dynamic> json) {
    return FlowtrackProject(
      id: json['id'].toString(),
      tenantId: json['tenant_id'].toString(),
      ownerId: _stringOrNull(json['owner_id']),
      name: json['name'] as String? ?? '',
      description: json['description'] as String? ?? '',
      status: json['status'] as String? ?? 'draft',
      health: json['health'] as String? ?? 'green',
      startDate: _stringOrNull(json['start_date']),
      targetEndDate: _stringOrNull(json['target_end_date']),
      budgetNotes: json['budget_notes'] as String? ?? '',
      createdAt: json['created_at'] as String? ?? '',
      updatedAt: json['updated_at'] as String? ?? '',
    );
  }
}

class FlowtrackProjectDetail extends FlowtrackProject {
  final List<FlowtrackMilestone> milestones;
  final List<FlowtrackTask> tasks;
  final int linkedTicketCount;
  final List<FlowtrackRelease> releases;

  const FlowtrackProjectDetail({
    required super.id,
    required super.tenantId,
    required super.ownerId,
    required super.name,
    required super.description,
    required super.status,
    required super.health,
    required super.startDate,
    required super.targetEndDate,
    required super.budgetNotes,
    required super.createdAt,
    required super.updatedAt,
    required this.milestones,
    required this.tasks,
    required this.linkedTicketCount,
    required this.releases,
  });

  factory FlowtrackProjectDetail.fromJson(Map<String, dynamic> json) {
    final project = FlowtrackProject.fromJson(json);
    final milestones = json['milestones'] as List<dynamic>? ?? <dynamic>[];
    final tasks = json['tasks'] as List<dynamic>? ?? <dynamic>[];
    final releases = json['releases'] as List<dynamic>? ?? <dynamic>[];

    return FlowtrackProjectDetail(
      id: project.id,
      tenantId: project.tenantId,
      ownerId: project.ownerId,
      name: project.name,
      description: project.description,
      status: project.status,
      health: project.health,
      startDate: project.startDate,
      targetEndDate: project.targetEndDate,
      budgetNotes: project.budgetNotes,
      createdAt: project.createdAt,
      updatedAt: project.updatedAt,
      milestones: milestones
          .map(
            (item) => FlowtrackMilestone.fromJson(item as Map<String, dynamic>),
          )
          .toList(),
      tasks: tasks
          .map((item) => FlowtrackTask.fromJson(item as Map<String, dynamic>))
          .toList(),
      linkedTicketCount: (json['linked_ticket_count'] as num? ?? 0).toInt(),
      releases: releases
          .map(
            (item) => FlowtrackRelease.fromJson(item as Map<String, dynamic>),
          )
          .toList(),
    );
  }
}

typedef FlowtrackTicketPage = PaginatedResponse<FlowtrackTicket>;
typedef FlowtrackProjectPage = PaginatedResponse<FlowtrackProject>;
