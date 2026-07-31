import Link from 'next/link';
import Navigation from '@/components/Navigation';
import Footer from '@/components/Footer';
import StatusBadge from '@/components/StatusBadge';
import CoastalHazardClient, { CoastalMetricExplorerClient } from './CoastalHazardClient';

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
              The headline product is the composite <strong>Hazard Index</strong>, built from
              <strong> two</strong> equally weighted components — compound-event frequency and mean
              integrated severity — on the 808-point native ocean grid and displayed directly on the
              coastline. The former third component, mean overlap duration, was retired from the
              index on 2026-07-29 and is published as a diagnostic only. Behind it, each
              grid point carries metrics derived from the storm catalogs produced in Step 3.1:
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
              <ModuleCard color="#756bb1" title="3.2 Compound" body="Temporal overlap between Hₛ and tide-free zos episodes, gated by max(SWL) > HAT. Integrated severity over the HAT datum." />
              <ModuleCard color="#2171b5" title="3.3 Duration" body="Storm episode duration statistics: mean, median, P95. Inter-event times and persistence." />
              <ModuleCard color="#238b45" title="3.4 Seasonality" body="Monthly/seasonal storm frequency. Peak month for Hₛ, SSH, and compound events." />
              <ModuleCard color="#d94801" title="3.5 Trends" body="Mann–Kendall + Sen slope for annual storm counts, peak intensity, and mean duration (1993–2025)." />
              <ModuleCard color="#cb181d" title="3.6 EVA" body="GPD-based return levels: 2, 5, 10, 20, 50-yr for Hₛ and SSH_total peaks-over-threshold." />
              <ModuleCard color="#6a51a3" title="3.7 Dependence" body="Wave–surge correlation: Kendall τ, Spearman ρ, extremal dependence coefficients χ and χ̄." />
            </div>
          </div>
        </div>

        {/* ── Coastal Hazard Index map (primary result) ───────────────── */}
        <div className="py-10">
          <div className="mx-auto max-w-6xl px-6">
            <div className="mb-6 flex flex-wrap items-baseline justify-between gap-2">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-blue-600">
                  Main result
                </p>
                <h2 className="text-xl font-bold text-gray-900">
                  Compound-event characteristics and Hazard Index along the coast
                </h2>
              </div>
              <Link
                href="/methodology/hazard-index"
                className="inline-flex items-center gap-1 text-sm font-semibold text-blue-600 hover:underline"
              >
                How the Hazard Index is built
                <ChevronSvg />
              </Link>
            </div>
            <p className="mb-6 max-w-3xl text-xs leading-relaxed text-gray-500">
              The two index components are shown in their own catalog units — events yr⁻¹ and the
              dimensionless integrated severity — and the Hazard Index is the composite 0–1 layer
              built from them. The duration and peak-intensity panels are retired diagnostics,
              kept for comparison but carrying no weight in the index. The values are calculated on the 808 native
              ocean grid points and drawn on the Natural Earth coastline; the coastal rendering
              does not recalculate the index. This is the same construction as figure{' '}
              <code className="rounded bg-gray-100 px-1 font-mono text-[11px]">
                coastal_hazard_index_components.png
              </code>{' '}
              in the article.
            </p>
            <CoastalHazardClient />
          </div>
        </div>

        {/* ── Per-grid-point diagnostics (supporting) ─────────────────── */}
        <div className="border-t border-gray-200 py-10">
          <div className="mx-auto max-w-6xl px-6">
            <p className="text-xs font-semibold uppercase tracking-wider text-gray-500">
              Supporting diagnostics
            </p>
            <h2 className="text-xl font-bold text-gray-900">
              Per-grid-point explorer — 87 characterization metrics
            </h2>
            <p className="mt-2 mb-6 max-w-3xl text-xs leading-relaxed text-gray-500">
              This secondary panel exposes the full Step 3 metric catalog: compound statistics,
              storm duration and persistence, seasonality, Mann–Kendall trends, GPD return levels,
              and wave–surge dependence. The metrics are calculated at the native ocean grid points
              and drawn on the coastline with exactly the same transposition and graphic style as
              the Hazard Index above. It is a diagnostic view of the underlying characterization,
              not the Hazard Index product itself.
            </p>
            <CoastalMetricExplorerClient />
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
              compound detection, the characterization suite, the composite Hazard Index, and the hand-off
              to the municipal risk index — with formulas and assumptions.
            </p>

            <div className="mb-6 rounded-xl border border-blue-200 bg-blue-50 p-5">
              <p className="text-xs font-semibold uppercase tracking-wider text-blue-700">
                How the maps on this page are drawn
              </p>
              <h3 className="mt-1 text-sm font-bold text-gray-900">
                From ocean grid points to the coastline
              </h3>
              <p className="mt-2 text-xs leading-relaxed text-gray-700">
                Every metric on this page — the Hazard Index and all 87 characterization metrics —
                is calculated <strong>at the 808 ocean grid points</strong>, never along the shore.
                Because results are easier to read on the coast than as a cloud of offshore dots,
                both maps apply the same three-step transposition:
              </p>
              <ol className="mt-2 list-decimal space-y-1 pl-5 text-xs leading-relaxed text-gray-700">
                <li>
                  take the Natural Earth 10-m coastline and keep only the stretch next to the
                  coastal municipalities;
                </li>
                <li>
                  cut that line into short pieces (at most 5 km) using a metric projection
                  (EPSG:5880);
                </li>
                <li>
                  paint each piece with the value of the <strong>nearest</strong> ocean grid point.
                </li>
              </ol>
              <p className="mt-2 text-xs leading-relaxed text-gray-700">
                Nothing is interpolated, smoothed, or recalculated in the process — the coastline is
                simply a more legible place to show the grid values. Hovering a stretch of coast
                reports the grid point behind it, its distance, and the nearest coastal
                municipality, which is the unit used later in the risk integration.
              </p>
            </div>

            <div className="grid gap-6 md:grid-cols-2">
              <div className="space-y-3 text-xs text-gray-600 leading-relaxed">
                <p>
                  <strong className="text-gray-800">Storm catalogs.</strong>{' '}
                  Base catalogs produced in Step 3.1 using peaks-over-threshold. <strong>These base
                  catalogs still carry the superseded q90/q90 pair on Hₛ and SSH_total and have not
                  been regenerated under the current method</strong>; the compound product in 3.2 is
                  computed independently from the unified dataset. Consecutive exceedance days are merged
                  into episodes (gap ≤ 1 day). 808 coastal grid points, 1993–2025.
                </p>
                <p>
                  <strong className="text-gray-800">Compound detection.</strong>{' '}
                  A compound event is identified when an Hₛ episode (local q70) and a tide-free
                  <em> zos</em> episode (local q99) overlap by ≥ 1 calendar day <strong>and</strong> the
                  still water level over those shared days exceeds the local HAT.
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
                  The still water level combines GLORYS zos sampled at 00:00 UTC with the daily-maximum FES2022 tide — these do not
                  share the same timestamp, so it overestimates the true instantaneous total sea level.
                  The q70/q99 detection thresholds were calibrated against reported Santa Catarina events and applied
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
