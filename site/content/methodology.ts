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
          'First-pass inspection of joint Hₛ and SSH (zos) exceedances at q90 during each of the 91 reported coastal disasters in the Leal et al. (2024) SC database (full coast, 5 sectors, 22 municipalities). Per-event ±3-day windows; MagicA peaks-over-threshold; concomitance metrics. 22 of 91 events (24%) show at least one day of concurrent Hₛ + SSH q90 exceedance, spread across 10 municipalities (Barra Velha, Florianópolis, Navegantes, Itapoá, Bombinhas, and others). Baseline for threshold calibration.',
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
    label: 'STEP 3 — Hazard Characterization',
    description:
      'The central analysis block. Generates independent storm catalogs for Hₛ and SSH_total '
      + 'at each coastal grid point (q90/q90 from Step 2e), then runs the full hazard '
      + 'characterization suite: compound detection, duration/persistence, seasonality, '
      + 'Mann–Kendall trend analysis, POT–GPD extreme value analysis, and Hs–SSH dependence (τ, ρ, χ, χ̄).',
    status: 'done',
    stepNumber: 3,
    isCurrent: false,
    href: '/methodology/compound-detection',
    hrefLabel: 'Read the full compound-detection methodology',
    subSteps: [
      {
        id: 'step-3-1',
        label: '3.1 — Storm Catalogs',
        description:
          'POT detection + episode clustering on the full 1993–2025 record. '
          + '808 coastal grid points, 404k Hₛ storms, 325k SSH_total storms.',
        status: 'done',
      },
      {
        id: 'step-3-2',
        label: '3.2 — Compound Detection',
        description:
          'Temporal overlap of Hₛ/SSH_total storms → compound events. '
          + 'Union-find grouping, overlap duration, peak lag, normalized intensity.',
        status: 'done',
      },
      {
        id: 'step-3-3',
        label: '3.3 — Duration & Persistence',
        description:
          'Per-grid-point persistence statistics: mean/p95/max duration, '
          + 'inter-event times, integrated intensity.',
        status: 'done',
      },
      {
        id: 'step-3-4',
        label: '3.4 — Monthly Seasonality',
        description:
          'Monthly counts, peak month, seasonal split (DJF/MAM/JJA/SON) '
          + 'for Hₛ, SSH_total, and compound events.',
        status: 'done',
      },
      {
        id: 'step-3-5',
        label: '3.5 — Trend Analysis',
        description:
          'Mann–Kendall + Sen slope for 9 annual series. '
          + 'Modified MK (Hamed & Rao 1998) when autocorrelation detected.',
        status: 'done',
      },
      {
        id: 'step-3-6',
        label: '3.6 — Univariate EVA',
        description:
          'POT–GPD on declustered storm peaks. Return levels for '
          + '2, 5, 10, 20, 50 years with delta-method confidence intervals.',
        status: 'done',
      },
      {
        id: 'step-3-7',
        label: '3.7 — Dependence Analysis',
        description:
          'Hs–SSH_total statistical dependence from compound event pairs: '
          + "Kendall's τ, Spearman's ρ, extremal dependence χ and χ̄.",
        status: 'done',
      },
      {
        id: 'step-3-8',
        label: '3.8 — Site Export',
        description:
          'Unified JSON export of all metrics for the results website interactive maps.',
        status: 'done',
      },
    ],
  },
  {
    id: 'step-4',
    label: 'STEP 4 — Exposure, Vulnerability & Risk Integration',
    description:
      'Municipal-scale integration of compound hazard characterization with social vulnerability (Karine Bastos Leal / INPE). '
      + 'Exposure is operationalized through spatial association of oceanic hazard metrics with coastal municipalities. '
      + 'SVI_Coast_2022 was constructed from 10 IBGE Census variables via PCA for 281 municipalities (0–100). '
      + 'Hazard_Index = [norm(compound_c) + norm(mean_overl) + norm(mean_compo)] / 3. '
      + 'Risk_Comp = (SVI/100) × norm(compound_c); Risk_Hazard = (SVI/100) × Hazard_Index.',
    status: 'done',
    stepNumber: 4,
    subSteps: [
      {
        id: 'step-4-1',
        label: '4.1 — Exposure Spatialization',
        description:
          'Oceanic grid-point hazard metrics converted to shapefile and associated with coastal municipalities via spatial join. '
          + 'The nearest grid point with the highest compound_c value is spatially overlaid per municipality.',
        status: 'done',
      },
      {
        id: 'step-4-2',
        label: '4.2 — Social Vulnerability Index (SVI_Coast_2022)',
        description:
          'Ten IBGE Census 2022 variables (pop_house, pop_rent, pop_poverty, pop_agevul, pop_nonwhite, pop_illiterate, '
          + 'pop_nowater, pop_nosewage, pop_nogarbage, pop_nopaving) standardized with StandardScaler, submitted to PCA. '
          + 'PC1 sign adjusted so higher values = higher vulnerability. Normalized 0–100.',
        status: 'done',
      },
      {
        id: 'step-4-3',
        label: '4.3 — Hazard Index & Risk Indices',
        description:
          'Hazard_Index = mean of norm(compound_c), norm(mean_overl), norm(mean_compo). '
          + 'Risk_Comp = (SVI/100) × norm(compound_c). Risk_Hazard = (SVI/100) × Hazard_Index.',
        status: 'done',
      },
    ],
  },
  {
    id: 'step-5',
    label: 'STEP 5 — Physical Interpretation (Optional)',
    description:
      'Select the most severe compound events and characterize synoptic conditions using ERA5. Discuss dominant atmospheric mechanisms and assess uncertainties.',
    status: 'planned',
    stepNumber: 5,
  },
];

export const conceptualFramework = `
The project is structured around a hazard–exposure–vulnerability–risk framework, following
established practices in multi-hazard coastal risk assessment. The compound hazard component
(wave and surge extremes) is the foundation. Hazard characterization is complete for the full
Brazilian coast (808 grid points, 1993–2025). Exposure spatialization, social vulnerability,
and risk integration are complete at municipal scale (281 coastal municipalities).

The framework separates two distinct stages. In the calibration stage (Step 2), candidate
Hₛ and SSH_total thresholds are selected by matching joint exceedances to reported coastal
disasters within an asymmetric causal/antecedent window [D-2, D-1, D, D+1 00Z] around each
event date — a matching tolerance that accounts for antecedent forcing and the 00:00 UTC daily
snapshot convention, not a property of the compound events themselves. This window is used only
to relate model exceedances to disaster records during threshold selection. The thresholds
(Hₛ=q90, SSH_total=q90) are empirically established by Step 2e (PU Composite Calibration),
which applies a positive-unlabeled framework against a combined positive-event set (147 events,
27 municipalities) to address systematic under-reporting in the Civil Defense disaster database.

In the detection stage (Step 3), the calibrated thresholds are applied to the full metocean
record (1993–2025). Hₛ and SSH_total (= GLORYS12 SSH + FES2022 astronomical tide, daily maximum)
are catalogued as independent storm episodes at each grid point, and a compound event is defined
as an Hₛ episode and an SSH_total episode that overlap by at least one calendar day at the same
grid point (grouped by union-find). The overlap rule — not the calibration matching window —
governs the compound catalog. Reported coastal disaster records supported threshold selection
and calibration; they are not a separate downstream validation product. The CSI grid scan
(Step 2d) served as a diagnostic exploration and confirmed that classical verification metrics
are not suitable under database incompleteness (FAR=0.984). This approach follows Zscheischler
et al. (2020) and Bekker and Davis (2020), consistent with the physical understanding that wave
generation and surge propagation are driven by the same atmospheric systems at the regional scale.

Exposure is operationalized through spatial association of oceanic hazard metrics with coastal
municipalities. The Social Vulnerability Index (SVI_Coast_2022, Lima et al. 2024) integrates
10 IBGE Census 2022 variables via PCA for 281 municipalities. Risk indices (Risk_Comp and
Risk_Hazard) combine SVI with compound-event frequency and Hazard_Index.
`;
