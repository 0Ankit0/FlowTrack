import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/models/paginated_response.dart';
import '../../../../core/providers/dio_provider.dart';
import '../../data/models/flowtrack_models.dart';
import '../../data/repositories/flowtrack_repository.dart';

final flowtrackRepositoryProvider = Provider<FlowtrackRepository>((ref) {
  return FlowtrackRepository(ref.watch(dioClientProvider));
});

final flowtrackTenantsProvider = FutureProvider<List<WorkspaceTenant>>((ref) {
  return ref.watch(flowtrackRepositoryProvider).getTenants();
});

final selectedFlowtrackTenantIdProvider = StateProvider<String?>((ref) => null);

final selectedFlowtrackTenantProvider = Provider<WorkspaceTenant?>((ref) {
  final selectedTenantId = ref.watch(selectedFlowtrackTenantIdProvider);
  final tenants = ref.watch(flowtrackTenantsProvider).valueOrNull ?? [];

  for (final tenant in tenants) {
    if (tenant.id == selectedTenantId) return tenant;
  }

  return tenants.isNotEmpty ? tenants.first : null;
});

final selectedFlowtrackSummaryProvider =
    FutureProvider<FlowtrackOperationalSummary?>((ref) async {
      final tenant = ref.watch(selectedFlowtrackTenantProvider);
      if (tenant == null) return null;
      return ref
          .watch(flowtrackRepositoryProvider)
          .getOperationalSummary(tenant.id);
    });

final selectedFlowtrackTicketsProvider =
    FutureProvider<PaginatedResponse<FlowtrackTicket>?>((ref) async {
      final tenant = ref.watch(selectedFlowtrackTenantProvider);
      if (tenant == null) return null;
      return ref.watch(flowtrackRepositoryProvider).getTickets(tenant.id);
    });

final flowtrackTicketDetailProvider =
    FutureProvider.family<FlowtrackTicketDetail, String>((ref, ticketId) async {
      return ref.watch(flowtrackRepositoryProvider).getTicketDetail(ticketId);
    });

final selectedFlowtrackProjectsProvider =
    FutureProvider<PaginatedResponse<FlowtrackProject>?>((ref) async {
      final tenant = ref.watch(selectedFlowtrackTenantProvider);
      if (tenant == null) return null;
      return ref.watch(flowtrackRepositoryProvider).getProjects(tenant.id);
    });

final flowtrackProjectDetailProvider =
    FutureProvider.family<FlowtrackProjectDetail, String>((
      ref,
      projectId,
    ) async {
      return ref.watch(flowtrackRepositoryProvider).getProjectDetail(projectId);
    });

final selectedFlowtrackReleasesProvider =
    FutureProvider<List<FlowtrackRelease>?>((ref) async {
      final tenant = ref.watch(selectedFlowtrackTenantProvider);
      if (tenant == null) return null;
      return ref.watch(flowtrackRepositoryProvider).getReleases(tenant.id);
    });
