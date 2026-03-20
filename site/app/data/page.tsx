import Link from 'next/link';
import { dataSources } from '@/content/datasources';
import StatusBadge from '@/components/StatusBadge';

export const metadata = {
  title: 'Input Data Sources | OSR11',
  description: 'CMEMS reanalyses, ERA5, disaster databases, and vulnerability indicators',
};

export default function DataPage() {
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
            Input Data Sources
          </h1>
          <p className="text-lg text-gray-600 max-w-3xl">
            Comprehensive overview of oceanographic reanalyses, atmospheric data, disaster databases, and vulnerability indicators used in the analysis
          </p>
        </div>
      </section>

      {/* Data Sources Grid */}
      <section className="py-16">
        <div className="mx-auto max-w-5xl px-6">
          <div className="grid gap-6">
            {dataSources.map((source) => (
              <div
                key={source.id}
                className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm"
              >
                <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-bold text-gray-900">{source.name}</h2>
                    <p className="mt-1 text-sm text-blue-600 font-medium">{source.shortName}</p>
                  </div>
                  <StatusBadge status={source.status} />
                </div>

                <p className="mb-4 text-sm leading-relaxed text-gray-700">
                  {source.description}
                </p>

                <div className="grid gap-4 sm:grid-cols-2 mb-4">
                  {source.variables && (
                    <div className="rounded-lg border border-gray-200 bg-gray-50 p-3">
                      <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-600">
                        Variables
                      </p>
                      <p className="text-sm text-gray-800">{source.variables}</p>
                    </div>
                  )}

                  {source.resolution && (
                    <div className="rounded-lg border border-gray-200 bg-gray-50 p-3">
                      <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-600">
                        Resolution
                      </p>
                      <p className="text-sm text-gray-800">{source.resolution}</p>
                    </div>
                  )}

                  {source.period && (
                    <div className="rounded-lg border border-gray-200 bg-gray-50 p-3">
                      <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-600">
                        Period
                      </p>
                      <p className="text-sm text-gray-800">{source.period}</p>
                    </div>
                  )}

                  {source.role && (
                    <div className="rounded-lg border border-gray-200 bg-gray-50 p-3">
                      <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-600">
                        Role
                      </p>
                      <p className="text-sm text-gray-800">{source.role}</p>
                    </div>
                  )}
                </div>

                {source.stage && (
                  <div className="rounded-lg border-l-4 border-blue-500 bg-blue-50 p-3">
                    <p className="text-xs font-semibold uppercase tracking-wider text-blue-700 mb-1">
                      Usage Stage
                    </p>
                    <p className="text-sm text-gray-800">{source.stage}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
