import Link from 'next/link';
import Navigation from '@/components/Navigation';
import Footer from '@/components/Footer';
import StatusBadge from '@/components/StatusBadge';
import RiskIntegrationClient from './RiskIntegrationClient';

export const metadata = {
  title: 'Exposure, Vulnerability & Risk Integration | OSR11',
  description:
    'Municipal-scale coastal risk indices combining compound-event hazard metrics and social vulnerability for Brazilian coastal municipalities.',
};

export default function RiskIntegrationPage() {
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
              <span className="text-gray-600">Risk Integration</span>
            </div>

            <div className="mb-4 flex flex-wrap items-start gap-2">
              <StatusBadge status="done" />
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">
                Exposure, Vulnerability & Risk Integration
              </span>
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">
                Municipal scale · Karine risk-index outputs
              </span>
            </div>

            <h1 className="text-3xl font-bold text-gray-900 md:text-4xl">
              Exposure, Vulnerability & Risk Integration
              <br />
              <span className="text-blue-600">Municipal Coastal Risk Indices</span>
            </h1>
            <p className="mt-3 max-w-3xl text-sm text-gray-600">
              Municipal-scale coastal risk indices combining compound-event hazard metrics and social vulnerability.
              The panel maps SVI_Coast_2022, Hazard_Index, Risk_Comp, and Risk_Hazard where those fields are
              populated in Karine&apos;s shapefile outputs.
            </p>
          </div>
        </div>

        <div className="border-b border-gray-200 bg-gray-50 py-10">
          <div className="mx-auto max-w-6xl px-6">
            <h2 className="mb-4 text-lg font-bold text-gray-900">Integration Layers</h2>
            <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
              <ModuleCard
                color="#756bb1"
                title="SVI_Coast_2022"
                body="IBGE/SIDRA 2022 social vulnerability index, PCA/PC1 based and normalized from 0 to 100."
              />
              <ModuleCard
                color="#2171b5"
                title="Hazard_Index"
                body="Compound-event hazard index from normalized frequency, overlap duration, and intensity metrics."
              />
              <ModuleCard
                color="#d94801"
                title="Risk_Comp"
                body="Risk based on social vulnerability and normalized compound-event frequency."
              />
              <ModuleCard
                color="#cb181d"
                title="Risk_Hazard"
                body="Integrated coastal risk from social vulnerability and the compound-event hazard index."
              />
            </div>
          </div>
        </div>

        <div className="py-10">
          <div className="mx-auto max-w-6xl px-6">
            <RiskIntegrationClient />
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

function ModuleCard({ color, title, body }: { color: string; title: string; body: string }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-3">
      <div className="mb-1.5 flex items-center gap-2">
        <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} />
        <h3 className="text-xs font-bold text-gray-900">{title}</h3>
      </div>
      <p className="text-[10px] leading-relaxed text-gray-500">{body}</p>
    </div>
  );
}
