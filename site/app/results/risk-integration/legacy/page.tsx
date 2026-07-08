import Link from 'next/link';
import Navigation from '@/components/Navigation';
import Footer from '@/components/Footer';
import StatusBadge from '@/components/StatusBadge';
import RiskIntegrationClient from '../RiskIntegrationClient';

export const metadata = {
  title: 'Legacy Multi-Metric Risk Integration | OSR11',
  description:
    'Legacy municipal coastal risk indices using the former frequency, duration, and intensity hazard aggregation.',
};

export default function LegacyRiskIntegrationPage() {
  return (
    <>
      <Navigation />
      <main className="pt-16">
        <div className="border-b border-gray-200 bg-white py-16">
          <div className="mx-auto max-w-6xl px-6">
            <div className="mb-4 flex items-center gap-2 text-xs text-gray-500">
              <Link href="/" className="transition-colors hover:text-gray-700">Overview</Link>
              <ChevronSvg />
              <Link href="/results" className="transition-colors hover:text-gray-700">Results</Link>
              <ChevronSvg />
              <Link href="/results/risk-integration" className="transition-colors hover:text-gray-700">Risk Integration</Link>
              <ChevronSvg />
              <span className="text-gray-600">Legacy</span>
            </div>

            <div className="mb-4 flex flex-wrap items-start gap-2">
              <StatusBadge status="done" />
              <span className="rounded-full border border-amber-300 bg-amber-50 px-2.5 py-1 text-xs text-amber-800">
                Legacy multi-metric product
              </span>
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">
                Retained for audit and comparison
              </span>
            </div>

            <h1 className="text-3xl font-bold text-gray-900 md:text-4xl">
              Legacy Risk Integration
              <br />
              <span className="text-amber-700">Frequency, Duration &amp; Intensity Hazard</span>
            </h1>
            <p className="mt-3 max-w-3xl text-sm text-gray-600">
              This page preserves the former municipal risk product. Its Hazard_Index averages
              norm(compound_c), norm(mean_overl), and norm(mean_compo). The current recommended product
              now uses only compound-event count in the hazard layer because duration and intensity carry
              additional interpretation uncertainty near river mouths and estuaries.
            </p>
            <Link
              href="/results/risk-integration"
              className="mt-5 inline-flex rounded-lg border border-blue-200 bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700 transition-colors hover:bg-blue-100"
            >
              Return to current compound-count product
            </Link>
          </div>
        </div>

        <div className="py-10">
          <div className="mx-auto max-w-6xl px-6">
            <RiskIntegrationClient
              dataUrl="/data/risk_index_legacy_municipalities.geojson"
              metadataUrl="/data/risk_index_legacy_metadata.json"
              loadingLabel="Loading legacy municipal risk-index data..."
            />
          </div>
        </div>
      </main>
      <Footer />
    </>
  );
}

function ChevronSvg() {
  return (
    <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
    </svg>
  );
}
