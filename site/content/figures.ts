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

// ── Step 2e — PU Composite Calibration figures ────────────────────────────────
// Source: outputs/threshold_calibration/figures/summary/fig_TC5_*.png
// Subdir: site/public/figures/tc5_summary/
//
// These figures are from the PU Composite Calibration (Step 2e), which performs
// an independent threshold sweep using a composite score that treats unmatched
// detected episodes as unlabeled rather than automatically as false alarms.
// The calibration uses the COMBINED positive-event set:
//   expanded (56 events, 14 cities) + legacy (91 events, 22 cities)
//   = 147 unique (municipality, date) pairs, 27 municipalities, 1998–2020.
// B_target_effective = 12 ep/yr/muni × 27 municipalities = 324 ep/yr.

export const tc5Figures: FigureItem[] = [
  // Score heatmaps (H series)
  // Colour convention (consistent across all four heatmaps):
  //   lighter cell = better result  /  darker cell = worse result
  //   Maximize metrics (H1, H2): YlGn_r — high value = light yellow, low = dark green
  //   Minimize metrics (H3, H4): YlOrRd — low value = light yellow, high = dark red
  {
    filename: 'tc5_summary/fig_TC5_H1_score_heatmap.png',
    title: 'PU Composite Score Surface — Threshold Grid',
    caption:
      'Heatmap of the PU composite score Score(θ) = w₁·R_pos − w₂·B − w₃·F_soft/P across the 9×9 threshold grid (Hₛ × SSH_total, q50–q90). Colour scale: lighter (yellow) = higher score = better; darker (green) = lower score = worse. The optimal pair (black rectangle) maximises Score. Default weights: w₁=0.60 (recall), w₂=0.20 (burden), w₃=0.20 (soft penalty). Combined positive-event set: 147 events (expanded 56 + legacy 91), 27 municipalities, 1998–2020.',
    group: 'Score Surface',
    part: 'Step 2e',
  },
  {
    filename: 'tc5_summary/fig_TC5_H2_recall_heatmap.png',
    title: 'Positive Recall R_pos Surface — Threshold Grid',
    caption:
      'Heatmap of positive recall R_pos(θ) = H/P across the 9×9 threshold grid. Colour scale: lighter (yellow) = higher recall = better; darker (green) = lower recall = worse. More permissive (lower percentile) thresholds capture more events at the cost of higher burden. Combined positive-event set: 147 events (expanded 56 + legacy 91, 27 municipalities). The optimal pair is marked with a black rectangle.',
    group: 'Score Surface',
    part: 'Step 2e',
  },
  {
    filename: 'tc5_summary/fig_TC5_H3_burden_heatmap.png',
    title: 'Annual Burden B(θ) Surface — Threshold Grid',
    caption:
      'Heatmap of the normalised annual burden B(θ) = min(1, (H+U)/(Y·B_target)) across the 9×9 threshold grid. Colour scale: lighter (yellow) = lower burden = better; darker (red) = higher burden = worse. B_target_effective = 12 ep/yr/muni × 27 municipalities (union of expanded + legacy) = 324 ep/yr total. The optimal pair is marked with a black rectangle.',
    group: 'Score Surface',
    part: 'Step 2e',
  },
  {
    filename: 'tc5_summary/fig_TC5_H4_fsoft_heatmap.png',
    title: 'Normalised Soft Penalty F_soft(θ)/P Surface — Threshold Grid',
    caption:
      'Heatmap of the soft unmatched penalty F_soft(θ)/P across the 9×9 threshold grid. F_soft = Σᵢ(1 − qᵢ): low qᵢ = low plausibility (large penalty); high qᵢ = plausible unmatched episode (small penalty). Colour scale: lighter (yellow) = lower penalty = better; darker (red) = higher penalty = worse. Normalised by P (147 combined events). The optimal pair is marked with a black rectangle.',
    group: 'Score Surface',
    part: 'Step 2e',
  },
  // Summary / comparison figures (S series)
  {
    filename: 'tc5_summary/fig_TC5_S1_csi_vs_pu.png',
    title: 'CSI Optimal Pair vs PU Optimal Pair — Threshold Comparison',
    caption:
      'Side-by-side bar chart comparing the threshold percentiles selected by Step 2d (CSI optimisation, 91-event legacy database) and Step 2e (PU composite calibration, combined 147-event positive set: expanded 56 + legacy 91, 27 municipalities). Both methods converge on q90/q90 for Hₛ and SSH_total, providing independent confirmation that the q90 pair is robust to the choice of events database and calibration metric. The convergence suggests the result is not an artefact of a single database or method.',
    group: 'Comparison',
    part: 'Step 2e',
  },
  {
    filename: 'tc5_summary/fig_TC5_S2_sensitivity_weights.png',
    title: 'Weight Sensitivity — Optimal Pair Stability',
    caption:
      'Sensitivity of the PU-optimal threshold pair to alternative (w₁, w₂, w₃) weight triplets. Each row shows the optimal Hₛ and SSH_total threshold percentile for one weight preset: high_recall (w₁=0.70), balanced (w₁=0.50), and default (w₁=0.60). Stability across presets confirms that the q90/q90 result does not depend on the specific weight choice within a reasonable range.',
    group: 'Sensitivity',
    part: 'Step 2e',
  },
  {
    filename: 'tc5_summary/fig_TC5_S3_sensitivity_b_target.png',
    title: 'B_target Sensitivity — Score vs Per-Municipality Burden Target',
    caption:
      'Sensitivity of the PU composite score and optimal threshold pair to alternative per-municipality annual burden targets (6, 12, 18, 24 episodes/year/municipality). The effective domain budget scales with n_union_municipalities = 27 (union of both databases; total = value × 27). Left axis: composite score; right axis: optimal threshold percentiles (Hₛ in red, SSH in orange). The optimal pair remains q90/q90 across all tested targets, demonstrating robustness. Score improves (less negative) with more permissive targets, reflecting the reduced burden penalty.',
    group: 'Sensitivity',
    part: 'Step 2e',
  },
  {
    filename: 'tc5_summary/fig_TC5_S4_sensitivity_gap_days.png',
    title: 'Episode Gap Sensitivity — Score vs Gap Tolerance',
    caption:
      'Sensitivity of the PU composite score and optimal threshold pair to alternative episode gap tolerance values (0, 1, 2, 3 days). The gap tolerance controls how many non-exceedance days can separate consecutive exceedance days within a single episode (EPISODE_MAX_GAP_DAYS). Left axis: composite score; right axis: optimal threshold percentiles (Hₛ in red, SSH in orange). The optimal pair remains q90/q90 across all tested values. Score improves monotonically with larger gaps (fewer, longer episodes reduce burden), but the effect is modest (Score ranges from -3.22 at gap=0 to -3.02 at gap=3).',
    group: 'Sensitivity',
    part: 'Step 2e',
  },
  // Audit figures (A series)
  {
    filename: 'tc5_summary/fig_TC5_A1_qi_distribution.png',
    title: 'Distribution of qᵢ Confidence Weights — Unmatched Episodes',
    caption:
      'Histogram of qᵢ confidence weights for all unmatched episodes at the PU-optimal threshold pair (q90/q90). qᵢ = clip(α_E·Eᵢ + α_I·Iᵢ + α_C·Cᵢ, 0, 1) aggregates external evidence (Eᵢ), physical intensity (Iᵢ), and context coherence (Cᵢ) for each unmatched episode. Red dashed line: mean; orange dotted line: median. Episodes clustered near 0 have low plausibility (few circumstantial indicators of a real event); episodes near 1 are highly plausible but unconfirmed in the documentary database, likely reflecting under-reporting.',
    group: 'Episode Audit',
    part: 'Step 2e',
  },
  {
    filename: 'tc5_summary/fig_TC5_A2_city_source_audit.png',
    title: 'Municipality Audit Map — Combined Positive-Event Set (SC Coast)',
    caption:
      'Georeferenced map (Santa Catarina coast, cartopy/Natural Earth) of the 27 unique municipalities in the combined 147-event positive set. Open circles mark the matched WAVERYS/GLORYS12 grid points; thin lines connect municipality centroids to grid points. Municipalities marked ★ have near-match events across constituent databases (within ±3 days; confirmed at Florianópolis). The combined positive set is the analysis object for Step 2e. Total: 147 events, 27 municipalities, B_target_effective = 12 × 27 = 324 ep/yr. Database provenance details are available in tab_TC5_positive_event_union_audit.csv.',
    group: 'City Audit',
    part: 'Step 2e',
  },
  // Event-level capture diagnostics (E series) — sector-coloured, SSH_total mandatory
  {
    filename: 'tc5_summary/fig_TC5_E1_event_capture.png',
    title: 'TC5-E1 — Peak Hₛ per Event, by Coastal Sector (PU-optimal pair)',
    caption:
      'Peak Hₛ within the causal window [D-2 … D+1] for all 147 combined positive events sorted by coastal sector (canonical order: North → Central-north → Central → Central-south → South) and then by date. Colour encodes coastal sector, consistent with Step 2d sector-colour convention (SECTOR_COLORS). Filled markers = captured (compound hit at Hₛ q90 ∧ SSH_total q90); open = missed. Dashed horizontal line = median local Hₛ q90 threshold across all grid points (individual thresholds vary). Light green shading marks the zone above the median threshold.',
    group: 'Event Capture',
    part: 'Step 2e',
  },
  {
    filename: 'tc5_summary/fig_TC5_E2_ssh_capture.png',
    title: 'TC5-E2 — Peak SSH_total per Event, by Coastal Sector (PU-optimal pair)',
    caption:
      'Analogous to TC5-E1 but with peak SSH_total = zos + FES2022 tide on the y-axis. Events sorted by coastal sector then date. SSH_total is computed as the daily-maximum SSH (GLORYS12 zos) plus the FES2022 astronomical tide at hourly resolution, resampled to daily maxima. Dotted horizontal line = median local SSH_total q90 threshold. Light blue shading marks the zone above the threshold. Filled = captured; open = missed at the PU-optimal pair (q90/q90).',
    group: 'Event Capture',
    part: 'Step 2e',
  },
  {
    filename: 'tc5_summary/fig_TC5_E3_peak_scatter.png',
    title: 'TC5-E3 — Peak Hₛ vs SSH_total Scatter (PU-optimal pair)',
    caption:
      'Scatter of peak Hₛ (x-axis) vs peak SSH_total = zos + FES2022 tide (y-axis) within the causal window [D-2 … D+1] for all 147 combined positive events. Colour encodes coastal sector; filled = captured (compound hit), open = missed at the PU-optimal pair (Hₛ q90 / SSH_total q90). Dashed and dotted reference lines show the median local thresholds across grid points. Light green shading marks the zone where both thresholds are exceeded. This figure is the Step 2e analogue of Step 2d TC4-S5, applied to the final combined 147-event positive set.',
    group: 'Event Capture',
    part: 'Step 2e',
  },
];

export const tc5FigureGroups = [
  'Score Surface',
  'Comparison',
  'Sensitivity',
  'Episode Audit',
  'City Audit',
  'Event Capture',
];
