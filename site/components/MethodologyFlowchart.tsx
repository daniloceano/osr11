import { methodologySteps, conceptualFramework } from '@/content/methodology';
import StatusBadge from './StatusBadge';

export default function MethodologyFlowchart() {
  return (
    <section id="methodology" className="border-b border-gray-200 bg-white py-20">
      <div className="mx-auto max-w-5xl px-6">
        {/* Section header */}
        <div className="mb-12">
          <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-blue-600">
            Analytical Framework
          </p>
          <h2 className="text-3xl font-bold text-gray-900">Methodology Pipeline</h2>
          <p className="mt-3 max-w-2xl text-sm text-gray-700">
            The analysis follows a sequential pipeline from data acquisition to risk integration.
            Steps are colour-coded by status. The current active stage is highlighted.
          </p>
        </div>

        {/* Conceptual framework note */}
        <div className="mb-10 rounded-xl border border-gray-200 bg-gray-50 p-5">
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-600">
            Conceptual Framework
          </h3>
          <p className="text-sm leading-relaxed text-gray-600">
            {conceptualFramework.trim()}
          </p>
        </div>

        {/* Pipeline */}
        <div className="relative">
          {/* Connector line */}
          <div className="absolute left-[22px] top-4 bottom-4 w-px bg-gray-100 md:left-1/2 md:-translate-x-px" />

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
                          ? 'border-blue-500 bg-blue-100 text-blue-700 shadow-lg'
                          : isDone
                          ? 'border-emerald-500 bg-emerald-100 text-emerald-700'
                          : 'border-gray-300 bg-gray-50 text-gray-500'
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
                          ? 'border-blue-300 bg-blue-50 shadow-md'
                          : isDone
                          ? 'border-emerald-300 bg-emerald-50'
                          : 'border-gray-200 bg-gray-50'
                      }`}
                    >
                      <div className="mb-2 flex flex-wrap items-center gap-2">
                        <h3
                          className={`text-sm font-semibold ${
                            isCurrent
                              ? 'text-blue-700'
                              : isDone
                              ? 'text-emerald-700'
                              : isPlanned
                              ? 'text-gray-500'
                              : 'text-gray-800'
                          }`}
                        >
                          {step.label}
                        </h3>
                        {isCurrent && (
                          <span className="rounded-full border border-sky-400/40 bg-sky-400/10 px-2 py-0.5 text-xs font-medium text-blue-600">
                            Current stage
                          </span>
                        )}
                        <StatusBadge status={step.status} size="sm" />
                      </div>
                      <p className={`text-xs leading-relaxed ${isPlanned ? 'text-gray-500' : 'text-gray-700'}`}>
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
        <div className="mt-10 flex flex-wrap gap-4 rounded-xl border border-gray-200 bg-gray-50 p-4">
          <p className="w-full text-xs font-semibold uppercase tracking-wider text-gray-500">
            Legend
          </p>
          {[
            { status: 'done' as const, desc: 'Pipeline step completed' },
            { status: 'in-progress' as const, desc: 'Active analysis stage' },
            { status: 'planned' as const, desc: 'Scheduled for future phases' },
          ].map((item) => (
            <div key={item.status} className="flex items-center gap-2">
              <StatusBadge status={item.status} size="sm" />
              <span className="text-xs text-gray-500">{item.desc}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
