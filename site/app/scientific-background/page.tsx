import Link from 'next/link';
import {
  projectContext,
  scientificMotivation,
  generalObjective,
  specificObjectives,
  currentScope,
  conceptualFramework,
  stakeholders,
} from '@/content/project';

export const metadata = {
  title: 'Scientific Background | OSR11',
  description: 'Scientific context, motivation, conceptual framework, stakeholders, and objectives',
};

export default function ScientificBackgroundPage() {
  return (
    <main className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <section className="border-b border-gray-200 bg-white py-16">
        <div className="mx-auto max-w-5xl px-6">
          <Link 
            href="/"
            className="mb-6 inline-flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700 transition-colors"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Home
          </Link>
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Scientific Background
          </h1>
          <p className="text-lg text-gray-600 max-w-3xl">
            Context, motivation, conceptual framework, stakeholders, and research objectives
          </p>
        </div>
      </section>

      {/* Content */}
      <section className="py-16">
        <div className="mx-auto max-w-5xl px-6">
          
          {/* Context & Motivation */}
          <div className="grid gap-8 md:grid-cols-2 mb-12">
            <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
              <h2 className="mb-4 text-xl font-bold text-gray-900">Scientific Context</h2>
              <p className="text-sm leading-relaxed text-gray-700">{projectContext.trim()}</p>
            </div>

            <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
              <h2 className="mb-4 text-xl font-bold text-gray-900">Scientific Motivation</h2>
              <p className="text-sm leading-relaxed text-gray-700">{scientificMotivation.trim()}</p>
            </div>
          </div>

          {/* Conceptual Framework */}
          <div className="mb-12 rounded-xl border-2 border-blue-200 bg-white p-8 shadow-sm">
            <h2 className="mb-6 text-2xl font-bold text-gray-900">
              {conceptualFramework.title}
            </h2>
            <div className="mb-6 rounded-lg bg-blue-50 border-2 border-blue-200 p-5 text-center">
              <p className="text-base font-bold text-blue-900 tracking-wide">
                {conceptualFramework.chain}
              </p>
            </div>
            <div className="space-y-4">
              {conceptualFramework.components.map((comp, i) => (
                <div key={i} className="rounded-lg border border-gray-300 bg-gray-50 p-4">
                  <p className="text-base font-bold text-gray-900 mb-2">{comp.term}</p>
                  <p className="text-sm text-gray-700 leading-relaxed">{comp.definition}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Stakeholders */}
          <div className="mb-12">
            <h2 className="mb-6 text-2xl font-bold text-gray-900">Target Stakeholders</h2>
            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {stakeholders.map((stakeholder, i) => (
                <div key={i} className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
                  <p className="mb-3 text-base font-bold text-gray-900">{stakeholder.name}</p>
                  <p className="text-sm leading-relaxed text-gray-600">{stakeholder.description}</p>
                </div>
              ))}
            </div>
          </div>

          {/* General Objective */}
          <div className="mb-12 rounded-xl border-2 border-blue-200 bg-blue-50 p-8">
            <h2 className="mb-4 text-2xl font-bold text-blue-900">General Objective</h2>
            <p className="text-base leading-relaxed text-gray-900">{generalObjective.trim()}</p>
          </div>

          {/* Specific Objectives */}
          <div className="mb-12">
            <h2 className="mb-6 text-2xl font-bold text-gray-900">Specific Objectives</h2>
            <div className="grid gap-5 sm:grid-cols-2">
              {specificObjectives.map((obj, i) => (
                <div key={i} className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
                  <div className="mb-3 flex items-center gap-3">
                    <span className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-blue-600 bg-blue-50 text-sm font-bold text-blue-600">
                      {i + 1}
                    </span>
                    <p className="text-base font-bold text-gray-900">{obj.label}</p>
                  </div>
                  <p className="text-sm leading-relaxed text-gray-700 pl-11">{obj.description}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Current Implementation Status */}
          <div className="rounded-xl border-2 border-amber-300 bg-amber-50 p-8">
            <div className="flex items-start gap-4">
              <svg className="mt-1 h-6 w-6 flex-shrink-0 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <div>
                <h2 className="mb-3 text-xl font-bold text-amber-900">Current Implementation Status</h2>
                <div className="text-sm leading-relaxed text-gray-900 space-y-3">
                  {currentScope.trim().split('\n\n').map((para, i) => (
                    <p key={i}>{para}</p>
                  ))}
                </div>
              </div>
            </div>
          </div>

        </div>
      </section>
    </main>
  );
}
