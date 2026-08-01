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
      + 'Step 2e, recalibrated on 2026-07-30 over an extended 121-pair grid scoring the production '
      + 'detector, selects Hₛ=q70 / tide-free zos=q99. Its earlier agreement with Step 2d on q90/q90 '
      + 'is now understood as an artefact of both sweeps stopping at q90. '
      + 'Expected rate anchor = 2.0 detections/municipality/yr (combined positive-event set: 147 events, 27 municipalities).',
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
          '81 threshold pairs (q50–q90 × q50–q90) evaluated with causal window [D-2, D-1, D, D+1 00Z]. Percentile thresholds computed from the full metocean record (1993–2025); validation scan restricted to 1998–2020. Optimal pair: Hₛ=q90, SSH_total=q90 (H=21, M=70, F=1261, CSI=0.0155, FAR=0.984) — on the boundary of the scanned range. High FAR indicates Civil Defense under-reporting. This step is diagnostic and has not been re-run since the detector changed; its result is a historical record, not the calibrated pair.',
        status: 'done',
      },
      {
        id: 'step-2e',
        label: '2e — PU Composite Calibration (Final)',
        description:
          'Threshold sweep using a positive-unlabeled (PU) composite score against the combined positive-event set (expanded 56 + legacy 91 = 147 events, 27 municipalities, 1998–2020), over an 11×11 grid of 121 pairs (q50–q90 plus q95 and q99). Thresholds from full metocean record; validation scan restricted to event-database period. Score balances positive recall (w1=0.30), two-sided deviation from an expected rate of 2.0 detections/municipality/yr (w2=0.60), and soft unmatched penalty (w3=0.10); confidence weights α_E=0.20, α_I=0.50, α_C=0.30. Selected pair q70/q99 (H=28, M=119, U=831, R_pos=0.191, B=0.148, F_soft=420.4, Score=−0.318). Across the 14 sensitivity variants the level percentile q99 is selected in 14 of 14; the wave percentile is not determined by the score, spanning q50–q80 among pairs within 1 % of the optimum.',
        status: 'done',
      },
    ],
  },
  {
    id: 'step-3',
    label: 'STEP 3 — Hazard Characterization',
    description:
      'The central analysis block. Generates independent storm catalogs for Hₛ and sea level '
      + 'at each coastal grid point, then runs the full hazard '
      + 'characterization suite: compound detection, duration/persistence, seasonality, '
      + 'Mann–Kendall trend analysis, POT–GPD extreme value analysis, and Hₛ–zos dependence (τ, ρ, χ, χ̄). '
      + 'The whole step was regenerated on 2026-07-31 on the q70/q99 pair with the HAT-gated detector: '
      + 'Step 3.1 rebuilt the catalogues on tide-free zos in place of SSH_total, and Steps 3.3–3.8 were '
      + 'rerun from those catalogues.',
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
          'POT detection + episode clustering on the full 1993–2025 record at q70 (Hₛ) and q99 (tide-free zos). '
          + '808 coastal grid points, 707,453 Hₛ episodes, 42,455 zos episodes.',
        status: 'done',
      },
      {
        id: 'step-3-2',
        label: '3.2 — Compound Detection',
        description:
          'Temporal overlap of Hₛ and tide-free zos episodes, gated by max(SWL) > HAT → compound events. '
          + 'Union-find grouping, integrated severity over the HAT datum; overlap duration and peak intensity retained as diagnostics.',
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
          + 'for Hₛ, tide-free zos, and compound events.',
        status: 'done',
      },
      {
        id: 'step-3-5',
        label: '3.5 — Trend Analysis',
        description:
          'Mann–Kendall + Sen slope for 8 annual series. '
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
          'Hₛ–zos statistical dependence from compound event pairs: '
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
      + 'Exposure uses weighted resident populations in cumulative 1, 2, 5 and 10 km coastline bands (IBGE Grade Estatística 2022). '
      + 'SVI_Coast_2022 was constructed from 10 IBGE Census variables via PCA for 282 municipalities (0–100); it is social only, with no physical susceptibility layer. '
      + 'Current scope: compound-event frequency and mean integrated severity use fixed anchors of 99 events and 1.0, then are averaged with equal weights. '
      + 'Risk_Hazard = (Hazard_Index_mun · Exposure_Index · Φ(PC1/sd(PC1)))^(1/3), without floor or final Min–Max.',
    status: 'done',
    stepNumber: 4,
    href: '/methodology/hazard-index',
    hrefLabel: 'Read the full Hazard Index methodology',
    subSteps: [
      {
        id: 'step-4-1',
        label: '4.1 — Exposure Spatialization',
        description:
          'Oceanic grid-point hazard metrics converted to shapefile and associated with coastal municipalities via spatial join. '
          + 'The associated grid point with the highest compound_c value is spatially overlaid per municipality.',
        status: 'done',
      },
      {
        id: 'step-4-2',
        label: '4.2 — Social Vulnerability Index (SVI_Coast_2022)',
        description:
          'Ten IBGE Census 2022 variables (pop_house, pop_rent, pop_poverty, pop_agevul, pop_nonwhite, pop_illiterate, '
          + 'pop_nowater, pop_nosewage, pop_nogarbage, pop_nopaving) standardized with StandardScaler, submitted to PCA. '
          + 'The pipeline flips the PC1 sign only if its mean correlation with the inputs is negative; audited in 2026-07-31, that condition never triggered (mean correlation +0.468), so the delivered component is PC1 as extracted. '
          + 'SVI_Coast_2022 is that component rescaled 0–100 by Min–Max and is published as a layer; what enters the risk index is Phi(PC1/sd(PC1)), which has no exact anchors.',
        status: 'done',
      },
      {
        id: 'step-4-3',
        label: '4.3 — Multimetric Hazard & Risk Indices',
        description:
          'Hazard_Index = norm_grid{[norm_grid(compound_count_total) + norm_grid(mean_integrated_severity)] / 2}, '
          + 'using fixed anchors; the transferred Hazard_Index_mun is not rescaled over municipalities. '
          + 'Risk_Hazard = (Hazard_Index_mun × Exposure_Index × Φ(PC1/sd(PC1)))^(1/3), with no floor or final Min–Max. '
          + 'The composite hazard is displayed on the Natural Earth coastline by nearest-grid-point association, a purely cartographic step.',
        status: 'done',
      },
    ],
  },
];

export const conceptualFramework = `
The project is structured around a hazard–exposure–vulnerability–risk framework, following
established practices in multi-hazard coastal risk assessment. The compound hazard component
(wave and surge extremes) is the foundation. Hazard characterization is complete for the full
Brazilian coast (808 grid points, 1993–2025). Population exposure, social vulnerability and
risk integration are complete at municipal scale (282 coastal municipalities): the three
components are combined by geometric mean, which is conjunctive — risk requires a hazard,
people exposed to it, and a susceptibility.

The framework separates two distinct stages. In the calibration stage (Step 2), candidate
Hₛ and sea-level thresholds are selected by matching joint exceedances to reported coastal
disasters within an asymmetric causal/antecedent window [D-2, D-1, D, D+1 00Z] around each
event date — a matching tolerance that accounts for antecedent forcing and the 00:00 UTC daily
snapshot convention, not a property of the compound events themselves. This window is used only
to relate model exceedances to disaster records during threshold selection. The thresholds
(Hₛ=q70, tide-free zos=q99) are empirically established by Step 2e (PU Composite Calibration),
which applies a positive-unlabeled framework against a combined positive-event set (147 events,
27 municipalities) to address systematic under-reporting in the Civil Defense disaster database.

In the detection stage (Step 3), the calibrated thresholds are applied to the full metocean
record (1993–2025). Hₛ and tide-free sea level (GLORYS12 zos at 00:00 UTC) are catalogued as
independent storm episodes at each grid point, and a compound event is defined as an Hₛ episode
and a zos episode that overlap by at least one calendar day at the same grid point (grouped by
union-find), subject to a level gate: the still-water level, SWL = (zos − local mean of zos) +
daily-maximum FES2022 tide, must reach the local Highest Astronomical Tide on at least one day
of the overlap. Audit AUD-01 established why the threshold cannot be applied to SSH_total
directly — a percentile of zos + tide is dominated by tidal phase, so it selects on the lunar
cycle rather than on storm forcing. HAT serves as both the gate and the datum from which
severity is measured, so that the excess is interpretable as distance above the condition that
defines an event. The overlap rule — not the calibration matching window — governs the compound
catalog. Reported coastal disaster records supported threshold selection and calibration; they
are not a separate downstream validation product. The CSI grid scan (Step 2d) served as a
diagnostic exploration and confirmed that classical verification metrics are not suitable under
database incompleteness (FAR=0.984). This approach follows Zscheischler
et al. (2020) and Bekker and Davis (2020), consistent with the physical understanding that wave
generation and surge propagation are driven by the same atmospheric systems at the regional scale.

Exposure is a weighted effective resident (de jure) population from cumulative 1, 2, 5 and 10 km coastline bands, from the IBGE Grade
Estatística 2022; the seasonal population of the resort municipalities is not represented. The
Social Vulnerability Index (SVI_Coast_2022, Lima et al. 2024) integrates 10 IBGE Census 2022
variables via PCA for 282 municipalities and measures social susceptibility only — no physical
susceptibility layer exists in this product. The current risk index is the conjunctive geometric
mean of that vulnerability, the exposure, and a native-grid Hazard_Index constructed from
normalized compound-event frequency and mean integrated severity. The former count-only
repository product and the originally delivered fields are retained for audit.
`;
