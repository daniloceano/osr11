import type { ResultCard } from '@/lib/types';

export const resultCards: ResultCard[] = [
  {
    id: 'threshold-calibration',
    title: 'Step 2 — Threshold Calibration',
    subtitle: 'Empirical detection framework · EDA · Preliminary · Tidal sensitivity · CSI scan · PU calibration',
    status: 'done',
    description:
      'Umbrella step that empirically establishes the compound event detection framework. All five sub-steps completed: (2a) Exploratory Data Analysis validates the pipeline and municipality–grid associations; (2b) Preliminary Compound Analysis inspects q90 exceedances for all 91 events; (2c) Tidal Sensitivity adds FES2022 tide to form SSH_total; (2d) CSI Grid Scan (diagnostic) identifies optimal pair q90/q90 using the 91-event legacy database; (2e) PU Composite Calibration (final), recalibrated on 2026-07-30 to score the production detector over an extended 11×11 grid, selects q70/q99. The earlier agreement of 2d and 2e on q90/q90 is now understood as an artefact of the grid stopping at q90: extending it showed the old composite score had no interior optimum.',
    rationale:
      'Before detecting compound events at scale, thresholds must be calibrated against observed coastal disasters. This two-stage approach (Step 2d diagnostic + Step 2e final) separates the exploratory verification framework from the final calibration, which uses a positive-unlabeled score to account for systematic under-reporting in the Civil Defense database. The calibrated pair is q70/q99, set by Step 2e on 2026-07-30.',
    outputs: [
      '2a: Spatial maximum maps, time series, municipality–grid association, per-sector boxplots',
      '2a: Seasonal cycles, compound quick-look at empirical q90, marginal distributions',
      '2b: 91 per-event time series figures with MagicA exceedance shading',
      '2b: Consolidated metrics table, threshold statistics, concomitance heatmaps',
      '2c: 91 per-event 3-panel figures (Hₛ / SSH / SSH_total with FES2022 tide overlay)',
      '2c: Detection change analysis (22 → 26 events), tidal fraction metrics',
      '2d: CSI, POD, FAR for all 81 threshold pairs (q50–q90 × q50–q90)',
      '2d: Optimal pair q90/q90 (H=21, M=70, F=1261, CSI=0.0155, diagnostic)',
      '2d: Per-municipality hit/miss/FA heatmaps, capture lag distribution',
      '2e: PU composite score (R_pos, two-sided rate deviation, soft penalty) for 121 pairs using combined 147-event set',
      '2e (recalibrated 2026-07-30): selected pair q70/q99 (H=28 of 147, R_pos=0.191, B=0.148, F_soft=420.4, Score=-0.318) — same recall as q90/q90 with 62% fewer unmatched detections',
      '2e: Sensitivity analyses (weights, alpha, expected rate, gap_days) — the level percentile q99 is selected in 14 of 14 variants; the wave percentile is the poorly determined axis, spanning q50–q80 within 1% of the best score',
      '2e: Confidence weight distribution and unmatched episode audit',
    ],
    href: '/results/threshold-calibration',
    parts: ['2a — EDA', '2b — Preliminary', '2c — Tidal', '2d — CSI Scan', '2e — PU Calibration'],
  },
  {
    id: 'hazard-characterization',
    title: 'Step 3 — Hazard Characterization',
    subtitle: '808 grid points · coastal Hazard Index + 7 analysis submodules · 1993–2025',
    status: 'done',
    description:
      'Central analysis block: compound detection on Hₛ (q70) and tide-free zos (q99) gated by HAT, '
      + 'followed by compound detection, duration/persistence, monthly seasonality, '
      + 'Mann–Kendall trends, POT–GPD EVA, and Hs–SSH dependence (τ, ρ, χ, χ̄). '
      + '404k Hₛ storms, 325k SSH_total storms, ~96k compound events across 808 coastal grid points. '
      + 'The composite Hazard Index and its three components — compound-event frequency (events yr⁻¹), '
      + 'mean overlap duration (days), and mean compound intensity (dimensionless) — are shown directly '
      + 'on the coastline.',
    rationale:
      'The storm catalogs are the foundation for all downstream hazard characterization. '
      + 'The submodule suite quantifies frequency, intensity, seasonality, trends, return levels, '
      + 'and dependence — providing a complete statistical portrait of compound coastal hazards.',
    outputs: [
      '3.1: 404,535 Hₛ + 324,929 SSH_total storm episodes (JSON + CSV)',
      '3.2: ~96k compound events, classification (Hₛ-only / SSH-only / compound), overlap metrics',
      '3.3: Per-grid persistence statistics (mean/p95/max duration, inter-event times)',
      '3.4: Monthly climatology, peak month, seasonal DJF/MAM/JJA/SON split',
      '3.5: Mann–Kendall + Sen slope trends for 8 annual series per grid point',
      '3.6: POT–GPD return levels (2, 5, 10, 20, 50 yr) with delta-method CIs',
      '3.7: Kendall τ, Spearman ρ, extremal χ and χ̄ for Hs–SSH compound pairs',
      '3.8: Unified JSON for interactive maps on the results website',
      'Coastal Hazard Index layers projected onto the Natural Earth 10-m coastline (GeoJSON + metadata)',
    ],
    href: '/results/hazard-characterization',
    parts: [
      '3.1 — Storm Catalogs',
      '3.2 — Compound Detection',
      '3.3 — Duration & Persistence',
      '3.4 — Seasonality',
      '3.5 — Trends',
      '3.6 — EVA',
      '3.7 — Dependence',
      '3.8 — Site Export',
      'Coastal Hazard Index',
    ],
  },
  {
    id: 'exposure',
    title: 'Population Exposure',
    subtitle: 'IBGE Grade Estatística 2022 · 200 m urban / 1 km rural · distance bands from the coastline',
    status: 'done',
    description:
      'Counts the people and the occupied households that live near the coast, between the physical hazard '
      + 'and the integrated risk. Population comes from the IBGE Grade Estatística 2022, a direct totalisation '
      + 'of census microdata over the CNEFE household coordinates rather than a modelled disaggregation. '
      + 'Cells are attributed by centroid to a municipality and to a distance band, in EPSG:5880. '
      + '30.8 million residents fall within 10 km of the coastline, against 37.4 million in the 282 coastal '
      + 'municipalities as a whole. Bands of 1, 2, 5 and 10 km are all published so the criterion can be varied.',
    rationale:
      'The hazard says where compound extremes are frequent, long and intense; the vulnerability index says who '
      + 'would cope badly with them. Neither says how many people are there — without exposure the product is a '
      + 'vulnerability-weighted hazard index, not risk in the IPCC sense. Bringing a population count onto [0,1] '
      + 'is itself a scientific choice: Min–Max is affine, so applied to a count skewed above 7 it leaves nine '
      + 'municipalities in ten below 0.05. The adopted term follows INFORM, pairing a log-scaled count between '
      + 'fixed goalposts with the municipal share, because the count alone favours the metropolitan municipalities '
      + 'and the share alone favours the small entirely-coastal ones.',
    outputs: [
      'municipal_exposure.csv: population and occupied households per municipality for the whole municipality and the ≤1, ≤2, ≤5 and ≤10 km bands',
      'Exposure_Index = √(absolute × relative) — adopted; absolute is log10(pop_10km) between fixed goalposts of 10² and 10⁶ inhabitants',
      'Rejected candidates retained for inspection: minmax(log10), percentile rank, and the degenerate minmax of the raw count',
      'Interactive municipal choropleth with both halves of the term, the raw counts and the coastal share, and hover values in every band',
      'Two exploratory figures: the normalisation comparison, and the risk map with and without exposure',
      'Reproducible acquisition of the 20 grid quadrants covering the coastline, with SHA-256 provenance',
    ],
    href: '/results/exposure',
    parts: ['Grade Estatística', 'Distance bands', 'Absolute half', 'Coastal share', 'Exposure_Index'],
  },
  {
    id: 'risk-integration',
    title: 'Exposure, Vulnerability & Risk Integration',
    subtitle: 'Municipal choropleth · hazard × exposure × vulnerability · geometric, conjunctive',
    status: 'done',
    description:
      'Municipal-scale integration of compound hazard characterization with social vulnerability (Karine Bastos Leal). '
      + 'Exposure is operationalized by associating oceanic hazard metrics with Brazilian coastal municipalities through spatial join: '
      + 'the current Hazard_Index combines normalized compound-event frequency, mean overlap duration, and mean intensity on the native grid. '
      + 'Social vulnerability (SVI_Coast_2022) was constructed via PCA on 10 socioeconomic and infrastructure variables '
      + 'from the 2022 IBGE Census for 281 coastal municipalities, normalized 0–100. '
      + 'The former count-only product and the originally delivered fields are retained for audit and comparison. '
      + 'Risk_Hazard integrates SVI with the multimetric hazard layer to identify priority coastal risk hotspots.',
    rationale:
      'The hazard alone is insufficient for risk assessment. Reported coastal disaster records supported threshold calibration '
      + '(Step 2, q70/q99 selection) but are not a separate downstream validation product. '
      + 'Combining compound-event hazard with municipal-scale exposure spatialization and social vulnerability transforms '
      + 'hazard maps into actionable risk indices for adaptation planning and policy communication. '
      + 'The equal-weight index is compensatory: high frequency can be offset by lower mean duration or intensity.',
    outputs: [
      'SVI_Coast_2022: Social Vulnerability Index (PCA on 10 IBGE Census variables, 281 municipalities, 0–100)',
      'Exposure: spatial join of oceanic compound-event metrics to coastal municipalities',
      'Current Hazard_Index = norm_grid{[norm_grid(frequency) + norm_grid(duration) + norm_grid(intensity)] / 3}',
      'Current Risk_Hazard_raw = (SVI_Coast_2022 / 100) × Hazard_Index',
      'Current Risk_Hazard = norm_municipal(Risk_Hazard_raw), scaled from 0 to 1',
      'Raw stages published alongside the normalized ones: Hazard_Index_raw and Risk_Hazard_raw',
      'Interactive municipal choropleth with raw and normalized stages of every index, popups, discrete legend, statistics, and ranking table',
    ],
    href: '/results/risk-integration',
    parts: ['Hazard Components', 'Hazard Index', 'SVI', 'Risk (raw)', 'Risk Hazard'],
  },
];
