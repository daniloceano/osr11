import Image from 'next/image';
import Link from 'next/link';
import Navigation from '@/components/Navigation';
import Footer from '@/components/Footer';
import StatusBadge from '@/components/StatusBadge';
import TsEventSelector from '@/components/TsEventSelector';

export const metadata = {
  title: 'Tidal Sensitivity Analysis — OSR11',
  description:
    'Sensitivity test extending the preliminary compound event occurrence analysis by adding FES2022 astronomical tide to GLORYS12 SSH. Comparison of compound event detection with SSH-only vs SSH + tide (SSH_total). Full SC coast, 91 events.',
};

export default function TidalSensitivityPage() {
  return (
    <>
      <Navigation />
      <main className="pt-16">

        {/* ── Page header ──────────────────────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-white py-16">
          <div className="mx-auto max-w-5xl px-6">
            <div className="mb-4 flex items-center gap-2 text-xs text-gray-500">
              <Link href="/" className="hover:text-gray-700 transition-colors">Overview</Link>
              <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              <span>Results</span>
              <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              <span className="text-gray-600">Tidal Sensitivity Analysis</span>
            </div>

            <div className="flex flex-wrap items-start gap-2 mb-4">
              <StatusBadge status="done" />
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">Step 2b</span>
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">Full SC coast · 5 sectors · 91 events</span>
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">FES2022 · eo-tides</span>
            </div>

            <h1 className="text-3xl font-bold text-gray-900 md:text-4xl">
              Tidal Sensitivity Analysis
              <br />
              <span className="text-blue-600">SSH vs SSH + FES2022 Astronomical Tide</span>
            </h1>
            <p className="mt-3 max-w-2xl text-sm text-gray-600">
              Extension of the preliminary compound event occurrence analysis: the FES2022
              astronomical tide (via eo-tides) is added to the GLORYS12/WAVERYS SSH signal
              to form a total sea level (SSH_total = SSH + tide). Compound event detection
              is then compared between SSH-only and SSH_total for all 91 reported SC coastal
              disasters, revealing whether the tidal signal changes the number or distribution
              of concurrent Hₛ and SSH exceedances.
            </p>

            <div className="mt-6 flex flex-wrap gap-3">
              {[
                { label: 'Tide model',   value: 'FES2022 · eo-tides v0.10' },
                { label: 'Tide files',   value: 'data/tide_models_clipped_brasil' },
                { label: 'Total level',  value: 'SSH_total = zos + FES2022' },
                { label: 'Threshold',    value: 'q90 · full annual series (per variable)' },
                { label: 'Resolution',   value: 'Daily (midnight UTC)' },
                { label: 'Events',       value: '91 events · 22 municipalities' },
              ].map((m) => (
                <div key={m.label} className="rounded-lg border border-gray-300/60 bg-gray-50 px-3 py-2">
                  <div className="text-xs text-gray-500">{m.label}</div>
                  <div className="text-xs font-medium text-gray-800">{m.value}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── What this analysis is about ───────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-gray-50 py-14">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-4 text-xl font-bold text-gray-900">What this analysis is about</h2>
            <div className="grid gap-6 md:grid-cols-2">
              <p className="text-sm text-gray-700 leading-relaxed">
                The GLORYS12 SSH variable (<code className="text-xs bg-gray-200 px-1 rounded">zos</code>)
                represents sea surface height above the geoid — it captures the storm surge and
                sub-tidal sea-level signal but does <strong>not</strong> include the astronomical
                tide (which is filtered out by GLORYS12&apos;s tidal-free assimilation). For
                coastal flooding, however, the total sea level — including the tide — is what
                matters for overtopping and inundation.
                <br /><br />
                This sensitivity test asks: if we add the FES2022 tidal prediction back onto the
                GLORYS12 SSH, does the compound event detection rate change? Specifically, are more
                reported SC coastal disasters identified as compound events (concurrent Hₛ and SSH_total
                exceedances at q90) when the tidal contribution is included?
              </p>
              <p className="text-sm text-gray-700 leading-relaxed">
                The key caveat is <strong>temporal resolution</strong>. Both the unified dataset
                and the tidal prediction are evaluated daily (24-hour mean / midnight UTC). At
                daily resolution, the tidal oscillation (~12.4 h for semi-diurnal tides) is
                averaged out: the mean daily tide is close to zero, and the tidal range visible in
                the daily signal reflects only the residual between the day&apos;s tidal cycle.
                <br /><br />
                As a result, this test captures whether the <em>daily-mean</em> tidal level during
                the event window shifts the total sea level meaningfully — but it does not resolve
                sub-daily tidal peaks that may coincide with extreme wave arrival. A full tidal
                sensitivity test would require hourly data and a different workflow.
              </p>
            </div>
          </div>
        </div>

        {/* ── Key findings ─────────────────────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-white py-14">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-6 text-xl font-bold text-gray-900">Key Findings</h2>
            <div className="grid gap-5 md:grid-cols-2">
              {[
                {
                  icon: '📊',
                  title: '30 → 13 concurrent events at q90',
                  text: 'The SSH-only analysis detects 30 of 91 events as having at least one day of concurrent Hₛ and SSH exceedance at q90. When FES2022 tide is added, the count drops to 13. No new detections are gained — the tide strictly reduces the concurrent count.',
                },
                {
                  icon: '📉',
                  title: 'Adding tide reduces rather than increases detections',
                  text: 'At daily resolution, adding the FES2022 tide raises the q90 threshold for SSH_total (because the tidal distribution has higher variance). For most events, the threshold increase more than offsets any elevation from the tide itself. When the tide is at a trough during the event window, SSH_total can even be lower than SSH, causing additional detection losses.',
                },
                {
                  icon: '🌊',
                  title: '17 events lose detection — 0 gain it',
                  text: 'Of the 30 SSH-only detections: 13 are maintained, 17 are lost. No event that was not detected with SSH alone becomes newly detected with SSH_total. The sensitivity is asymmetric: the tidal contribution at daily resolution primarily weakens the relative anomaly of the sea-level signal during events.',
                },
                {
                  icon: '⏱️',
                  title: 'Daily resolution is the critical limitation',
                  text: 'Astronomical tides in SC have a typical range of ~0.4–0.8 m and period ~12.4 h. At daily resolution (midnight UTC mean), the tidal oscillation is averaged out and the residual daily tidal signal is small. The real compound hazard requires hourly resolution to capture tidal peaks aligning with surge/wave extremes.',
                },
              ].map((f) => (
                <div key={f.title} className="rounded-xl border border-gray-200 p-5">
                  <div className="flex items-start gap-3">
                    <span className="text-2xl">{f.icon}</span>
                    <div>
                      <h3 className="text-sm font-semibold text-gray-900 mb-1.5">{f.title}</h3>
                      <p className="text-xs text-gray-600 leading-relaxed">{f.text}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Detection summary table */}
            <div className="mt-6 overflow-x-auto rounded-xl border border-gray-200 bg-gray-50">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-100">
                    <th className="px-4 py-3 text-left font-semibold text-gray-700">Category</th>
                    <th className="px-4 py-3 text-center font-semibold text-gray-700">Events</th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-700">Description</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { cat: 'Maintained',     n: '13', color: 'text-blue-700',   desc: 'Concurrent at q90 in both SSH-only and SSH_total' },
                    { cat: 'Lost with tide', n: '17', color: 'text-red-700',    desc: 'Concurrent with SSH alone but NOT with SSH_total' },
                    { cat: 'New with tide',  n: '0',  color: 'text-green-700',  desc: 'Only concurrent when tide is added (none)' },
                    { cat: 'Neither',        n: '61', color: 'text-gray-600',   desc: 'No concurrent exceedance in either analysis' },
                  ].map((r, i) => (
                    <tr key={r.cat} className={`border-b border-gray-100 ${i % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}`}>
                      <td className={`px-4 py-2.5 font-medium ${r.color}`}>{r.cat}</td>
                      <td className="px-4 py-2.5 text-center font-bold text-gray-800">{r.n}</td>
                      <td className="px-4 py-2.5 text-gray-600">{r.desc}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* ── Per-event figures ──────────────────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-gray-50 py-14">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-2 text-xl font-bold text-gray-900">Individual Event Figures</h2>
            <p className="mb-6 text-sm text-gray-600 max-w-2xl">
              Each figure shows three stacked panels: (a) Hₛ, (b) SSH (zos only), (c) SSH + FES2022
              tide. Panels (b) and (c) use their respective q90 thresholds; the dashed green line in
              panel (c) shows the tidal component alone. The title bar colour indicates the detection
              outcome: blue = concurrent in both, red = detection lost with tide, grey = not detected.
              Filter by sector or detection-change category using the controls below.
            </p>
            <TsEventSelector />
          </div>
        </div>

        {/* ── Figure C1: detection comparison ──────────────────────────────── */}
        <div className="border-b border-gray-200 bg-white py-14">
          <div className="mx-auto max-w-5xl px-6">
            <div className="flex flex-wrap items-center gap-3 mb-2">
              <span className="rounded-full bg-gray-100 border border-gray-300 px-2.5 py-1 text-xs font-semibold text-gray-700">
                Figure TS-C1
              </span>
              <h2 className="text-xl font-bold text-gray-900">Detection Comparison</h2>
            </div>
            <p className="mb-6 text-sm text-gray-600 max-w-2xl">
              Grouped bar chart showing the concurrent exceedance fraction for each event using SSH-only
              (blue) and SSH_total (purple). Bars coloured green mark events where tide adds a new
              detection; red bars mark events where detection is lost when tide is included.
            </p>
            <div className="rounded-xl border border-gray-200 bg-white overflow-hidden shadow-sm">
              <div className="p-5">
                <Image
                  src="/figures/ts_summary/fig_TS_C1_detection_comparison.png"
                  alt="Figure TS-C1 — Detection Comparison"
                  width={1200}
                  height={500}
                  className="w-full h-auto rounded-lg"
                  unoptimized
                />
              </div>
              <div className="border-t border-gray-100 px-5 py-4">
                <p className="text-xs text-gray-500 leading-relaxed italic">
                  Concurrent exceedance fraction (days with both Hₛ &gt; q90 and SSH(total) &gt; q90 ÷ window length)
                  for SSH-only (blue) and SSH + tide (purple), per event. Events are sorted by coastal sector then municipality.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* ── Figure C2: scatter ────────────────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-gray-50 py-14">
          <div className="mx-auto max-w-5xl px-6">
            <div className="flex flex-wrap items-center gap-3 mb-2">
              <span className="rounded-full bg-gray-100 border border-gray-300 px-2.5 py-1 text-xs font-semibold text-gray-700">
                Figure TS-C2
              </span>
              <h2 className="text-xl font-bold text-gray-900">Normalised Maxima: SSH vs SSH_total</h2>
            </div>
            <p className="mb-6 text-sm text-gray-600 max-w-2xl">
              Scatter of SSH-only normalised maximum (x) vs SSH_total normalised maximum (y) for all
              events with valid data. Points above the 1:1 diagonal had a larger normalised peak with
              the tide included; points below had a smaller one. Colour indicates the detection-change
              category.
            </p>
            <div className="rounded-xl border border-gray-200 bg-white overflow-hidden shadow-sm">
              <div className="p-5">
                <Image
                  src="/figures/ts_summary/fig_TS_C2_scatter_ssh_vs_total.png"
                  alt="Figure TS-C2 — SSH vs SSH_total scatter"
                  width={900}
                  height={700}
                  className="w-full h-auto rounded-lg"
                  unoptimized
                />
              </div>
              <div className="border-t border-gray-100 px-5 py-4">
                <p className="text-xs text-gray-500 leading-relaxed italic">
                  SSH-only max/mean (x) vs SSH_total max/mean (y), coloured by detection-change category.
                  Dashed line is 1:1. Most points fall near the diagonal, confirming that the tidal
                  contribution at daily resolution is small relative to the storm surge anomaly.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* ── Figures C3, C4 side by side ───────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-white py-14">
          <div className="mx-auto max-w-5xl px-6">
            <div className="grid gap-8 md:grid-cols-2">

              <div>
                <div className="flex flex-wrap items-center gap-3 mb-2">
                  <span className="rounded-full bg-gray-100 border border-gray-300 px-2.5 py-1 text-xs font-semibold text-gray-700">
                    Figure TS-C3
                  </span>
                  <h2 className="text-base font-bold text-gray-900">Detection Change by Sector</h2>
                </div>
                <p className="mb-4 text-xs text-gray-600">
                  Event counts per detection-change category, broken down by coastal sector.
                  Reveals whether the tidal effect is geographically uniform or sector-dependent.
                </p>
                <div className="rounded-xl border border-gray-200 bg-white overflow-hidden shadow-sm">
                  <div className="p-4">
                    <Image
                      src="/figures/ts_summary/fig_TS_C3_detection_change_by_sector.png"
                      alt="Figure TS-C3 — Detection change by sector"
                      width={600}
                      height={500}
                      className="w-full h-auto rounded-lg"
                      unoptimized
                    />
                  </div>
                </div>
              </div>

              <div>
                <div className="flex flex-wrap items-center gap-3 mb-2">
                  <span className="rounded-full bg-gray-100 border border-gray-300 px-2.5 py-1 text-xs font-semibold text-gray-700">
                    Figure TS-C4
                  </span>
                  <h2 className="text-base font-bold text-gray-900">Tidal Fraction of SSH_total</h2>
                </div>
                <p className="mb-4 text-xs text-gray-600">
                  For each event, the fraction of SSH_total maximum attributable to the FES2022 tidal
                  component (|tide_max| ÷ SSH_total_max). A fraction &gt; 0.5 means the tide exceeds
                  50% of the total sea-level peak during the event window.
                </p>
                <div className="rounded-xl border border-gray-200 bg-white overflow-hidden shadow-sm">
                  <div className="p-4">
                    <Image
                      src="/figures/ts_summary/fig_TS_C4_tidal_fraction.png"
                      alt="Figure TS-C4 — Tidal fraction"
                      width={600}
                      height={600}
                      className="w-full h-auto rounded-lg"
                      unoptimized
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ── Limitations and next steps ────────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-gray-50 py-14">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-5 text-xl font-bold text-gray-900">Assumptions &amp; Limitations</h2>
            <ul className="space-y-2.5 mb-8">
              {[
                'Daily resolution is the main limitation. Astronomical tides in SC have a dominant semi-diurnal period (~12.4 h). A daily time step averages out most of the tidal oscillation. The residual daily-mean tidal signal is small, and the sensitivity test at this resolution underestimates the true role of astronomical tides in compound flooding.',
                'The q90 threshold is computed from the full SSH_total distribution. Adding the tide shifts both the events and the threshold upward, partly cancelling the effect. For a threshold-based detection framework, the relevant quantity is the tide anomaly relative to its own seasonal cycle — not the raw tidal height.',
                'FES2022 tides are evaluated at 00:00 UTC (midnight). SC reporting times in the Leal et al. (2024) database may not correspond to this time, which introduces timing uncertainty.',
                'No seasonal stratification. Tidal ranges and storm surge peaks have seasonality. Annual q90 thresholds treat all months equally.',
                'Grid resolution: the nearest ocean grid cell is used for both SSH and tidal computation. Coastal geometry (estuaries, bays) is unresolved.',
              ].map((lim, i) => (
                <li key={i} className="flex gap-2.5 text-sm text-gray-600">
                  <span className="text-orange-500 font-bold flex-shrink-0 mt-0.5">!</span>
                  <span>{lim}</span>
                </li>
              ))}
            </ul>

            <div className="rounded-lg border border-gray-200 bg-white p-5">
              <h3 className="text-sm font-semibold text-gray-900 mb-3">What this tells us for the next steps</h3>
              <ul className="space-y-1.5">
                {[
                  'For the formal threshold calibration (CSI grid scan), use SSH (zos) without the tidal correction — the daily-mean tidal signal adds noise at this resolution.',
                  'When the pipeline moves to hourly data (if available), repeat this sensitivity test at hourly resolution to capture tidal phasing with wave/surge peaks.',
                  'Consider de-meaning the tidal signal (removing the daily mean) before adding to SSH, to isolate the sub-tidal tidal contribution at daily resolution.',
                  'The FES2022 model and eo-tides infrastructure are validated and ready for use with hourly data in future pipeline steps.',
                ].map((s, i) => (
                  <li key={i} className="flex gap-2 text-xs text-gray-600">
                    <span className="text-blue-600 font-bold flex-shrink-0">→</span>
                    <span>{s}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* ── Navigation ────────────────────────────────────────────────────── */}
        <div className="bg-white py-12">
          <div className="mx-auto max-w-5xl px-6 flex items-center justify-between">
            <Link
              href="/results/preliminary-compound"
              className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Preliminary Compound Analysis
            </Link>
            <Link
              href="/results"
              className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-800 transition-colors font-medium"
            >
              All Results
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          </div>
        </div>

      </main>
      <Footer />
    </>
  );
}
