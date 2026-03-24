import '../../../../core/error/error_handler.dart';
import '../../../../core/models/paginated_response.dart';
import '../../../../core/network/api_endpoints.dart';
import '../../../../core/network/dio_client.dart';
import '../models/flowtrack_models.dart';

class FlowtrackRepository {
  final DioClient _dioClient;

  FlowtrackRepository(this._dioClient);

  Future<List<WorkspaceTenant>> getTenants() async {
    try {
      final response = await _dioClient.dio.get(
        ApiEndpoints.tenants,
        queryParameters: {'limit': 100},
      );
      final payload = response.data as Map<String, dynamic>;
      final items = payload['items'] as List<dynamic>? ?? <dynamic>[];
      return items
          .map((item) => WorkspaceTenant.fromJson(item as Map<String, dynamic>))
          .toList();
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<FlowtrackOperationalSummary> getOperationalSummary(
    String tenantId,
  ) async {
    try {
      final response = await _dioClient.dio.get(
        ApiEndpoints.flowtrackOperationalSummary,
        queryParameters: {'tenant_id': tenantId},
      );
      return FlowtrackOperationalSummary.fromJson(
        response.data as Map<String, dynamic>,
      );
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<PaginatedResponse<FlowtrackTicket>> getTickets(
    String tenantId, {
    int limit = 40,
    String? status,
  }) async {
    try {
      final response = await _dioClient.dio.get(
        ApiEndpoints.flowtrackTickets,
        queryParameters: {
          'tenant_id': tenantId,
          'limit': limit,
          if (status != null && status.isNotEmpty) 'status': status,
        },
      );
      return PaginatedResponse.fromJson(
        response.data as Map<String, dynamic>,
        FlowtrackTicket.fromJson,
      );
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<FlowtrackTicketDetail> getTicketDetail(String ticketId) async {
    try {
      final response = await _dioClient.dio.get(
        ApiEndpoints.flowtrackTicket(ticketId),
      );
      return FlowtrackTicketDetail.fromJson(
        response.data as Map<String, dynamic>,
      );
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<FlowtrackTicket> createTicket({
    required String tenantId,
    required String title,
    required String description,
    required String type,
    required String severity,
    required String priority,
    String? category,
    String? environment,
  }) async {
    try {
      final response = await _dioClient.dio.post(
        ApiEndpoints.flowtrackTickets,
        data: {
          'tenant_id': tenantId,
          'title': title,
          'description': description,
          'type': type,
          'severity': severity,
          'priority': priority,
          if (category != null && category.isNotEmpty) 'category': category,
          if (environment != null && environment.isNotEmpty)
            'environment': environment,
        },
      );
      return FlowtrackTicket.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<FlowtrackTicketComment> addTicketComment({
    required String ticketId,
    required String body,
    String visibility = 'public',
  }) async {
    try {
      final response = await _dioClient.dio.post(
        ApiEndpoints.flowtrackTicketComments(ticketId),
        data: {'body': body, 'visibility': visibility},
      );
      return FlowtrackTicketComment.fromJson(
        response.data as Map<String, dynamic>,
      );
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<PaginatedResponse<FlowtrackProject>> getProjects(
    String tenantId,
  ) async {
    try {
      final response = await _dioClient.dio.get(
        ApiEndpoints.flowtrackProjects,
        queryParameters: {'tenant_id': tenantId, 'limit': 100},
      );
      return PaginatedResponse.fromJson(
        response.data as Map<String, dynamic>,
        FlowtrackProject.fromJson,
      );
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<FlowtrackProjectDetail> getProjectDetail(String projectId) async {
    try {
      final response = await _dioClient.dio.get(
        ApiEndpoints.flowtrackProject(projectId),
      );
      return FlowtrackProjectDetail.fromJson(
        response.data as Map<String, dynamic>,
      );
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<List<FlowtrackRelease>> getReleases(
    String tenantId, {
    String? projectId,
  }) async {
    try {
      final response = await _dioClient.dio.get(
        ApiEndpoints.flowtrackReleases,
        queryParameters: {
          'tenant_id': tenantId,
          if (projectId != null && projectId.isNotEmpty)
            'project_id': projectId,
        },
      );
      final payload = response.data as List<dynamic>;
      return payload
          .map(
            (item) => FlowtrackRelease.fromJson(item as Map<String, dynamic>),
          )
          .toList();
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }
}
