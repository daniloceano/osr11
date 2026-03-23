import Image from 'next/image';
import Link from 'next/link';
import Navigation from '@/components/Navigation';
import Footer from '@/components/Footer';
import StatusBadge from '@/components/StatusBadge';

export const metadata = {
  title: 'Threshold Calibration — OSR11',
  description:
    'Initial visual calibration of q90 thresholds for Hₛ and SSH against reported Santa Catarina coastal disaster events. Full SC coast domain. MagicA peaks-over-threshold, per-event time series analysis, and concomitance metrics.',
};

const figures = [
  {
    key: 'S1',
    filename: '/figures/fig_TC_S1_normalised_maxima_per_event.png',
    title: 'Normalised Maxima per Event (S1)',
    caption:
      'Grouped bar chart of within-window Hₛ and SSH maxima, each divided by their long-term climatological mean at the same grid point. Each group on the x-axis represents one reported event. A bar reaching 1.0 means the peak value equalled the climatological mean; a bar at 2.0 means the peak was double the mean. Grey bars indicate that data were not available at the nearest grid point (mostly northern SC municipalities where the ~0.2° reanalysis grid falls over land or in non-resolved bays). Note that SSH normalised maxima systematically exceed Hₛ maxima — this reflects the smaller mean and variance of SSH compared to Hₛ, rather than a true difference in hazard intensity.',
  },
  {
    key: 'S2',
    filename: '/figures/fig_TC_S2_scatter_normalised_hs_ssh.png',
    title: 'Normalised Hₛ vs SSH Scatter (S2)',
    caption:
      'Scatter of normalised Hₛ maximum vs normalised SSH maximum for all events with valid data at both variables. Each point is one reported event. Filled circles mark events where both variables simultaneously exceeded q90 at the same daily time step (concurrent exceedances). Open circles are events where the variables peaked at different times within the 7-day window. Only 2 out of 10 events with valid joint data show concurrent exceedances — both in Barra Velha (North sector). This low rate at q90 is expected: requiring both variables to simultaneously clear high annual thresholds is a strict criterion, and will be systematically relaxed in the threshold optimisation phase.',
  },
  {
    key: 'S3',
    filename: '/figures/fig_TC_S3_concomitance_fraction_per_event.png',
    title: 'Concomitance Fraction per Event (S3)',
    caption:
      'Horizontal bar chart showing, for each event, the fraction of days within the 7-day window in which both Hₛ and SSH simultaneously exceeded their q90 thresholds. Most events show zero fraction (no concurrent exceedances at q90), confirming that joint extreme exceedances are uncommon even during officially documented coastal disasters. The two events with non-zero concomitance (Barra Velha, 2001 and 2019) represent the clearest compound signals identified in this initial calibration pass.',
  },
  {
    key: 'S4',
    filename: '/figures/fig_TC_S4_heatmap_concomitance.png',
    title: 'Concomitance Heatmap (S4)',
    caption:
      'Heatmap of the concurrent-exceedance fraction for all municipality–event combinations. Rows are municipalities; columns are event dates. Colour intensity encodes the fraction of the 7-day window with concurrent Hₛ > q90 and SSH > q90. White cells indicate either zero concomitance or missing data. The heatmap shows that concurrent exceedances are spatially and temporally sparse at the q90 level. This does not mean compound events are absent — it means the q90 threshold is too strict for this exploratory calibration to reliably detect them. The next phase will scan a range of lower percentile thresholds to find the level that maximises consistency with reported disaster dates.',
  },
];

const keyFindings = [
  {
    icon: '📊',
    title: '91 events analysed across 22 municipalities',
    text: 'All five coastal sectors of the Leal et al. (2024) database are now included: North, Central-north, Central, Central-south, and South. Previously, the analysis covered only the South sector (7 municipalities). Expanding to full SC adds 15 municipalities and 82 additional event records.',
  },
  {
    icon: '⚠️',
    title: 'Grid coverage gaps in northern sectors',
    text: 'Of the 91 events, 47 have valid Hₛ data and only 10 have valid data for both Hₛ and SSH simultaneously. The gaps are concentrated in the North sector (44 events), where the nearest WAVERYS (~0.2°) and GLORYS12 (1/12°) ocean grid points frequently fall over land or in embayments that the reanalysis grid does not resolve. This is a known limitation of applying coarse-resolution reanalyses to complex coastal geometries.',
  },
  {
    icon: '🌊',
    title: 'Strong wave signal during reported events',
    text: 'Among events with valid Hₛ data, the within-window maximum Hₛ was on average 1.74× the climatological mean at the grid point, with the top event (Barra Velha, August 2005) reaching 3.3× the mean. This confirms that the reanalysis captures elevated wave conditions during at least a subset of reported coastal disasters.',
  },
  {
    icon: '🔗',
    title: 'Low concurrent exceedances at q90',
    text: 'Only 2 of the 91 events (2%) show any concurrent exceedance of both q90 thresholds within the 7-day window — both in Barra Velha (May 2001, March 2019). This low rate is expected at q90 and will drive the next phase: scanning lower thresholds (p50–p85) to find the level that best distinguishes reported-disaster days from background conditions.',
  },
];

const limitations = [
  'Grid coverage gaps: many northern SC municipalities have the nearest ocean grid cell over land or in geometrically unresolved bays, producing NaN values in thresholds and metrics. This affects ~50% of the 91 analysed events.',
  'q90 thresholds are computed from the full annual series (no seasonal decomposition). Because wave heights peak in austral winter, the annual q90 may underperform relative to a seasonally stratified threshold.',
  'Municipality–grid assignment uses the nearest ocean grid cell to an approximate coastal centroid. No spatial interpolation is applied between grid cells.',
  'The ±3-day window is a fixed preliminary choice. Sensitivity to window width (±5, ±7 days) will be tested in the next phase.',
  'Normalisation by climatological mean can produce inflated SSH normalised values when the mean SSH is close to zero. This is visible in some events.',
  'This is a visual calibration only — systematic threshold optimisation (hit rate, false-alarm rate, critical success index over a threshold grid) is the immediate next step.',
  'The dataset is daily (WAVERYS resampled from 3-hourly using daily mean). Sub-daily compound exceedances are not resolved at this stage.',
];

const analysisParts = [
  {
    part: 'Part TC-1',
    title: 'Per-event Time Series',
    description:
      'For each of the 91 reported coastal disaster events, the nearest ocean grid cell in the unified daily dataset is identified. A 7-day window (±3 days centred on the reported date) is extracted from the full 1993–2025 climatological series. Each figure shows two panels — Hₛ (top) and SSH (bottom) — with the q90 threshold marked as a dashed line, contiguous exceedance periods shaded using MagicA peaks-over-threshold (event_wise), the reported event date as a vertical marker, and the within-window maximum highlighted. A text box summarises normalised maxima and whether a concurrent exceedance was detected.',
    outputs: [
      '91 PNGs — one per reported event: fig_TC_event_{id}_{municipality}_{date}.png',
      'Annotations: q90 threshold, MagicA exceedance shading, event date, peak markers',
    ],
  },
  {
    part: 'Part TC-Summary',
    title: 'Cross-event Summary Figures',
    description:
      'Four summary figures consolidate the per-event metrics across all 91 events and 22 municipalities. They provide a comparative overview of signal strength, scatter structure, and concomitance for the full SC dataset.',
    outputs: [
      'fig_TC_S1 — Grouped bar chart: normalised Hₛ and SSH maxima per event',
      'fig_TC_S2 — Scatter: normalised Hₛ vs SSH, concurrent events highlighted',
      'fig_TC_S3 — Concomitance fraction bar chart per event',
      'fig_TC_S4 — Concomitance heatmap: municipality × event date',
    ],
  },
];

const metricsDefinitions = [
  { metric: 'hs_max_window', description: 'Maximum Hₛ in the 7-day event window (m)' },
  { metric: 'ssh_max_window', description: 'Maximum SSH in the 7-day event window (m)' },
  { metric: 'hs_max_norm', description: 'hs_max_window ÷ climatological mean Hₛ at grid point' },
  { metric: 'ssh_max_norm', description: 'ssh_max_window ÷ climatological mean SSH at grid point' },
  { metric: 'hs_days_above', description: 'Days in window with Hₛ > q90' },
  { metric: 'ssh_days_above', description: 'Days in window with SSH > q90' },
  { metric: 'n_concurrent', description: 'Days with both Hₛ > q90 AND SSH > q90 simultaneously' },
  { metric: 'concurrent_fraction', description: 'n_concurrent ÷ window length' },
  { metric: 'is_concurrent', description: '1 if any concurrent exceedance, 0 otherwise' },
];

export default function ThresholdCalibrationPage() {
  return (
    <>
      <Navigation />
      <main className="pt-16">

        {/* ── Page header ──────────────────────────────────────────────── */}
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
              <span className="text-gray-600">Threshold Calibration</span>
            </div>

            <div className="flex flex-wrap items-start gap-3 mb-4">
              <StatusBadge status="in-progress" />
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">Step 3</span>
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">Full SC coast · 22 municipalities</span>
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">MagicA POT</span>
              <span className="rounded-full border border-blue-200 bg-blue-50 px-2.5 py-1 text-xs text-blue-700">Updated: full SC domain</span>
            </div>

            <h1 className="text-3xl font-bold text-gray-900 md:text-4xl">
              Threshold Calibration
              <br />
              <span className="text-blue-600">Initial Visual Calibration — q90 · Full SC Coast</span>
            </h1>
            <p className="mt-3 max-w-2xl text-sm text-gray-600">
              Per-event time series inspection in ±3-day windows around each reported coastal disaster
              in the Leal et al. (2024) database, now covering the <strong>full Santa Catarina coast</strong> (5 sectors,
              22 municipalities, 91 events). q90 thresholds from the full 1993–2025 climatological series
              at the nearest coastal grid point. Exceedance identification via MagicA peaks-over-threshold.
              Concomitance metrics for Hₛ and SSH.
            </p>

            {/* Metadata chips */}
            <div className="mt-6 flex flex-wrap gap-3">
              {[
                { label: 'Dataset', value: 'Unified daily (VHM0 + zos, WAVERYS grid)' },
                { label: 'Domain', value: 'Full SC coast · lat −29.4° to −26.0°' },
                { label: 'Period', value: '1993–2025' },
                { label: 'Threshold', value: 'q90 · full annual series' },
                { label: 'Window', value: '±3 days centred on event date' },
                { label: 'Events DB', value: 'Leal et al. (2024) · all SC sectors' },
                { label: 'Events analysed', value: '91 (22 municipalities)' },
                { label: 'POT tool', value: 'MagicA (event_wise)' },
              ].map((m) => (
                <div key={m.label} className="rounded-lg border border-gray-300/60 bg-gray-50 px-3 py-2">
                  <div className="text-xs text-gray-500">{m.label}</div>
                  <div className="text-xs font-medium text-gray-800">{m.value}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── Context: why this step matters ───────────────────────────── */}
        <div className="border-b border-gray-200 bg-gray-50 py-14">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-4 text-xl font-bold text-gray-900">What this step is about</h2>
            <div className="grid gap-6 md:grid-cols-2">
              <div>
                <p className="text-sm text-gray-700 leading-relaxed">
                  Before building the compound event catalog, we need to decide at what intensity level Hₛ and SSH
                  count as "extreme." This choice — the threshold — is inherently subjective, but it can be grounded
                  empirically by asking: <em>do the reanalysis signals actually behave as extremes on days when coastal
                  disasters were officially reported?</em>
                </p>
                <p className="mt-3 text-sm text-gray-700 leading-relaxed">
                  This is the purpose of the threshold calibration step. For each reported event in the Leal et al. (2024)
                  database, we look at what Hₛ and SSH were doing in the 7 days around the disaster date, flag how many
                  days both variables simultaneously exceeded q90, and track how strong the peaks were relative to the
                  local climatology.
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-700 leading-relaxed">
                  The current results use q90 as a first-pass threshold. A q90 threshold is deliberately high: it marks
                  only the top 10% of daily values. Requiring <em>both</em> Hₛ and SSH to simultaneously exceed q90
                  is therefore a strict criterion — and indeed, only 2 of the 91 events show any concurrent exceedance
                  at this level.
                </p>
                <p className="mt-3 text-sm text-gray-700 leading-relaxed">
                  The low concomitance rate is not a failure — it is a calibration signal. The next phase will
                  systematically scan a grid of lower thresholds (e.g. p50–p85) and compute hit rate, false-alarm rate,
                  and critical success index against the disaster database to find the threshold combination that best
                  discriminates hazardous days from background conditions.
                </p>
              </div>
            </div>

            {/* Domain expansion note */}
            <div className="mt-6 rounded-lg border border-blue-200 bg-blue-50 p-4">
              <div className="flex gap-3">
                <span className="text-blue-600 text-lg flex-shrink-0">↗</span>
                <div>
                  <p className="text-sm font-semibold text-blue-800">Domain expanded to full Santa Catarina</p>
                  <p className="text-xs text-blue-700 mt-1">
                    The previous exploratory phase used a south SC test domain (7 municipalities, South sector only).
                    This step now covers the complete Leal et al. (2024) database: 5 sectors, 22 municipalities,
                    91 reported events. The expansion required a new test fixture (lat −29.5° to −25.9°S) and a new
                    unified metocean dataset interpolated to the WAVERYS grid. Many northern municipalities still show
                    data gaps due to reanalysis grid coverage limitations (see Limitations section).
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ── Key findings ─────────────────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-white py-14">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-6 text-xl font-bold text-gray-900">Key Findings</h2>
            <div className="grid gap-5 md:grid-cols-2">
              {keyFindings.map((f) => (
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
          </div>
        </div>

        {/* ── Results figures ───────────────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-[#0a0f1e] py-16">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-2 text-xl font-bold text-white">Summary Results</h2>
            <p className="mb-8 text-sm text-gray-400 max-w-2xl">
              Four summary figures consolidate the per-event metrics across all 91 events.
              Each figure is described below with its scientific interpretation.
            </p>
            <div className="space-y-12">
              {figures.map((fig) => (
                <div key={fig.key} className="rounded-2xl border border-gray-700 bg-gray-900/60 overflow-hidden">
                  <div className="p-5 border-b border-gray-700">
                    <span className="rounded-full bg-blue-900/60 border border-blue-700 px-2.5 py-1 text-xs font-semibold text-blue-300">
                      Figure TC-{fig.key}
                    </span>
                    <h3 className="mt-2 text-sm font-semibold text-white">{fig.title}</h3>
                  </div>
                  <div className="p-5">
                    <div className="mb-4 overflow-hidden rounded-lg border border-gray-700">
                      <Image
                        src={fig.filename}
                        alt={fig.title}
                        width={900}
                        height={500}
                        className="w-full h-auto"
                        unoptimized
                      />
                    </div>
                    <p className="text-xs text-gray-400 leading-relaxed italic">{fig.caption}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── Analysis parts ────────────────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-white py-14">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-6 text-xl font-bold text-gray-900">Analysis Parts</h2>
            <div className="grid gap-5 md:grid-cols-2">
              {analysisParts.map((part) => (
                <div key={part.part} className="rounded-xl border border-gray-200 p-5 flex flex-col gap-3">
                  <span className="rounded-full bg-gray-100 border border-gray-300 px-2.5 py-1 text-xs font-semibold text-gray-700 w-fit">
                    {part.part}
                  </span>
                  <h3 className="font-semibold text-gray-900 text-sm">{part.title}</h3>
                  <p className="text-xs text-gray-600 leading-relaxed">{part.description}</p>
                  {part.outputs.length > 0 && (
                    <div className="mt-auto pt-2 border-t border-gray-100">
                      <p className="text-xs font-medium text-gray-400 mb-1.5">Outputs</p>
                      <ul className="space-y-1">
                        {part.outputs.map((o, i) => (
                          <li key={i} className="text-xs text-gray-500 flex gap-1.5">
                            <span className="text-blue-500 mt-0.5 flex-shrink-0">→</span>
                            <span>{o}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── Metrics dictionary ────────────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-gray-50 py-14">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-4 text-xl font-bold text-gray-900">Metrics Dictionary</h2>
            <p className="mb-5 text-sm text-gray-600 max-w-2xl">
              The consolidated table{' '}
              <code className="text-xs bg-gray-200 px-1 py-0.5 rounded">tab_TC_event_metrics.csv</code> contains
              the following fields per event. Normalisation uses the full 1993–2025 climatological mean at the
              same grid point.
            </p>
            <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50">
                    <th className="px-4 py-3 text-left font-semibold text-gray-700">Column</th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-700">Description</th>
                  </tr>
                </thead>
                <tbody>
                  {metricsDefinitions.map((m, i) => (
                    <tr key={m.metric} className={`border-b border-gray-100 ${i % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}`}>
                      <td className="px-4 py-2.5 font-mono text-blue-700">{m.metric}</td>
                      <td className="px-4 py-2.5 text-gray-600">{m.description}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* ── Limitations ───────────────────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-white py-14">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-5 text-xl font-bold text-gray-900">Assumptions &amp; Limitations</h2>
            <ul className="space-y-2.5">
              {limitations.map((lim, i) => (
                <li key={i} className="flex gap-2.5 text-sm text-gray-600">
                  <span className="text-orange-500 font-bold flex-shrink-0 mt-0.5">!</span>
                  <span>{lim}</span>
                </li>
              ))}
            </ul>

            {/* Next steps */}
            <div className="mt-8 rounded-lg border border-gray-200 bg-gray-50 p-5">
              <h3 className="text-sm font-semibold text-gray-900 mb-2">Immediate next steps</h3>
              <ul className="space-y-1.5">
                {[
                  'Threshold grid scan: compute hit rate, false-alarm rate, and CSI for q50–q90 × q50–q90 combinations to identify the optimal threshold pair.',
                  'Seasonal threshold: test a seasonally stratified q90 (DJF/MAM/JJA/SON) to address the annual-cycle bias in the current approach.',
                  'Grid coverage audit: identify which municipalities have ocean grid cells within <20 km of their coastline and flag the rest as coverage-limited.',
                  'Extend the Part E municipality–grid table to cover all SC sectors to replace hardcoded approximate coordinates.',
                ].map((s, i) => (
                  <li key={i} className="flex gap-2 text-xs text-gray-600">
                    <span className="text-green-600 font-bold flex-shrink-0">→</span>
                    <span>{s}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* ── Navigation ────────────────────────────────────────────────── */}
        <div className="bg-white py-12">
          <div className="mx-auto max-w-5xl px-6 flex items-center justify-between">
            <Link
              href="/results/south-sc"
              className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Exploratory Analysis
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
