import {
  projectContext,
  scientificMotivation,
  generalObjective,
  specificObjectives,
  currentScope,
} from '@/content/project';

export default function ProjectOverview() {
  return (
    <section id="overview" className="border-b border-slate-800 bg-slate-950 py-20">
      <div className="mx-auto max-w-5xl px-6">
        {/* Section header */}
        <div className="mb-12">
          <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-sky-400">
            Scientific Context
          </p>
          <h2 className="text-3xl font-bold text-slate-100">
            Project Overview
          </h2>
        </div>

        <div className="grid gap-8 md:grid-cols-2">
          {/* Context */}
          <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">
            <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-sky-400">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064" />
              </svg>
              Scientific Context
            </h3>
            <p className="text-sm leading-relaxed text-slate-400">{projectContext.trim()}</p>
          </div>

          {/* Motivation */}
          <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">
            <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-sky-400">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Scientific Motivation
            </h3>
            <p className="text-sm leading-relaxed text-slate-400">{scientificMotivation.trim()}</p>
          </div>
        </div>

        {/* General objective */}
        <div className="mt-8 rounded-xl border border-sky-500/20 bg-sky-500/5 p-6">
          <h3 className="mb-3 text-sm font-semibold text-sky-400">General Objective</h3>
          <p className="text-sm leading-relaxed text-slate-300">{generalObjective.trim()}</p>
        </div>

        {/* Specific objectives */}
        <div className="mt-8">
          <h3 className="mb-5 text-sm font-semibold text-slate-400 uppercase tracking-wider">
            Specific Objectives
          </h3>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {specificObjectives.map((obj, i) => (
              <div
                key={i}
                className="rounded-lg border border-slate-800 bg-slate-900 p-4"
              >
                <div className="mb-2 flex items-center gap-2">
                  <span className="flex h-5 w-5 items-center justify-center rounded-full border border-slate-700 text-xs font-semibold text-slate-500">
                    {i + 1}
                  </span>
                  <p className="text-xs font-semibold text-slate-300">{obj.label}</p>
                </div>
                <p className="text-xs leading-relaxed text-slate-500">{obj.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Current scope */}
        <div className="mt-8 rounded-xl border border-amber-500/20 bg-amber-500/5 p-6">
          <div className="flex items-start gap-3">
            <svg className="mt-0.5 h-4 w-4 flex-shrink-0 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div>
              <h3 className="mb-2 text-sm font-semibold text-amber-400">Current Scope</h3>
              <p className="text-sm leading-relaxed text-slate-400">{currentScope.trim()}</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
