import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../data/models/flowtrack_models.dart';
import '../providers/flowtrack_provider.dart';
import '../widgets/flowtrack_widgets.dart';

class FlowtrackProjectsPage extends ConsumerWidget {
  const FlowtrackProjectsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selectedTenant = ref.watch(selectedFlowtrackTenantProvider);
    final projectsAsync = ref.watch(selectedFlowtrackProjectsProvider);

    return Scaffold(
      backgroundColor: const Color(0xFFF6F2EB),
      appBar: AppBar(title: const Text('Projects')),
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(selectedFlowtrackProjectsProvider);
          ref.invalidate(selectedFlowtrackSummaryProvider);
        },
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 120),
          children: [
            const FlowtrackSectionHeader(
              eyebrow: 'Portfolio',
              title: 'Milestones, tasks, and blockers',
            ),
            const SizedBox(height: 8),
            Text(
              selectedTenant == null
                  ? 'Select a workspace from the dashboard to inspect its delivery portfolio.'
                  : 'Review active project health and milestone readiness for ${selectedTenant.name}.',
              style: const TextStyle(color: Color(0xFF475569), height: 1.5),
            ),
            const SizedBox(height: 18),
            projectsAsync.when(
              data: (page) {
                final projects = page?.items ?? [];
                if (selectedTenant == null) {
                  return const FlowtrackEmptyState(
                    title: 'No workspace selected',
                    description:
                        'Pick a tenant from the dashboard before opening the project portfolio.',
                    icon: Icons.apartment_rounded,
                  );
                }
                if (projects.isEmpty) {
                  return const FlowtrackEmptyState(
                    title: 'No projects in scope',
                    description:
                        'Projects will appear here as soon as delivery planning starts in this workspace.',
                    icon: Icons.folder_copy_outlined,
                  );
                }

                return Column(
                  children: projects.map((project) {
                    return _ProjectCard(
                      project: project,
                      onTap: () => showModalBottomSheet<void>(
                        context: context,
                        isScrollControlled: true,
                        useSafeArea: true,
                        backgroundColor: Colors.transparent,
                        builder: (_) =>
                            _ProjectDetailSheet(projectId: project.id),
                      ),
                    );
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
                title: 'Unable to load projects',
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

class _ProjectCard extends StatelessWidget {
  final FlowtrackProject project;
  final VoidCallback onTap;

  const _ProjectCard({required this.project, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(28),
      child: Container(
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
                FlowtrackStatusChip(value: project.status),
                FlowtrackStatusChip(value: project.health),
              ],
            ),
            const SizedBox(height: 14),
            Text(
              project.name,
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w700,
                color: Color(0xFF0F172A),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              project.description,
              maxLines: 3,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(height: 1.5, color: Color(0xFF475569)),
            ),
          ],
        ),
      ),
    );
  }
}

class _ProjectDetailSheet extends ConsumerWidget {
  final String projectId;

  const _ProjectDetailSheet({required this.projectId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final detailAsync = ref.watch(flowtrackProjectDetailProvider(projectId));

    return Container(
      decoration: const BoxDecoration(
        color: Color(0xFFF6F2EB),
        borderRadius: BorderRadius.vertical(top: Radius.circular(32)),
      ),
      child: detailAsync.when(
        data: (project) => ListView(
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
          children: [
            Center(
              child: Container(
                width: 44,
                height: 4,
                decoration: BoxDecoration(
                  color: const Color(0xFFCBD5E1),
                  borderRadius: BorderRadius.circular(999),
                ),
              ),
            ),
            const SizedBox(height: 16),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                FlowtrackStatusChip(value: project.status),
                FlowtrackStatusChip(value: project.health),
              ],
            ),
            const SizedBox(height: 16),
            Text(
              project.name,
              style: const TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.w700,
                color: Color(0xFF0F172A),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              project.description,
              style: const TextStyle(color: Color(0xFF475569), height: 1.6),
            ),
            const SizedBox(height: 12),
            _InfoLine(
              label: 'Linked tickets',
              value: '${project.linkedTicketCount}',
            ),
            const SizedBox(height: 24),
            const FlowtrackSectionHeader(
              eyebrow: 'Milestones',
              title: 'Delivery checkpoints',
            ),
            const SizedBox(height: 12),
            if (project.milestones.isEmpty)
              const FlowtrackEmptyState(
                title: 'No milestones yet',
                description:
                    'Project checkpoints will appear here when planning is baselined.',
                icon: Icons.flag_outlined,
              )
            else
              ...project.milestones.map(
                (milestone) => _MilestoneCard(milestone: milestone),
              ),
            const SizedBox(height: 24),
            const FlowtrackSectionHeader(
              eyebrow: 'Tasks',
              title: 'Execution threads',
            ),
            const SizedBox(height: 12),
            if (project.tasks.isEmpty)
              const FlowtrackEmptyState(
                title: 'No tasks yet',
                description:
                    'Tasks linked to this project will show here once work is broken down.',
                icon: Icons.task_outlined,
              )
            else
              ...project.tasks.map((task) => _TaskCard(task: task)),
            if (project.releases.isNotEmpty) ...[
              const SizedBox(height: 24),
              const FlowtrackSectionHeader(
                eyebrow: 'Releases',
                title: 'Shipping bundles',
              ),
              const SizedBox(height: 12),
              ...project.releases.map(
                (release) => _ReleaseCard(release: release),
              ),
            ],
          ],
        ),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => Center(child: Text(error.toString())),
      ),
    );
  }
}

class _MilestoneCard extends StatelessWidget {
  final FlowtrackMilestone milestone;

  const _MilestoneCard({required this.milestone});

  @override
  Widget build(BuildContext context) {
    final plannedDate = DateFormat.yMMMd().format(
      DateTime.parse(milestone.plannedDate),
    );

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: const Color(0xFFE2E8F0)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          FlowtrackStatusChip(value: milestone.status),
          const SizedBox(height: 12),
          Text(
            milestone.name,
            style: const TextStyle(
              fontSize: 17,
              fontWeight: FontWeight.w700,
              color: Color(0xFF0F172A),
            ),
          ),
          const SizedBox(height: 6),
          Text(
            'Planned $plannedDate',
            style: const TextStyle(color: Color(0xFF64748B), fontSize: 13),
          ),
          if (milestone.completionCriteria.isNotEmpty) ...[
            const SizedBox(height: 10),
            ...milestone.completionCriteria
                .take(3)
                .map(
                  (criterion) => Padding(
                    padding: const EdgeInsets.only(bottom: 6),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Padding(
                          padding: EdgeInsets.only(top: 7),
                          child: Icon(Icons.circle, size: 6),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            criterion,
                            style: const TextStyle(
                              color: Color(0xFF475569),
                              height: 1.4,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
          ],
        ],
      ),
    );
  }
}

class _TaskCard extends StatelessWidget {
  final FlowtrackTask task;

  const _TaskCard({required this.task});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: const Color(0xFFE2E8F0)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          FlowtrackStatusChip(value: task.status),
          const SizedBox(height: 12),
          Text(
            task.title,
            style: const TextStyle(
              fontSize: 17,
              fontWeight: FontWeight.w700,
              color: Color(0xFF0F172A),
            ),
          ),
          if (task.description.isNotEmpty) ...[
            const SizedBox(height: 6),
            Text(
              task.description,
              style: const TextStyle(color: Color(0xFF475569), height: 1.5),
            ),
          ],
        ],
      ),
    );
  }
}

class _ReleaseCard extends StatelessWidget {
  final FlowtrackRelease release;

  const _ReleaseCard({required this.release});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
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
          const SizedBox(height: 12),
          Text(
            release.version,
            style: const TextStyle(
              fontSize: 17,
              fontWeight: FontWeight.w700,
              color: Color(0xFF0F172A),
            ),
          ),
          if (release.notes.isNotEmpty) ...[
            const SizedBox(height: 6),
            Text(
              release.notes,
              style: const TextStyle(color: Color(0xFF475569), height: 1.5),
            ),
          ],
        ],
      ),
    );
  }
}

class _InfoLine extends StatelessWidget {
  final String label;
  final String value;

  const _InfoLine({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Text(
          label,
          style: const TextStyle(
            fontWeight: FontWeight.w600,
            color: Color(0xFF334155),
          ),
        ),
        const Spacer(),
        Text(value, style: const TextStyle(color: Color(0xFF64748B))),
      ],
    );
  }
}
