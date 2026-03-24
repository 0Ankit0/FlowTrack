import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../data/models/flowtrack_models.dart';

class FlowtrackStatusChip extends StatelessWidget {
  final String value;

  const FlowtrackStatusChip({super.key, required this.value});

  static ({Color background, Color foreground}) _palette(String value) {
    switch (value) {
      case 'new':
      case 'planned':
      case 'P4':
      case 'public':
        return (
          background: const Color(0xFFDCEEFE),
          foreground: const Color(0xFF0F5E9C),
        );
      case 'awaiting_clarification':
      case 'at_risk':
      case 'pending':
      case 'P3':
      case 'amber':
        return (
          background: const Color(0xFFFCE8C9),
          foreground: const Color(0xFF9D5C00),
        );
      case 'triaged':
      case 'assigned':
      case 'in_progress':
      case 'baselined':
      case 'active':
      case 'todo':
        return (
          background: const Color(0xFFDDF4F0),
          foreground: const Color(0xFF0E6B61),
        );
      case 'blocked':
      case 'rolled_back':
      case 'red':
      case 'quarantined':
      case 'P1':
        return (
          background: const Color(0xFFF7D9D6),
          foreground: const Color(0xFFA3352B),
        );
      case 'ready_for_qa':
      case 'replanning':
      case 'internal':
        return (
          background: const Color(0xFFEADFFB),
          foreground: const Color(0xFF6A35B1),
        );
      case 'closed':
      case 'completed':
      case 'done':
      case 'deployed':
      case 'green':
      case 'clean':
        return (
          background: const Color(0xFFDFF2DF),
          foreground: const Color(0xFF206A35),
        );
      case 'reopened':
      case 'P2':
      case 'on_hold':
        return (
          background: const Color(0xFFFFE5D0),
          foreground: const Color(0xFFB45A1B),
        );
      default:
        return (
          background: const Color(0xFFE9EDF3),
          foreground: const Color(0xFF475569),
        );
    }
  }

  @override
  Widget build(BuildContext context) {
    final colors = _palette(value);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: colors.background,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        value.replaceAll('_', ' '),
        style: TextStyle(
          color: colors.foreground,
          fontSize: 11,
          fontWeight: FontWeight.w700,
          letterSpacing: 1.1,
        ),
      ),
    );
  }
}

class FlowtrackTenantSelector extends StatelessWidget {
  final List<WorkspaceTenant> tenants;
  final WorkspaceTenant? selectedTenant;
  final ValueChanged<String?> onChanged;

  const FlowtrackTenantSelector({
    super.key,
    required this.tenants,
    required this.selectedTenant,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    if (tenants.isEmpty) {
      return const SizedBox.shrink();
    }

    return DecoratedBox(
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.14),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.white.withValues(alpha: 0.16)),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12),
        child: DropdownButtonHideUnderline(
          child: DropdownButton<String>(
            value: selectedTenant?.id ?? tenants.first.id,
            dropdownColor: const Color(0xFF0F172A),
            iconEnabledColor: Colors.white,
            style: const TextStyle(color: Colors.white),
            onChanged: onChanged,
            items: tenants
                .map(
                  (tenant) => DropdownMenuItem<String>(
                    value: tenant.id,
                    child: Text(tenant.name, overflow: TextOverflow.ellipsis),
                  ),
                )
                .toList(),
          ),
        ),
      ),
    );
  }
}

class FlowtrackSectionHeader extends StatelessWidget {
  final String eyebrow;
  final String title;
  final String? actionLabel;
  final VoidCallback? onAction;

  const FlowtrackSectionHeader({
    super.key,
    required this.eyebrow,
    required this.title,
    this.actionLabel,
    this.onAction,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                eyebrow.toUpperCase(),
                style: const TextStyle(
                  color: Color(0xFF94A3B8),
                  fontSize: 11,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 1.6,
                ),
              ),
              const SizedBox(height: 6),
              Text(
                title,
                style: GoogleFonts.fraunces(
                  fontSize: 24,
                  fontWeight: FontWeight.w600,
                  color: const Color(0xFF0F172A),
                ),
              ),
            ],
          ),
        ),
        if (actionLabel != null && onAction != null)
          TextButton(onPressed: onAction, child: Text(actionLabel!)),
      ],
    );
  }
}

class FlowtrackEmptyState extends StatelessWidget {
  final String title;
  final String description;
  final IconData icon;

  const FlowtrackEmptyState({
    super.key,
    required this.title,
    required this.description,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(28),
        border: Border.all(color: const Color(0xFFE2E8F0)),
      ),
      child: Column(
        children: [
          CircleAvatar(
            radius: 28,
            backgroundColor: const Color(0xFFDDF4F0),
            child: Icon(icon, color: const Color(0xFF0E6B61)),
          ),
          const SizedBox(height: 14),
          Text(
            title,
            textAlign: TextAlign.center,
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w700,
              color: Color(0xFF0F172A),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            description,
            textAlign: TextAlign.center,
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
