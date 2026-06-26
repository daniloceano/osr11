import Link from 'next/link';
import Navigation from '@/components/Navigation';
import Footer from '@/components/Footer';
import StatusBadge from '@/components/StatusBadge';
import HazardCharacterizationClient from './HazardCharacterizationClient';

export const metadata = {
  title: 'Hazard Characterization — Step 3 | OSR11',
  description:
    'Full hazard characterization of coastal storm events along the Brazilian coast (1993–2025): compound detection, duration persistence, seasonality, trends, return levels, and wave–surge dependence.',
};

export default function HazardCharacterizationPage() {
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
              <span className="text-gray-600">Hazard Characterization</span>
            </div>

            <div className="flex flex-wrap items-start gap-2 mb-4">
              <StatusBadge status="done" />
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">
                Step 3 — Hazard Characterization
              </span>
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">
                Full Brazilian coast · 808 grid points · 1993–2025
              </span>
            </div>

            <h1 className="text-3xl font-bold text-gray-900 md:text-4xl">
              Coastal Hazard Characterization
              <br />
              <span className="text-blue-600">Compound · Duration · Seasonality · Trends · EVA · Dependence</span>
            </h1>
            <p className="mt-3 max-w-3xl text-sm text-gray-600">
              Complete statistical characterization of extreme ocean events along the Brazilian coast.
              Each grid point carries 87 metrics derived from the storm catalogs produced in Step 3.1:
              compound event detection, storm duration and persistence, monthly seasonality,
              decadal trends (Mann–Kendall + Sen slope), univariate extreme value analysis (GPD return levels),
              and wave–surge dependence structure (Kendall τ, Spearman ρ, extremal χ/χ̄).
            </p>
          </div>
        </div>

        {/* ── Analysis modules overview ──────────────────────────────── */}
        <div className="border-b border-gray-200 bg-gray-50 py-10">
          <div className="mx-auto max-w-6xl px-6">
            <h2 className="mb-4 text-lg font-bold text-gray-900">Analysis Modules</h2>
            <div className="grid gap-3 md:grid-cols-3 lg:grid-cols-6">
              <ModuleCard color="#756bb1" title="3.2 Compound" body="Temporal overlap between Hₛ and SSH_total storms. Normalized intensity, overlap duration, peak lag." />
              <ModuleCard color="#2171b5" title="3.3 Duration" body="Storm episode duration statistics: mean, median, P95. Inter-event times and persistence." />
              <ModuleCard color="#238b45" title="3.4 Seasonality" body="Monthly/seasonal storm frequency. Peak month for Hₛ, SSH, and compound events." />
              <ModuleCard color="#d94801" title="3.5 Trends" body="Mann–Kendall + Sen slope for annual storm counts, peak intensity, and mean duration (1993–2025)." />
              <ModuleCard color="#cb181d" title="3.6 EVA" body="GPD-based return levels: 2, 5, 10, 20, 50-yr for Hₛ and SSH_total peaks-over-threshold." />
              <ModuleCard color="#6a51a3" title="3.7 Dependence" body="Wave–surge correlation: Kendall τ, Spearman ρ, extremal dependence coefficients χ and χ̄." />
            </div>
          </div>
        </div>

        {/* ── Interactive map (client component) ──────────────────────── */}
        <div className="py-10">
          <div className="mx-auto max-w-6xl px-6">
            <HazardCharacterizationClient />
          </div>
        </div>

        {/* ── Methodology notes ──────────────────────────────────────── */}
        <div className="border-t border-gray-200 bg-gray-50 py-10">
          <div className="mx-auto max-w-6xl px-6">
            <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2">
              <h2 className="text-lg font-bold text-gray-900">Methodology Notes</h2>
              <Link
                href="/methodology/compound-detection"
                className="inline-flex items-center gap-1 text-sm font-semibold text-blue-600 hover:underline"
              >
                Read the full Step 3 methodology
                <ChevronSvg />
              </Link>
            </div>
            <p className="mb-6 max-w-3xl text-xs leading-relaxed text-gray-500">
              A condensed summary follows; the linked page gives the full pipeline in order — storm catalogs,
              compound detection, the characterization suite, and the hand-off to the municipal risk index —
              with formulas and assumptions.
            </p>
            <div className="grid gap-6 md:grid-cols-2">
              <div className="space-y-3 text-xs text-gray-600 leading-relaxed">
                <p>
                  <strong className="text-gray-800">Storm catalogs.</strong>{' '}
                  Base catalogs produced in Step 3.1 using peaks-over-threshold with q90 for both Hₛ (WAVERYS)
                  and SSH_total (GLORYS zos + FES2022 daily-max tide). Consecutive exceedance days are merged
                  into episodes (gap ≤ 1 day). 808 coastal grid points, 1993–2025.
                </p>
                <p>
                  <strong className="text-gray-800">Compound detection.</strong>{' '}
                  A compound event is identified when an Hₛ episode and an SSH_total episode overlap by ≥ 1 calendar day.
                  Normalized intensity = 0.5 × (Hₛ_norm + SSH_norm), scaled via domain-wide Q05/Q95.
                </p>
                <p>
                  <strong className="text-gray-800">Trend testing.</strong>{' '}
                  Mann–Kendall test for monotonic trend significance (α = 0.05).
                  Sen slope estimator for robust magnitudes.
                  Applied to 8 annual series: storm counts (Hₛ, SSH_total, compound), mean peak
                  (Hₛ, SSH_total), mean storm duration (Hₛ, SSH_total), and mean compound overlap duration.
                </p>
              </div>
              <div className="space-y-3 text-xs text-gray-600 leading-relaxed">
                <p>
                  <strong className="text-gray-800">Extreme value analysis.</strong>{' '}
                  Generalized Pareto Distribution (GPD) fitted to storm peak exceedances above the q90 threshold.
                  Return levels estimated for 2, 5, 10, 20, and 50-year return periods.
                  Grid points with &lt; 10 exceedances are excluded.
                </p>
                <p>
                  <strong className="text-gray-800">Dependence structure.</strong>{' '}
                  Kendall&apos;s τ and Spearman&apos;s ρ measure rank correlation between Hₛ and SSH_total peaks in compound events.
                  Extremal dependence coefficients χ (asymptotic) and χ̄ (sub-asymptotic) quantify joint tail behavior;
                  χ̄ is most informative when χ ≈ 0, indicating the strength of residual tail association under asymptotic independence
                  (Ledford &amp; Tawn, 1996). With only ~12–16 effective pairs above the u = 0.95 tail threshold per grid point,
                  χ/χ̄ here are <strong>screening diagnostics, not definitive tail-dependence classifications</strong>.
                </p>
                <p>
                  <strong className="text-gray-800">Limitations.</strong>{' '}
                  Daily temporal resolution means sub-daily co-occurrence cannot be resolved.
                  SSH_total combines GLORYS zos sampled at 00:00 UTC with the daily-maximum FES2022 tide — these do not
                  share the same timestamp, so SSH_total overestimates the true instantaneous total sea level.
                  The q90/q90 detection thresholds were calibrated against reported Santa Catarina events and applied
                  coast-wide; their optimality outside SC is untested.
                  GPD parameter estimation may be unreliable for grid points with few exceedances.
                  Trend significance over 33 years is limited for low-frequency events.
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

function ModuleCard({ color, title, body }: { color: string; title: string; body: string }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-3">
      <div className="mb-1.5 flex items-center gap-2">
        <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} />
        <h3 className="text-xs font-bold text-gray-900">{title}</h3>
      </div>
      <p className="text-[10px] text-gray-500 leading-relaxed">{body}</p>
    </div>
  );
}
