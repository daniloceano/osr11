import Link from 'next/link';
import Navigation from '@/components/Navigation';
import Footer from '@/components/Footer';
import StatusBadge from '@/components/StatusBadge';
import RiskIntegrationClient from './RiskIntegrationClient';

export const metadata = {
  title: 'Compound-Count Coastal Risk Integration | OSR11',
  description:
    'Municipal-scale coastal risk indices using compound-event counts as the hazard layer and social vulnerability for Brazilian coastal municipalities.',
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
                Compound-count hazard scope
              </span>
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">
                Municipal scale · legacy product retained
              </span>
            </div>

            <h1 className="text-3xl font-bold text-gray-900 md:text-4xl">
              Exposure, Vulnerability & Risk Integration
              <br />
              <span className="text-blue-600">Compound-Count Coastal Risk</span>
            </h1>
            <p className="mt-3 max-w-3xl text-sm text-gray-600">
              Municipal-scale coastal risk indices combining social vulnerability with a revised hazard layer:
              only the total compound-event count (<code className="rounded bg-gray-100 px-1 text-xs">compound_c</code>)
              is used in the current Hazard_Index. Duration and intensity metrics remain available as diagnostics
              and in the{' '}
              <Link href="/results/risk-integration/legacy" className="font-semibold text-blue-600 hover:underline">
                legacy multi-metric product
              </Link>
              .
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
                body="Current hazard layer: Min-Max normalized compound-event count, norm(compound_c)."
              />
              <ModuleCard
                color="#d94801"
                title="Risk_Hazard"
                body="Current final risk: social vulnerability multiplied by the compound-count hazard layer."
              />
              <ModuleCard
                color="#737373"
                title="Legacy product"
                body="Previous frequency-duration-intensity hazard retained for audit, comparison, and reproducibility."
              />
            </div>
          </div>
        </div>

        <div className="py-10">
          <div className="mx-auto max-w-6xl px-6">
            <RiskIntegrationClient />
          </div>
        </div>

        <div className="border-t border-gray-200 bg-gray-50 py-10">
          <div className="mx-auto max-w-6xl px-6">
            <h2 className="mb-4 text-lg font-bold text-gray-900">Methodology &amp; Caveats</h2>
            <div className="grid gap-6 md:grid-cols-2">
              <div className="space-y-3 text-xs text-gray-600 leading-relaxed">
                <p>
                  <strong className="text-gray-800">Current index definitions.</strong>{' '}
                  Hazard_Index = norm(compound_c); Risk_Hazard = (SVI_Coast_2022 / 100)·Hazard_Index,
                  where norm(·) is Min–Max scaling across municipalities. <strong>compound_c is the
                  absolute compound-event count over 1993–2025, not an annual rate.</strong> Risk_Comp is
                  retained as a compatibility alias for the same frequency-only risk calculation.
                </p>
                <p>
                  <strong className="text-gray-800">Scope change.</strong>{' '}
                  The earlier Hazard_Index averaged normalized frequency, mean overlap duration, and mean
                  compound intensity. That product is now legacy because duration/intensity can express
                  uncertain or river-mouth-driven signals, especially near large estuaries such as the
                  Amazon, and should not be interpreted as direct coastal hazard intensity without further
                  treatment.
                </p>
              </div>
              <div className="space-y-3 text-xs text-gray-600 leading-relaxed">
                <p>
                  <strong className="text-gray-800">Hazard provenance.</strong>{' '}
                  Each municipality takes the values of the single oceanic grid point with the highest
                  compound_c in its association. Municipalities without populated hazard fields are
                  shown only for SVI and excluded from the hazard/risk layers.
                </p>
                <p>
                  <strong className="text-gray-800">Legacy access and caveats.</strong>{' '}
                  The previous multi-metric output remains accessible at{' '}
                  <Link href="/results/risk-integration/legacy" className="font-semibold text-blue-600 hover:underline">
                    /results/risk-integration/legacy
                  </Link>
                  . Underlying Step 3 caveats still apply: daily resolution (sub-daily co-occurrence unresolved);
                  SSH_total mixes zos at 00:00 UTC with the daily-maximum tide (overestimates total
                  level); q90/q90 thresholds were calibrated on Santa Catarina events and applied
                  coast-wide. Results are preliminary — do not cite without consulting the authors.
                </p>
              </div>
            </div>
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
