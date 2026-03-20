import Link from 'next/link';
import Navigation from '@/components/Navigation';
import FigureGallery from '@/components/FigureGallery';
import Footer from '@/components/Footer';
import StatusBadge from '@/components/StatusBadge';
import { southScFigures } from '@/content/figures';

export const metadata = {
  title: 'South SC Exploratory Analysis — OSR11',
  description:
    'Detailed results of the exploratory data analysis for the southern Santa Catarina sector (test domain). WAVERYS and GLORYS12, 1993–2025.',
};

const analysisModules = [
  {
    part: 'Part A',
    title: 'Spatial Maxima Maps',
    description:
      'Spatial distribution of period-maximum Hₛ (WAVERYS) and SSH (GLORYS12) across the test domain. Coastal grid points selected via the Natural Earth 10 m coastline (cells within 50 km of the coastline). Provides a first look at where the most extreme values occur in the domain and reveals spatial gradients in peak wave and sea-level activity.',
    outputs: ['fig_A1a — Period-max Hₛ map', 'fig_A1b — Period-max SSH map'],
  },
  {
    part: 'Part B',
    title: 'Time Series at Peak Grid Points',
    description:
      'Time series centred on the peak-value event at the Hₛ-maximum and SSH-maximum grid points. A ±15-day window is shown for each variable, with the event date marked. This allows a first qualitative assessment of the temporal structure of the extreme events and whether the two maxima co-occur.',
    outputs: ['fig_B1 — 4-panel time series at Hₛ-max and SSH-max points'],
  },
  {
    part: 'Part D',
    title: 'Reported Events EDA',
    description:
      'Exploratory analysis of the Leal et al. (2024) coastal disaster database for the south SC sector (test domain). Includes event counts per municipality, boxplots of Hₛ and SSH at event dates (extracted from WAVERYS and GLORYS12 at the nearest coastal grid point), and monthly seasonality of reported events.',
    outputs: [
      'fig_D1 — Event counts per municipality',
      'fig_D2 — Hₛ and SSH boxplots at event dates',
      'fig_D4 — Monthly seasonality',
      'tab — Summary statistics by municipality and sector',
    ],
  },
  {
    part: 'Part E',
    title: 'Municipality–Grid Association',
    description:
      'Association of IBGE municipality centroids (fetched via IBGE Localidades API) to the nearest WAVERYS and GLORYS12 coastal grid points using a KD-tree (Euclidean distance in km). Separate flags for whether each municipality falls within the WAVERYS and GLORYS12 test-domain extents.',
    outputs: [
      'tab — Municipality coordinates, nearest grid points, domain flags, distances',
    ],
  },
  {
    part: 'Part F',
    title: 'Sector Overview Figure',
    description:
      'Three-panel composite figure for the south SC sector: (left) geographic map with municipality centroids, coastal grid points, and test-domain bounding box; (centre) Hₛ boxplots per municipality ordered south to north; (right) SSH boxplots per municipality. Provides an integrated view of spatial configuration and statistical properties at each location.',
    outputs: ['fig_F — South sector map + Hₛ + SSH boxplots'],
  },
  {
    part: 'Part G',
    title: 'Statistical Analyses',
    description:
      'Six supplementary statistical analyses per municipality: descriptive statistics table (G1); Hₛ vs SSH scatter coloured by year (G2); seasonal cycle as monthly median ± IQR for both variables (G3a, G3b); compound co-occurrence quick-look using empirical q90 thresholds (G4); top compound events time series (G5); and marginal distributions as histograms (G6a, G6b).',
    outputs: [
      'tab_G1 — Descriptive statistics (mean, p75, p90, p99, max)',
      'fig_G2 — Hₛ vs SSH scatter per municipality',
      'fig_G3a/G3b — Seasonal cycles',
      'fig_G4 — Compound quick-look',
      'fig_G5 — Top compound events per municipality',
      'fig_G6a/G6b — Marginal distributions',
    ],
  },
];

const limitations = [
  'Restricted to the south SC test domain; northern and central-north SC municipalities are outside the dataset extent.',
  'No spatial interpolation: each municipality is assigned the single nearest coastal grid point.',
  'GLORYS12 has a finer ocean mask than WAVERYS; some municipalities with a valid WAVERYS point may lack a GLORYS12 match.',
  'WAVERYS 3-hourly data is resampled to daily means for paired analysis with GLORYS12.',
  'Compound thresholds in Part G are empirical q90 values, exploratory only — not the final physically motivated definition.',
  'IBGE municipality coordinates are derived from outer polygon centroids and may not align with the actual coastal exposure point.',
  'Natural Earth 10 m coastline is suitable for features ~10 km and larger; finer-scale nearshore geometry is not resolved.',
];

export default function SouthSCPage() {
  return (
    <>
      <Navigation />
      <main className="pt-16">
        {/* Page header */}
        <div className="border-b border-slate-800 bg-slate-950 py-16">
          <div className="mx-auto max-w-5xl px-6">
            <div className="mb-4 flex items-center gap-2 text-xs text-slate-500">
              <Link href="/" className="hover:text-slate-300 transition-colors">
                Overview
              </Link>
              <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              <span>Results</span>
              <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              <span className="text-slate-400">South SC — Exploratory Analysis</span>
            </div>

            <div className="flex flex-wrap items-start gap-3 mb-4">
              <StatusBadge status="in-progress" />
              <span className="rounded-full border border-slate-700 bg-slate-900 px-2.5 py-1 text-xs text-slate-400">
                Phase 1
              </span>
              <span className="rounded-full border border-slate-700 bg-slate-900 px-2.5 py-1 text-xs text-slate-400">
                Test domain · South SC
              </span>
            </div>

            <h1 className="text-3xl font-bold text-slate-100 md:text-4xl">
              Exploratory Analysis
              <br />
              <span className="text-sky-400">Southern Santa Catarina</span>
            </h1>
            <p className="mt-3 max-w-2xl text-sm text-slate-400">
              First-look EDA on WAVERYS and GLORYS12 test datasets for the south SC sector
              (~−29.4° to −27.6°S, ~−50° to −48°W). Seven analysis blocks covering spatial
              maps, time series, reported events, municipality–grid association, sector
              figures, and statistical characterisation.
            </p>

            {/* Metadata chips */}
            <div className="mt-6 flex flex-wrap gap-3">
              {[
                { label: 'Domain', value: '~29.4°S – 27.6°S · 50°W – 48°W' },
                { label: 'Wave data', value: 'WAVERYS (VHM0, VMDR) · 3-hourly' },
                { label: 'Sea-level data', value: 'GLORYS12 (zos) · daily' },
                { label: 'Period', value: '1993–2025' },
                { label: 'Events DB', value: 'Leal et al. (2024) · 1998–2023' },
                { label: 'Figures', value: `${southScFigures.length} outputs` },
              ].map((m) => (
                <div
                  key={m.label}
                  className="rounded-lg border border-slate-700/60 bg-slate-900 px-3 py-2"
                >
                  <div className="text-xs text-slate-500">{m.label}</div>
                  <div className="text-xs font-medium text-slate-200">{m.value}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Analysis modules */}
        <div className="border-b border-slate-800 bg-[#0a0f1e] py-16">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-8 text-xl font-bold text-slate-100">Analysis Modules</h2>
            <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
              {analysisModules.map((mod) => (
                <div
                  key={mod.part}
                  className="rounded-xl border border-slate-800 bg-slate-900 p-5 flex flex-col gap-3"
                >
                  <div className="flex items-center gap-2">
                    <span className="rounded border border-slate-700 bg-slate-800 px-1.5 py-0.5 text-xs font-semibold text-sky-400">
                      {mod.part}
                    </span>
                    <h3 className="text-xs font-semibold text-slate-200">{mod.title}</h3>
                  </div>
                  <p className="text-xs leading-relaxed text-slate-400">{mod.description}</p>
                  <div className="mt-auto border-t border-slate-800 pt-3">
                    <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-slate-600">
                      Outputs
                    </p>
                    <ul className="space-y-0.5">
                      {mod.outputs.map((o) => (
                        <li key={o} className="flex items-start gap-1.5 text-xs text-slate-500">
                          <span className="mt-1.5 h-1 w-1 flex-shrink-0 rounded-full bg-sky-600" />
                          {o}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Design decisions */}
        <div className="border-b border-slate-800 bg-slate-950 py-16">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-6 text-xl font-bold text-slate-100">
              Key Methodological Decisions
            </h2>
            <div className="grid gap-4 md:grid-cols-2">
              {[
                {
                  title: 'Coastal point selection',
                  body: 'Grid cells are classified as "coastal" if they lie within 50 km of the Natural Earth 10 m coastline (NE shapefile), using a KD-tree in km coordinates. This replaces the previously used minimum-longitude heuristic and is more robust to irregular coastlines and complex bathymetry.',
                },
                {
                  title: 'Separate domain flags',
                  body: 'WAVERYS and GLORYS12 have different horizontal resolutions (~0.2° vs 1/12°) and slightly different ocean masks near the coast. Each municipality is therefore assigned separate flags (in_wave_domain, in_gl_domain) and separate nearest-point assignments, rather than assuming a common coastal mask.',
                },
                {
                  title: 'Municipality ordering',
                  body: 'Municipalities are always displayed in south-to-north order by centroid latitude. This provides a consistent geographic reference across all figures and tables, regardless of the order in which data are loaded or events are counted.',
                },
                {
                  title: 'Exploratory compound thresholds',
                  body: 'The compound co-occurrence analysis in Part G uses empirical q90 thresholds computed from domain-mean distributions. These are intentionally preliminary and will be replaced by physically motivated, location-specific thresholds in the next pipeline phase (threshold calibration).',
                },
              ].map((item) => (
                <div
                  key={item.title}
                  className="rounded-xl border border-slate-800 bg-slate-900 p-5"
                >
                  <h3 className="mb-2 text-xs font-semibold text-sky-400">{item.title}</h3>
                  <p className="text-xs leading-relaxed text-slate-400">{item.body}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Figure gallery */}
        <div className="border-b border-slate-800 bg-[#0a0f1e] py-16">
          <div className="mx-auto max-w-5xl px-6">
            <div className="mb-8">
              <h2 className="text-xl font-bold text-slate-100">Figure Gallery</h2>
              <p className="mt-2 text-sm text-slate-400">
                All figures generated by the analysis pipeline (Parts A–G). Click any figure
                to expand and read the full caption. Filter by analysis group using the tabs.
              </p>
            </div>
            <FigureGallery figures={southScFigures} />
          </div>
        </div>

        {/* Limitations */}
        <div className="border-b border-slate-800 bg-slate-950 py-16">
          <div className="mx-auto max-w-5xl px-6">
            <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-6">
              <div className="flex items-center gap-2 mb-4">
                <svg className="h-4 w-4 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <h2 className="text-base font-bold text-amber-300">Known Limitations</h2>
              </div>
              <ul className="space-y-2">
                {limitations.map((lim, i) => (
                  <li key={i} className="flex items-start gap-2.5 text-sm text-slate-400">
                    <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-amber-500/60" />
                    {lim}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* Next steps */}
        <div className="bg-slate-950 py-16">
          <div className="mx-auto max-w-5xl px-6">
            <div className="rounded-xl border border-sky-500/20 bg-sky-500/5 p-6">
              <h2 className="mb-3 text-base font-bold text-sky-300">Next Steps</h2>
              <ul className="space-y-2">
                {[
                  'Run the full pipeline with complete CMEMS downloads for the entire SC coast (all sectors).',
                  'Calibrate physically motivated extreme thresholds for Hₛ and SSH (POT/GPD approach, validated against Leal et al. 2024).',
                  'Apply compound detection framework using calibrated thresholds and event segmentation.',
                  'Cross-validate compound event catalog with Leal et al. (2024) and S2ID databases.',
                  'Extend to the full Brazilian coastal domain.',
                  'Integrate ERA5 atmospheric data for physical interpretation of compound events.',
                ].map((step, i) => (
                  <li key={i} className="flex items-start gap-2.5 text-sm text-slate-400">
                    <span className="mt-0.5 flex h-4 w-4 flex-shrink-0 items-center justify-center rounded-full border border-sky-500/40 text-xs font-bold text-sky-500">
                      {i + 1}
                    </span>
                    {step}
                  </li>
                ))}
              </ul>
            </div>

            <div className="mt-6 flex items-center justify-between">
              <Link
                href="/"
                className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-slate-200 transition-colors"
              >
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                Back to Overview
              </Link>
              <p className="text-xs text-slate-600">
                Results are preliminary · Not for citation without author consent
              </p>
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </>
  );
}
