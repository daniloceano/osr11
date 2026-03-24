import { timelinePhases } from '@/content/project';
import StatusBadge from './StatusBadge';

export default function ProgressTimeline() {
  const doneCount = timelinePhases.filter((p) => p.status === 'done').length;
  const inProgressCount = timelinePhases.filter((p) => p.status === 'in-progress').length;
  const totalCount = timelinePhases.length;

  return (
    <section id="progress" className="border-b border-gray-200 bg-white py-20">
      <div className="mx-auto max-w-5xl px-6">
        {/* Header */}
        <div className="mb-12">
          <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-blue-600">
            Project Status
          </p>
          <h2 className="text-3xl font-bold text-gray-900">Roadmap</h2>
          <p className="mt-3 max-w-2xl text-sm text-gray-600">
            Full pipeline from data acquisition to risk integration. Exploratory analysis and
            initial threshold calibration are complete for the full Santa Catarina coast.
          </p>
        </div>

        {/* Progress bar summary */}
        <div className="mb-10 rounded-xl border border-gray-200 bg-gray-50 p-6">
          <div className="flex flex-wrap gap-6 mb-4">
            <div>
              <span className="text-2xl font-bold text-emerald-400">{doneCount}</span>
              <span className="ml-1 text-sm text-gray-500">phase{doneCount !== 1 ? 's' : ''} complete</span>
            </div>
            <div>
              <span className="text-2xl font-bold text-amber-400">{inProgressCount}</span>
              <span className="ml-1 text-sm text-gray-500">in progress</span>
            </div>
            <div>
              <span className="text-2xl font-bold text-gray-400">{totalCount - doneCount - inProgressCount}</span>
              <span className="ml-1 text-sm text-gray-500">planned</span>
            </div>
          </div>

          {/* Bar */}
          <div className="h-2 w-full rounded-full bg-gray-100 overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-amber-400 transition-all"
              style={{
                width: `${((doneCount + inProgressCount * 0.5) / totalCount) * 100}%`,
              }}
            />
          </div>
          <p className="mt-1.5 text-xs text-gray-400">
            Pipeline, data acquisition, exploratory analysis complete · Threshold calibration in progress
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
                    ? 'border-emerald-500/20 bg-gray-50'
                    : 'border-gray-200 bg-gray-50/50 opacity-70'
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
                          : 'border-gray-300 bg-gray-50 text-gray-400'
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
                      <h3 className={`text-sm font-semibold ${isCurrent ? 'text-amber-300' : isDone ? 'text-emerald-300' : 'text-gray-500'}`}>
                        {phase.label}
                      </h3>
                      <p className={`text-xs ${isCurrent || isDone ? 'text-gray-600' : 'text-gray-400'}`}>
                        {phase.description}
                      </p>
                    </div>
                  </div>
                  <StatusBadge status={phase.status} size="sm" />
                </div>

                {/* Task list */}
                {(isDone || isCurrent) && (
                  <ul className="mt-3 grid gap-1 sm:grid-cols-2 border-t border-gray-200 pt-3">
                    {phase.tasks.map((task, j) => (
                      <li key={j} className="flex items-start gap-2 text-xs text-gray-500">
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
