import Image from 'next/image';
import Link from 'next/link';
import Navigation from '@/components/Navigation';
import Footer from '@/components/Footer';
import StatusBadge from '@/components/StatusBadge';
import EventFigureSelector from '@/components/EventFigureSelector';
import SectorFigureTabs from '@/components/SectorFigureTabs';

export const metadata = {
  title: 'Threshold Calibration — OSR11',
  description:
    'Initial visual calibration of q90 thresholds for Hₛ and SSH against reported Santa Catarina coastal disaster events. Full SC coast domain. MagicA peaks-over-threshold, per-event time series analysis, and concomitance metrics.',
};

// ── Summary figure data ─────────────────────────────────────────────────────

const SECTORS = [
  { label: 'North',          suffix: 'north_sector' },
  { label: 'Central-north',  suffix: 'central_north_sector' },
  { label: 'Central',        suffix: 'central_sector' },
  { label: 'Central-south',  suffix: 'central_south_sector' },
  { label: 'South',          suffix: 'south_sector' },
];

const s1Tabs = SECTORS.map((s) => ({
  label: s.label,
  file:  `fig_TC_S1_normalised_maxima_${s.suffix}.png`,
}));

const s3Tabs = SECTORS.map((s) => ({
  label: s.label,
  file:  `fig_TC_S3_concomitance_${s.suffix}.png`,
}));

const s4Tabs = SECTORS.map((s) => ({
  label: s.label,
  file:  `fig_TC_S4_heatmap_${s.suffix}.png`,
}));

// ── Key findings ────────────────────────────────────────────────────────────

const keyFindings = [
  {
    icon: '📊',
    title: '91 events · 22 municipalities · 5 sectors',
    text: 'The full Leal et al. (2024) Santa Catarina coastal disaster database is now covered: North, Central-north, Central, Central-south, and South sectors. The previous exploratory phase used only the South sector (7 municipalities, 8 events).',
  },
  {
    icon: '⚠️',
    title: 'Grid coverage gaps in northern sectors',
    text: 'Of the 91 events, 47 have valid Hₛ data and only 10 have valid joint Hₛ + SSH data. Gaps are concentrated in the North sector (~44 events), where the nearest WAVERYS/GLORYS12 ocean grid cells frequently fall over land or in geometrically unresolved bays.',
  },
  {
    icon: '🌊',
    title: 'Strong wave signal during reported events',
    text: 'Among events with valid Hₛ data, the within-window maximum Hₛ averaged 1.74× the climatological mean at each grid point. The strongest signal (Barra Velha, August 2005) reached 3.3× the mean, confirming the reanalysis captures elevated wave conditions during at least a subset of reported disasters.',
  },
  {
    icon: '🔗',
    title: 'Low concurrent exceedances at q90 — expected',
    text: 'Only 2 of 91 events (2%) show concurrent Hₛ and SSH exceedances at q90 within the 7-day window. This is not a failure: it is a calibration signal. The next phase will scan q50–q85 to find the threshold level that best separates hazardous days from background conditions.',
  },
];

// ── Metrics ─────────────────────────────────────────────────────────────────

const metricsDefinitions = [
  { metric: 'hs_max_window',       description: 'Maximum Hₛ in the 7-day event window (m)' },
  { metric: 'ssh_max_window',      description: 'Maximum SSH in the 7-day event window (m)' },
  { metric: 'hs_max_norm',         description: 'hs_max_window ÷ climatological mean Hₛ at grid point' },
  { metric: 'ssh_max_norm',        description: 'ssh_max_window ÷ climatological mean SSH at grid point' },
  { metric: 'hs_days_above',       description: 'Days in window with Hₛ > q90' },
  { metric: 'ssh_days_above',      description: 'Days in window with SSH > q90' },
  { metric: 'n_concurrent',        description: 'Days with both Hₛ > q90 AND SSH > q90 simultaneously' },
  { metric: 'concurrent_fraction', description: 'n_concurrent ÷ window length' },
  { metric: 'is_concurrent',       description: '1 if any concurrent exceedance, 0 otherwise' },
];

// ── Limitations ─────────────────────────────────────────────────────────────

const limitations = [
  'Grid coverage gaps: many northern SC municipalities have their nearest ocean grid cell over land or in geometrically unresolved bays, producing NaN values in thresholds and metrics. This affects ~50% of the 91 analysed events.',
  'q90 thresholds are computed from the full annual series (no seasonal decomposition). Because wave heights peak in austral winter, the annual q90 may underperform relative to a seasonally stratified threshold.',
  'Municipality–grid assignment uses the nearest ocean grid cell to an approximate coastal centroid. No spatial interpolation is applied between grid cells.',
  'The ±3-day window is a fixed preliminary choice. Sensitivity to window width (±5, ±7 days) will be tested in the next phase.',
  'Normalisation by climatological mean can produce inflated SSH normalised values when the mean SSH is close to zero.',
  'This is a visual calibration only — systematic threshold optimisation (hit rate, false-alarm rate, critical success index over a threshold grid) is the immediate next step.',
  'The dataset is daily (WAVERYS resampled from 3-hourly using daily mean). Sub-daily compound exceedances are not resolved at this stage.',
];

// ── Page ────────────────────────────────────────────────────────────────────

export default function ThresholdCalibrationPage() {
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
              <span className="text-gray-600">Threshold Calibration</span>
            </div>

            <div className="flex flex-wrap items-start gap-2 mb-4">
              <StatusBadge status="in-progress" />
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">Step 2</span>
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">Full SC coast · 5 sectors · 22 municipalities</span>
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">MagicA POT</span>
            </div>

            <h1 className="text-3xl font-bold text-gray-900 md:text-4xl">
              Threshold Calibration
              <br />
              <span className="text-blue-600">Initial Visual Calibration — q90</span>
            </h1>
            <p className="mt-3 max-w-2xl text-sm text-gray-600">
              Per-event time series inspection in ±3-day windows around each reported coastal
              disaster in the Leal et al. (2024) database — full Santa Catarina coast (5 sectors,
              22 municipalities, 91 events, 1998–2020). q90 thresholds from the full 1993–2025
              climatological series at the nearest coastal grid point. Exceedance identification
              via MagicA peaks-over-threshold.
            </p>

            <div className="mt-6 flex flex-wrap gap-3">
              {[
                { label: 'Dataset',        value: 'Unified daily · VHM0 + zos · WAVERYS grid' },
                { label: 'Period',         value: '1993–2025' },
                { label: 'Threshold',      value: 'q90 · full annual series' },
                { label: 'Window',         value: '±3 days centred on event date' },
                { label: 'Events DB',      value: 'Leal et al. (2024) · full SC coast' },
                { label: 'Events total',   value: '91 · 22 municipalities' },
                { label: 'POT tool',       value: 'MagicA (event_wise)' },
              ].map((m) => (
                <div key={m.label} className="rounded-lg border border-gray-300/60 bg-gray-50 px-3 py-2">
                  <div className="text-xs text-gray-500">{m.label}</div>
                  <div className="text-xs font-medium text-gray-800">{m.value}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── What this step is about ──────────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-gray-50 py-14">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-4 text-xl font-bold text-gray-900">What this step is about</h2>
            <div className="grid gap-6 md:grid-cols-2">
              <p className="text-sm text-gray-700 leading-relaxed">
                Before building the compound event catalog, we need to decide at what intensity
                level Hₛ and SSH count as "extreme." This choice — the threshold — is inherently
                subjective, but can be grounded empirically: <em>do the reanalysis signals actually
                behave as extremes on days when coastal disasters were officially reported?</em>
                <br /><br />
                For each reported event in the Leal et al. (2024) database, we inspect what Hₛ and
                SSH were doing in the 7 days around the disaster date, flag concurrent exceedances,
                and track how strong the peaks were relative to the local climatology.
              </p>
              <p className="text-sm text-gray-700 leading-relaxed">
                The current results use q90 as a first-pass threshold — it marks the top 10% of
                daily values. Requiring both variables to simultaneously exceed q90 is strict, and
                indeed only 2 of 91 events show any concurrent exceedance at this level.
                <br /><br />
                This low concomitance rate is a calibration signal, not a failure. The next phase
                will scan a grid of lower thresholds (e.g. p50–p85) and compute hit rate,
                false-alarm rate, and critical success index to find the combination that best
                discriminates hazardous days from background conditions.
              </p>
            </div>
          </div>
        </div>

        {/* ── Key findings ─────────────────────────────────────────────────── */}
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

        {/* ── Per-event figures (interactive selector) ─────────────────────── */}
        <div className="border-b border-gray-200 bg-gray-50 py-14">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-2 text-xl font-bold text-gray-900">Individual Event Figures</h2>
            <p className="mb-6 text-sm text-gray-600 max-w-2xl">
              One figure per reported event: two panels (Hₛ top, SSH bottom) showing the 7-day window,
              q90 threshold line, MagicA exceedance shading (coloured fill for periods above threshold),
              reported event date (vertical marker), and within-window maximum (circle). The text box
              summarises normalised maxima and concomitance. Events marked with ⬤ show concurrent
              exceedance of both q90 thresholds within the window.
            </p>
            <EventFigureSelector />
          </div>
        </div>

        {/* ── Figure S1: normalised maxima ─────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-white py-14">
          <div className="mx-auto max-w-5xl px-6">
            <div className="flex flex-wrap items-center gap-3 mb-2">
              <span className="rounded-full bg-gray-100 border border-gray-300 px-2.5 py-1 text-xs font-semibold text-gray-700">
                Figure TC-S1
              </span>
              <h2 className="text-xl font-bold text-gray-900">Normalised Maxima per Event</h2>
            </div>
            <p className="mb-6 text-sm text-gray-600 max-w-2xl">
              Grouped bar chart of within-window Hₛ and SSH maxima, each divided by their long-term
              climatological mean at the same grid point. A bar at 1.0 means the peak equalled
              the climatological mean; a bar at 2.0 means it was double. Grey bars indicate missing
              data (municipality not covered by the reanalysis grid). Note that SSH normalised maxima
              systematically exceed Hₛ — this reflects the smaller mean and variance of SSH, not a
              difference in hazard intensity.
            </p>
            <SectorFigureTabs
              figureKey="S1"
              overallFile="fig_TC_S1_normalised_maxima_per_event.png"
              sectorTabs={s1Tabs}
              caption="Normalised Hₛ and SSH maxima per event within the ±3-day window, divided by the full 1993–2025 climatological mean at the nearest coastal grid point. Tabs show the full SC dataset or individual sectors. Events are ordered by municipality then date within each sector."
            />
          </div>
        </div>

        {/* ── Figure S2: scatter ───────────────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-gray-50 py-14">
          <div className="mx-auto max-w-5xl px-6">
            <div className="flex flex-wrap items-center gap-3 mb-2">
              <span className="rounded-full bg-gray-100 border border-gray-300 px-2.5 py-1 text-xs font-semibold text-gray-700">
                Figure TC-S2
              </span>
              <h2 className="text-xl font-bold text-gray-900">Normalised Hₛ vs SSH Scatter</h2>
            </div>
            <p className="mb-6 text-sm text-gray-600 max-w-2xl">
              Each point is one reported event. Filled circles mark events where both Hₛ and SSH
              simultaneously exceeded q90 at the same daily time step (concurrent exceedances).
              Open circles are events where the variables peaked at different times within the
              7-day window. Only 2 of 10 events with valid joint data show concurrent exceedances —
              both in Barra Velha (North sector). This low rate at q90 is expected and will drive
              the next threshold optimisation phase.
            </p>
            <div className="rounded-xl border border-gray-200 bg-white overflow-hidden shadow-sm">
              <div className="p-5">
                <Image
                  src="/figures/tc_summary/fig_TC_S2_scatter_normalised_hs_ssh.png"
                  alt="Figure TC-S2 — Normalised Hₛ vs SSH Scatter"
                  width={900}
                  height={600}
                  className="w-full h-auto rounded-lg"
                  unoptimized
                />
              </div>
              <div className="border-t border-gray-100 px-5 py-4">
                <p className="text-xs text-gray-500 leading-relaxed italic">
                  Scatter of normalised Hₛ maximum vs normalised SSH maximum per event, coloured by
                  municipality. Filled circles indicate concurrent exceedances (both variables above q90
                  simultaneously). Reference lines at 1.0 mark the climatological mean.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* ── Figure S3: concomitance bars ─────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-white py-14">
          <div className="mx-auto max-w-5xl px-6">
            <div className="flex flex-wrap items-center gap-3 mb-2">
              <span className="rounded-full bg-gray-100 border border-gray-300 px-2.5 py-1 text-xs font-semibold text-gray-700">
                Figure TC-S3
              </span>
              <h2 className="text-xl font-bold text-gray-900">Concomitance Fraction per Event</h2>
            </div>
            <p className="mb-6 text-sm text-gray-600 max-w-2xl">
              Fraction of days within the 7-day window in which both Hₛ and SSH simultaneously
              exceeded their q90 thresholds. Most events show zero fraction — confirming that joint
              q90 exceedances are uncommon even during documented coastal disasters. Events with
              non-zero concomitance represent the clearest compound signals identified in this
              initial calibration pass.
            </p>
            <SectorFigureTabs
              figureKey="S3"
              overallFile="fig_TC_S3_concomitance_fraction_per_event.png"
              sectorTabs={s3Tabs}
              caption="Concomitance fraction (days with both Hₛ > q90 and SSH > q90 simultaneously, divided by window length) for each event. Coloured bars indicate non-zero concomitance; grey bars indicate zero. Per-sector tabs allow comparison across coastal sectors."
            />
          </div>
        </div>

        {/* ── Figure S4: heatmap ───────────────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-gray-50 py-14">
          <div className="mx-auto max-w-5xl px-6">
            <div className="flex flex-wrap items-center gap-3 mb-2">
              <span className="rounded-full bg-gray-100 border border-gray-300 px-2.5 py-1 text-xs font-semibold text-gray-700">
                Figure TC-S4
              </span>
              <h2 className="text-xl font-bold text-gray-900">Concomitance Heatmap</h2>
            </div>
            <p className="mb-6 text-sm text-gray-600 max-w-2xl">
              Heatmap of concurrent-exceedance fraction for all municipality–event combinations.
              Rows are municipalities; columns are event dates. Colour intensity encodes the
              fraction of the 7-day window with concurrent Hₛ and SSH exceedances. White cells
              indicate either zero concomitance or missing data. Concurrent exceedances are sparse
              at q90 — the next phase will lower the threshold to find the level that maximises
              consistency with reported disaster dates.
            </p>
            <SectorFigureTabs
              figureKey="S4"
              overallFile="fig_TC_S4_heatmap_concomitance.png"
              sectorTabs={s4Tabs}
              caption="Concomitance heatmap: municipality × event date. Colour = fraction of 7-day window with both Hₛ > q90 and SSH > q90. White = zero or missing. Per-sector views improve readability for sectors with many municipalities."
            />
          </div>
        </div>

        {/* ── Analysis parts ───────────────────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-white py-14">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-6 text-xl font-bold text-gray-900">Analysis Parts</h2>
            <div className="grid gap-5 md:grid-cols-2">
              {[
                {
                  part: 'Part TC-1',
                  title: 'Per-event Time Series',
                  description: 'For each of the 91 reported coastal disaster events, the nearest ocean grid cell in the unified daily dataset is identified. A 7-day window (±3 days centred on the reported date) is extracted from the full 1993–2025 climatological series. Each figure shows two panels — Hₛ (top) and SSH (bottom) — with the q90 threshold, MagicA exceedance shading, reported event date marker, and within-window maximum. A text box summarises normalised maxima and concurrent exceedance.',
                  outputs: [
                    '91 PNGs — fig_TC_event_{id}_{municipality}_{date}.png',
                    'MagicA event_wise POT: one peak marker per contiguous exceedance episode',
                  ],
                },
                {
                  part: 'Part TC-Summary',
                  title: 'Cross-event Summary Figures',
                  description: 'Four summary figure types (S1–S4) consolidate the per-event metrics across all 91 events and 22 municipalities, each available both for the full SC dataset and per coastal sector. S1 compares normalised maxima; S2 shows joint scatter; S3 shows concomitance fraction; S4 shows the municipality–event heatmap.',
                  outputs: [
                    '6 × S1 figures (overall + 5 sectors)',
                    '1 × S2 scatter (overall)',
                    '6 × S3 figures (overall + 5 sectors)',
                    '6 × S4 figures (overall + 5 sectors)',
                  ],
                },
              ].map((part) => (
                <div key={part.part} className="rounded-xl border border-gray-200 p-5 flex flex-col gap-3">
                  <span className="rounded-full bg-gray-100 border border-gray-300 px-2.5 py-1 text-xs font-semibold text-gray-700 w-fit">
                    {part.part}
                  </span>
                  <h3 className="font-semibold text-gray-900 text-sm">{part.title}</h3>
                  <p className="text-xs text-gray-600 leading-relaxed">{part.description}</p>
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
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── Metrics dictionary ───────────────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-gray-50 py-14">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-4 text-xl font-bold text-gray-900">Metrics Dictionary</h2>
            <p className="mb-5 text-sm text-gray-600 max-w-2xl">
              The consolidated table{' '}
              <code className="text-xs bg-gray-200 px-1 py-0.5 rounded">tab_TC_event_metrics.csv</code>{' '}
              contains the following fields per event. Normalisation uses the full 1993–2025
              climatological mean at the same grid point.
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

        {/* ── Limitations + next steps ─────────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-white py-14">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-5 text-xl font-bold text-gray-900">Assumptions &amp; Limitations</h2>
            <ul className="space-y-2.5 mb-8">
              {limitations.map((lim, i) => (
                <li key={i} className="flex gap-2.5 text-sm text-gray-600">
                  <span className="text-orange-500 font-bold flex-shrink-0 mt-0.5">!</span>
                  <span>{lim}</span>
                </li>
              ))}
            </ul>

            <div className="rounded-lg border border-gray-200 bg-gray-50 p-5">
              <h3 className="text-sm font-semibold text-gray-900 mb-3">Immediate next steps</h3>
              <ul className="space-y-1.5">
                {[
                  'Threshold grid scan: compute hit rate, false-alarm rate, and CSI for q50–q90 × q50–q90 combinations.',
                  'Seasonal threshold: test a seasonally stratified q90 (DJF/MAM/JJA/SON) to address the annual-cycle bias.',
                  'Grid coverage audit: identify which municipalities have ocean grid cells within <20 km of their coastline.',
                  'Extend the municipality–grid table to cover all SC sectors and replace hardcoded approximate coordinates.',
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

        {/* ── Navigation ───────────────────────────────────────────────────── */}
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
