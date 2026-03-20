import type { ProjectObjective, TimelinePhase } from '@/lib/types';

export const projectMeta = {
  title: 'Compound Coastal Flooding',
  subtitle: 'Joint Wave–Surge Extremes on the South Atlantic Eastern Coast of Brazil',
  shortTitle: 'OSR11 — Compound Flooding',
  institution: 'Institute of Astronomy, Geophysics and Atmospheric Sciences — IAG-USP',
  authors: [
    'Danilo Couto de Souza',
    'Carolina Barnez Gramcianinov',
    'Ricardo de Camargo',
    'Karine Bastos Leal',
  ],
  status: 'in-progress' as const,
  statusLabel: 'Research in Progress',
  dataRange: '1993–2025',
  region: 'South Atlantic Eastern Coast of Brazil',
  focus: 'Santa Catarina (test domain: southern sector)',
};

export const projectContext = `
Compound coastal flooding events — characterised by the simultaneous or near-simultaneous
occurrence of extreme significant wave heights and elevated sea surface levels associated
with meteorological tides and storm surges — represent a disproportionate share of observed
coastal disasters along the Brazilian coast. Despite the documented socioeconomic impact
of these events, their joint statistical behaviour, physical drivers, and geographic
distribution remain poorly quantified at regional scales.
`;

export const scientificMotivation = `
Isolated extreme wave or surge events already pose severe hazards. When they co-occur,
their compound nature amplifies coastal flooding, erosion, and infrastructure damage
in ways that cannot be captured by single-variable analyses. Characterising compound
events is therefore essential for credible coastal risk assessment, hazard mapping,
and climate-informed adaptation planning.
`;

export const generalObjective = `
Quantify the joint occurrence, intensity, and temporal structure of sea-level extremes
and significant wave height extremes along the eastern coast of Brazil, using multiyear
satellite-era reanalyses (GLORYS12 and WAVERYS), and assess their association with
observed coastal disaster events.
`;

export const specificObjectives: ProjectObjective[] = [
  {
    label: 'Characterise individual extremes',
    description:
      'Establish marginal distributions of significant wave height (Hₛ) and sea surface height (SSH/zos) at nearshore grid points along the Brazilian coast.',
  },
  {
    label: 'Detect compound events',
    description:
      'Identify episodes in which Hₛ and SSH exceed physically motivated thresholds within a defined temporal coincidence window, constituting compound wave–surge events.',
  },
  {
    label: 'Validate against observed impacts',
    description:
      'Compare the detected compound event catalog with the Leal et al. (2024) database of reported coastal disasters in Santa Catarina (1998–2023) and with the S2ID/Atlas Digital national disaster registry.',
  },
  {
    label: 'Spatial risk mapping',
    description:
      'Produce municipality-scale hotspot maps of compound event frequency and intensity along the target coastal sectors.',
  },
  {
    label: 'Integrate exposure and vulnerability',
    description:
      'In a subsequent phase, combine hazard characterisation with exposure (population, built environment) and vulnerability proxies to derive compound coastal risk indicators.',
  },
  {
    label: 'Physical interpretation',
    description:
      'Identify the synoptic and mesoscale atmospheric conditions (ERA5) associated with the most intense compound events, linking hazard statistics to physical drivers.',
  },
];

export const currentScope = `
The current implementation is restricted to the southern sector of Santa Catarina (SC),
using test-domain subsets of GLORYS12 and WAVERYS (~29.4°S to 27.6°S; ~50°W to 48°W).
This constitutes the exploratory and sanity-check phase of the project, aimed at
validating the data pipeline, methodological choices, and analysis framework before
extension to the full Brazilian coastal domain.
`;

export const timelinePhases: TimelinePhase[] = [
  {
    id: 'phase-0',
    label: 'Data Acquisition & Pipeline Setup',
    description: 'Download, organise, and QC CMEMS reanalysis products; build test fixtures; set up analysis environment.',
    status: 'done',
    tasks: [
      'Download WAVERYS (GLOBAL_MULTIYEAR_WAV_001_032) for SC',
      'Download GLORYS12 (GLOBAL_MULTIYEAR_PHY_001_030) for SC',
      'Build test-domain NetCDF subsets (south SC sector)',
      'Convert reported events database to structured CSV',
      'Set up shared configuration and plot styling',
    ],
  },
  {
    id: 'phase-1',
    label: 'Exploratory Analysis — South SC Test Domain',
    description: 'First-look EDA on test data: spatial maps, time series, reported events, municipality–grid association, basic statistics.',
    status: 'in-progress',
    tasks: [
      'Spatial maxima maps (Hₛ and SSH) — Part A ✓',
      'Time series at peak grid points — Part B ✓',
      'Reported events database EDA — Part D ✓',
      'Municipality–grid point association via IBGE API — Part E ✓',
      'Per-sector boxplot figures — Part F ✓',
      'Descriptive statistics, scatterplots, seasonal cycle, compound quick-look — Part G ✓',
    ],
  },
  {
    id: 'phase-2',
    label: 'Threshold Calibration & Storm Catalog',
    description: 'Define physically motivated extreme thresholds; construct event catalogs for Hₛ and SSH separately.',
    status: 'planned',
    tasks: [
      'Evaluate threshold methods (percentile-based, POT/GPD)',
      'Define storm segmentation parameters (duration, separation)',
      'Build individual event catalogs (wave storms, surge events)',
      'Validate against observational records',
    ],
  },
  {
    id: 'phase-3',
    label: 'Compound Event Detection',
    description: 'Apply compound detection framework using calibrated thresholds and validated coincidence windows.',
    status: 'planned',
    tasks: [
      'Define compound event criteria (joint exceedance + time window)',
      'Build compound event catalog',
      'Compute co-occurrence statistics (frequency, duration, intensity)',
      'Generate hotspot maps',
    ],
  },
  {
    id: 'phase-4',
    label: 'Validation Against Reported Disasters',
    description: 'Cross-reference compound event catalog with Leal et al. (2024) and S2ID disaster databases.',
    status: 'planned',
    tasks: [
      'Match event catalog to reported disaster dates',
      'Assess hit rate and false alarm statistics',
      'Identify cases with/without documented impact',
      'Analyse factors driving non-detected events',
    ],
  },
  {
    id: 'phase-5',
    label: 'Extension to Full Brazilian Coastal Domain',
    description: 'Scale validated pipeline to the full target domain using complete CMEMS downloads.',
    status: 'planned',
    tasks: [
      'Download full-domain CMEMS reanalyses',
      'Run compound detection pipeline for all coastal sectors',
      'Produce regional climatology and trend analysis',
      'Generate manuscript-quality figures',
    ],
  },
  {
    id: 'phase-6',
    label: 'Exposure, Vulnerability & Risk Integration',
    description: 'Combine hazard characterisation with exposure and vulnerability data.',
    status: 'planned',
    tasks: [
      'Acquire exposure data (IBGE census, infrastructure)',
      'Construct vulnerability proxies',
      'Compute compound coastal risk indicators',
      'Produce risk maps for target municipalities',
    ],
  },
];
