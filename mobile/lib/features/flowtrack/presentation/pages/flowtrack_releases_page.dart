import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../data/models/flowtrack_models.dart';
import '../providers/flowtrack_provider.dart';
import '../widgets/flowtrack_widgets.dart';

class FlowtrackReleasesPage extends ConsumerWidget {
  const FlowtrackReleasesPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selectedTenant = ref.watch(selectedFlowtrackTenantProvider);
    final releasesAsync = ref.watch(selectedFlowtrackReleasesProvider);

    return Scaffold(
      backgroundColor: const Color(0xFFF6F2EB),
      appBar: AppBar(title: const Text('Releases')),
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(selectedFlowtrackReleasesProvider);
        },
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 120),
          children: [
            const FlowtrackSectionHeader(
              eyebrow: 'Shipping',
              title: 'Release plan and deployment rhythm',
            ),
            const SizedBox(height: 8),
            Text(
              selectedTenant == null
                  ? 'Pick a workspace from the dashboard before opening release tracking.'
                  : 'Release bundles for ${selectedTenant.name} appear here with project-linked work context.',
              style: const TextStyle(color: Color(0xFF475569), height: 1.5),
            ),
            const SizedBox(height: 18),
            releasesAsync.when(
              data: (releases) {
                final items = releases ?? [];
                if (selectedTenant == null) {
                  return const FlowtrackEmptyState(
                    title: 'No workspace selected',
                    description:
                        'Open the dashboard first and choose a tenant to load its releases.',
                    icon: Icons.apartment_rounded,
                  );
                }
                if (items.isEmpty) {
                  return const FlowtrackEmptyState(
                    title: 'No releases yet',
                    description:
                        'Release planning and deployment history will appear here once a project starts shipping.',
                    icon: Icons.rocket_launch_outlined,
                  );
                }

                return Column(
                  children: items.map((release) {
                    return _ReleaseTimelineCard(release: release);
                  }).toList(),
                );
              },
              loading: () => const Center(
                child: Padding(
                  padding: EdgeInsets.symmetric(vertical: 48),
                  child: CircularProgressIndicator(),
                ),
              ),
              error: (error, _) => FlowtrackEmptyState(
                title: 'Unable to load releases',
                description: error.toString(),
                icon: Icons.error_outline_rounded,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ReleaseTimelineCard extends StatelessWidget {
  final FlowtrackRelease release;

  const _ReleaseTimelineCard({required this.release});

  @override
  Widget build(BuildContext context) {
    final plannedLabel = release.plannedAt == null
        ? 'No planned date'
        : DateFormat.yMMMd().add_jm().format(
            DateTime.parse(release.plannedAt!),
          );

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(28),
        border: Border.all(color: const Color(0xFFE2E8F0)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              FlowtrackStatusChip(value: release.status),
              FlowtrackStatusChip(value: release.releaseType),
            ],
          ),
          const SizedBox(height: 14),
          Text(
            release.version,
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w700,
              color: Color(0xFF0F172A),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            release.notes.isEmpty
                ? 'No release notes recorded yet.'
                : release.notes,
            style: const TextStyle(color: Color(0xFF475569), height: 1.5),
          ),
          const SizedBox(height: 14),
          Wrap(
            spacing: 12,
            runSpacing: 10,
            children: [
              _InfoPill(label: plannedLabel),
              _InfoPill(label: '${release.ticketIds.length} tickets'),
              _InfoPill(label: '${release.taskIds.length} tasks'),
            ],
          ),
        ],
      ),
    );
  }
}

class _InfoPill extends StatelessWidget {
  final String label;

  const _InfoPill({required this.label});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: const Color(0xFFF8FAFC),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: const Color(0xFFE2E8F0)),
      ),
      child: Text(
        label,
        style: const TextStyle(fontSize: 12, color: Color(0xFF475569)),
      ),
    );
  }
}
