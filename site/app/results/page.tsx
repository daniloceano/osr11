import Link from 'next/link';
import ResultsGrid from '@/components/ResultsGrid';

export const metadata = {
  title: 'Analysis & Outputs | OSR11',
  description: 'Storm catalogs, exposure maps, vulnerability index, and risk maps',
};

export default function ResultsPage() {
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
            Analysis & Outputs
          </h1>
          <p className="text-lg text-gray-600 max-w-3xl">
            Overview of analytical blocks: storm catalogs, compound event identification, exposure mapping, vulnerability assessment, and integrated risk analysis
          </p>
        </div>
      </section>

      {/* Results Grid */}
      <ResultsGrid />
    </main>
  );
}
