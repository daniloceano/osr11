import type { MethodStep } from '@/lib/types';

export const methodologySteps: MethodStep[] = [
  {
    id: 'step-1',
    label: 'Data Acquisition & Organisation',
    description: 'Download WAVERYS and GLORYS12 from CMEMS; organise into structured directories; build test-domain fixtures for development; convert reported-events database to structured CSV.',
    status: 'done',
  },
  {
    id: 'step-2',
    label: 'Exploratory Data Analysis',
    description: 'First-look inspection of spatial distributions, temporal variability, and events database. Coastal grid point selection via Natural Earth coastline. Municipality–grid association.',
    status: 'in-progress',
    isCurrent: true,
  },
  {
    id: 'step-3',
    label: 'Threshold Calibration & QC',
    description: 'Define physically motivated extreme thresholds for Hₛ and SSH. Evaluate POT (peaks-over-threshold) and percentile-based approaches. Quality control of reanalysis near the coast.',
    status: 'planned',
  },
  {
    id: 'step-4',
    label: 'Storm & Surge Event Cataloging',
    description: 'Apply storm segmentation algorithm to identify discrete wave storm and surge episodes. Validate event timing and intensity against observational records.',
    status: 'planned',
  },
  {
    id: 'step-5',
    label: 'Compound Event Detection',
    description: 'Identify joint exceedances of Hₛ and SSH within a defined temporal coincidence window. Compute co-occurrence statistics: frequency, intensity, duration, and seasonal distribution.',
    status: 'planned',
  },
  {
    id: 'step-6',
    label: 'Validation Against Reported Disasters',
    description: 'Cross-reference compound event catalog with Leal et al. (2024) SC database and S2ID national registry. Assess detection rate and investigate non-detected events.',
    status: 'planned',
  },
  {
    id: 'step-7',
    label: 'ERA5 Physical Interpretation',
    description: 'Characterise synoptic conditions (MSLP, wind, SST) associated with high-intensity compound events. Link hazard statistics to large-scale circulation patterns.',
    status: 'planned',
  },
  {
    id: 'step-8',
    label: 'Regional Scaling',
    description: 'Extend validated pipeline to the full Brazilian coastal domain using complete CMEMS downloads. Produce regional compound event climatology.',
    status: 'planned',
  },
  {
    id: 'step-9',
    label: 'Exposure, Vulnerability & Risk',
    description: 'Integrate hazard characterisation with exposure data (IBGE, infrastructure) and vulnerability proxies to produce compound coastal risk indicators and hotspot maps.',
    status: 'planned',
  },
];

export const conceptualFramework = `
The project is structured around a hazard–exposure–vulnerability–risk framework, following
established practices in multi-hazard coastal risk assessment. The compound hazard component
(wave and surge extremes) is the primary focus of the current phase. Exposure and vulnerability
integration will follow once the hazard characterisation is validated and scaled to the
full study domain.

The joint exceedance framework defines compound events as episodes in which both Hₛ and SSH
exceed their respective extreme thresholds within a temporal coincidence window (currently
set to ±3 days for exploratory purposes, to be calibrated with observational data). This
definition follows Zscheischler et al. (2020) and is consistent with the physical
understanding that wave generation and surge propagation are driven by the same atmospheric
systems at the regional scale.
`;
