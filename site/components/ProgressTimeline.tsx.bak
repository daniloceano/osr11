import { timelinePhases } from '@/content/project';
import StatusBadge from './StatusBadge';

export default function ProgressTimeline() {
  const doneCount = timelinePhases.filter((p) => p.status === 'done').length;
  const inProgressCount = timelinePhases.filter((p) => p.status === 'in-progress').length;
  const totalCount = timelinePhases.length;

  return (
    <section id="progress" className="border-b border-slate-800 bg-slate-950 py-20">
      <div className="mx-auto max-w-5xl px-6">
        {/* Header */}
        <div className="mb-12">
          <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-sky-400">
            Project Status
          </p>
          <h2 className="text-3xl font-bold text-slate-100">Roadmap</h2>
          <p className="mt-3 max-w-2xl text-sm text-slate-400">
            Full pipeline from data acquisition to risk integration. All results presented in
            this site correspond to Phase 1 (exploratory analysis, south SC test domain).
          </p>
        </div>

        {/* Progress bar summary */}
        <div className="mb-10 rounded-xl border border-slate-800 bg-slate-900 p-6">
          <div className="flex flex-wrap gap-6 mb-4">
            <div>
              <span className="text-2xl font-bold text-emerald-400">{doneCount}</span>
              <span className="ml-1 text-sm text-slate-500">phase{doneCount !== 1 ? 's' : ''} complete</span>
            </div>
            <div>
              <span className="text-2xl font-bold text-amber-400">{inProgressCount}</span>
              <span className="ml-1 text-sm text-slate-500">in progress</span>
            </div>
            <div>
              <span className="text-2xl font-bold text-slate-600">{totalCount - doneCount - inProgressCount}</span>
              <span className="ml-1 text-sm text-slate-500">planned</span>
            </div>
          </div>

          {/* Bar */}
          <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-amber-400 transition-all"
              style={{
                width: `${((doneCount + inProgressCount * 0.5) / totalCount) * 100}%`,
              }}
            />
          </div>
          <p className="mt-1.5 text-xs text-slate-600">
            Estimated completion: pipeline and data acquisition phases done · exploratory analysis ongoing
          </p>
        </div>

        {/* Phases */}
        <div className="space-y-4">
          {timelinePhases.map((phase, i) => {
            const isDone = phase.status === 'done';
            const isCurrent = phase.status === 'in-progress';

            return (
              <div
                key={phase.id}
                className={`rounded-xl border p-6 transition-all ${
                  isCurrent
                    ? 'border-amber-500/30 bg-amber-500/5'
                    : isDone
                    ? 'border-emerald-500/20 bg-slate-900'
                    : 'border-slate-800 bg-slate-900/50 opacity-70'
                }`}
              >
                <div className="flex flex-wrap items-start justify-between gap-3 mb-3">
                  <div className="flex items-center gap-3">
                    <div
                      className={`flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full border text-xs font-bold ${
                        isDone
                          ? 'border-emerald-500 bg-emerald-500/15 text-emerald-400'
                          : isCurrent
                          ? 'border-amber-400 bg-amber-400/15 text-amber-300'
                          : 'border-slate-700 bg-slate-900 text-slate-600'
                      }`}
                    >
                      {isDone ? (
                        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                        </svg>
                      ) : (
                        i
                      )}
                    </div>
                    <div>
                      <h3 className={`text-sm font-semibold ${isCurrent ? 'text-amber-300' : isDone ? 'text-emerald-300' : 'text-slate-500'}`}>
                        {phase.label}
                      </h3>
                      <p className={`text-xs ${isCurrent || isDone ? 'text-slate-400' : 'text-slate-600'}`}>
                        {phase.description}
                      </p>
                    </div>
                  </div>
                  <StatusBadge status={phase.status} size="sm" />
                </div>

                {/* Task list */}
                {(isDone || isCurrent) && (
                  <ul className="mt-3 grid gap-1 sm:grid-cols-2 border-t border-slate-800 pt-3">
                    {phase.tasks.map((task, j) => (
                      <li key={j} className="flex items-start gap-2 text-xs text-slate-500">
                        <svg className={`mt-0.5 h-3.5 w-3.5 flex-shrink-0 ${isDone ? 'text-emerald-500' : 'text-amber-500'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                        </svg>
                        {task}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
