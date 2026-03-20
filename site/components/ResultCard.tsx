import Link from 'next/link';
import type { ResultCard as ResultCardType } from '@/lib/types';
import StatusBadge from './StatusBadge';

export default function ResultCard({ card }: { card: ResultCardType }) {
  const isClickable = !!card.href;

  const inner = (
    <div
      className={`group h-full rounded-xl border p-6 flex flex-col gap-4 transition-all duration-200 ${
        isClickable
          ? 'border-sky-500/30 bg-slate-900 hover:border-sky-500/50 hover:bg-sky-500/5 cursor-pointer'
          : 'border-slate-800 bg-slate-900'
      }`}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <StatusBadge status={card.status} />
            {card.parts && card.parts.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {card.parts.map((p) => (
                  <span
                    key={p}
                    className="rounded border border-slate-700 bg-slate-800 px-1.5 py-0.5 text-xs text-slate-500"
                  >
                    {p}
                  </span>
                ))}
              </div>
            )}
          </div>
          <h3 className={`text-base font-semibold ${isClickable ? 'text-sky-300 group-hover:text-sky-200' : 'text-slate-200'}`}>
            {card.title}
          </h3>
          <p className="mt-0.5 text-xs text-slate-500">{card.subtitle}</p>
        </div>
        {isClickable && (
          <svg className="h-4 w-4 flex-shrink-0 text-sky-500 opacity-0 group-hover:opacity-100 transition-opacity mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        )}
      </div>

      {/* Description */}
      <p className="text-sm leading-relaxed text-slate-400">{card.description}</p>

      {/* Rationale */}
      <div className="rounded-lg border border-slate-800 bg-slate-950/50 px-4 py-3">
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">
          Scientific Rationale
        </p>
        <p className="text-xs leading-relaxed text-slate-500">{card.rationale}</p>
      </div>

      {/* Outputs */}
      <div className="flex-1">
        <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
          Outputs
        </p>
        <ul className="space-y-1">
          {card.outputs.map((output, i) => (
            <li key={i} className="flex items-start gap-2 text-xs text-slate-400">
              <span className="mt-1.5 h-1 w-1 flex-shrink-0 rounded-full bg-emerald-500" />
              {output}
            </li>
          ))}
        </ul>
      </div>

      {/* CTA */}
      {isClickable && (
        <div className="border-t border-slate-800 pt-3">
          <span className="text-xs font-medium text-sky-400 group-hover:text-sky-300">
            View detailed results →
          </span>
        </div>
      )}
    </div>
  );

  return isClickable ? (
    <Link href={card.href!} className="block h-full">
      {inner}
    </Link>
  ) : (
    inner
  );
}
