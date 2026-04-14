import type { MethodStep } from '@/lib/types';


export const methodologySteps: MethodStep[] = [
  {
    id: 'step-1',
    label: 'STEP 1 — Data Preparation',
    description:
      'Compile, harmonize, and quality-check all datasets. Download CMEMS reanalyses (WAVERYS, GLORYS12), preprocess reported events databases, standardize spatial reference systems and temporal coverage, and generate unified metocean datasets on a common grid.',
    status: 'done',
    stepNumber: 1,
  },
  {
    id: 'step-2',
    label: 'STEP 2 — Threshold Calibration',
    description:
      'Umbrella step that empirically establishes the compound event detection framework. '
      + 'Five sub-steps — all complete: 2a (Exploratory Data Analysis), 2b (Preliminary Compound Analysis), '
      + '2c (Tidal Sensitivity), 2d (CSI Grid Scan, diagnostic), and 2e (PU Composite Calibration, final). '
      + 'Steps 2d and 2e both independently select Hₛ=q90 / SSH_total=q90. '
      + 'B_target_effective = 12 × 27 = 324 ep/yr (combined positive-event set: 147 events, 27 municipalities).',
    status: 'done',
    stepNumber: 2,
    subSteps: [
      {
        id: 'step-2a',
        label: '2a — Exploratory Data Analysis',
        description:
          'First-look inspection of WAVERYS and GLORYS12 spatial distributions, temporal variability, and the events database. Coastal grid-point selection via Natural Earth coastline. Municipality–grid association via IBGE API. Per-sector boxplots, seasonal cycles, and compound quick-look at empirical q90.',
        status: 'done',
      },
      {
        id: 'step-2b',
        label: '2b — Preliminary Compound Analysis',
        description:
          'First-pass inspection of joint Hₛ and SSH (zos) exceedances at q90 during each of the 91 reported coastal disasters in the Leal et al. (2024) SC database (full coast, 5 sectors, 22 municipalities). Per-event ±3-day windows; MagicA peaks-over-threshold; concomitance metrics. 2 of 91 events show concurrent Hₛ + SSH q90 exceedances (South sector, Barra Velha). Baseline for threshold calibration.',
        status: 'done',
      },
      {
        id: 'step-2c',
        label: '2c — Tidal Sensitivity',
        description:
          'FES2022 astronomical tide (eo-tides, hourly evaluation) added to GLORYS12 SSH to form SSH_total = zos(00:00 UTC) + tide(daily max). Detection at q90: 22 → 26 events (+7 new, −3 lost, 19 maintained). Establishes the canonical SSH_total definition.',
        status: 'done',
      },
      {
        id: 'step-2d',
        label: '2d — CSI Grid Scan (Diagnostic)',
        description:
          '81 threshold pairs (q50–q90 × q50–q90) evaluated with causal window [D-2, D-1, D, D+1 00Z]. Percentile thresholds computed from the full metocean record (1993–2025); validation scan restricted to 1998–2020. Optimal pair: Hₛ=q90, SSH_total=q90 (H=21, M=70, F=1261, CSI=0.0155, FAR=0.984). High FAR indicates Civil Defense under-reporting. This step is diagnostic; Step 2e is the final calibration.',
        status: 'done',
      },
      {
        id: 'step-2e',
        label: '2e — PU Composite Calibration (Final)',
        description:
          'Independent threshold sweep using a positive-unlabeled (PU) composite score against the combined positive-event set (expanded 56 + legacy 91 = 147 events, 27 municipalities, 1998–2020). Thresholds from full metocean record; validation scan restricted to event-database period. Score balances positive recall (w1=0.60), operational burden (w2=0.20), and soft unmatched penalty (w3=0.20). Independently confirms q90/q90 (H=35, R_pos=0.238, B=0.428, Score=-3.159). Robust across all 4 sensitivity dimensions: weights, alpha, B_target, and episode gap tolerance.',
        status: 'done',
      },
    ],
  },
  {
    id: 'step-3',
    label: 'STEP 3 — Storm Catalog Generation',
    description:
      'Construct independent storm catalogs for sea-level and wave extremes at each coastal grid point using the calibrated thresholds (q90/q90 from Step 2e). Apply peaks-over-threshold to the full 1993–2025 series; merge consecutive exceedances into discrete storm events; record start, end, duration, peak, and integrated intensity in structured JSON format.',
    status: 'planned',
    stepNumber: 3,
    isCurrent: true,
  },
  {
    id: 'step-4',
    label: 'STEP 4 — Compound Event Detection',
    description:
      'Identify compound events as temporal overlaps between independent sea-level and wave storms from the Step 3 catalogs. Compute co-occurrence statistics: frequency, intensity, duration, peak time lags, and seasonal distribution.',
    status: 'planned',
    stepNumber: 4,
  },
  {
    id: 'step-5',
    label: 'STEP 5 — Exposure Analysis',
    description:
      'Quantify compound hazard exposure along the SC coast: mean annual frequency, intensity metrics, temporal trends, and recurrence estimates. Combine into a Compound Exposure Hazard Index.',
    status: 'planned',
    stepNumber: 5,
  },
  {
    id: 'step-6',
    label: 'STEP 6 — Vulnerability Analysis',
    description:
      'Construct coastal vulnerability index integrating social indicators (IBGE), physical-territorial variables (Macrodiagnóstico da Zona Costeira), and historical damage records (S2ID/Atlas Digital).',
    status: 'planned',
    stepNumber: 6,
  },
  {
    id: 'step-7',
    label: 'STEP 7 — Risk Integration',
    description:
      'Produce coastal risk maps by combining hazard, exposure, and vulnerability components. Generate risk classes (Low / Moderate / High / Very High) and identify priority hotspots for adaptation planning.',
    status: 'planned',
    stepNumber: 7,
  },
  {
    id: 'step-8',
    label: 'STEP 8 — Physical Interpretation (Optional)',
    description:
      'Select the most severe compound events and characterize synoptic conditions using ERA5. Discuss dominant atmospheric mechanisms and assess uncertainties in threshold choices.',
    status: 'planned',
    stepNumber: 8,
  },
];

export const conceptualFramework = `
The project is structured around a hazard–exposure–vulnerability–risk framework, following
established practices in multi-hazard coastal risk assessment. The compound hazard component
(wave and surge extremes) is the primary focus of the current phase. Exposure and vulnerability
integration will follow once the hazard characterisation is validated and scaled to the
full study domain.

The joint exceedance framework defines compound events as episodes in which both Hₛ and
SSH_total (= GLORYS12 SSH + FES2022 astronomical tide, daily maximum) exceed their respective
extreme thresholds within a causal/antecedent matching window. The detection thresholds
(Hₛ=q90, SSH_total=q90) are empirically established by Step 2e (PU Composite Calibration),
which applies a positive-unlabeled framework against a combined positive-event set (147 events,
27 municipalities) to address systematic under-reporting in the Civil Defense disaster database.
The matching window [D-2, D-1, D, D+1 00Z] was established in Steps 2b–2d and is inherited
by Step 2e. The CSI grid scan (Step 2d) served as a diagnostic exploration and confirmed
that classical verification metrics are not suitable under database incompleteness (FAR=0.984).
This approach follows Zscheischler et al. (2020) and Bekker and Davis (2020), consistent with
the physical understanding that wave generation and surge propagation are driven by the same
atmospheric systems at the regional scale.
`;
