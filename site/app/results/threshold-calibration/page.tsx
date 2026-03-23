import Link from 'next/link';
import Navigation from '@/components/Navigation';
import Footer from '@/components/Footer';
import StatusBadge from '@/components/StatusBadge';

export const metadata = {
  title: 'Threshold Calibration — OSR11',
  description:
    'Initial visual calibration of q90 thresholds for Hₛ and SSH against reported South SC coastal disaster events. MagicA peaks-over-threshold, per-event time series analysis, and concomitance metrics.',
};

const analysisParts = [
  {
    part: 'Part TC-1',
    title: 'Per-event Time Series',
    description:
      'For each reported coastal disaster event in the South SC sector, the nearest grid point in the unified daily dataset is identified and a 7-day window (±3 days centred on the reported date) is extracted. Each figure shows two panels — Hₛ (top) and SSH (bottom) — with the q90 threshold, exceedance periods shaded using MagicA peaks-over-threshold (event_wise), the reported event date marked, and the within-window maximum highlighted. A text box summarises normalised maxima and concomitance.',
    outputs: [
      'One PNG per reported event: fig_TC_event_{id}_{municipality}_{date}.png',
      'Panels: Hₛ and SSH time series with q90 threshold and MagicA exceedance shading',
      'Annotations: reported date, peak marker, normalised maxima, concomitance flag',
    ],
  },
  {
    part: 'Summary TC-S1',
    title: 'Normalised Maxima per Event',
    description:
      'Grouped bar chart comparing the within-window Hₛ and SSH maxima normalised by the long-term climatological mean at the same grid point. Bars are grouped by event and ordered by municipality then date. A reference line at 1.0 marks the climatological mean.',
    outputs: ['fig_TC_S1 — Grouped bar chart: Hₛ_max/Hₛ_mean and SSH_max/SSH_mean per event'],
  },
  {
    part: 'Summary TC-S2',
    title: 'Normalised Hₛ vs SSH Scatter',
    description:
      'Scatter plot of normalised Hₛ maximum vs normalised SSH maximum per event, coloured by municipality. Concurrent events (both variables above q90 at the same time step) are shown as filled circles; non-concurrent events as open circles. Reference lines mark the climatological mean (normalised value = 1).',
    outputs: [
      'fig_TC_S2 — Scatter: Hₛ_max/Hₛ_mean vs SSH_max/SSH_mean, concurrent events highlighted',
    ],
  },
  {
    part: 'Summary TC-S3',
    title: 'Concomitance Fraction per Event',
    description:
      'Horizontal bar chart of the fraction of days within the 7-day window in which both Hₛ and SSH simultaneously exceed their q90 thresholds. Events with zero concomitance are shown in grey.',
    outputs: [
      'fig_TC_S3 — Concomitance fraction (days with both > q90 ÷ window length)',
    ],
  },
  {
    part: 'Summary TC-S4',
    title: 'Concomitance Heatmap',
    description:
      'Heatmap of concomitance fraction for all municipality–event combinations. Rows are municipalities; columns are event dates. Colour intensity encodes the fraction of the 7-day window with concurrent exceedances. Provides a quick overview of which events and locations show the strongest co-occurrence of extreme Hₛ and SSH.',
    outputs: [
      'fig_TC_S4 — Heatmap: municipality × event date, colour = concurrent fraction',
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

const limitations = [
  'Restricted to the south SC test domain (−29.4° to −27.6°S); municipalities outside this extent are not covered.',
  'q90 thresholds are computed from the full annual series (no seasonal decomposition); extreme values in winter may be underrepresented if the annual cycle is strong.',
  'Municipality–grid assignment uses the nearest grid cell; no spatial interpolation between grid points.',
  'The ±3-day window is a single fixed choice; longer windows (±5–7 days) may be explored in the next phase.',
  'Normalisation by climatological mean can be misleading when the mean is close to zero (e.g. SSH with strong tidal signal).',
  'This is a preliminary visual calibration — systematic threshold optimisation (hit rate, false-alarm rate, CSI) is planned for the next phase.',
  'MagicA event-wise POT markers rely on the 7-day window only; the full-series block maxima analysis is deferred to the storm catalog phase.',
];

export default function ThresholdCalibrationPage() {
  return (
    <>
      <Navigation />
      <main className="pt-16">
        {/* Page header */}
        <div className="border-b border-gray-200 bg-white py-16">
          <div className="mx-auto max-w-5xl px-6">
            <div className="mb-4 flex items-center gap-2 text-xs text-gray-500">
              <Link href="/" className="hover:text-gray-700 transition-colors">
                Overview
              </Link>
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
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">
                Step 3
              </span>
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">
                Test domain · South SC
              </span>
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">
                MagicA POT
              </span>
            </div>

            <h1 className="text-3xl font-bold text-gray-900 md:text-4xl">
              Threshold Calibration
              <br />
              <span className="text-blue-600">Initial Visual Calibration — q90</span>
            </h1>
            <p className="mt-3 max-w-2xl text-sm text-gray-600">
              Per-event time series inspection in ±3-day windows around each reported coastal
              disaster. q90 thresholds from the full 1993–2025 climatological series at the
              nearest coastal grid point. Exceedance identification via MagicA peaks-over-threshold.
              Concomitance metrics for Hₛ and SSH.
            </p>

            {/* Metadata chips */}
            <div className="mt-6 flex flex-wrap gap-3">
              {[
                { label: 'Dataset', value: 'Unified daily (VHM0 + zos, WAVERYS grid)' },
                { label: 'Period', value: '1993–2025' },
                { label: 'Threshold', value: 'q90 · full annual series' },
                { label: 'Window', value: '±3 days centred on event date' },
                { label: 'Events DB', value: 'Leal et al. (2024) · South sector' },
                { label: 'POT tool', value: 'MagicA (event_wise)' },
              ].map((m) => (
                <div
                  key={m.label}
                  className="rounded-lg border border-gray-300/60 bg-gray-50 px-3 py-2"
                >
                  <div className="text-xs text-gray-500">{m.label}</div>
                  <div className="text-xs font-medium text-gray-800">{m.value}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Analysis parts */}
        <div className="border-b border-gray-200 bg-[#0a0f1e] py-16">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-8 text-xl font-bold text-white">Analysis Parts</h2>
            <div className="grid gap-5 md:grid-cols-2">
              {analysisParts.map((part) => (
                <div
                  key={part.part}
                  className="rounded-xl border border-gray-700 bg-gray-800/50 p-5 flex flex-col gap-3"
                >
                  <div className="flex items-center gap-2">
                    <span className="rounded-full bg-blue-900/60 border border-blue-700 px-2.5 py-1 text-xs font-semibold text-blue-300">
                      {part.part}
                    </span>
                  </div>
                  <h3 className="font-semibold text-white text-sm">{part.title}</h3>
                  <p className="text-xs text-gray-400 leading-relaxed">{part.description}</p>
                  {part.outputs.length > 0 && (
                    <div className="mt-auto pt-2 border-t border-gray-700">
                      <p className="text-xs font-medium text-gray-500 mb-1.5">Outputs</p>
                      <ul className="space-y-1">
                        {part.outputs.map((o, i) => (
                          <li key={i} className="text-xs text-gray-400 flex gap-1.5">
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

        {/* Metrics definitions */}
        <div className="border-b border-gray-200 bg-white py-16">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-6 text-xl font-bold text-gray-900">Metrics Dictionary</h2>
            <p className="mb-6 text-sm text-gray-600 max-w-2xl">
              The consolidated table <code className="text-xs bg-gray-100 px-1 py-0.5 rounded">tab_TC_event_metrics.csv</code> contains
              the following fields per event. Normalisation uses the full 1993–2025
              climatological mean at the same grid point as reference.
            </p>
            <div className="overflow-x-auto rounded-xl border border-gray-200">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50">
                    <th className="px-4 py-3 text-left font-semibold text-gray-700">Column</th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-700">Description</th>
                  </tr>
                </thead>
                <tbody>
                  {metricsDefinitions.map((m, i) => (
                    <tr
                      key={m.metric}
                      className={`border-b border-gray-100 ${i % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}`}
                    >
                      <td className="px-4 py-2.5 font-mono text-blue-700">{m.metric}</td>
                      <td className="px-4 py-2.5 text-gray-600">{m.description}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Limitations */}
        <div className="border-b border-gray-200 bg-gray-50 py-16">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-6 text-xl font-bold text-gray-900">Assumptions & Limitations</h2>
            <ul className="space-y-2">
              {limitations.map((lim, i) => (
                <li key={i} className="flex gap-2.5 text-sm text-gray-600">
                  <span className="text-orange-500 font-bold flex-shrink-0 mt-0.5">!</span>
                  <span>{lim}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Navigation */}
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
