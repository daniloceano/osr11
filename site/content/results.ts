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
    id: 'preliminary-compound',
    title: 'Preliminary Compound Event Occurrence Analysis',
    subtitle: 'Joint q90 exceedance inspection · Full SC coast · 5 sectors · 91 events',
    status: 'done',
    description:
      'Preliminary analysis of joint Hₛ and SSH exceedances during the 91 reported coastal disasters in the Leal et al. (2024) Santa Catarina database (5 sectors, 22 municipalities, 1998–2020). For each event, the ±3-day window at the nearest ocean grid point is inspected using a first-pass q90 threshold. MagicA peaks-over-threshold identifies distinct exceedance episodes. Key finding: only 2 of 91 events show concurrent q90 exceedances — a calibration signal that motivates the next step: a systematic threshold grid scan (hit rate / CSI optimisation across q50–q90 combinations).',
    rationale:
      'Before calibrating thresholds formally, it is essential to characterise how the reanalysis signal behaves during known disaster dates. This preliminary occurrence analysis documents the distribution of Hₛ and SSH anomalies during reported events and establishes the empirical baseline for the CSI-based threshold optimisation that follows.',
    outputs: [
      '91 per-event time series figures with MagicA exceedance shading',
      'Consolidated metrics table: raw maxima, normalised maxima, days above threshold, concomitance',
      'Threshold statistics table per municipality (q90, mean, std, p99)',
      'fig_TC_S1 — Normalised Hₛ and SSH maxima per event (grouped bar chart)',
      'fig_TC_S2 — Normalised Hₛ vs SSH scatter, concurrent events highlighted',
      'fig_TC_S3 — Concomitance fraction bar chart per event',
      'fig_TC_S4 — Concomitance heatmap: municipality × event date',
    ],
    href: '/results/preliminary-compound',
  },
  {
    id: 'tidal-sensitivity',
    title: 'Tidal Sensitivity Analysis',
    subtitle: 'SSH vs SSH + FES2022 · Daily resolution · 91 events',
    status: 'done',
    description:
      'Sensitivity test adding FES2022 astronomical tide (via eo-tides) to the GLORYS12 SSH signal to form total sea level (SSH_total = SSH + tide). Compound event detection is compared between SSH-only and SSH_total for all 91 reported SC coastal disasters. Key finding: at daily resolution, adding the tide reduces concurrent detections from 30 to 13 — the q90 threshold shift from the added tidal variance offsets any elevation gain, and no new events are detected. Confirms that hourly resolution is required for a meaningful tidal sensitivity test.',
    rationale:
      'GLORYS12 SSH (zos) is a tidal-residual product. Adding astronomical tides is physically necessary for a realistic total water level. This sensitivity test quantifies how much difference the tidal component makes at the current daily temporal resolution, before deciding whether to include tides in the formal threshold calibration step.',
    outputs: [
      '91 per-event 3-panel figures: Hₛ / SSH / SSH_total (with FES2022 tide overlay)',
      'tab_TS_event_metrics.csv — SSH-only and SSH_total metrics per event with detection_change column',
      'tab_TS_tidal_thresholds.csv — SSH_total q90 thresholds per municipality',
      'fig_TS_C1 — Detection comparison grouped bar chart',
      'fig_TS_C2 — SSH vs SSH_total normalised maxima scatter, coloured by detection change',
      'fig_TS_C3 — Detection change counts by coastal sector',
      'fig_TS_C4 — Tidal fraction of SSH_total max per event',
    ],
    href: '/results/tidal-sensitivity',
  },
  {
    id: 'threshold-calibration',
    title: 'Threshold Calibration (CSI Grid Scan)',
    subtitle: 'q50–q90 × q50–q90 · 81 threshold pairs · causal window [D-2, D+1]',
    status: 'in-progress',
    description:
      'Systematic optimisation of Hₛ and SSH_total (= SSH + FES2022 tide) exceedance thresholds against the 91-event SC coastal disaster database. For each of 81 threshold pair combinations (q50–q90 in steps of 0.05 for both variables), the analysis evaluates hits, misses, and false alarms using an asymmetric causal matching window [D-2, D-1, D, D+1 00Z]. The optimal threshold pair is selected by maximising CSI (Critical Success Index), with FAR (False Alarm Ratio) as tiebreaker.',
    rationale:
      'Steps 2–3 revealed that a fixed q90 threshold captures very few events (2–13 of 91 at concurrent exceedance). A systematic grid scan identifies which threshold pair best balances sensitivity (POD) against specificity (1-FAR), providing an empirically grounded detection framework rather than an arbitrary cut-off. The calibrated thresholds directly determine the event catalogs in Step 5.',
    outputs: [
      'tab_TC4_metrics_full.csv — CSI, POD, FAR for all 81 threshold pairs',
      'tab_TC4_metrics_ranked.csv — ranked by optimal selection hierarchy (CSI → FAR → restrictiveness)',
      'tab_TC4_event_hits_optimal.csv — per-event hit/miss at the optimal threshold pair',
      'tab_TC4_lag_summary.csv — capture lag distribution (D-2 / D-1 / D / D+1)',
      'tab_TC4_optimal_pair.csv — optimal pair reference for Step 5',
      'fig_TC4_H1 — CSI heatmap (Hₛ × SSH_total threshold grid)',
      'fig_TC4_H2 — FAR heatmap',
      'fig_TC4_H3 — POD heatmap',
      'fig_TC4_S1 — Ranking scatter: POD vs FAR (bubble = CSI)',
      'fig_TC4_S2 — Per-event hit/miss bar chart at optimal pair',
      'fig_TC4_S3 — Capture lag distribution',
      'fig_TC4_S4 — POD by coastal sector at optimal pair',
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
