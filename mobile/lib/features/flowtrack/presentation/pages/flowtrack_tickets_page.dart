import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../../../shared/widgets/app_text_field.dart';
import '../../data/models/flowtrack_models.dart';
import '../providers/flowtrack_provider.dart';
import '../widgets/flowtrack_widgets.dart';

class FlowtrackTicketsPage extends ConsumerWidget {
  const FlowtrackTicketsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selectedTenant = ref.watch(selectedFlowtrackTenantProvider);
    final ticketsAsync = ref.watch(selectedFlowtrackTicketsProvider);

    return Scaffold(
      backgroundColor: const Color(0xFFF6F2EB),
      appBar: AppBar(
        title: const Text('Tickets'),
        actions: [
          IconButton(
            onPressed: selectedTenant == null
                ? null
                : () => showModalBottomSheet<void>(
                    context: context,
                    isScrollControlled: true,
                    useSafeArea: true,
                    backgroundColor: Colors.transparent,
                    builder: (_) => _CreateTicketSheet(tenant: selectedTenant),
                  ),
            icon: const Icon(Icons.add_circle_outline_rounded),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(selectedFlowtrackTicketsProvider);
          ref.invalidate(selectedFlowtrackSummaryProvider);
        },
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 120),
          children: [
            const FlowtrackSectionHeader(
              eyebrow: 'Queue',
              title: 'Client intake and support flow',
            ),
            const SizedBox(height: 8),
            Text(
              selectedTenant == null
                  ? 'Choose a workspace from the dashboard to browse tenant-scoped ticket queues.'
                  : 'Review, comment on, and create requests for ${selectedTenant.name}.',
              style: const TextStyle(color: Color(0xFF475569), height: 1.5),
            ),
            const SizedBox(height: 18),
            ticketsAsync.when(
              data: (page) {
                final tickets = page?.items ?? [];
                if (selectedTenant == null) {
                  return const FlowtrackEmptyState(
                    title: 'No workspace selected',
                    description:
                        'Open the mobile dashboard and pick a tenant before opening the ticket queue.',
                    icon: Icons.apartment_rounded,
                  );
                }
                if (tickets.isEmpty) {
                  return const FlowtrackEmptyState(
                    title: 'No tickets in this workspace',
                    description:
                        'Create the first ticket from the plus button to start tracking work on mobile.',
                    icon: Icons.confirmation_number_outlined,
                  );
                }

                return Column(
                  children: tickets.map((ticket) {
                    return _TicketCard(
                      ticket: ticket,
                      onTap: () => showModalBottomSheet<void>(
                        context: context,
                        isScrollControlled: true,
                        useSafeArea: true,
                        backgroundColor: Colors.transparent,
                        builder: (_) => _TicketDetailSheet(ticketId: ticket.id),
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
                title: 'Unable to load tickets',
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

class _TicketCard extends StatelessWidget {
  final FlowtrackTicket ticket;
  final VoidCallback onTap;

  const _TicketCard({required this.ticket, required this.onTap});

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
                FlowtrackStatusChip(value: ticket.status),
                FlowtrackStatusChip(value: ticket.priority),
              ],
            ),
            const SizedBox(height: 14),
            Text(
              ticket.title,
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w700,
                color: Color(0xFF0F172A),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              ticket.description,
              maxLines: 3,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(height: 1.5, color: Color(0xFF475569)),
            ),
            const SizedBox(height: 14),
            Wrap(
              spacing: 12,
              runSpacing: 10,
              children: [
                _MetaText(label: ticket.type),
                _MetaText(label: ticket.severity),
                _MetaText(
                  label: DateFormat.yMMMd().format(
                    DateTime.parse(ticket.createdAt),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _TicketDetailSheet extends ConsumerStatefulWidget {
  final String ticketId;

  const _TicketDetailSheet({required this.ticketId});

  @override
  ConsumerState<_TicketDetailSheet> createState() => _TicketDetailSheetState();
}

class _TicketDetailSheetState extends ConsumerState<_TicketDetailSheet> {
  late final TextEditingController _commentController;
  bool _isSubmitting = false;

  @override
  void initState() {
    super.initState();
    _commentController = TextEditingController();
  }

  @override
  void dispose() {
    _commentController.dispose();
    super.dispose();
  }

  Future<void> _submitComment() async {
    final body = _commentController.text.trim();
    if (body.isEmpty) return;

    setState(() => _isSubmitting = true);
    try {
      await ref
          .read(flowtrackRepositoryProvider)
          .addTicketComment(ticketId: widget.ticketId, body: body);
      _commentController.clear();
      ref.invalidate(flowtrackTicketDetailProvider(widget.ticketId));
      ref.invalidate(selectedFlowtrackTicketsProvider);
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final detailAsync = ref.watch(
      flowtrackTicketDetailProvider(widget.ticketId),
    );

    return Container(
      decoration: const BoxDecoration(
        color: Color(0xFFF6F2EB),
        borderRadius: BorderRadius.vertical(top: Radius.circular(32)),
      ),
      child: detailAsync.when(
        data: (ticket) => ListView(
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
                FlowtrackStatusChip(value: ticket.status),
                FlowtrackStatusChip(value: ticket.priority),
                FlowtrackStatusChip(value: ticket.type),
              ],
            ),
            const SizedBox(height: 16),
            Text(
              ticket.title,
              style: const TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.w700,
                color: Color(0xFF0F172A),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              ticket.description,
              style: const TextStyle(color: Color(0xFF475569), height: 1.6),
            ),
            const SizedBox(height: 20),
            _InfoStrip(
              items: [
                'Severity ${ticket.severity}',
                'Environment ${ticket.environment}',
                'Created ${DateFormat.yMMMd().format(DateTime.parse(ticket.createdAt))}',
              ],
            ),
            const SizedBox(height: 24),
            const FlowtrackSectionHeader(
              eyebrow: 'Discussion',
              title: 'Comments',
            ),
            const SizedBox(height: 12),
            if (ticket.comments.isEmpty)
              const FlowtrackEmptyState(
                title: 'No comments yet',
                description:
                    'Use the field below to add clarification or provide a delivery update.',
                icon: Icons.forum_outlined,
              )
            else
              ...ticket.comments.map(
                (comment) => Container(
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
                          FlowtrackStatusChip(value: comment.visibility),
                          _MetaText(
                            label: DateFormat.yMMMd().add_jm().format(
                              DateTime.parse(comment.createdAt),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 10),
                      Text(
                        comment.body,
                        style: const TextStyle(
                          height: 1.5,
                          color: Color(0xFF334155),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            const SizedBox(height: 24),
            AppTextField(
              controller: _commentController,
              label: 'Add a comment',
              prefixIcon: Icons.chat_bubble_outline_rounded,
              maxLines: 4,
            ),
            const SizedBox(height: 12),
            FilledButton(
              onPressed: _isSubmitting ? null : _submitComment,
              child: _isSubmitting
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Text('Post comment'),
            ),
            if (ticket.attachments.isNotEmpty) ...[
              const SizedBox(height: 24),
              const FlowtrackSectionHeader(
                eyebrow: 'Evidence',
                title: 'Attachments',
              ),
              const SizedBox(height: 12),
              ...ticket.attachments.map(
                (attachment) => Container(
                  margin: const EdgeInsets.only(bottom: 10),
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(22),
                    border: Border.all(color: const Color(0xFFE2E8F0)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.image_outlined),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              attachment.filename,
                              style: const TextStyle(
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                            Text(
                              attachment.mimeType,
                              style: const TextStyle(
                                fontSize: 12,
                                color: Color(0xFF64748B),
                              ),
                            ),
                          ],
                        ),
                      ),
                      FlowtrackStatusChip(value: attachment.scanStatus),
                    ],
                  ),
                ),
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

class _CreateTicketSheet extends ConsumerStatefulWidget {
  final WorkspaceTenant tenant;

  const _CreateTicketSheet({required this.tenant});

  @override
  ConsumerState<_CreateTicketSheet> createState() => _CreateTicketSheetState();
}

class _CreateTicketSheetState extends ConsumerState<_CreateTicketSheet> {
  late final TextEditingController _titleController;
  late final TextEditingController _descriptionController;
  late final TextEditingController _categoryController;
  String _type = 'bug';
  String _severity = 'medium';
  String _priority = 'P3';
  bool _isSubmitting = false;

  @override
  void initState() {
    super.initState();
    _titleController = TextEditingController();
    _descriptionController = TextEditingController();
    _categoryController = TextEditingController();
  }

  @override
  void dispose() {
    _titleController.dispose();
    _descriptionController.dispose();
    _categoryController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_titleController.text.trim().isEmpty ||
        _descriptionController.text.trim().isEmpty) {
      return;
    }

    setState(() => _isSubmitting = true);
    try {
      await ref
          .read(flowtrackRepositoryProvider)
          .createTicket(
            tenantId: widget.tenant.id,
            title: _titleController.text.trim(),
            description: _descriptionController.text.trim(),
            type: _type,
            severity: _severity,
            priority: _priority,
            category: _categoryController.text.trim(),
            environment: 'production',
          );
      ref.invalidate(selectedFlowtrackTicketsProvider);
      ref.invalidate(selectedFlowtrackSummaryProvider);
      if (mounted) Navigator.of(context).pop();
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: Color(0xFFF6F2EB),
        borderRadius: BorderRadius.vertical(top: Radius.circular(32)),
      ),
      child: ListView(
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
          const SizedBox(height: 18),
          const FlowtrackSectionHeader(
            eyebrow: 'Create ticket',
            title: 'Log a new request',
          ),
          const SizedBox(height: 8),
          Text(
            'Submitting into ${widget.tenant.name}.',
            style: const TextStyle(color: Color(0xFF475569)),
          ),
          const SizedBox(height: 20),
          AppTextField(
            controller: _titleController,
            label: 'Title',
            prefixIcon: Icons.title_rounded,
          ),
          const SizedBox(height: 12),
          AppTextField(
            controller: _descriptionController,
            label: 'Description',
            prefixIcon: Icons.subject_rounded,
            maxLines: 5,
          ),
          const SizedBox(height: 12),
          AppTextField(
            controller: _categoryController,
            label: 'Category',
            prefixIcon: Icons.category_outlined,
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: _SelectorField(
                  label: 'Type',
                  value: _type,
                  options: const [
                    'bug',
                    'incident',
                    'service_request',
                    'change_request',
                  ],
                  onChanged: (value) => setState(() => _type = value!),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _SelectorField(
                  label: 'Severity',
                  value: _severity,
                  options: const ['low', 'medium', 'high', 'critical'],
                  onChanged: (value) => setState(() => _severity = value!),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          _SelectorField(
            label: 'Priority',
            value: _priority,
            options: const ['P1', 'P2', 'P3', 'P4'],
            onChanged: (value) => setState(() => _priority = value!),
          ),
          const SizedBox(height: 18),
          FilledButton(
            onPressed: _isSubmitting ? null : _submit,
            child: _isSubmitting
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Text('Create ticket'),
          ),
        ],
      ),
    );
  }
}

class _SelectorField extends StatelessWidget {
  final String label;
  final String value;
  final List<String> options;
  final ValueChanged<String?> onChanged;

  const _SelectorField({
    required this.label,
    required this.value,
    required this.options,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return InputDecorator(
      decoration: InputDecoration(labelText: label),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<String>(
          value: value,
          isExpanded: true,
          onChanged: onChanged,
          items: options
              .map(
                (option) => DropdownMenuItem<String>(
                  value: option,
                  child: Text(option.replaceAll('_', ' ')),
                ),
              )
              .toList(),
        ),
      ),
    );
  }
}

class _MetaText extends StatelessWidget {
  final String label;

  const _MetaText({required this.label});

  @override
  Widget build(BuildContext context) {
    return Text(
      label,
      style: const TextStyle(
        fontSize: 12,
        color: Color(0xFF64748B),
        fontWeight: FontWeight.w600,
      ),
    );
  }
}

class _InfoStrip extends StatelessWidget {
  final List<String> items;

  const _InfoStrip({required this.items});

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 10,
      runSpacing: 10,
      children: items
          .map(
            (item) => Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(999),
                border: Border.all(color: const Color(0xFFE2E8F0)),
              ),
              child: Text(
                item,
                style: const TextStyle(fontSize: 12, color: Color(0xFF475569)),
              ),
            ),
          )
          .toList(),
    );
  }
}
