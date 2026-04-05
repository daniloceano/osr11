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
    id: 'threshold-calibration',
    title: 'Threshold Calibration',
    subtitle: 'Tidal sensitivity (Step 4a) + CSI grid scan (Step 4b) · 91 events · FES2022',
    status: 'done',
    description:
      'Empirical calibration of compound event detection thresholds against the 91-event SC coastal disaster database, in two sub-steps. Step 4a (tidal sensitivity): FES2022 daily-maximum tide is added to GLORYS12 SSH to form SSH_total; detection increases from 22 to 26 events at q90. Step 4b (CSI grid scan): 81 threshold pairs (q50–q90 × q50–q90) are evaluated with a causal window [D-2, D+1 00Z]; the optimal pair is q90/q90 (H=21, M=70, F=1 298, CSI=0.0151, FAR=0.984). The high FAR is structural — compound daily exceedances are ~62× more frequent than reported disasters, likely reflecting under-reporting in the Civil Defense database.',
    rationale:
      'Steps 2 and 3 used a fixed q90 threshold as a conventional starting point. Step 4 asks whether any threshold pair in q50–q90 achieves a better skill score, and whether adding the FES2022 astronomical tide improves detection. The calibrated q90/q90 pair and the SSH_total definition (SSH + FES2022 daily max tide) are carried into Steps 5–9.',
    outputs: [
      'Step 4a: 91 per-event 3-panel figures: Hₛ / SSH / SSH_total (with FES2022 tide overlay)',
      'Step 4a: tab_TS_event_metrics.csv — detection_change per event (maintained/new/lost/neither)',
      'Step 4a: fig_TS_C1–C4 — detection comparison, scatter, sector breakdown, tidal fraction',
      'Step 4b: tab_TC4_metrics_full.csv — CSI, POD, FAR for all 81 threshold pairs',
      'Step 4b: tab_TC4_optimal_pair.csv — q90/q90 optimal pair reference for Step 5',
      'Step 4b: fig_TC4_H1–H3 — CSI, FAR, POD heatmaps over threshold grid',
      'Step 4b: fig_TC4_S1–S5 — ranking scatter, hit/miss, lag distribution, sector POD, peak scatter',
      'Step 4b: fig_TC4_M1–M3 — per-municipality hit rate, miss rate, false alarm heatmaps',
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
