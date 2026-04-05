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
  statusLabel: 'Methodology Development and Exploratory Analysis',
  dataRange: '1993–2025',
  region: 'South Atlantic Eastern Coast of Brazil',
  focus: 'Santa Catarina coast — full domain (5 sectors)',
};

export const projectContext = `
Coastal communities and infrastructure along Brazil's South Atlantic Eastern Coast are increasingly exposed to compound coastal flooding, where meteorological tides (storm surges) coincide with extreme wave events. These compound hazards can amplify inundation, overtopping, erosion, and port disruption, producing severe socioeconomic impacts that are still poorly quantified at regional scale in Brazil. Despite the documented impact of these events, their joint statistical behavior, physical drivers, and geographic distribution remain poorly characterized at regional scales.
`;

export const scientificMotivation = `
Isolated extreme wave or surge events already pose severe hazards. When they co-occur, their compound nature amplifies coastal flooding, erosion, and infrastructure damage in ways that cannot be captured by single-variable analyses. A compound-event framework grounded in validated thresholds and integrated with exposure and vulnerability data is therefore essential for credible coastal risk assessment, hazard mapping, and climate-informed adaptation planning along the Brazilian coast.
`;

export const generalObjective = `
Quantify the joint occurrence, intensity, and temporal structure of sea-level extremes and significant wave height extremes along the eastern coast of Brazil using multiyear CMEMS reanalyses (GLORYS12 and WAVERYS), validate the compound event framework against observed coastal disaster events, and integrate hazard characterization with exposure and vulnerability data to produce coastal risk maps and identify priority hotspots for adaptation planning.
`;

export const specificObjectives: ProjectObjective[] = [
  {
    label: 'Data compilation and quality control',
    description:
      'Compile, harmonize, and quality-check CMEMS oceanographic reanalyses (GLORYS12, WAVERYS), ERA5 atmospheric forcing, and Brazilian coastal disaster databases (S2ID, Atlas Digital, SC Civil Defense).',
  },
  {
    label: 'Threshold calibration and validation',
    description:
      'Calibrate extreme event thresholds for sea level and significant wave height by comparing detected storms with historically reported disasters in Santa Catarina, establishing a pragmatic, empirically validated detection framework.',
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
    label: 'Exposure mapping',
    description:
      'Produce spatial exposure maps of compound event frequency, intensity, and temporal trends along the Brazilian coast.',
  },
  {
    label: 'Vulnerability integration',
    description:
      'Integrate exposure layers with coastal vulnerability data—social indicators (IBGE), physical-territorial variables (Macrodiagnóstico da Zona Costeira e Marinha), and historical damage records—to construct a Vulnerability Index.',
  },
  {
    label: 'Coastal risk mapping',
    description:
      'Generate coastal risk maps by combining hazard, exposure, and vulnerability components, identifying priority hotspots for targeted adaptation measures.',
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
      definition: 'The spatial frequency, intensity, and duration of compound events at coastal locations, quantifying where and when hazards occur.'
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
The current implementation covers the full Santa Catarina (SC) coast, using GLORYS12 and WAVERYS reanalyses interpolated to a common WAVERYS spatial grid (~29.4°S to 26.0°S). Steps 1–3 are complete: (1) exploratory data analysis validating the pipeline and municipality–grid associations; (2) preliminary compound event occurrence analysis inspecting q90 exceedances for all 91 events in the Leal et al. (2024) SC disaster database — 22 of 91 events show concurrent SSH-only exceedances; (3) tidal sensitivity analysis adding FES2022 daily-maximum tide to SSH to form SSH_total — detection increases to 26 of 91 at q90. Step 4 (Threshold Calibration) is in progress: sub-step 4b (CSI grid scan) is complete, identifying q90/q90 as the optimal threshold pair (H=21, M=70, F=1 298, CSI=0.0151); sub-step 4c (false alarm attribution) is planned before advancing to Step 5.
`;

export const timelinePhases: TimelinePhase[] = [
  {
    id: 'data-prep',
    label: 'Data Preparation',
    description: 'Compile, harmonize, and quality-check all datasets. Download CMEMS reanalyses for the SC domain; convert disaster database to structured CSV; set up shared configuration and plot styling.',
    status: 'done',
    stepNumber: 0,
    tasks: [
      'Download WAVERYS (GLOBAL_MULTIYEAR_WAV_001_032) for SC',
      'Download GLORYS12 (GLOBAL_MULTIYEAR_PHY_001_030) for SC',
      'Convert SC reported events database to structured CSV',
      'Set up shared configuration and publication plot style',
    ],
  },
  {
    id: 'step-1',
    label: 'STEP 1 — Exploratory Data Analysis',
    description: 'First-look inspection of WAVERYS and GLORYS12 spatial distributions, temporal variability, and the events database. Coastal grid-point selection and municipality–grid association.',
    status: 'done',
    stepNumber: 1,
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
    id: 'step-2',
    label: 'STEP 2 — Preliminary Compound Event Occurrence Analysis',
    description: 'First-pass inspection of joint Hₛ and SSH exceedances at q90 during the 91 reported SC coastal disasters (full coast, 5 sectors, 22 municipalities). 22 of 91 events show concurrent SSH-only exceedances at q90. Establishes the baseline for formal threshold calibration in Step 4.',
    status: 'done',
    stepNumber: 2,
    tasks: [
      'Per-event ±3-day time-series windows (MagicA POT) — 91 events ✓',
      'q90 thresholds from full 1993–2025 climatological series ✓',
      'Concomitance metrics (Hₛ and SSH joint exceedances) ✓',
      'Cross-event summary figures and metrics table ✓',
      '22 of 91 events show concurrent SSH-only exceedances at q90 ✓',
    ],
  },
  {
    id: 'step-3',
    label: 'STEP 3 — Tidal Sensitivity Analysis',
    description: 'Sub-step 4a of Threshold Calibration. FES2022 astronomical tide (eo-tides, hourly eval.) added to GLORYS12 SSH to form SSH_total = zos(00:00 UTC) + tide(daily max). Detection at q90: 22 → 26 events (+7 new, −3 lost, 19 maintained). Establishes the canonical SSH_total definition reused by Step 4b.',
    status: 'done',
    stepNumber: 3,
    tasks: [
      'FES2022 tide evaluated at hourly resolution, daily max retained ✓',
      'SSH_total = zos(00:00 UTC) + FES2022 tide(daily max) per municipality ✓',
      'Detection at q90: 22 → 26 (+7 new, −3 lost, 19 maintained) ✓',
      'Per-event 3-panel figures (Hₛ / SSH / SSH_total) — 91 events ✓',
      'Summary figures C1–C4 and tidal metrics table ✓',
    ],
  },
  {
    id: 'step-4',
    label: 'STEP 4 — Threshold Calibration',
    description: 'Umbrella calibration step. Sub-step 4b (CSI Grid Scan): 81 threshold pairs evaluated, optimal pair q90/q90 identified. Sub-step 4c (Planned — False Alarm Attribution): cross-reference 1 298 flagged episodes with independent databases to distinguish under-reported events from spurious detections.',
    status: 'in-progress',
    stepNumber: 4,
    tasks: [
      '[4b] CSI grid scan: 81 pairs (q50–q90 × q50–q90) evaluated ✓',
      '[4b] Optimal pair: q90/q90 — H=21, M=70, F=1 298, CSI=0.0151 ✓',
      '[4b] Per-municipality hit/miss/FA heatmaps (M1–M3) ✓',
      '[4b] Capture lag: D (43%), D-1 (33%), D+1 (14%), D-2 (10%) ✓',
      '[4c] False alarm attribution vs S2ID/Atlas Digital — planned',
    ],
  },
  {
    id: 'step-5',
    label: 'STEP 5 — Storm Catalog Generation',
    description: 'Construct independent storm catalogs for sea-level and wave extremes at each coastal grid point using calibrated thresholds (q90/q90 from Step 4b). Apply POT to the full 1993–2025 series; merge consecutive exceedances into discrete storm events; record start, end, duration, peak, and integrated intensity.',
    status: 'planned',
    stepNumber: 5,
    tasks: [
      'Identify Hₛ and SSH_total threshold exceedances at each grid point',
      'Merge consecutive exceedances into discrete storm events',
      'Record start, end, duration, peak, integrated intensity',
      'Save catalogs in structured JSON format',
    ],
  },
  {
    id: 'step-6',
    label: 'STEP 6 — Compound Event Detection',
    description: 'Identify compound events as temporal overlaps between sea-level storms and wave storms.',
    status: 'planned',
    stepNumber: 6,
    tasks: [
      'Compare sea-level and wave storm catalogs at each grid point',
      'Classify compound events based on temporal overlap criterion',
      'Record overlap duration, peak time lag, joint intensity',
      'Compute annual frequency, seasonality, spatial distribution',
    ],
  },
  {
    id: 'step-7',
    label: 'STEP 7 — Exposure Analysis',
    description: 'Quantify compound hazard exposure: frequency, intensity, trends, and recurrence along the SC coast.',
    status: 'planned',
    stepNumber: 7,
    tasks: [
      'Compute mean annual frequency of compound events',
      'Calculate intensity metrics and overlap duration statistics',
      'Estimate temporal trends (linear/non-parametric)',
      'Normalize and combine into Compound Exposure Hazard Index',
    ],
  },
  {
    id: 'step-8',
    label: 'STEP 8 — Vulnerability Analysis',
    description: 'Construct coastal vulnerability index integrating social, physical-territorial, and historical damage layers.',
    status: 'planned',
    stepNumber: 8,
    tasks: [
      'Compile IBGE social indicators (population, income, infrastructure)',
      'Extract Macrodiagnóstico physical-territorial variables',
      'Integrate S2ID/Atlas Digital historical damage records',
      'Standardize and combine into Vulnerability Index',
    ],
  },
  {
    id: 'step-9',
    label: 'STEP 9 — Risk Integration',
    description: 'Produce coastal risk map by combining hazard, exposure, and vulnerability components.',
    status: 'planned',
    stepNumber: 9,
    tasks: [
      'Rescale exposure and vulnerability to [0, 1]',
      'Combine via weighted mean or multiplicative approach',
      'Generate risk classes (Low / Moderate / High / Very High)',
      'Identify priority hotspots and compare with reported impacts',
    ],
  },
  {
    id: 'step-10',
    label: 'Extension to Full Brazilian Coastal Domain',
    description: 'Scale validated pipeline to the complete Brazilian coast using full CMEMS downloads.',
    status: 'planned',
    stepNumber: 10,
    tasks: [
      'Download full-domain CMEMS reanalyses',
      'Run Steps 4–9 pipeline for all coastal sectors',
      'Produce regional climatology and trend analysis',
      'Generate manuscript-quality figures and risk maps',
    ],
  },
];
