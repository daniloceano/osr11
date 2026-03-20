import type { ProjectObjective, TimelinePhase } from '@/lib/types';

export const projectMeta = {
  title: 'Compound Flooding Events in the South Atlantic Eastern Coast',
  subtitle: 'The Joint Effect of Meteorological Tides and Extreme Wave Events',
  shortTitle: 'OSR11 — Compound Flooding',
  institution: 'Institute of Astronomy, Geophysics and Atmospheric Sciences — IAG-USP',
  authors: [
    'Danilo Couto de Souza',
    'Carolina Barnez Gramcianinov',
    'Ricardo de Camargo',
    'Karine Bastos Leal',
  ],
  status: 'in-progress' as const,
  statusLabel: 'Methodology Development and Exploratory Analysis',
  dataRange: '1993–2025',
  region: 'South Atlantic Eastern Coast of Brazil',
  focus: 'Santa Catarina (test domain: southern sector)',
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

export const conceptualFramework = `
The project adopts the standard risk assessment chain:

**COMPOUND HAZARD → EXPOSURE → VULNERABILITY → RISK**

- **Compound hazard:** The simultaneous occurrence of sea-level extremes (associated with storm surge and meteorological tides) and extreme wave events, capable of amplifying coastal impacts beyond what isolated extremes would produce.

- **Exposure:** The spatial frequency, intensity, and duration of compound events at coastal locations, quantifying where and when hazards occur.

- **Vulnerability:** The physical susceptibility (geomorphology, land use, natural barriers) and social susceptibility (population, infrastructure, income) of coastal municipalities and sectors.

- **Risk:** The integration of hazard, exposure, and vulnerability to identify priority hotspots and inform adaptation interventions.
`;

export const currentScope = `
The current implementation is restricted to the southern sector of Santa Catarina (SC), using test-domain subsets of GLORYS12 and WAVERYS (~29.4°S to 27.6°S; ~50°W to 48°W). This constitutes the exploratory and data familiarization phase of the project, aimed at validating the data pipeline, sanity-checking methodological choices, and testing analysis workflows before extension to the full Brazilian coastal domain.

**Important:** The current exploratory analysis (Phase 1) is not the final compound event detection framework. It uses empirical q90 thresholds as placeholders and does not implement the validated threshold calibration or storm-based catalog approach described in the scientific methodology (Steps 2–4).
`;

export const timelinePhases: TimelinePhase[] = [
  {
    id: 'step-1',
    label: 'STEP 1 — Data Preparation',
    description: 'Compile, harmonize, and quality-check all datasets. Standardize spatial and temporal reference systems.',
    status: 'done',
    tasks: [
      'Download WAVERYS (GLOBAL_MULTIYEAR_WAV_001_032) for SC',
      'Download GLORYS12 (GLOBAL_MULTIYEAR_PHY_001_030) for SC',
      'Build test-domain NetCDF subsets (south SC sector)',
      'Convert SC reported events database to structured CSV',
      'Set up shared configuration and plot styling',
    ],
  },
  {
    id: 'step-1b',
    label: 'Exploratory Analysis — South SC Test Domain',
    description: 'Preliminary EDA on test data to validate pipelines and familiarize with datasets. Not the final compound detection framework.',
    status: 'in-progress',
    tasks: [
      'Spatial maxima maps (Hₛ and SSH) — Part A ✓',
      'Time series at peak grid points — Part B ✓',
      'Reported events database EDA — Part D ✓',
      'Municipality–grid point association via IBGE API — Part E ✓',
      'Per-sector boxplot figures — Part F ✓',
      'Descriptive statistics, scatterplots, seasonal cycle, compound quick-look (empirical q90) — Part G ✓',
    ],
  },
  {
    id: 'step-2',
    label: 'STEP 2 — Threshold Calibration',
    description: 'Calibrate extreme thresholds by comparing detected storms with SC Civil Defense reported disasters. Select best-performing threshold combination.',
    status: 'planned',
    tasks: [
      'Define candidate threshold ranges for Hₛ and SSH',
      'For each combination, detect storms in SC and compute matching statistics',
      'Select threshold with maximum hit rate and minimum false alarms',
      'Document pragmatic validation strategy and regional bias',
    ],
  },
  {
    id: 'step-3',
    label: 'STEP 3 — Storm Catalog Generation',
    description: 'Construct independent storm catalogs for sea-level and wave extremes at each coastal grid point.',
    status: 'planned',
    tasks: [
      'Identify threshold exceedances at each grid point',
      'Merge consecutive exceedances into single storm events',
      'Record start, end, duration, peak, integrated intensity',
      'Save catalogs in structured JSON format',
    ],
  },
  {
    id: 'step-4',
    label: 'STEP 4 — Compound Event Detection',
    description: 'Identify compound events as temporal overlaps between sea-level storms and wave storms.',
    status: 'planned',
    tasks: [
      'Compare sea-level and wave storm catalogs at each grid point',
      'Classify compound events based on temporal overlap criterion',
      'Record overlap duration, peak time lag, joint intensity',
      'Compute annual frequency, seasonality, spatial distribution',
    ],
  },
  {
    id: 'step-5',
    label: 'STEP 5 — Exposure Analysis',
    description: 'Quantify compound hazard exposure: frequency, intensity, trends, recurrence.',
    status: 'planned',
    tasks: [
      'Compute mean annual frequency of compound events',
      'Calculate intensity metrics and overlap duration statistics',
      'Estimate temporal trends (linear/non-parametric)',
      'Normalize and combine into Compound Exposure Hazard Index',
    ],
  },
  {
    id: 'step-6',
    label: 'STEP 6 — Vulnerability Analysis',
    description: 'Construct coastal vulnerability index integrating social, physical-territorial, and historical damage layers.',
    status: 'planned',
    tasks: [
      'Compile IBGE social indicators (population, income, infrastructure)',
      'Extract Macrodiagnóstico physical-territorial variables (geomorphology, erosion, barriers)',
      'Integrate S2ID/Atlas Digital historical damage records',
      'Standardize variables and combine into Vulnerability Index',
    ],
  },
  {
    id: 'step-7',
    label: 'STEP 7 — Risk Integration',
    description: 'Produce coastal risk map by combining hazard, exposure, and vulnerability components.',
    status: 'planned',
    tasks: [
      'Rescale exposure and vulnerability to [0, 1]',
      'Combine via weighted mean or multiplicative approach',
      'Generate risk classes (Low / Moderate / High / Very High)',
      'Identify priority hotspots and compare with reported impacts',
    ],
  },
  {
    id: 'step-8',
    label: 'STEP 8 — Physical Interpretation',
    description: 'Optional stage: characterize synoptic conditions of severe events and assess uncertainties.',
    status: 'planned',
    tasks: [
      'Select most severe compound events from catalog',
      'Analyze seasonality and monthly distribution',
      'Characterize ERA5 synoptic patterns (MSLP, winds, circulation)',
      'Discuss dominant mechanisms and uncertainty sources',
    ],
  },
  {
    id: 'step-9',
    label: 'Extension to Full Brazilian Coastal Domain',
    description: 'Scale validated pipeline to complete target domain using full CMEMS downloads.',
    status: 'planned',
    tasks: [
      'Download full-domain CMEMS reanalyses',
      'Run Steps 2–7 pipeline for all coastal sectors',
      'Produce regional climatology and trend analysis',
      'Generate manuscript-quality figures and risk maps',
    ],
  },
];
