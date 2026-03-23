import type { ResultCard } from '@/lib/types';

export const resultCards: ResultCard[] = [
  {
    id: 'south-sc-eda',
    title: 'Exploratory Analysis — South Santa Catarina',
    subtitle: 'Test-domain EDA: spatial maps, time series, events, statistics',
    status: 'done',
    description:
      'First systematic look at the WAVERYS and GLORYS12 test datasets for the southern sector of Santa Catarina (~29.4°S to 27.6°S). This analysis constitutes the sanity-check and pipeline-validation phase of the project, verifying that data loading, coastal point selection, and analysis routines behave correctly before scaling to the full domain.',
    rationale:
      'The exploratory phase is essential to (1) validate the data pipeline, (2) develop and test methodological choices (e.g., coastal grid selection, municipality–grid association), (3) characterise the statistical properties of Hₛ and SSH in the test domain, and (4) establish a first qualitative link between reanalysis signals and observed coastal disasters before proceeding to a rigorous compound detection framework.',
    outputs: [
      'Spatial maximum maps of Hₛ and SSH over the full 1993–2025 period',
      'Time series at peak-value grid points with event-window highlighting',
      'Reported events EDA: count per municipality, Hₛ/SSH boxplots, monthly seasonality',
      'Municipality–grid association table (IBGE coordinates, nearest WAVERYS/GLORYS cells)',
      'Per-sector boxplot figures (map + Hₛ + SSH by municipality)',
      'Descriptive statistics tables (mean, p75, p90, p99, max)',
      'Scatter plots (Hₛ vs SSH, one per municipality, coloured by year)',
      'Seasonal cycle figures (monthly median ± IQR for Hₛ and SSH)',
      'Compound quick-look: joint exceedances at empirical q90 thresholds',
      'Top compound events time series (per municipality)',
      'Marginal distribution histograms (Hₛ and SSH per municipality)',
    ],
    href: '/results/south-sc',
    parts: ['Part A', 'Part B', 'Part D', 'Part E', 'Part F', 'Part G'],
  },
  {
    id: 'threshold-calibration',
    title: 'Threshold Calibration',
    subtitle: 'q90 visual calibration · Full SC coast · 5 sectors · 91 events',
    status: 'in-progress',
    description:
      'Initial threshold calibration phase using the Leal et al. (2024) reported coastal disaster database, now covering the full Santa Catarina coast (5 sectors, 22 municipalities, 91 events). For each event, the nearest ocean grid point in the unified daily dataset is identified, a q90 threshold is computed from the full 1993–2025 climatological series, and the ±3-day window around the disaster date is inspected for Hₛ and SSH exceedances. MagicA (peaks-over-threshold, event_wise) identifies distinct exceedance episodes. Key finding: only 2 of 91 events show concurrent q90 exceedances — driving the next phase of systematic threshold optimisation.',
    rationale:
      'The threshold choice critically determines the sensitivity and specificity of the compound event catalog. Visual inspection against known disaster dates provides a first assessment of reanalysis signal quality and sets the empirical baseline for systematic hit-rate / CSI optimisation across a threshold grid.',
    outputs: [
      '91 per-event time series figures with MagicA exceedance shading',
      'Consolidated metrics table: raw maxima, normalised maxima, days above threshold, concomitance',
      'Threshold statistics table per municipality (q90, mean, std, p99)',
      'fig_TC_S1 — Normalised Hₛ and SSH maxima per event (grouped bar chart)',
      'fig_TC_S2 — Normalised Hₛ vs SSH scatter, concurrent events highlighted',
      'fig_TC_S3 — Concomitance fraction bar chart per event',
      'fig_TC_S4 — Concomitance heatmap: municipality × event date',
    ],
    href: '/results/threshold-calibration',
  },
  {
    id: 'compound-detection',
    title: 'Compound Event Detection',
    subtitle: 'Joint wave–surge exceedances along the Brazilian coast',
    status: 'planned',
    description:
      'Application of the compound detection framework to the full study domain. Identification of episodes in which both Hₛ and SSH exceed their respective extreme thresholds within the calibrated temporal coincidence window. Statistical characterisation of compound event frequency, intensity, duration, and seasonal distribution.',
    rationale:
      'The compound event catalog is the primary scientific deliverable of the hazard phase and the foundation for validation, risk mapping, and physical interpretation.',
    outputs: [
      'Compound event catalog for the full study domain',
      'Co-occurrence statistics: frequency, intensity, seasonality',
      'Municipal-scale hotspot maps',
      'Comparison of compound vs. individual extreme statistics',
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
