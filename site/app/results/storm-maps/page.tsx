import Link from 'next/link';
import Navigation from '@/components/Navigation';
import Footer from '@/components/Footer';
import StatusBadge from '@/components/StatusBadge';
import StormMapsClient from './StormMapsClient';

export const metadata = {
  title: 'Storm Maps — Occurrence & Intensity | OSR11',
  description:
    'Spatial distribution of wave-only, surge-only, and compound storm events along the Brazilian coast (1993–2025). Interactive maps of storm frequency, mean intensity, and extreme percentiles at each coastal grid point.',
};

export default function StormMapsPage() {
  return (
    <>
      <Navigation />
      <main className="pt-16">
        {/* ── Header ─────────────────────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-white py-16">
          <div className="mx-auto max-w-6xl px-6">
            <div className="mb-4 flex items-center gap-2 text-xs text-gray-500">
              <Link href="/" className="hover:text-gray-700 transition-colors">Overview</Link>
              <ChevronSvg />
              <Link href="/results" className="hover:text-gray-700 transition-colors">Results</Link>
              <ChevronSvg />
              <span className="text-gray-600">Storm Maps</span>
            </div>

            <div className="flex flex-wrap items-start gap-2 mb-4">
              <StatusBadge status="done" />
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">
                Steps 3 + 4
              </span>
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">
                Full Brazilian coast · 808 grid points · 1993–2025
              </span>
            </div>

            <h1 className="text-3xl font-bold text-gray-900 md:text-4xl">
              Storm Occurrence & Intensity Maps
              <br />
              <span className="text-blue-600">Wave, Surge, and Compound Events</span>
            </h1>
            <p className="mt-3 max-w-3xl text-sm text-gray-600">
              Spatial distribution of extreme ocean events along the Brazilian coast,
              derived from 33 years of WAVERYS significant wave height (H<sub>s</sub>)
              and GLORYS12 total sea level (SSH_total = GLORYS zos + FES2022 daily-max tide).
              Events are classified as wave-only, surge-only, or compound based on
              temporal overlap at each 0.2° coastal grid point.
            </p>
          </div>
        </div>

        {/* ── Definitions panel ──────────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-gray-50 py-10">
          <div className="mx-auto max-w-6xl px-6">
            <h2 className="mb-4 text-lg font-bold text-gray-900">Event Classification</h2>
            <div className="grid gap-4 md:grid-cols-3">
              <DefinitionCard
                color="#3182bd"
                title="Hₛ only"
                body="Wave storm (Hₛ ≥ local q90) with no temporal overlap with any SSH_total storm at the same grid point."
              />
              <DefinitionCard
                color="#2ca25f"
                title="SSH_total only"
                body="Sea-level storm (SSH_total ≥ local q90) with no temporal overlap with any Hₛ storm at the same grid point."
              />
              <DefinitionCard
                color="#756bb1"
                title="Compound"
                body="Temporal overlap between an Hₛ storm and an SSH_total storm at the same grid point (shared ≥ 1 calendar day). Intensity is a normalized [0–1] score: 0.5 × (Hₛ_norm + SSH_norm), where each component is scaled via domain-wide Q05/Q95."
              />
            </div>
          </div>
        </div>

        {/* ── Map (client component) ─────────────────────────────────── */}
        <div className="py-10">
          <div className="mx-auto max-w-6xl px-6">
            <StormMapsClient />
          </div>
        </div>

        {/* ── Methodology notes ──────────────────────────────────────── */}
        <div className="border-t border-gray-200 bg-gray-50 py-10">
          <div className="mx-auto max-w-6xl px-6">
            <h2 className="mb-4 text-lg font-bold text-gray-900">Methodology Notes</h2>
            <div className="grid gap-6 md:grid-cols-2">
              <div className="space-y-3 text-xs text-gray-600 leading-relaxed">
                <p>
                  <strong className="text-gray-800">Threshold calibration.</strong>{' '}
                  Peaks-over-threshold with q90 (90th percentile) for both Hₛ and SSH_total,
                  independently calibrated at each coastal grid point over the full 1993–2025 record.
                  The q90/q90 pair was selected via the PU composite calibration (Step 2e),
                  confirmed by CSI diagnostic scan (Step 2d).
                </p>
                <p>
                  <strong className="text-gray-800">Storm clustering.</strong>{' '}
                  Consecutive exceedance days are merged into a single storm episode.
                  A gap of ≤ 1 day between exceedances is bridged (episode_max_gap_days = 1).
                </p>
                <p>
                  <strong className="text-gray-800">Compound detection.</strong>{' '}
                  Temporal overlap between Hₛ and SSH_total storms at the same grid point.
                  If multiple storms from either catalog overlap, they are grouped into a single compound event.
                </p>
              </div>
              <div className="space-y-3 text-xs text-gray-600 leading-relaxed">
                <p>
                  <strong className="text-gray-800">Grid coverage.</strong>{' '}
                  808 coastal grid points (WAVERYS 0.2° grid) within 50 km of the Natural Earth 10m coastline.
                  176 additional grid points were excluded due to insufficient data coverage (&lt;80% valid days).
                </p>
                <p>
                  <strong className="text-gray-800">Intensity definitions.</strong>{' '}
                  For Hₛ-only storms, intensity = peak daily Hₛ during the episode.
                  For SSH_total-only storms, intensity = peak daily SSH_total.
                  For compound events, intensity is a normalized dimensionless score [0–1]:
                  each component (peak Hₛ, peak SSH_total) is scaled to [0, 1] using domain-wide
                  5th and 95th percentiles of all compound event peaks, then averaged with equal
                  weight (0.5 × Hₛ_norm + 0.5 × SSH_norm). This ensures comparability across
                  grid points regardless of differences in baseline wave height or tidal regime.
                </p>
                <p>
                  <strong className="text-gray-800">Limitations.</strong>{' '}
                  Daily temporal resolution means sub-daily co-occurrence is not resolved.
                  Nearshore wave transformation (shoaling, refraction) is not represented in the 0.2° WAVERYS grid.
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

/* ── Tiny helpers ─────────────────────────────────────────────────────── */

function ChevronSvg() {
  return (
    <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
    </svg>
  );
}

function DefinitionCard({ color, title, body }: { color: string; title: string; body: string }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <div className="mb-2 flex items-center gap-2">
        <span className="inline-block h-3 w-3 rounded-full" style={{ backgroundColor: color }} />
        <h3 className="text-sm font-bold text-gray-900">{title}</h3>
      </div>
      <p className="text-xs text-gray-600 leading-relaxed">{body}</p>
    </div>
  );
}
