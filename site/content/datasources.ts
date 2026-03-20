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
    status: 'in-progress',
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
    status: 'in-progress',
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
    name: 'SC Reported Coastal Events Database',
    shortName: 'Leal et al. (2024)',
    description:
      'Coastal disaster database for Santa Catarina state, Brazil, compiled by Leal et al. (2024) from Civil Defense records and news archives. Contains 105 reported coastal events (1998–2023), with reported wave conditions, damage estimates, and affected municipalities.',
    variables: [
      'Event date and municipality',
      'Reported significant wave height (m)',
      'Wind speed and peak period estimates',
      'Damage type and severity',
    ],
    resolution: 'Event-level (point-in-time), municipality resolution',
    period: '1998–2023',
    role: 'Validation and calibration of compound event detection; ground-truth for hazard-impact association.',
    stage: 'Exploratory analysis (Phase 1), Validation (Phase 4)',
    status: 'in-progress',
  },
  {
    id: 's2id',
    name: 'S2ID / Atlas Digital de Desastres do Brasil',
    shortName: 'S2ID / Atlas Digital',
    description:
      'National disaster registry maintained by the Brazilian Federal Government. Covers officially declared disaster events across Brazil, including coastal and hydrological disasters, with socioeconomic impact data.',
    variables: [
      'Disaster type and date',
      'Affected municipalities',
      'Official damage declarations',
    ],
    resolution: 'Event-level, municipal resolution',
    period: '1991–present',
    role: 'Complementary validation source for compound event catalog; broader spatial coverage than SC regional database.',
    stage: 'Validation phase (Phase 4)',
    status: 'planned',
  },
  {
    id: 'ibge',
    name: 'IBGE — Coastal Municipality Data',
    shortName: 'IBGE',
    description:
      'Brazilian Institute of Geography and Statistics. Provides municipal boundary polygons, centroid coordinates, and demographic/exposure data. Access via IBGE Localidades and Malhas APIs.',
    variables: [
      'Municipality centroid coordinates',
      'Municipal boundary polygons',
      'Population and demographic data (future)',
    ],
    resolution: 'Municipal (Brazil administrative unit)',
    period: 'Current',
    role: 'Municipality–grid association for spatial analysis; future source of exposure data (population, urban extent).',
    stage: 'Exploratory analysis (Phase 1); Exposure (Phase 6)',
    status: 'in-progress',
  },
  {
    id: 'vulnerability',
    name: 'Exposure & Vulnerability Sources (TBD)',
    shortName: 'Exposure / Vulnerability',
    description:
      'Sources for exposure (e.g., IBGE census data, coastal built environment mapping) and social vulnerability indicators to be integrated in the risk phase. Specific datasets to be confirmed.',
    variables: [
      'Population density',
      'Infrastructure and critical assets',
      'Social vulnerability indicators',
    ],
    resolution: 'Municipal to sub-municipal',
    period: 'TBD',
    role: 'Risk integration: combine hazard (compound events) with exposure and vulnerability to produce compound coastal risk indicators.',
    stage: 'Risk integration phase (Phase 6)',
    status: 'planned',
  },
];
