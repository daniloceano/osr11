import type { FigureItem } from '@/lib/types';

export const southScFigures: FigureItem[] = [
  // Part A — Spatial Maxima Maps
  {
    filename: 'fig_A1a_spatial_max_Hs_event.png',
    title: 'Period-Maximum Significant Wave Height',
    caption:
      'Spatial distribution of the period-maximum significant wave height (Hₛ, m) over the test domain (southern SC, 1993–2025). Values represent the single highest Hₛ recorded at each WAVERYS grid point over the full record. Warm colours indicate higher peak values. Coastal grid points (within 50 km of the Natural Earth coastline) are shown; open ocean points are masked.',
    group: 'Spatial Maxima',
    part: 'Part A',
  },
  {
    filename: 'fig_A1b_spatial_max_SSH_event.png',
    title: 'Period-Maximum Sea Surface Height',
    caption:
      'Spatial distribution of the period-maximum sea surface height above geoid (SSH / zos, m) over the test domain (southern SC, 1993–2025). Values represent the highest daily SSH at each GLORYS12 grid point over the full record. Blue–green colourmap; high values indicate episodes of significant positive sea-level anomaly, associated with storm surge and wave setup contributions.',
    group: 'Spatial Maxima',
    part: 'Part A',
  },
  // Part B — Time Series
  {
    filename: 'fig_B1_timeseries_at_maxima.png',
    title: 'Time Series at Peak-Value Grid Points',
    caption:
      'Four-panel time series centred on the date of the period-maximum Hₛ (top two panels) and SSH (bottom two panels) at their respective peak grid points. Each panel shows a ±15-day window. Red vertical line marks the peak event date. This figure illustrates the temporal co-occurrence of wave and surge signals and provides a first qualitative look at the atmospheric event associated with the extreme values.',
    group: 'Time Series',
    part: 'Part B',
  },
  // Part D — Reported Events
  {
    filename: 'fig_D1_events_by_municipality.png',
    title: 'Reported Coastal Events by Municipality',
    caption:
      'Number of coastal disaster events reported by municipality in the Leal et al. (2024) database for the test domain (south SC sector, 1998–2023). Bars are colour-coded by municipality. This figure establishes the spatial distribution of historically documented impacts, providing context for the subsequent comparison with the reanalysis-derived compound event catalog.',
    group: 'Reported Events',
    part: 'Part D',
  },
  {
    filename: 'fig_D2_Hs_SSH_boxplot_by_municipality.png',
    title: 'Hₛ and SSH at Event Dates — by Municipality',
    caption:
      'Side-by-side boxplots of (left) significant wave height and (right) sea surface height extracted from WAVERYS and GLORYS12 at the dates of reported coastal events in the Leal et al. (2024) database, disaggregated by municipality. The WAVERYS Hₛ values correspond to the nearest coastal grid point; SSH is extracted from GLORYS12 at the nearest ocean cell. This figure provides a first-order assessment of reanalysis signal at observed disaster dates.',
    group: 'Reported Events',
    part: 'Part D',
  },
  {
    filename: 'fig_D4_monthly_seasonality.png',
    title: 'Monthly Seasonality of Reported Events',
    caption:
      'Monthly distribution of reported coastal disaster events in the Leal et al. (2024) database for the south SC sector. The bar chart reveals the seasonal concentration of impactful events, which reflects the seasonal cycle of both wave climate (stronger austral winter swells) and synoptic activity (higher frequency of cold fronts and extratropical cyclones in austral autumn–winter).',
    group: 'Reported Events',
    part: 'Part D',
  },
  // Part F — Sector Figure
  {
    filename: 'fig_F_South_sector.png',
    title: 'South Sector Overview: Map, Hₛ and SSH Boxplots',
    caption:
      'Three-panel sector figure for the south Santa Catarina coastal sector. Left panel: geographic map with municipality centroids (coloured points), nearest WAVERYS and GLORYS12 coastal grid points, and the test-domain bounding box. Centre panel: Hₛ distribution per municipality (boxplots, ordered south to north by latitude). Right panel: SSH distribution per municipality. This figure synthesises the spatial configuration of the analysis and the distributional properties of both hazard variables at each municipality.',
    group: 'Sector Overview',
    part: 'Part F',
  },
  // Part G — Statistics
  {
    filename: 'fig_G2_scatter_Hs_SSH_per_municipality.png',
    title: 'Hₛ vs SSH Scatter — by Municipality',
    caption:
      'Scatterplots of daily significant wave height (Hₛ) versus sea surface height (SSH) at the nearest coastal grid point for each municipality in the test domain, coloured by year. Points are drawn at the nearest paired WAVERYS–GLORYS12 time steps (WAVERYS resampled to daily). The scatter reveals the degree of linear and non-linear association between wave and surge signals at each location.',
    group: 'Statistics',
    part: 'Part G',
  },
  {
    filename: 'fig_G3a_seasonal_cycle_Hs_per_municipality.png',
    title: 'Seasonal Cycle of Hₛ — by Municipality',
    caption:
      'Monthly median (solid line) and interquartile range (shading) of significant wave height (Hₛ) at each municipality in the test domain, computed from the full 1993–2025 record. The seasonal cycle reflects the dominance of austral autumn–winter swells and cold front passages, with a secondary signal from tropical systems in austral summer.',
    group: 'Statistics',
    part: 'Part G',
  },
  {
    filename: 'fig_G3b_seasonal_cycle_SSH_per_municipality.png',
    title: 'Seasonal Cycle of SSH — by Municipality',
    caption:
      'Monthly median (solid line) and interquartile range (shading) of sea surface height (SSH / zos) at each municipality in the test domain. The seasonal SSH cycle integrates contributions from steric sea level, wind-driven setup, and regional oceanographic variability.',
    group: 'Statistics',
    part: 'Part G',
  },
  {
    filename: 'fig_G4_compound_quicklook_per_municipality.png',
    title: 'Compound Co-occurrence Quick-Look — by Municipality',
    caption:
      'Exploratory compound co-occurrence figure for each municipality, using empirical q90 thresholds (computed from the domain-mean distributions). Points above both threshold lines indicate potential compound events under this exploratory definition. Note: these thresholds are preliminary and will be replaced by physically motivated estimates in the threshold calibration phase.',
    group: 'Statistics',
    part: 'Part G',
  },
  {
    filename: 'fig_G5_timeseries_compound_araranguá.png',
    title: 'Top Compound Events — Araranguá',
    caption:
      'Two-panel time series of the highest-ranking compound events (by joint Hₛ + SSH exceedance) at the nearest coastal grid point to Araranguá. Upper panel: Hₛ time series with threshold marker. Lower panel: SSH time series with threshold marker. Compound event windows are highlighted. This figure illustrates the temporal co-occurrence structure of compound episodes at this municipality.',
    group: 'Compound Events',
    part: 'Part G',
  },
  {
    filename: 'fig_G5_timeseries_compound_balneário_rincão.png',
    title: 'Top Compound Events — Balneário Rincão',
    caption:
      'Top compound events time series at the coastal grid point nearest to Balneário Rincão. Format as above.',
    group: 'Compound Events',
    part: 'Part G',
  },
  {
    filename: 'fig_G5_timeseries_compound_balneário_gaivota.png',
    title: 'Top Compound Events — Balneário Gaivota',
    caption:
      'Top compound events time series at the coastal grid point nearest to Balneário Gaivota. Format as above.',
    group: 'Compound Events',
    part: 'Part G',
  },
  {
    filename: 'fig_G5_timeseries_compound_balneário_arroio_do_silva.png',
    title: 'Top Compound Events — Balneário Arroio do Silva',
    caption:
      'Top compound events time series at the coastal grid point nearest to Balneário Arroio do Silva. Format as above.',
    group: 'Compound Events',
    part: 'Part G',
  },
  {
    filename: 'fig_G5_timeseries_compound_garopaba.png',
    title: 'Top Compound Events — Garopaba',
    caption:
      'Top compound events time series at the coastal grid point nearest to Garopaba. Format as above.',
    group: 'Compound Events',
    part: 'Part G',
  },
  {
    filename: 'fig_G5_timeseries_compound_passo_de_torres.png',
    title: 'Top Compound Events — Passo de Torres',
    caption:
      'Top compound events time series at the coastal grid point nearest to Passo de Torres. Format as above.',
    group: 'Compound Events',
    part: 'Part G',
  },
  {
    filename: 'fig_G6a_distributions_Hs_per_municipality.png',
    title: 'Marginal Distribution of Hₛ — by Municipality',
    caption:
      'Histograms of significant wave height (Hₛ) at the nearest coastal grid point for each municipality in the test domain, computed from the full 1993–2025 daily record. The right-skewed distributions reflect the asymmetric wave climate, with a dominant swell regime and infrequent but intense storm events.',
    group: 'Statistics',
    part: 'Part G',
  },
  {
    filename: 'fig_G6b_distributions_SSH_per_municipality.png',
    title: 'Marginal Distribution of SSH — by Municipality',
    caption:
      'Histograms of sea surface height (SSH / zos) at the nearest coastal grid point for each municipality in the test domain, computed from the full 1993–2025 daily record. SSH distributions are more symmetric than Hₛ, reflecting the combined steric and dynamic sea-level variability captured by GLORYS12.',
    group: 'Statistics',
    part: 'Part G',
  },
];

export const figureGroups = [
  'Spatial Maxima',
  'Time Series',
  'Sector Overview',
  'Reported Events',
  'Statistics',
  'Compound Events',
];
