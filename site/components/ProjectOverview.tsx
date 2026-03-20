import {
  projectContext,
  scientificMotivation,
  generalObjective,
  specificObjectives,
  currentScope,
  conceptualFramework,
  stakeholders,
} from '@/content/project';

export default function ProjectOverview() {
  return (
    <section id="overview" className="border-b border-gray-200 bg-white py-20">
      <div className="mx-auto max-w-5xl px-6">
        {/* Section header */}
        <div className="mb-12">
          <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-blue-600">
            Scientific Context
          </p>
          <h2 className="text-3xl font-bold text-gray-900">
            Project Overview
          </h2>
        </div>

        <div className="grid gap-8 md:grid-cols-2">
          {/* Context */}
          <div className="rounded-xl border border-gray-200 bg-gray-50 p-6">
            <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-blue-600">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064" />
              </svg>
              Scientific Context
            </h3>
            <p className="text-sm leading-relaxed text-gray-600">{projectContext.trim()}</p>
          </div>

          {/* Motivation */}
          <div className="rounded-xl border border-gray-200 bg-gray-50 p-6">
            <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-blue-600">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Scientific Motivation
            </h3>
            <p className="text-sm leading-relaxed text-gray-600">{scientificMotivation.trim()}</p>
          </div>
        </div>

        {/* Conceptual Framework */}
        <div className="mt-8 rounded-xl border border-blue-200 bg-blue-50 p-6">
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-blue-600">
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
            </svg>
            Conceptual Framework
          </h3>
          <div className="prose prose-sm prose-blue max-w-none text-gray-700">
            {conceptualFramework.trim().split('\n\n').map((para, i) => (
              <p key={i} className="text-sm leading-relaxed mb-3 last:mb-0">{para.trim()}</p>
            ))}
          </div>
        </div>

        {/* Stakeholders */}
        <div className="mt-8">
          <h3 className="mb-5 text-sm font-semibold text-gray-600 uppercase tracking-wider">
            Target Stakeholders
          </h3>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {stakeholders.map((stakeholder, i) => (
              <div
                key={i}
                className="rounded-lg border border-gray-200 bg-gray-50 p-4"
              >
                <p className="mb-2 text-xs font-semibold text-gray-700">{stakeholder.name}</p>
                <p className="text-xs leading-relaxed text-gray-500">{stakeholder.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* General objective */}
        <div className="mt-8 rounded-xl border border-blue-200 bg-blue-50 p-6">
          <h3 className="mb-3 text-sm font-semibold text-blue-600">General Objective</h3>
          <p className="text-sm leading-relaxed text-gray-700">{generalObjective.trim()}</p>
        </div>

        {/* Specific objectives */}
        <div className="mt-8">
          <h3 className="mb-5 text-sm font-semibold text-gray-600 uppercase tracking-wider">
            Specific Objectives
          </h3>
          <div className="grid gap-4 sm:grid-cols-2">
            {specificObjectives.map((obj, i) => (
              <div
                key={i}
                className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm"
              >
                <div className="mb-2 flex items-center gap-2">
                  <span className="flex h-5 w-5 items-center justify-center rounded-full border border-blue-600 bg-blue-50 text-xs font-semibold text-blue-600">
                    {i + 1}
                  </span>
                  <p className="text-xs font-semibold text-gray-900">{obj.label}</p>
                </div>
                <p className="text-xs leading-relaxed text-gray-600">{obj.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Current scope */}
        <div className="mt-8 rounded-xl border border-amber-200 bg-amber-50 p-6">
          <div className="flex items-start gap-3">
            <svg className="mt-0.5 h-4 w-4 flex-shrink-0 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div>
              <h3 className="mb-2 text-sm font-semibold text-amber-700">Current Implementation Status</h3>
              <p className="text-sm leading-relaxed text-gray-700 whitespace-pre-line">{currentScope.trim()}</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
