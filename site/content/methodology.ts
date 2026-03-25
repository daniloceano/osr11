import type { MethodStep } from '@/lib/types';

export const methodologySteps: MethodStep[] = [
  {
    id: 'step-1',
    label: 'STEP 1 — Exploratory Data Analysis',
    description: 'First-look inspection of WAVERYS and GLORYS12 spatial distributions, temporal variability, and the events database. Coastal grid-point selection via Natural Earth coastline. Municipality–grid association via IBGE API. Per-sector boxplots, seasonal cycles, and compound quick-look at empirical q90.',
    status: 'done',
  },
  {
    id: 'step-2',
    label: 'STEP 2 — Preliminary Compound Event Occurrence Analysis',
    description: 'First-pass inspection of joint Hₛ and SSH exceedances at q90 during each of the 91 reported coastal disasters in the Leal et al. (2024) SC database. Per-event ±3-day windows; MagicA peaks-over-threshold; concomitance metrics. 30 of 91 events show concurrent exceedances at q90 (full SC coast, 5 sectors, 22 municipalities).',
    status: 'done',
  },
  {
    id: 'step-3',
    label: 'STEP 3 — Tidal Sensitivity Analysis',
    description: 'FES2022 astronomical tide (eo-tides) added to GLORYS12 SSH to form SSH_total = SSH + tide(00:00 UTC). q90 thresholds recomputed for the composite series. Detection comparison: 30 → 13 concurrent events at q90 (17 lost, 0 gained). Per-event figures with hourly tidal rhythm overlay; summary figures C1–C4.',
    status: 'done',
  },
  {
    id: 'step-4',
    label: 'STEP 4 — Threshold Calibration (CSI Grid Scan)',
    description: 'Systematic optimisation of Hₛ and SSH exceedance thresholds by computing hit rate (HR), false-alarm rate (FAR), and Critical Success Index (CSI) for all q50–q90 × q50–q90 combinations against the 91-event SC disaster database. Identifies the threshold pair that maximises CSI and establishes the empirical detection framework.',
    status: 'planned',
    isCurrent: true,
  },
  {
    id: 'step-5',
    label: 'STEP 5 — Storm Catalog Generation',
    description: 'Construct independent storm catalogs for sea-level and wave extremes at each coastal grid point using calibrated thresholds. Record start, end, duration, peak, and integrated intensity in structured JSON format.',
    status: 'planned',
  },
  {
    id: 'step-6',
    label: 'STEP 6 — Compound Event Detection',
    description: 'Identify compound events as temporal overlaps between independent sea-level and wave storms. Compute co-occurrence statistics: frequency, intensity, duration, peak time lags, and seasonal distribution.',
    status: 'planned',
  },
  {
    id: 'step-7',
    label: 'STEP 7 — Exposure Analysis',
    description: 'Quantify compound hazard exposure along the SC coast: mean annual frequency, intensity metrics, temporal trends, and recurrence estimates. Combine into a Compound Exposure Hazard Index.',
    status: 'planned',
  },
  {
    id: 'step-8',
    label: 'STEP 8 — Vulnerability Analysis',
    description: 'Construct coastal vulnerability index integrating social indicators (IBGE), physical-territorial variables (Macrodiagnóstico da Zona Costeira), and historical damage records (S2ID/Atlas Digital).',
    status: 'planned',
  },
  {
    id: 'step-9',
    label: 'STEP 9 — Risk Integration',
    description: 'Produce coastal risk maps by combining hazard, exposure, and vulnerability components. Generate risk classes (Low / Moderate / High / Very High) and identify priority hotspots for adaptation planning.',
    status: 'planned',
  },
  {
    id: 'step-10',
    label: 'Extension to Full Brazilian Coastal Domain',
    description: 'Scale validated pipeline to the complete Brazilian coast using full CMEMS downloads. Produce regional compound event climatology, trend analysis, and manuscript-quality risk maps.',
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
