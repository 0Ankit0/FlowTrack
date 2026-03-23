import { Building2 } from 'lucide-react';

export function TenantEmptyState({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-[28px] border border-[rgba(15,23,42,0.08)] bg-white p-8 shadow-[0_24px_80px_rgba(15,23,42,0.08)]">
      <div className="flex max-w-xl items-start gap-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[linear-gradient(135deg,rgba(12,74,110,0.12),rgba(190,24,93,0.14))]">
          <Building2 className="h-5 w-5 text-slate-700" />
        </div>
        <div className="space-y-2">
          <h2 className="text-2xl font-semibold text-slate-900">{title}</h2>
          <p className="text-sm leading-6 text-slate-600">{description}</p>
        </div>
      </div>
    </div>
  );
}
