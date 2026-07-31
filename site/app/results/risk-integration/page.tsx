import Link from 'next/link';
import Navigation from '@/components/Navigation';
import Footer from '@/components/Footer';
import StatusBadge from '@/components/StatusBadge';
import RiskIntegrationClient from './RiskIntegrationClient';

export const metadata = {
  title: 'Multimetric Coastal Risk Integration | OSR11',
  description:
    'Municipal-scale coastal risk indices using a normalized frequency-duration-intensity hazard layer and social vulnerability for Brazilian coastal municipalities.',
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
                Multimetric hazard scope
              </span>
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">
                Municipal scale · fixed-anchor components
              </span>
            </div>

            <h1 className="text-3xl font-bold text-gray-900 md:text-4xl">
              Exposure, Vulnerability & Risk Integration
              <br />
              <span className="text-blue-600">Multimetric Coastal Risk</span>
            </h1>
            <p className="mt-3 max-w-3xl text-sm text-gray-600">
              Municipal-scale coastal risk from its three IPCC components: the native-grid
              Hazard_Index (equal-weight compound-event frequency and mean integrated severity),
              weighted effective population from the cumulative 1, 2, 5 and 10 km bands, and
              vulnerability transformed as Φ(PC1/sd). They are combined by <strong>geometric mean</strong>, which
              is conjunctive — risk requires a hazard, people exposed to it, and a susceptibility.
              The four population bands and pop_eff are available as separate exposure layers,
              alongside the fixed-anchor index components. No sample-dependent Min–Max is applied.
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
                body="Original SVI retained for audit; integration uses the monotonic Φ(PC1/sd) vulnerability scale."
              />
              <ModuleCard
                color="#2171b5"
                title="Hazard_Index"
                body="Equal-weight combination of frequency and integrated severity using fixed anchors of 99 events and 1.0."
              />
              <ModuleCard
                color="#31a354"
                title="Exposure_Index"
                body="Weighted combination of cumulative populations ≤1, ≤2, ≤5 and ≤10 km. Each band and pop_eff can be mapped separately."
              />
              <ModuleCard
                color="#d94801"
                title="Risk_Hazard"
                body="Geometric mean of hazard, exposure and vulnerability, without floor or final Min–Max."
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
            <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2">
              <h2 className="text-lg font-bold text-gray-900">Methodology &amp; Caveats</h2>
              <Link
                href="/methodology/hazard-index"
                className="inline-flex items-center gap-1 text-sm font-semibold text-blue-600 hover:underline"
              >
                Full Hazard Index methodology
                <ChevronSvg />
              </Link>
            </div>
            <div className="grid gap-6 md:grid-cols-2">
              <div className="space-y-3 text-xs text-gray-600 leading-relaxed">
                <p>
                  <strong className="text-gray-800">Current index definitions.</strong>{' '}
                  Hazard_Index = [min(count/99,1) + min(severity/1,1)]/2; Exposure_Index uses
                  pop_eff = 0.4·pop_1km + 0.3·pop_2km + 0.2·pop_5km + 0.1·pop_10km; and
                  Risk_Hazard = (Hazard_Index_mun · Exposure_Index · Φ(PC1/sd(PC1)))^(1/3).
                  There is no floor, municipal hazard Min–Max, or final risk Min–Max.
                </p>
                <p>
                  <strong className="text-gray-800">Component aggregation.</strong>{' '}
                  Inside the hazard, frequency and mean integrated severity receive equal weights
                  and combine arithmetically; the two are positively correlated (Spearman +0.60), so
                  that layer reinforces rather than cancels, though it remains compensatory. Across the three risk
                  components the aggregation is <em>geometric</em> and therefore not compensatory:
                  a municipality with almost nobody within 10 km of the coast cannot reach a high
                  risk on vulnerability alone.
                </p>
              </div>
              <div className="space-y-3 text-xs text-gray-600 leading-relaxed">
                <p>
                  <strong className="text-gray-800">Hazard provenance.</strong>{' '}
                  Each municipality takes the values of the single oceanic grid point with the highest
                  compound_c in its association, and receives the Hazard Index <em>already normalized
                  on the 808-point native grid</em> — it is not renormalized after the transfer, so the
                  municipal values are directly comparable with the{' '}
                  <Link href="/results/hazard-characterization" className="font-semibold text-blue-600 hover:underline">
                    coastal hazard map
                  </Link>
                  . Municipalities without populated hazard fields are shown only for SVI and excluded
                  from the hazard/risk layers.
                </p>
                <p>
                  <strong className="text-gray-800">Caveats.</strong>{' '}
                  Underlying Step 3 caveats still apply: daily resolution (sub-daily co-occurrence
                  unresolved); the still water level mixes zos at 00:00 UTC with the daily-maximum
                  tide, so it does not share a timestamp; the q70/q99 thresholds were calibrated on
                  Santa Catarina events and applied coast-wide, and the wave percentile is the
                  poorly determined axis of that calibration — at q70 the local wave threshold falls
                  below 1.5 m at 256 of the 808 points (AUD-02, open and aggravated). Exposure is a proximity criterion — no water level is propagated
                  over land anywhere in this workflow, so it counts residents near the coast and
                  never residents affected — and it uses de jure residents on a single census date
                  against 33 years of metocean record. The export carries a single product, so
                  every value on this page comes from the current method.
                  Results are preliminary — do not cite without consulting the authors.
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
