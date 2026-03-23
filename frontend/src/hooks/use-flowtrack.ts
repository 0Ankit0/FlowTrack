'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import type {
  Milestone,
  MilestoneCreatePayload,
  OperationalSummary,
  Project,
  ProjectCreatePayload,
  ProjectDetail,
  Release,
  ReleaseCreatePayload,
  SlaPolicy,
  Task,
  TaskCreatePayload,
  Ticket,
  TicketAssignment,
  TicketAssignmentPayload,
  TicketAttachment,
  TicketAttachmentPayload,
  TicketComment,
  TicketCommentPayload,
  TicketCreatePayload,
  TicketDetail,
  TicketUpdatePayload,
  TicketPriority,
  TicketSeverity,
  TicketStatus,
} from '@/types';
import type { PaginatedResponse } from '@/types';

interface TicketQueryParams {
  tenantId?: string;
  status?: TicketStatus;
  projectId?: string;
  assigneeId?: string;
  priority?: TicketPriority;
  severity?: TicketSeverity;
  limit?: number;
}

export function useOperationalSummary(tenantId?: string) {
  return useQuery({
    queryKey: ['flowtrack', 'summary', tenantId],
    queryFn: async () => {
      const response = await apiClient.get<OperationalSummary>('/reports/operational-summary', {
        params: { tenant_id: tenantId },
      });
      return response.data;
    },
    enabled: Boolean(tenantId),
  });
}

export function useTickets(params: TicketQueryParams) {
  return useQuery({
    queryKey: ['flowtrack', 'tickets', params],
    queryFn: async () => {
      const response = await apiClient.get<PaginatedResponse<Ticket>>('/tickets/', {
        params: {
          tenant_id: params.tenantId,
          status: params.status,
          project_id: params.projectId,
          assignee_id: params.assigneeId,
          priority: params.priority,
          severity: params.severity,
          limit: params.limit ?? 50,
        },
      });
      return response.data;
    },
    enabled: Boolean(params.tenantId),
  });
}

export function useTicket(ticketId?: string) {
  return useQuery({
    queryKey: ['flowtrack', 'ticket', ticketId],
    queryFn: async () => {
      const response = await apiClient.get<TicketDetail>(`/tickets/${ticketId}`);
      return response.data;
    },
    enabled: Boolean(ticketId),
  });
}

export function useCreateTicket() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: TicketCreatePayload) => {
      const response = await apiClient.post<Ticket>('/tickets/', payload);
      return response.data;
    },
    onSuccess: (ticket) => {
      queryClient.invalidateQueries({ queryKey: ['flowtrack', 'tickets'] });
      queryClient.invalidateQueries({ queryKey: ['flowtrack', 'summary', ticket.tenant_id] });
    },
  });
}

export function useUpdateTicket() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ ticketId, payload }: { ticketId: string; payload: TicketUpdatePayload }) => {
      const response = await apiClient.patch<Ticket>(`/tickets/${ticketId}`, payload);
      return response.data;
    },
    onSuccess: (ticket) => {
      queryClient.invalidateQueries({ queryKey: ['flowtrack', 'tickets'] });
      queryClient.invalidateQueries({ queryKey: ['flowtrack', 'ticket', ticket.id] });
      queryClient.invalidateQueries({ queryKey: ['flowtrack', 'summary', ticket.tenant_id] });
      queryClient.invalidateQueries({ queryKey: ['flowtrack', 'projects'] });
    },
  });
}

export function useAddTicketComment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ ticketId, payload }: { ticketId: string; payload: TicketCommentPayload }) => {
      const response = await apiClient.post<TicketComment>(`/tickets/${ticketId}/comments`, payload);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['flowtrack', 'ticket', variables.ticketId] });
      queryClient.invalidateQueries({ queryKey: ['flowtrack', 'tickets'] });
    },
  });
}

export function useRegisterTicketAttachment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      ticketId,
      payload,
    }: {
      ticketId: string;
      payload: TicketAttachmentPayload;
    }) => {
      const response = await apiClient.post<TicketAttachment>(
        `/tickets/${ticketId}/attachments`,
        payload
      );
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['flowtrack', 'ticket', variables.ticketId] });
    },
  });
}

export function useAssignTicket() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      ticketId,
      payload,
    }: {
      ticketId: string;
      payload: TicketAssignmentPayload;
    }) => {
      const response = await apiClient.post<TicketAssignment>(
        `/tickets/${ticketId}/assignments`,
        payload
      );
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['flowtrack', 'ticket', variables.ticketId] });
      queryClient.invalidateQueries({ queryKey: ['flowtrack', 'tickets'] });
      queryClient.invalidateQueries({ queryKey: ['flowtrack', 'summary'] });
    },
  });
}

export function useProjects(tenantId?: string) {
  return useQuery({
    queryKey: ['flowtrack', 'projects', tenantId],
    queryFn: async () => {
      const response = await apiClient.get<PaginatedResponse<Project>>('/projects/', {
        params: { tenant_id: tenantId, limit: 100 },
      });
      return response.data;
    },
    enabled: Boolean(tenantId),
  });
}

export function useProject(projectId?: string) {
  return useQuery({
    queryKey: ['flowtrack', 'project', projectId],
    queryFn: async () => {
      const response = await apiClient.get<ProjectDetail>(`/projects/${projectId}`);
      return response.data;
    },
    enabled: Boolean(projectId),
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: ProjectCreatePayload) => {
      const response = await apiClient.post<Project>('/projects/', payload);
      return response.data;
    },
    onSuccess: (project) => {
      queryClient.invalidateQueries({ queryKey: ['flowtrack', 'projects', project.tenant_id] });
      queryClient.invalidateQueries({ queryKey: ['flowtrack', 'summary', project.tenant_id] });
    },
  });
}

export function useCreateMilestone() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      projectId,
      payload,
    }: {
      projectId: string;
      payload: MilestoneCreatePayload;
    }) => {
      const response = await apiClient.post<Milestone>(
        `/projects/${projectId}/milestones`,
        payload
      );
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['flowtrack', 'project', variables.projectId] });
      queryClient.invalidateQueries({ queryKey: ['flowtrack', 'projects'] });
    },
  });
}

export function useCreateTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      milestoneId,
      payload,
    }: {
      milestoneId: string;
      payload: TaskCreatePayload;
    }) => {
      const response = await apiClient.post<Task>(`/milestones/${milestoneId}/tasks`, payload);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['flowtrack', 'project'] });
      queryClient.invalidateQueries({ queryKey: ['flowtrack', 'projects'] });
    },
  });
}

export function useReleases(tenantId?: string, projectId?: string) {
  return useQuery({
    queryKey: ['flowtrack', 'releases', tenantId, projectId],
    queryFn: async () => {
      const response = await apiClient.get<Release[]>('/releases/', {
        params: { tenant_id: tenantId, project_id: projectId },
      });
      return response.data;
    },
    enabled: Boolean(tenantId),
  });
}

export function useCreateRelease() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: ReleaseCreatePayload) => {
      const response = await apiClient.post<Release>('/releases/', payload);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['flowtrack', 'releases'] });
      queryClient.invalidateQueries({ queryKey: ['flowtrack', 'project'] });
    },
  });
}

export function useSlaPolicies() {
  return useQuery({
    queryKey: ['flowtrack', 'sla-policies'],
    queryFn: async () => {
      const response = await apiClient.get<SlaPolicy[]>('/admin/sla-policies');
      return response.data;
    },
  });
}
