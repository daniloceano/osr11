import type { Status } from '@/lib/types';

interface StatusBadgeProps {
  status: Status;
  size?: 'sm' | 'md';
}

const labels: Record<Status, string> = {
  done: 'Complete',
  'in-progress': 'In Progress',
  planned: 'Planned',
};

const styles: Record<Status, string> = {
  done: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  'in-progress': 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  planned: 'bg-slate-500/15 text-slate-400 border-slate-500/30',
};

const dots: Record<Status, string> = {
  done: 'bg-emerald-400',
  'in-progress': 'bg-amber-400 animate-pulse',
  planned: 'bg-slate-500',
};

export default function StatusBadge({ status, size = 'md' }: StatusBadgeProps) {
  const padding = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs';
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border font-medium ${padding} ${styles[status]}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${dots[status]}`} />
      {labels[status]}
    </span>
  );
}
