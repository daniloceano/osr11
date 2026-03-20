import { methodologySteps, conceptualFramework } from '@/content/methodology';
import StatusBadge from './StatusBadge';

export default function MethodologyFlowchart() {
  return (
    <section id="methodology" className="border-b border-slate-800 bg-[#0a0f1e] py-20">
      <div className="mx-auto max-w-5xl px-6">
        {/* Section header */}
        <div className="mb-12">
          <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-sky-400">
            Analytical Framework
          </p>
          <h2 className="text-3xl font-bold text-slate-100">Methodology Pipeline</h2>
          <p className="mt-3 max-w-2xl text-sm text-slate-400">
            The analysis follows a sequential pipeline from data acquisition to risk integration.
            Steps are colour-coded by status. The current active stage is highlighted.
          </p>
        </div>

        {/* Conceptual framework note */}
        <div className="mb-10 rounded-xl border border-slate-800 bg-slate-900 p-5">
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
            Conceptual Framework
          </h3>
          <p className="text-sm leading-relaxed text-slate-400">
            {conceptualFramework.trim()}
          </p>
        </div>

        {/* Pipeline */}
        <div className="relative">
          {/* Connector line */}
          <div className="absolute left-[22px] top-4 bottom-4 w-px bg-slate-800 md:left-1/2 md:-translate-x-px" />

          <div className="space-y-4">
            {methodologySteps.map((step, i) => {
              const isCurrent = step.isCurrent;
              const isDone = step.status === 'done';
              const isPlanned = step.status === 'planned';

              return (
                <div
                  key={step.id}
                  className={`relative flex gap-4 md:gap-8 ${
                    i % 2 === 0 ? 'md:flex-row' : 'md:flex-row-reverse'
                  }`}
                >
                  {/* Step node */}
                  <div className="relative z-10 flex-shrink-0 flex items-start justify-center md:w-1/2 md:justify-center">
                    <div
                      className={`flex h-11 w-11 items-center justify-center rounded-full border-2 text-sm font-bold transition-all ${
                        isCurrent
                          ? 'border-sky-400 bg-sky-400/20 text-sky-300 shadow-[0_0_20px_rgba(56,189,248,0.3)]'
                          : isDone
                          ? 'border-emerald-500 bg-emerald-500/15 text-emerald-400'
                          : 'border-slate-700 bg-slate-900 text-slate-600'
                      }`}
                    >
                      {isDone ? (
                        <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                        </svg>
                      ) : (
                        <span>{i + 1}</span>
                      )}
                    </div>
                  </div>

                  {/* Content card */}
                  <div className={`flex-1 pb-4 md:w-1/2 ${i % 2 === 0 ? 'md:text-left' : 'md:text-left'}`}>
                    <div
                      className={`rounded-xl border p-5 transition-all ${
                        isCurrent
                          ? 'border-sky-500/40 bg-sky-500/5 shadow-[0_0_30px_rgba(56,189,248,0.07)]'
                          : isDone
                          ? 'border-emerald-500/20 bg-slate-900'
                          : 'border-slate-800 bg-slate-900/50'
                      }`}
                    >
                      <div className="mb-2 flex flex-wrap items-center gap-2">
                        <h3
                          className={`text-sm font-semibold ${
                            isCurrent
                              ? 'text-sky-300'
                              : isDone
                              ? 'text-emerald-300'
                              : isPlanned
                              ? 'text-slate-500'
                              : 'text-slate-300'
                          }`}
                        >
                          {step.label}
                        </h3>
                        {isCurrent && (
                          <span className="rounded-full border border-sky-400/40 bg-sky-400/10 px-2 py-0.5 text-xs font-medium text-sky-400">
                            Current stage
                          </span>
                        )}
                        <StatusBadge status={step.status} size="sm" />
                      </div>
                      <p className={`text-xs leading-relaxed ${isPlanned ? 'text-slate-600' : 'text-slate-400'}`}>
                        {step.description}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Legend */}
        <div className="mt-10 flex flex-wrap gap-4 rounded-xl border border-slate-800 bg-slate-900 p-4">
          <p className="w-full text-xs font-semibold uppercase tracking-wider text-slate-500">
            Legend
          </p>
          {[
            { status: 'done' as const, desc: 'Pipeline step completed' },
            { status: 'in-progress' as const, desc: 'Active analysis stage' },
            { status: 'planned' as const, desc: 'Scheduled for future phases' },
          ].map((item) => (
            <div key={item.status} className="flex items-center gap-2">
              <StatusBadge status={item.status} size="sm" />
              <span className="text-xs text-slate-500">{item.desc}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
