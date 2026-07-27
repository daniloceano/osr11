import type { ProjectObjective, TimelinePhase } from '@/lib/types';


export const projectMeta = {
  title: 'Compound Flooding Events in the South Atlantic Eastern Coast',
  subtitle: 'The Joint Effect of Meteorological Tides and Extreme Wave Events',
  shortTitle: 'OSR11 — Compound Flooding',
  institution: 'Institute of Astronomy, Geophysics and Atmospheric Sciences — IAG-USP',
  authors: [
    { 
      name: 'Danilo Couto de Souza',
      affiliations: [
        'Institute of Astronomy, Geophysics and Atmospheric Sciences, University of São Paulo (IAG-USP)',
        'IRB(P&D)',
        'Brazilian Center of Risk and Resilience Studies'
      ]
    },
    {
      name: 'Carolina Barnez Gramcianinov',
      affiliations: ['Helmholtz-Zentrum Hereon']
    },
    {
      name: 'Ricardo de Camargo',
      affiliations: ['Institute of Astronomy, Geophysics and Atmospheric Sciences, University of São Paulo (IAG-USP)']
    },
    {
      name: 'Karine Bastos Leal',
      affiliations: ['Instituto Nacional de Pesquisas Espaciais (INPE)']
    },
  ],
  status: 'in-progress' as const,
  statusLabel: 'Hazard Characterization and Municipal Risk Integration Complete — Physical Interpretation Planned',
  dataRange: '1993–2025',
  region: 'South Atlantic Eastern Coast of Brazil',
  focus: 'Full Brazilian coast (808 grid points)',
};

export const projectContext = `
Coastal communities and infrastructure along Brazil's South Atlantic Eastern Coast are increasingly exposed to compound coastal flooding, where meteorological tides (storm surges) coincide with extreme wave events. These compound hazards can amplify inundation, overtopping, erosion, and port disruption, producing severe socioeconomic impacts that are still poorly quantified at regional scale in Brazil. Despite the documented impact of these events, their joint statistical behavior, physical drivers, and geographic distribution remain poorly characterized at regional scales.
`;

export const scientificMotivation = `
Isolated extreme wave or surge events already pose severe hazards. When they co-occur, their compound nature amplifies coastal flooding, erosion, and infrastructure damage in ways that cannot be captured by single-variable analyses. A compound-event framework grounded in validated thresholds and integrated with exposure and vulnerability data is therefore essential for credible coastal risk assessment, hazard mapping, and climate-informed adaptation planning along the Brazilian coast.
`;

export const generalObjective = `
Quantify the joint occurrence, intensity, and temporal structure of sea-level extremes and significant wave height extremes along the eastern coast of Brazil using multiyear CMEMS reanalyses (GLORYS12 and WAVERYS). Reported coastal disaster records support threshold calibration through a CSI grid scan and a PU composite framework. Hazard characterization is integrated with municipal-scale exposure spatialization and social vulnerability to produce compound coastal risk indices and identify priority hotspots for adaptation planning.
`;

export const specificObjectives: ProjectObjective[] = [
  {
    label: 'Data compilation and quality control',
    description:
      'Compile, harmonize, and quality-check CMEMS oceanographic reanalyses (GLORYS12, WAVERYS), ERA5 atmospheric forcing, and Brazilian coastal disaster databases (S2ID, Atlas Digital, SC Civil Defense).',
  },
  {
    label: 'Threshold calibration',
    description:
      'Calibrate extreme event thresholds for sea level and significant wave height using historically reported disasters in Santa Catarina as supporting evidence, establishing an empirically grounded detection framework through CSI grid scan (diagnostic) and PU Composite Calibration (final). Reported disasters support threshold selection, not a separate downstream validation product.',
  },
  {
    label: 'Storm catalog construction',
    description:
      'Construct independent storm catalogs for sea-level extremes and wave extremes, recording event characteristics (start, end, duration, peak intensity, integrated intensity) in structured JSON format.',
  },
  {
    label: 'Compound event detection',
    description:
      'Identify compound wave–surge events based on temporal overlap of independent storms, quantifying co-occurrence statistics, peak time lags, and overlap durations.',
  },
  {
    label: 'Exposure spatialization',
    description:
      'Operationalize exposure through spatial association between oceanic compound-event metrics and Brazilian coastal municipalities. Frequency, mean overlap duration, and mean normalized intensity are combined on the native grid into the current normalized multimetric Hazard Index and then transferred to municipalities.',
  },
  {
    label: 'Social vulnerability index',
    description:
      'Construct a Social Vulnerability Index (SVI_Coast_2022) from 2022 IBGE Census data for 281 coastal municipalities. Variables covering crowding, poverty, age vulnerability, race, literacy, and basic infrastructure are standardized with StandardScaler and submitted to PCA; PC1 (adjusted to increase with vulnerability) is normalized to 0–100.',
  },
  {
    label: 'Coastal risk mapping',
    description:
      'Generate compound coastal risk indices by combining SVI_Coast_2022 with the normalized frequency-duration-intensity Hazard_Index, identifying priority hotspots while preserving the former count-only and originally delivered products for audit.',
  },
  {
    label: 'Physical interpretation',
    description:
      'Characterize the synoptic and mesoscale atmospheric conditions (ERA5) associated with the most severe compound events, linking statistical hazard products to physical drivers.',
  },
];

export const stakeholders = [
  { name: 'Port Authorities', description: 'Risk assessment for port infrastructure and operations' },
  { name: 'Local Governments', description: 'Coastal adaptation planning and emergency preparedness' },
  { name: 'Brazilian Navy', description: 'Maritime operations and coastal zone management' },
  { name: 'Academia', description: 'Compound hazard research and climate services development' },
  { name: 'Civil Protection Agencies', description: 'Early warning systems and disaster risk reduction' },
];

export const conceptualFramework = {
  title: 'Risk Assessment Chain',
  chain: 'COMPOUND HAZARD → EXPOSURE → VULNERABILITY → RISK',
  components: [
    {
      term: 'Compound hazard',
      definition: 'The simultaneous occurrence of sea-level extremes (associated with storm surge and meteorological tides) and extreme wave events, capable of amplifying coastal impacts beyond what isolated extremes would produce.'
    },
    {
      term: 'Exposure',
      definition: 'The spatial association between oceanic compound-event metrics and Brazilian coastal municipalities. In the current risk scope, normalized frequency, mean overlap duration, and mean normalized intensity receive equal weights in a native-grid Hazard Index normalized to 0–1 before transfer to municipalities.'
    },
    {
      term: 'Vulnerability',
      definition: 'The physical susceptibility (geomorphology, land use, natural barriers) and social susceptibility (population, infrastructure, income) of coastal municipalities and sectors.'
    },
    {
      term: 'Risk',
      definition: 'The integration of hazard, exposure, and vulnerability to identify priority hotspots and inform adaptation interventions.'
    }
  ]
};

export const currentScope = `
The current implementation covers the full Brazilian coast — 808 coastal grid points, 1993–2025. Steps 1 (Data Preparation) and 2 (Threshold Calibration) are complete. The q90/q90 threshold pair was empirically calibrated using reported SC coastal disaster records as supporting evidence (CSI scan: CSI=0.0151; PU Composite Calibration: R_pos=0.268, B_target_effective=324 ep/yr). Step 3 (Hazard Characterization) is complete: storm catalogs (404k Hₛ + 325k SSH_total episodes), compound detection (~96k events), and all characterization submodules (duration, seasonality, trends, EVA, dependence) are done for all 808 grid points. Step 4 (Exposure, Vulnerability & Risk Integration) is complete at municipal scale: normalized compound-event frequency, mean overlap duration, and mean normalized intensity receive equal weights in a native-grid Hazard_Index normalized to 0–1 and transferred to municipalities. The raw SVI–hazard product is retained as Risk_Hazard_raw and the published Risk_Hazard is Min–Max normalized to 0–1 across municipalities. The former count-only repository product and the originally delivered fields remain accessible for audit.
`;

export const timelinePhases: TimelinePhase[] = [
  {
    id: 'step-1',
    label: 'STEP 1 — Data Preparation',
    description: 'Compile, harmonize, and quality-check all datasets. Download CMEMS reanalyses for the SC domain; convert disaster database to structured CSV; set up shared configuration and plot styling.',
    status: 'done',
    stepNumber: 1,
    tasks: [
      'Download WAVERYS (GLOBAL_MULTIYEAR_WAV_001_032) for SC ✓',
      'Download GLORYS12 (GLOBAL_MULTIYEAR_PHY_001_030) for SC ✓',
      'Convert SC reported events database to structured CSV ✓',
      'Set up shared configuration and publication plot style ✓',
    ],
  },
  {
    id: 'step-2',
    label: 'STEP 2 — Threshold Calibration',
    description: 'Umbrella calibration step with five sub-steps — all complete. Steps 2a–2d established SSH_total, swept 81 threshold pairs, and diagnostically selected q90/q90. Step 2e (PU Composite Calibration) independently confirmed q90/q90 using the combined positive-event set (expanded 56 + legacy 91 = 147 events, 27 municipalities) and a PU composite score designed for under-reported databases. B_target_effective = 12 × 27 = 324 ep/yr.',
    status: 'done',
    stepNumber: 2,
    tasks: [],
    subSteps: [
      {
        id: 'step-2a',
        label: '2a — Exploratory Data Analysis',
        description: 'First-look inspection of WAVERYS and GLORYS12 spatial distributions, temporal variability, and the events database. Coastal grid-point selection and municipality–grid association.',
        status: 'done',
        tasks: [
          'Spatial maxima maps (Hₛ and SSH) — full SC coast ✓',
          'Time series at peak grid points per sector ✓',
          'Reported events database EDA ✓',
          'Municipality–grid point association via IBGE API ✓',
          'Per-sector boxplots and seasonal cycle ✓',
          'Compound quick-look at empirical q90 ✓',
        ],
      },
      {
        id: 'step-2b',
        label: '2b — Preliminary Compound Analysis',
        description: 'First-pass inspection of joint Hₛ and SSH exceedances at q90 during the 91 reported SC coastal disasters (full coast, 5 sectors, 22 municipalities). 22 of 91 events (24%) show at least one day of concurrent Hₛ and SSH q90 exceedance, across 10 municipalities.',
        status: 'done',
        tasks: [
          'Per-event ±3-day time-series windows (MagicA POT) — 91 events ✓',
          'q90 thresholds from full 1993–2025 climatological series ✓',
          'Concomitance metrics (Hₛ and SSH joint exceedances) ✓',
          'Cross-event summary figures and metrics table ✓',
          '22 of 91 events show concurrent Hₛ and SSH exceedances at q90 ✓',
        ],
      },
      {
        id: 'step-2c',
        label: '2c — Tidal Sensitivity',
        description: 'SSH_total = zos(00:00 UTC) + FES2022 tide(daily max). Detection at q90: 22 → 26 events (+7 new, −3 lost, 19 maintained).',
        status: 'done',
        tasks: [
          'FES2022 tide evaluated at hourly resolution, daily max retained ✓',
          'SSH_total = zos(00:00 UTC) + FES2022 tide(daily max) per municipality ✓',
          'Detection at q90: 22 → 26 (+7 new, −3 lost, 19 maintained) ✓',
          'Per-event 3-panel figures (Hₛ / SSH / SSH_total) — 91 events ✓',
          'Summary figures C1–C4 and tidal metrics table ✓',
        ],
      },
      {
        id: 'step-2d',
        label: '2d — CSI Grid Scan',
        description: '81 threshold pairs (q50–q90 × q50–q90) evaluated. Optimal: Hₛ=q90 / SSH_total=q90 (H=21, M=70, F=1 298, CSI=0.0151).',
        status: 'done',
        tasks: [
          'CSI grid scan: 81 pairs (q50–q90 × q50–q90) evaluated ✓',
          'Optimal pair: q90/q90 — H=21, M=70, F=1 298, CSI=0.0151 ✓',
          'Per-municipality hit/miss/FA heatmaps (M1–M3) ✓',
          'Capture lag: D (43%), D-1 (33%), D+1 (14%), D-2 (10%) ✓',
        ],
      },
      {
        id: 'step-2e',
        label: '2e — PU Composite Calibration',
        description: 'Independent threshold sweep using a PU composite score (R_pos, annual burden, soft unmatched penalty) against the combined positive-event set: expanded (56 events, 14 cities) + legacy (91 events, 22 cities) = 147 unique (municipality, date) pairs across 27 municipalities, 1998–2020. B_target_effective = 12 × 27 = 324 ep/yr. Confirms q90/q90 as the final calibrated threshold pair.',
        status: 'done',
        tasks: [
          'Load combined positive-event set: expanded (56) + legacy (91) = 147 events, 27 municipalities ✓',
          'Export event provenance table (source flags, near-match detection) ✓',
          'Layer 1: event hit/miss scan — 81 pairs × combined set ✓',
          'Layer 2: collect unmatched episode metadata (peak Hₛ, SSH_total, dates) ✓',
          'Build episode audit table: compute Eᵢ, Iᵢ, Cᵢ, qᵢ per episode ✓',
          'Compute PU composite scores for all 81 pairs (B_target_effective = 12 × 27 = 324 ep/yr) ✓',
          'Optimal pair: q90/q90 — confirmed by combined-database PU sweep ✓',
          'Sensitivity analysis: weights, alphas, B_target — all confirm q90/q90 ✓',
          'City/database source audit figure (TC5-A2) ✓',
        ],
      },
    ],
  },
  {
    id: 'step-3',
    label: 'STEP 3 — Hazard Characterization',
    description: 'Storm catalog generation and full hazard characterization suite across the complete Brazilian coast. Applies PU-optimal q90/q90 thresholds to the full 1993–2025 record; 808 coastal grid points.',
    status: 'done',
    stepNumber: 3,
    tasks: [
      '404,535 Hₛ + 324,929 SSH_total storm episodes generated ✓',
      '~96k compound events detected across 808 coastal grid points ✓',
      'Duration, seasonality, Mann–Kendall trends, POT–GPD EVA complete ✓',
      'Hs–SSH dependence (τ, ρ, χ, χ̄) and site-export JSON complete ✓',
    ],
    subSteps: [
      {
        id: 'step-3-1',
        label: '3.1 — Storm Catalogs',
        description: 'POT detection + episode clustering on the full 1993–2025 record. 808 coastal grid points, 404k Hₛ storms, 325k SSH_total storms.',
        status: 'done',
      },
      {
        id: 'step-3-2',
        label: '3.2 — Compound Detection',
        description: 'Temporal overlap of Hₛ/SSH_total storms → ~96k compound events. Union-find grouping, overlap duration, peak lag, normalized intensity.',
        status: 'done',
      },
      {
        id: 'step-3-3',
        label: '3.3 — Duration & Persistence',
        description: 'Per-grid-point persistence statistics: mean/p95/max duration, inter-event times, integrated intensity.',
        status: 'done',
      },
      {
        id: 'step-3-4',
        label: '3.4 — Monthly Seasonality',
        description: 'Monthly counts, peak month, seasonal split (DJF/MAM/JJA/SON) for Hₛ, SSH_total, and compound events.',
        status: 'done',
      },
      {
        id: 'step-3-5',
        label: '3.5 — Trend Analysis',
        description: 'Mann–Kendall + Sen slope for 8 annual series. Modified MK (Hamed & Rao 1998) when autocorrelation detected.',
        status: 'done',
      },
      {
        id: 'step-3-6',
        label: '3.6 — Univariate EVA',
        description: 'POT–GPD on declustered storm peaks. Return levels for 2, 5, 10, 20, 50 years with delta-method confidence intervals.',
        status: 'done',
      },
      {
        id: 'step-3-7',
        label: '3.7 — Dependence Analysis',
        description: "Hs–SSH_total statistical dependence from compound event pairs: Kendall's τ, Spearman's ρ, extremal dependence χ and χ̄.",
        status: 'done',
      },
      {
        id: 'step-3-8',
        label: '3.8 — Site Export',
        description: 'Unified JSON export of all metrics for the results website interactive maps.',
        status: 'done',
      },
    ],
  },
  {
    id: 'step-4',
    label: 'STEP 4 — Exposure, Vulnerability & Risk Integration',
    description: 'Municipal-scale integration of compound hazard characterization with social vulnerability and exposure spatialization. Produces a normalized frequency-duration-intensity Hazard_Index on the native grid, transfers it to municipalities, and combines it with SVI_Coast_2022 to produce Risk_Hazard.',
    status: 'done',
    stepNumber: 4,
    tasks: [
      'SVI_Coast_2022 constructed via PCA on 10 IBGE Census variables (281 municipalities) ✓',
      'Exposure operationalized through spatial join of oceanic hazard metrics to municipalities ✓',
      'Current Hazard_Index = normalized equal-weight mean of native-grid frequency, duration, and intensity components ✓',
      'Current Risk_Hazard_raw = (SVI/100) × Hazard_Index ✓',
      'Current Risk_Hazard = norm(Risk_Hazard_raw), scaled 0–1 ✓',
      'Former count-only and originally delivered legacy fields retained for audit ✓',
    ],
  },
  {
    id: 'step-5',
    label: 'STEP 5 — Physical Interpretation (Optional)',
    description: 'Characterize the synoptic and mesoscale atmospheric conditions (ERA5) associated with the most severe compound events, linking statistical hazard products to physical drivers.',
    status: 'planned',
    stepNumber: 5,
    tasks: [],
  },
];
