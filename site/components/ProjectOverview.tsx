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

export default function ProjectOverview() {
  return (
    <section id="overview" className="border-b border-gray-200 bg-white py-20">
      <div className="mx-auto max-w-5xl px-6">
        {/* Section header */}
        <div className="mb-12">
          <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-blue-600">
            Project Overview
          </p>
          <h2 className="text-3xl font-bold text-gray-900">
            Key Components
          </h2>
        </div>

        {/* Card Grid */}
        <div className="grid gap-6 md:grid-cols-2">
          
          {/* Card 1: Scientific Background */}
          <Link 
            href="#scientific-background"
            className="group rounded-xl border-2 border-gray-200 bg-white p-6 hover:border-blue-400 hover:shadow-lg transition-all"
          >
            <div className="flex items-start gap-4">
              <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-blue-100 text-blue-600 group-hover:bg-blue-600 group-hover:text-white transition-colors">
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 mb-2 group-hover:text-blue-600 transition-colors">
                  Scientific Background
                </h3>
                <p className="text-sm text-gray-600 leading-relaxed">
                  Context, motivation, framework, stakeholders, and objectives
                </p>
              </div>
            </div>
          </Link>

          {/* Card 2: Analytical Framework */}
          <Link 
            href="#methodology"
            className="group rounded-xl border-2 border-gray-200 bg-white p-6 hover:border-blue-400 hover:shadow-lg transition-all"
          >
            <div className="flex items-start gap-4">
              <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-blue-100 text-blue-600 group-hover:bg-blue-600 group-hover:text-white transition-colors">
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                </svg>
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 mb-2 group-hover:text-blue-600 transition-colors">
                  Analytical Framework
                </h3>
                <p className="text-sm text-gray-600 leading-relaxed">
                  8-step algorithm from data to risk mapping
                </p>
              </div>
            </div>
          </Link>

          {/* Card 3: Data Sources */}
          <Link 
            href="#data"
            className="group rounded-xl border-2 border-gray-200 bg-white p-6 hover:border-blue-400 hover:shadow-lg transition-all"
          >
            <div className="flex items-start gap-4">
              <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-blue-100 text-blue-600 group-hover:bg-blue-600 group-hover:text-white transition-colors">
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
                </svg>
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 mb-2 group-hover:text-blue-600 transition-colors">
                  Input Data Sources
                </h3>
                <p className="text-sm text-gray-600 leading-relaxed">
                  CMEMS, ERA5, disaster databases, vulnerability data
                </p>
              </div>
            </div>
          </Link>

          {/* Card 4: Analysis & Outputs */}
          <Link 
            href="#results"
            className="group rounded-xl border-2 border-gray-200 bg-white p-6 hover:border-blue-400 hover:shadow-lg transition-all"
          >
            <div className="flex items-start gap-4">
              <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-blue-100 text-blue-600 group-hover:bg-blue-600 group-hover:text-white transition-colors">
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 mb-2 group-hover:text-blue-600 transition-colors">
                  Analysis & Outputs
                </h3>
                <p className="text-sm text-gray-600 leading-relaxed">
                  Catalogs, exposure maps, risk maps, hotspots
                </p>
              </div>
            </div>
          </Link>

        </div>

        {/* Scientific Background Section - Collapsed by default */}
        <div id="scientific-background" className="mt-16 scroll-mt-24">
          <h3 className="text-2xl font-bold text-gray-900 mb-8">Scientific Background</h3>
          
          <div className="grid gap-8 md:grid-cols-2 mb-8">
            <div className="rounded-xl border border-gray-200 bg-gray-50 p-6">
              <h4 className="mb-3 text-sm font-semibold text-blue-600">Scientific Context</h4>
              <p className="text-sm leading-relaxed text-gray-700">{projectContext.trim()}</p>
            </div>

            <div className="rounded-xl border border-gray-200 bg-gray-50 p-6">
              <h4 className="mb-3 text-sm font-semibold text-blue-600">Scientific Motivation</h4>
              <p className="text-sm leading-relaxed text-gray-700">{scientificMotivation.trim()}</p>
            </div>
          </div>

          {/* Conceptual Framework - Fixed background */}
          <div className="mb-8 rounded-xl border border-blue-200 bg-white p-6 shadow-sm">
            <h4 className="mb-4 text-sm font-semibold text-blue-700">
              {conceptualFramework.title}
            </h4>
            <div className="mb-4 rounded-lg bg-blue-50 border border-blue-200 p-4 text-center">
              <p className="text-sm font-bold text-blue-900">
                {conceptualFramework.chain}
              </p>
            </div>
            <div className="space-y-3">
              {conceptualFramework.components.map((comp, i) => (
                <div key={i} className="rounded-lg border border-gray-200 bg-gray-50 p-3">
                  <p className="text-sm font-bold text-gray-900 mb-1">{comp.term}</p>
                  <p className="text-sm text-gray-700 leading-relaxed">{comp.definition}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Stakeholders */}
          <div className="mb-8">
            <h4 className="mb-5 text-sm font-semibold text-gray-600 uppercase tracking-wider">
              Target Stakeholders
            </h4>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {stakeholders.map((stakeholder, i) => (
                <div key={i} className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
                  <p className="mb-2 text-sm font-semibold text-gray-900">{stakeholder.name}</p>
                  <p className="text-xs leading-relaxed text-gray-600">{stakeholder.description}</p>
                </div>
              ))}
            </div>
          </div>

          {/* General objective */}
          <div className="mb-8 rounded-xl border border-blue-200 bg-blue-50 p-6">
            <h4 className="mb-3 text-sm font-semibold text-blue-700">General Objective</h4>
            <p className="text-sm leading-relaxed text-gray-900">{generalObjective.trim()}</p>
          </div>

          {/* Specific objectives */}
          <div>
            <h4 className="mb-5 text-sm font-semibold text-gray-600 uppercase tracking-wider">
              Specific Objectives
            </h4>
            <div className="grid gap-4 sm:grid-cols-2">
              {specificObjectives.map((obj, i) => (
                <div key={i} className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
                  <div className="mb-2 flex items-center gap-2">
                    <span className="flex h-6 w-6 items-center justify-center rounded-full border-2 border-blue-600 bg-blue-50 text-xs font-bold text-blue-600">
                      {i + 1}
                    </span>
                    <p className="text-sm font-semibold text-gray-900">{obj.label}</p>
                  </div>
                  <p className="text-xs leading-relaxed text-gray-700 pl-8">{obj.description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Current scope warning - Fixed text color */}
        <div className="mt-8 rounded-xl border-2 border-amber-300 bg-amber-50 p-6">
          <div className="flex items-start gap-3">
            <svg className="mt-0.5 h-5 w-5 flex-shrink-0 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div>
              <h4 className="mb-2 text-sm font-semibold text-amber-900">Current Implementation Status</h4>
              <div className="text-sm leading-relaxed text-gray-900 space-y-2">
                {currentScope.trim().split('\n\n').map((para, i) => (
                  <p key={i}>{para}</p>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
