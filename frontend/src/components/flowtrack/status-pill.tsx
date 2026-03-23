import type {
  AttachmentScanStatus,
  CommentVisibility,
  MilestoneStatus,
  ProjectHealth,
  ProjectStatus,
  ReleaseStatus,
  TaskStatus,
  TicketPriority,
  TicketStatus,
} from '@/types';

type FlowtrackStatus =
  | TicketStatus
  | MilestoneStatus
  | ReleaseStatus
  | TicketPriority
  | ProjectStatus
  | ProjectHealth
  | TaskStatus
  | CommentVisibility
  | AttachmentScanStatus;

const toneMap: Record<string, string> = {
  new: 'bg-[rgba(30,64,175,0.12)] text-blue-700',
  awaiting_clarification: 'bg-[rgba(202,138,4,0.14)] text-amber-700',
  triaged: 'bg-[rgba(14,116,144,0.12)] text-cyan-700',
  assigned: 'bg-[rgba(8,145,178,0.12)] text-sky-700',
  in_progress: 'bg-[rgba(37,99,235,0.14)] text-blue-700',
  blocked: 'bg-[rgba(220,38,38,0.14)] text-red-700',
  ready_for_qa: 'bg-[rgba(124,58,237,0.12)] text-violet-700',
  closed: 'bg-[rgba(21,128,61,0.14)] text-emerald-700',
  reopened: 'bg-[rgba(194,65,12,0.14)] text-orange-700',
  draft: 'bg-[rgba(71,85,105,0.12)] text-slate-700',
  baselined: 'bg-[rgba(14,116,144,0.12)] text-cyan-700',
  at_risk: 'bg-[rgba(217,119,6,0.14)] text-amber-700',
  replanning: 'bg-[rgba(91,33,182,0.12)] text-purple-700',
  completed: 'bg-[rgba(21,128,61,0.14)] text-emerald-700',
  cancelled: 'bg-[rgba(100,116,139,0.16)] text-slate-700',
  planned: 'bg-[rgba(59,130,246,0.12)] text-blue-700',
  deployed: 'bg-[rgba(22,163,74,0.14)] text-green-700',
  rolled_back: 'bg-[rgba(220,38,38,0.14)] text-red-700',
  P1: 'bg-[rgba(127,29,29,0.12)] text-red-800',
  P2: 'bg-[rgba(194,65,12,0.12)] text-orange-700',
  P3: 'bg-[rgba(202,138,4,0.12)] text-amber-700',
  P4: 'bg-[rgba(8,145,178,0.12)] text-cyan-700',
  active: 'bg-[rgba(22,163,74,0.14)] text-green-700',
  on_hold: 'bg-[rgba(217,119,6,0.12)] text-amber-700',
  green: 'bg-[rgba(22,163,74,0.14)] text-green-700',
  amber: 'bg-[rgba(217,119,6,0.12)] text-amber-700',
  red: 'bg-[rgba(220,38,38,0.14)] text-red-700',
  todo: 'bg-[rgba(71,85,105,0.12)] text-slate-700',
  done: 'bg-[rgba(21,128,61,0.14)] text-emerald-700',
  public: 'bg-[rgba(8,145,178,0.12)] text-cyan-700',
  internal: 'bg-[rgba(91,33,182,0.12)] text-purple-700',
  pending: 'bg-[rgba(202,138,4,0.12)] text-amber-700',
  clean: 'bg-[rgba(21,128,61,0.14)] text-emerald-700',
  quarantined: 'bg-[rgba(220,38,38,0.14)] text-red-700',
};

function formatLabel(value: string) {
  return value.replace(/_/g, ' ');
}

export function StatusPill({ value }: { value: FlowtrackStatus }) {
  return (
    <span
      className={`inline-flex rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] ${toneMap[value] ?? 'bg-black/5 text-slate-700'}`}
    >
      {formatLabel(value)}
    </span>
  );
}
