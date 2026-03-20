import type { DataSource } from '@/lib/types';

export const dataSources: DataSource[] = [
  {
    id: 'waverys',
    name: 'WAVERYS — Global Ocean Waves Reanalysis',
    shortName: 'WAVERYS',
    description:
      'Multiyear ocean wave reanalysis produced by Copernicus Marine Service (CMEMS). Provides spectral wave parameters derived from the WaveWatch III model, assimilating satellite altimetry observations.',
    variables: [
      'VHM0 — Significant wave height (m)',
      'VMDR — Mean wave direction (°)',
    ],
    resolution: '~0.2° spatial, 3-hourly temporal',
    period: '1993–2025',
    role: 'Primary source for wave extreme characterisation and compound event detection.',
    stage: 'Data acquisition and exploratory analysis (Phases 0–1)',
    status: 'done',
  },
  {
    id: 'glorys',
    name: 'GLORYS12 — Global Ocean Physics Reanalysis',
    shortName: 'GLORYS12',
    description:
      'High-resolution global ocean physics reanalysis (1/12°) from Copernicus Marine Service. Assimilates satellite altimetry, sea surface temperature, and in-situ observations into the NEMO ocean model.',
    variables: [
      'zos — Sea surface height above geoid (m)',
    ],
    resolution: '1/12° (~9 km) spatial, daily temporal',
    period: '1993–2025',
    role: 'Primary source for sea-level extreme characterisation, including storm surge and meteorological tide signals.',
    stage: 'Data acquisition and exploratory analysis (Phases 0–1)',
    status: 'done',
  },
  {
    id: 'era5',
    name: 'ERA5 — ECMWF Reanalysis v5',
    shortName: 'ERA5',
    description:
      'Fifth-generation global atmospheric reanalysis from ECMWF. Hourly estimates of a large number of atmospheric, land, and oceanic climate variables from 1940 to present.',
    variables: [
      'MSLP — Mean sea level pressure (Pa)',
      'u10, v10 — 10 m wind components (m/s)',
      'SST — Sea surface temperature (K)',
      'Geopotential and wind at pressure levels',
    ],
    resolution: '~31 km (~0.25°) spatial, hourly temporal',
    period: '1993–2025',
    role: 'Physical interpretation of compound events; synoptic and mesoscale meteorological context for extreme episodes.',
    stage: 'Physical interpretation phase (Phase 5+)',
    status: 'planned',
  },
  {
    id: 'reported-events',
    name: 'SC Civil Defense Coastal Disaster Database',
    shortName: 'Leal et al. (2024)',
    description:
      'Coastal disaster database for Santa Catarina state, Brazil, compiled by Leal et al. (2024) from Civil Defense records. Contains 105 reported coastal events (1998–2023) with event dates, affected municipalities, and observed wave/damage information. Critical for threshold calibration and validation.',
    variables: [
      'Event date and municipality',
      'Reported significant wave height (where available)',
      'Damage type and severity indicators',
      'Coastal sector classification',
    ],
    resolution: 'Event-level (point-in-time), municipality resolution',
    period: '1998–2023',
    role: 'Threshold calibration: validate extreme thresholds by maximizing correspondence with reported events. Pragmatic validation strategy acknowledging regional bias when extrapolated.',
    stage: 'Exploratory analysis (Step 1), Threshold calibration (Step 2), Validation (Step 4)',
    status: 'done',
  },
  {
    id: 's2id',
    name: 'S2ID / Atlas Digital de Desastres do Brasil',
    shortName: 'S2ID / Atlas Digital',
    description:
      'National disaster registry maintained by the Brazilian Federal Government. Covers officially declared disaster events across Brazil, including coastal and hydrological disasters, with municipal-level socioeconomic impact data. Reporting is incomplete and uneven across regions—serves as minimum-estimate indicator.',
    variables: [
      'Disaster type and date',
      'Affected municipalities',
      'Material damages and economic losses (where reported)',
      'Affected population counts (where reported)',
    ],
    resolution: 'Event-level, municipal resolution',
    period: '1991–present',
    role: 'Compound event validation; historical damage records as auxiliary sensitivity layer for vulnerability analysis. Acknowledged data quality limitations.',
    stage: 'Validation (Step 4); Vulnerability (Step 6)',
    status: 'planned',
  },
  {
    id: 'macrodiagnostico',
    name: 'Macrodiagnóstico da Zona Costeira e Marinha do Brasil',
    shortName: 'Macrodiagnóstico MMA',
    description:
      'Comprehensive coastal and marine zone assessment by the Brazilian Ministry of Environment (MMA). Provides geomorphological, physical-territorial, and environmental data for the Brazilian coastal zone, including erosion susceptibility, natural barriers, land use, and occupation patterns.',
    variables: [
      'Geomorphological classification',
      'Erosional susceptibility and shoreline retreat rates',
      'Natural coastal barriers (dunes, mangroves, reefs)',
      'Coastal occupation and urbanization patterns',
      'Low-lying terrain and inundation susceptibility',
    ],
    resolution: 'Coastal segments (~1–10 km scale)',
    period: 'Various (current state)',
    role: 'Physical-territorial vulnerability component for risk integration: complements social vulnerability with geophysical and environmental susceptibility.',
    stage: 'Vulnerability analysis (Step 6)',
    status: 'planned',
  },
  {
    id: 'ibge',
    name: 'IBGE — Coastal Municipality Data',
    shortName: 'IBGE',
    description:
      'Brazilian Institute of Geography and Statistics. Provides municipal boundary polygons, centroid coordinates, census data, and socioeconomic indicators. Access via IBGE Localidades and Malhas APIs.',
    variables: [
      'Municipality centroid coordinates',
      'Municipal boundary polygons',
      'Population, density, and demographic data',
      'Income, poverty, and social indicators',
      'Housing, sanitation, and infrastructure quality',
    ],
    resolution: 'Municipal (Brazil administrative unit)',
    period: 'Current (census data ~2010, 2022)',
    role: 'Municipality–grid association for spatial analysis; social vulnerability indicators (population, income, infrastructure) for risk integration.',
    stage: 'Exploratory analysis (Step 1); Vulnerability (Step 6)',
    status: 'planned',
  },
  {
    id: 'natural-earth',
    name: 'Natural Earth 10m Coastline',
    shortName: 'Natural Earth',
    description:
      'Public domain coastline vector dataset at 10 m scale resolution. Used for coastal grid point selection and spatial filtering of reanalysis data to nearshore locations.',
    variables: [
      'Coastline polyline geometry',
    ],
    resolution: '10 m scale (~suitable for features > 10 km)',
    period: 'Current',
    role: 'Coastal grid point identification: filter WAVERYS/GLORYS12 grid cells within 50 km of coastline.',
    stage: 'Data preparation and exploratory analysis (Steps 1–2)',
    status: 'done',
  },
];
