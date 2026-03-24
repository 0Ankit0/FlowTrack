import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../../../core/constants/app_constants.dart';
import '../providers/flowtrack_provider.dart';
import '../widgets/flowtrack_widgets.dart';

class FlowtrackDashboardPage extends ConsumerWidget {
  const FlowtrackDashboardPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selectedTenant = ref.watch(selectedFlowtrackTenantProvider);
    final summaryAsync = ref.watch(selectedFlowtrackSummaryProvider);
    final ticketsAsync = ref.watch(selectedFlowtrackTicketsProvider);
    final projectsAsync = ref.watch(selectedFlowtrackProjectsProvider);
    final releasesAsync = ref.watch(selectedFlowtrackReleasesProvider);

    return Scaffold(
      backgroundColor: const Color(0xFFF6F2EB),
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(flowtrackTenantsProvider);
          ref.invalidate(selectedFlowtrackSummaryProvider);
          ref.invalidate(selectedFlowtrackTicketsProvider);
          ref.invalidate(selectedFlowtrackProjectsProvider);
          ref.invalidate(selectedFlowtrackReleasesProvider);
        },
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 120),
          children: [
            _DashboardHero(
              selectedTenantName: selectedTenant?.name,
              onTenantChanged: (tenantId) {
                ref.read(selectedFlowtrackTenantIdProvider.notifier).state =
                    tenantId;
              },
            ).animate().fadeIn(duration: 350.ms).slideY(begin: 0.04),
            const SizedBox(height: 18),
            summaryAsync.when(
              data: (summary) {
                if (summary == null) {
                  return const FlowtrackEmptyState(
                    title: 'No workspace selected yet',
                    description:
                        'Join or create a tenant to see ticket volume, delivery pressure, and release readiness on mobile.',
                    icon: Icons.apartment_rounded,
                  );
                }

                final cards = [
                  _MetricCard(
                    label: 'Open Tickets',
                    value: '${summary.openTicketCount}',
                    detail: 'Across active queues',
                    accent: const Color(0xFF0F766E),
                    icon: Icons.support_agent_rounded,
                  ),
                  _MetricCard(
                    label: 'SLA Risk',
                    value: '${summary.breachedTicketCount}',
                    detail: 'Breached or overdue',
                    accent: const Color(0xFFBE185D),
                    icon: Icons.sensors_rounded,
                  ),
                  _MetricCard(
                    label: 'Projects',
                    value: '${summary.activeProjectCount}',
                    detail: '${summary.projectCount} total in scope',
                    accent: const Color(0xFF0F5E9C),
                    icon: Icons.folder_copy_rounded,
                  ),
                  _MetricCard(
                    label: 'Milestones',
                    value:
                        '${(summary.milestoneCompletionRate * 100).round()}%',
                    detail: 'Completion pace',
                    accent: const Color(0xFF9D5C00),
                    icon: Icons.flag_rounded,
                  ),
                ];

                return GridView.builder(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: cards.length,
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 2,
                    mainAxisSpacing: 12,
                    crossAxisSpacing: 12,
                    childAspectRatio: 1.06,
                  ),
                  itemBuilder: (context, index) => cards[index]
                      .animate(delay: Duration(milliseconds: 80 * index))
                      .fadeIn(duration: 300.ms)
                      .slideY(begin: 0.08),
                );
              },
              loading: () => const _LoadingPanel(height: 220),
              error: (error, _) => _ErrorPanel(message: error.toString()),
            ),
            const SizedBox(height: 24),
            FlowtrackSectionHeader(
              eyebrow: 'Ticket queue',
              title: 'Latest intake',
              actionLabel: 'Open',
              onAction: () => context.push(AppConstants.ticketsRoute),
            ),
            const SizedBox(height: 12),
            ticketsAsync.when(
              data: (page) {
                final tickets = page?.items ?? [];
                if (tickets.isEmpty) {
                  return const FlowtrackEmptyState(
                    title: 'No tickets yet',
                    description:
                        'Once your team or clients start logging requests, the mobile queue will surface the latest work here.',
                    icon: Icons.confirmation_number_outlined,
                  );
                }

                return Column(
                  children: tickets.take(3).map((ticket) {
                    return _DashboardTicketCard(ticket: ticket);
                  }).toList(),
                );
              },
              loading: () => const _LoadingPanel(height: 210),
              error: (error, _) => _ErrorPanel(message: error.toString()),
            ),
            const SizedBox(height: 24),
            FlowtrackSectionHeader(
              eyebrow: 'Delivery',
              title: 'Project pulse',
              actionLabel: 'View all',
              onAction: () => context.push(AppConstants.projectsRoute),
            ),
            const SizedBox(height: 12),
            projectsAsync.when(
              data: (page) {
                final projects = page?.items ?? [];
                if (projects.isEmpty) {
                  return const FlowtrackEmptyState(
                    title: 'No projects in this workspace',
                    description:
                        'Projects appear here when the team starts shaping milestones and linked execution work.',
                    icon: Icons.space_dashboard_outlined,
                  );
                }

                return Column(
                  children: projects.take(3).map((project) {
                    return _DashboardProjectCard(project: project);
                  }).toList(),
                );
              },
              loading: () => const _LoadingPanel(height: 210),
              error: (error, _) => _ErrorPanel(message: error.toString()),
            ),
            const SizedBox(height: 24),
            FlowtrackSectionHeader(
              eyebrow: 'Shipping',
              title: 'Release rhythm',
              actionLabel: 'Manage',
              onAction: () => context.push(AppConstants.releasesRoute),
            ),
            const SizedBox(height: 12),
            releasesAsync.when(
              data: (releases) {
                final items = releases ?? [];
                if (items.isEmpty) {
                  return const FlowtrackEmptyState(
                    title: 'No releases recorded',
                    description:
                        'Your planned and deployed release bundles will show up here for quick mobile review.',
                    icon: Icons.rocket_launch_outlined,
                  );
                }

                return Column(
                  children: items.take(3).map((release) {
                    return _DashboardReleaseCard(release: release);
                  }).toList(),
                );
              },
              loading: () => const _LoadingPanel(height: 200),
              error: (error, _) => _ErrorPanel(message: error.toString()),
            ),
          ],
        ),
      ),
    );
  }
}

class _DashboardHero extends ConsumerWidget {
  final String? selectedTenantName;
  final ValueChanged<String?> onTenantChanged;

  const _DashboardHero({
    required this.selectedTenantName,
    required this.onTenantChanged,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final tenants = ref.watch(flowtrackTenantsProvider).valueOrNull ?? [];
    final selectedTenant = ref.watch(selectedFlowtrackTenantProvider);

    return Container(
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(32),
        gradient: const LinearGradient(
          colors: [Color(0xFF082F49), Color(0xFF0F766E), Color(0xFF9D174D)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        boxShadow: const [
          BoxShadow(
            color: Color(0x33082F49),
            blurRadius: 34,
            offset: Offset(0, 18),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  'Flowtrack mobile command view',
                  style: GoogleFonts.fraunces(
                    fontSize: 30,
                    height: 1.1,
                    fontWeight: FontWeight.w600,
                    color: Colors.white,
                  ),
                ),
              ),
              if (tenants.isNotEmpty)
                FlowtrackTenantSelector(
                  tenants: tenants,
                  selectedTenant: selectedTenant,
                  onChanged: onTenantChanged,
                ),
            ],
          ),
          const SizedBox(height: 14),
          Text(
            selectedTenantName == null
                ? 'Switch into a workspace to monitor incoming issues, active delivery risk, and release momentum.'
                : 'Tracking ${selectedTenantName!} across tickets, milestones, and release readiness from one screen.',
            style: const TextStyle(
              color: Color(0xD9FFFFFF),
              fontSize: 14,
              height: 1.6,
            ),
          ),
          const SizedBox(height: 18),
          const Wrap(
            spacing: 10,
            runSpacing: 10,
            children: [
              _HeroPill(
                icon: Icons.confirmation_number_outlined,
                label: 'Client intake',
              ),
              _HeroPill(
                icon: Icons.rule_folder_outlined,
                label: 'Delivery plans',
              ),
              _HeroPill(
                icon: Icons.rocket_launch_outlined,
                label: 'Release traceability',
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _HeroPill extends StatelessWidget {
  final IconData icon;
  final String label;

  const _HeroPill({required this.icon, required this.label});

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(999),
        color: Colors.white.withValues(alpha: 0.12),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 16, color: Colors.white),
            const SizedBox(width: 8),
            Text(
              label,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 12,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _MetricCard extends StatelessWidget {
  final String label;
  final String value;
  final String detail;
  final Color accent;
  final IconData icon;

  const _MetricCard({
    required this.label,
    required this.value,
    required this.detail,
    required this.accent,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(28),
        border: Border.all(color: const Color(0xFFE2E8F0)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          CircleAvatar(
            radius: 18,
            backgroundColor: accent.withValues(alpha: 0.14),
            child: Icon(icon, color: accent),
          ),
          const Spacer(),
          Text(
            label.toUpperCase(),
            style: const TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w700,
              letterSpacing: 1.4,
              color: Color(0xFF94A3B8),
            ),
          ),
          const SizedBox(height: 6),
          Text(
            value,
            style: GoogleFonts.fraunces(
              fontSize: 34,
              fontWeight: FontWeight.w600,
              color: const Color(0xFF0F172A),
            ),
          ),
          const SizedBox(height: 4),
          Text(
            detail,
            style: const TextStyle(color: Color(0xFF475569), fontSize: 13),
          ),
        ],
      ),
    );
  }
}

class _DashboardTicketCard extends StatelessWidget {
  final dynamic ticket;

  const _DashboardTicketCard({required this.ticket});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(26),
        border: Border.all(color: const Color(0xFFE2E8F0)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              FlowtrackStatusChip(value: ticket.status as String),
              FlowtrackStatusChip(value: ticket.priority as String),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            ticket.title as String,
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w700,
              color: Color(0xFF0F172A),
            ),
          ),
          const SizedBox(height: 6),
          Text(
            ticket.description as String,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
              fontSize: 14,
              height: 1.5,
              color: Color(0xFF475569),
            ),
          ),
        ],
      ),
    );
  }
}

class _DashboardProjectCard extends StatelessWidget {
  final dynamic project;

  const _DashboardProjectCard({required this.project});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(26),
        border: Border.all(color: const Color(0xFFE2E8F0)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              FlowtrackStatusChip(value: project.status as String),
              FlowtrackStatusChip(value: project.health as String),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            project.name as String,
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w700,
              color: Color(0xFF0F172A),
            ),
          ),
          const SizedBox(height: 6),
          Text(
            project.description as String,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
              fontSize: 14,
              height: 1.5,
              color: Color(0xFF475569),
            ),
          ),
        ],
      ),
    );
  }
}

class _DashboardReleaseCard extends StatelessWidget {
  final dynamic release;

  const _DashboardReleaseCard({required this.release});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(26),
        border: Border.all(color: const Color(0xFFE2E8F0)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              FlowtrackStatusChip(value: release.status as String),
              FlowtrackStatusChip(value: release.releaseType as String),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            release.version as String,
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w700,
              color: Color(0xFF0F172A),
            ),
          ),
          const SizedBox(height: 6),
          Text(
            (release.notes as String).isEmpty
                ? 'No release notes recorded yet.'
                : release.notes as String,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
              fontSize: 14,
              height: 1.5,
              color: Color(0xFF475569),
            ),
          ),
        ],
      ),
    );
  }
}

class _LoadingPanel extends StatelessWidget {
  final double height;

  const _LoadingPanel({required this.height});

  @override
  Widget build(BuildContext context) {
    return Container(
      height: height,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(28),
        border: Border.all(color: const Color(0xFFE2E8F0)),
      ),
      alignment: Alignment.center,
      child: const CircularProgressIndicator(),
    );
  }
}

class _ErrorPanel extends StatelessWidget {
  final String message;

  const _ErrorPanel({required this.message});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFFFDF2F2),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: const Color(0xFFF3D0D0)),
      ),
      child: Text(message, style: const TextStyle(color: Color(0xFF9F1239))),
    );
  }
}
