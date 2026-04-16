import type { ResultCard } from '@/lib/types';

export const resultCards: ResultCard[] = [
  {
    id: 'threshold-calibration',
    title: 'Step 2 — Threshold Calibration',
    subtitle: 'Empirical detection framework · EDA · Preliminary · Tidal sensitivity · CSI scan · PU calibration',
    status: 'done',
    description:
      'Umbrella step that empirically establishes the compound event detection framework. All five sub-steps completed: (2a) Exploratory Data Analysis validates the pipeline and municipality–grid associations; (2b) Preliminary Compound Analysis inspects q90 exceedances for all 91 events; (2c) Tidal Sensitivity adds FES2022 tide to form SSH_total; (2d) CSI Grid Scan (diagnostic) identifies optimal pair q90/q90 using the 91-event legacy database; (2e) PU Composite Calibration (final) independently confirms q90/q90 using the combined expanded (56) + legacy (91) = 147-event positive-event set and a PU composite score. Both methods converge on q90/q90, robust to database and methodology choices.',
    rationale:
      'Before detecting compound events at scale, thresholds must be calibrated against observed coastal disasters. This two-stage approach (Step 2d diagnostic + Step 2e final) distinguishes between methodological choices and provides independent confirmation of the q90/q90 threshold pair, accounting for systematic under-reporting in the Civil Defense database.',
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
      '2e: PU composite score (R_pos, burden, soft penalty) for 81 pairs using combined 147-event set',
      '2e: Independent confirmation q90/q90 (H=35, R_pos=0.238, B=0.428, Score=-3.159, B_target_effective=324 ep/yr)',
      '2e: Sensitivity analyses (weights, alpha, B_target, gap_days — all stable at q90/q90)',
      '2e: Confidence weight distribution and unmatched episode audit',
    ],
    href: '/results/threshold-calibration',
    parts: ['2a — EDA', '2b — Preliminary', '2c — Tidal', '2d — CSI Scan', '2e — PU Calibration'],
  },
  {
    id: 'hazard-characterization',
    title: 'Step 3 — Hazard Characterization',
    subtitle: '808 grid points · storm catalogs + 7 analysis submodules · 1993–2025',
    status: 'in-progress',
    description:
      'Central analysis block: independent storm catalogs for Hₛ and SSH_total (q90/q90), '
      + 'followed by compound detection, duration/persistence, monthly seasonality, '
      + 'Mann–Kendall trends, POT–GPD EVA, and Hs–SSH dependence (τ, ρ, χ, χ̄). '
      + '404k Hₛ storms, 325k SSH_total storms, ~96k compound events across 808 coastal grid points.',
    rationale:
      'The storm catalogs are the foundation for all downstream hazard characterization. '
      + 'The submodule suite quantifies frequency, intensity, seasonality, trends, return levels, '
      + 'and dependence — providing a complete statistical portrait of compound coastal hazards.',
    outputs: [
      '3.1: 404,535 Hₛ + 324,929 SSH_total storm episodes (JSON + CSV)',
      '3.2: ~96k compound events, classification (Hₛ-only / SSH-only / compound), overlap metrics',
      '3.3: Per-grid persistence statistics (mean/p95/max duration, inter-event times)',
      '3.4: Monthly climatology, peak month, seasonal DJF/MAM/JJA/SON split',
      '3.5: Mann–Kendall + Sen slope trends for 9 annual series per grid point',
      '3.6: POT–GPD return levels (2, 5, 10, 20, 50 yr) with delta-method CIs',
      '3.7: Kendall τ, Spearman ρ, extremal χ and χ̄ for Hs–SSH compound pairs',
      '3.8: Unified JSON for interactive maps on the results website',
    ],
    href: '/results/storm-maps',
    parts: [
      '3.1 — Storm Catalogs',
      '3.2 — Compound Detection',
      '3.3 — Duration & Persistence',
      '3.4 — Seasonality',
      '3.5 — Trends',
      '3.6 — EVA',
      '3.7 — Dependence',
      '3.8 — Site Export',
    ],
  },
  {
    id: 'validation',
    title: 'Validation Against Observed Disasters',
    subtitle: 'Cross-referencing compound events with Leal et al. (2024) and S2ID',
    status: 'planned',
    description:
      'Systematic cross-referencing of the compound event catalog with the Leal et al. (2024) Santa Catarina coastal disaster database and the national S2ID registry. Assessment of detection rates, false alarms, and temporal alignment between modelled events and reported impacts.',
    rationale:
      'Validation against independent observational records is critical to establish the physical credibility of the detected compound events and to identify systematic biases in the reanalysis representation of nearshore conditions.',
    outputs: [
      'Event-by-event match table (catalog vs. reported disasters)',
      'Detection statistics (hit rate, miss rate, false alarm rate)',
      'Case studies of high-impact missed or captured events',
    ],
  },
  {
    id: 'risk-integration',
    title: 'Exposure, Vulnerability & Risk Integration',
    subtitle: 'From hazard to compound coastal risk indicators',
    status: 'planned',
    description:
      'Integration of compound hazard characterisation with municipal-scale exposure data (population, infrastructure) and social vulnerability proxies. Production of compound coastal risk indicators and hotspot maps suitable for adaptation planning and policy communication.',
    rationale:
      'The hazard alone is insufficient for risk assessment. Combining frequency and intensity of compound events with information about who and what is exposed, and how resilient they are, transforms hazard maps into actionable risk products.',
    outputs: [
      'Exposure dataset for coastal municipalities',
      'Vulnerability index (TBD)',
      'Compound coastal risk maps',
      'Municipal risk ranking',
    ],
  },
];
