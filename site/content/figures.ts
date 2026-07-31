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
//
// RECALIBRATED 2026-07-30. All figures below were regenerated on that date.
// Five things changed and every caption reflects them:
//   * scored detector — Hs and TIDE-FREE zos, gated by max(SWL) > HAT.
//     It used to be Hs and SSH_total = zos + tide, a variable production no
//     longer reads.
//   * grid — 11 levels (q50…q90, q95, q99), 121 pairs, up from 9 levels / 81.
//   * burden — two-sided deviation from an expected rate of 2.0 detections per
//     municipality per year, anchored on Leal et al. (2024). It used to be a
//     one-sided ceiling at 12/yr, which was minimised at ZERO detections.
//   * weights — w = (0.30, 0.60, 0.10), was (0.60, 0.20, 0.20).
//   * alphas — (0.20, 0.50, 0.30), was (0.60, 0.30, 0.10).
// Selected pair: q70 (Hs) / q99 (zos). See AUD-01 §14.

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
      'Heatmap of the PU composite score Score(θ) = w₁·R_pos − w₂·B − w₃·F_soft/P across the 11×11 threshold grid (Hₛ × tide-free zos, q50–q90 plus q95 and q99). Colour scale: lighter (yellow) = higher score = better; darker (green) = lower score = worse. The selected pair q70/q99 (black rectangle) maximises Score at −0.3178. Weights: w₁=0.30 (recall), w₂=0.60 (rate deviation), w₃=0.10 (soft penalty), reweighted on 2026-07-30. The grid was extended past q90 because the previous optimum sat on the q90 edge; doing so revealed that under the old weights the score had no interior optimum at all — Spearman(Score, accepted episodes) = −0.999. Combined positive-event set: 147 events (expanded 56 + legacy 91), 27 municipalities, 1998–2020.',
    group: 'Score Surface',
    part: 'Step 2e',
  },
  {
    filename: 'tc5_summary/fig_TC5_H2_recall_heatmap.png',
    title: 'Positive Recall R_pos Surface — Threshold Grid',
    caption:
      'Heatmap of positive recall R_pos(θ) = H/P across the 11×11 threshold grid. Colour scale: lighter (yellow) = higher recall = better; darker (green) = lower recall = worse. More permissive (lower percentile) thresholds capture more events at the cost of a higher detection rate. At the selected pair q70/q99, R_pos = 0.1905 (H = 28 of 147) — identical to the superseded q90/q90 pair scored under the same detector, which the new pair matches while producing 62 % fewer unmatched detections. Combined positive-event set: 147 events, 27 municipalities. The selected pair is marked with a black rectangle.',
    group: 'Score Surface',
    part: 'Step 2e',
  },
  {
    filename: 'tc5_summary/fig_TC5_H3_burden_heatmap.png',
    title: 'Annual Burden B(θ) Surface — Threshold Grid',
    caption:
      'Heatmap of the burden term B(θ) = min(1, |log₁₀(rate(θ)/r*)|) across the 11×11 threshold grid, where rate(θ) = (H+U)/(Y·n_municipalities) and r* = 2.0 detections per municipality per year. Colour scale: lighter (yellow) = closer to the expected rate = better; darker (red) = further from it = worse. Since 2026-07-30 this is a TWO-SIDED deviation: detecting far fewer episodes than expected is penalised as much as flooding. The former one-sided ceiling was minimised at zero detections, so it pushed in the same direction as the soft penalty and could not anchor the selection — sweeping its weight from 0.20 to 0.69 left the optimum pinned at the emptiest pair of the grid. The anchor r* assumes under-reporting of about 8× the rate documented by Leal et al. (2024); sensitivity spans 0.5 to 6.0. The selected pair is marked with a black rectangle.',
    group: 'Score Surface',
    part: 'Step 2e',
  },
  {
    filename: 'tc5_summary/fig_TC5_H4_fsoft_heatmap.png',
    title: 'Normalised Soft Penalty F_soft(θ)/P Surface — Threshold Grid',
    caption:
      'Heatmap of the soft unmatched penalty F_soft(θ)/P across the 11×11 threshold grid. F_soft = Σᵢ(1 − qᵢ): low qᵢ = low plausibility (large penalty); high qᵢ = plausible unmatched episode (small penalty). Colour scale: lighter (yellow) = lower penalty = better; darker (red) = higher penalty = worse. Normalised by P (147 combined events). This term is unbounded above — it reaches 29.4 at q50/q50 against a maximum recall contribution of 0.60 — which is why its weight was cut from 0.20 to 0.10 on 2026-07-30: at the former weight it made the score a monotone preference for detecting nothing. The selected pair is marked with a black rectangle.',
    group: 'Score Surface',
    part: 'Step 2e',
  },
  // Summary / comparison figures (S series)
  {
    filename: 'tc5_summary/fig_TC5_S1_csi_vs_pu.png',
    title: 'CSI Optimal Pair vs PU Optimal Pair — Threshold Comparison',
    caption:
      'Side-by-side bar chart comparing the threshold percentiles selected by Step 2d (CSI optimisation, 91-event legacy database) and Step 2e (PU composite calibration, combined 147-event positive set). The two used to agree on q90/q90, and that agreement was read as convergent evidence. It was not: both sweeps stopped AT q90 and both scored a detector built on SSH_total. Recalibrating Step 2e on the production detector over a grid extended to q95 and q99 moved its answer to q70/q99. Step 2d remains a diagnostic step and has not been re-run; its q90/q90 result is retained here as the historical record of that scan, not as corroboration.',
    group: 'Comparison',
    part: 'Step 2e',
  },
  {
    filename: 'tc5_summary/fig_TC5_S2_sensitivity_weights.png',
    title: 'Weight Sensitivity — Optimal Pair Stability',
    caption:
      'Sensitivity of the selected threshold pair to alternative (w₁, w₂, w₃) weight triplets: recall_leaning (0.40/0.50/0.10), rate_anchored (0.20/0.70/0.10), penalty_leaning (0.30/0.55/0.15), default (0.30/0.60/0.10) and legacy_2026_07_29 (0.60/0.20/0.20). The level percentile q99 is selected under every triplet. The wave percentile is not stable — q70 under the default and recall_leaning presets, q50 under rate_anchored, q85 under penalty_leaning — and under the legacy triplet the optimum collapses back to the emptiest pair of the grid, which is what motivated the reweighting.',
    group: 'Sensitivity',
    part: 'Step 2e',
  },
  {
    filename: 'tc5_summary/fig_TC5_S3_sensitivity_b_target.png',
    title: 'B_target Sensitivity — Score vs Per-Municipality Burden Target',
    caption:
      'Sensitivity of the PU composite score and selected threshold pair to alternative expected detection rates r* (0.5, 1.0, 2.0, 3.0, 6.0 per municipality per year), spanning roughly 2× to 25× the 0.243 rate documented by Leal et al. (2024) plus the expanded archive. Left axis: composite score; right axis: selected threshold percentiles (Hₛ in red, zos in orange). The level percentile is q99 throughout. The wave percentile responds to the anchor: q95 at r*=0.5, q85 at r*=1.0, and q70 for r* ≥ 2.0, where it is stable. The anchor is a declared assumption about under-reporting, not a measurement — AUD-18 records that no independent validation base exists.',
    group: 'Sensitivity',
    part: 'Step 2e',
  },
  {
    filename: 'tc5_summary/fig_TC5_S4_sensitivity_gap_days.png',
    title: 'Episode Gap Sensitivity — Score vs Gap Tolerance',
    caption:
      'Sensitivity of the PU composite score and selected threshold pair to alternative episode gap tolerance values (0, 1, 2, 3 days), which control how many non-exceedance days may separate consecutive exceedance days within one episode. Left axis: composite score; right axis: selected threshold percentiles (Hₛ in red, zos in orange). The pair is q70/q99 at gaps 0, 1 and 2, and q55/q99 at gap 3, where the score is effectively tied (−0.3176 against −0.3178). Both layers of the scan are re-run for each gap value: since the level gate applies to the episode as a whole, merging or splitting episodes changes which ones clear max(SWL) > HAT, so holding Layer 1 fixed would silently mix gap tolerances between the two layers.',
    group: 'Sensitivity',
    part: 'Step 2e',
  },
  // Audit figures (A series)
  {
    filename: 'tc5_summary/fig_TC5_A1_qi_distribution.png',
    title: 'Distribution of qᵢ Confidence Weights — Unmatched Episodes',
    caption:
      'Histogram of qᵢ confidence weights for the 831 unmatched episodes at the selected pair q70/q99. qᵢ = clip(α_E·Eᵢ + α_I·Iᵢ + α_C·Cᵢ, 0, 1) aggregates external evidence (Eᵢ), physical intensity (Iᵢ) and context coherence (Cᵢ). Red dashed line: mean (0.494); orange dotted line: median (0.500). The alphas were rebalanced on 2026-07-30 from (0.60, 0.30, 0.10) to (0.20, 0.50, 0.30): Eᵢ = 1 in only 154 of 436 352 unmatched episodes across the sweep — 0.04 % — so α_E = 0.60 capped qᵢ at 0.40 by construction for 99.96 % of episodes. That measured the sparseness of the documentary register, not the implausibility of a detection, and contradicted the premise of the PU framework itself. Episodes near 1 are physically plausible but unconfirmed, most likely reflecting under-reporting.',
    group: 'Episode Audit',
    part: 'Step 2e',
  },
  {
    filename: 'tc5_summary/fig_TC5_A2_city_source_audit.png',
    title: 'Municipality Audit Map — Combined Positive-Event Set (SC Coast)',
    caption:
      'Georeferenced map (Santa Catarina coast, cartopy/Natural Earth) of the 27 unique municipalities in the combined 147-event positive set. Open circles mark the matched WAVERYS/GLORYS12 grid points; thin lines connect municipality centroids to grid points. Municipalities marked ★ have near-match events across constituent databases (within ±3 days; confirmed at Florianópolis). The combined positive set is the analysis object for Step 2e. Total: 147 events, 27 municipalities, against an expected-rate anchor of 2.0 detections/municipality/yr. Database provenance details are available in tab_TC5_positive_event_union_audit.csv.',
    group: 'City Audit',
    part: 'Step 2e',
  },
  // Event-level capture diagnostics (E series) — sector-coloured. Since the
  // 2026-07-30 recalibration the level driver on these axes is TIDE-FREE zos.
  {
    filename: 'tc5_summary/fig_TC5_E1_event_capture.png',
    title: 'TC5-E1 — Peak Hₛ per Event, by Coastal Sector (selected pair q70/q99)',
    caption:
      'Peak Hₛ within the causal window [D-2 … D+1] for all 147 combined positive events sorted by coastal sector (canonical order: North → Central-north → Central → Central-south → South) and then by date. Colour encodes coastal sector, consistent with Step 2d sector-colour convention (SECTOR_COLORS). Filled markers = captured (accepted compound episode overlapping the causal window at the selected pair Hₛ q70 ∧ zos q99, gated by max(SWL) > HAT); open = missed. Dashed horizontal line = median local Hₛ q70 threshold across all grid points (individual thresholds vary). Light green shading marks the zone above the median threshold.',
    group: 'Event Capture',
    part: 'Step 2e',
  },
  {
    filename: 'tc5_summary/fig_TC5_E2_ssh_capture.png',
    title: 'TC5-E2 — Peak Tide-Free zos per Event, by Coastal Sector (selected pair q70/q99)',
    caption:
      'Analogous to TC5-E1 but with the peak of the TIDE-FREE level driver, GLORYS12 zos, on the y-axis. Events sorted by coastal sector then date. Until 2026-07-30 this axis carried SSH_total = zos + FES2022 tide; the detector no longer reads that variable, so the axis now shows the quantity the level percentile is actually applied to. The dotted line is the median local q99 of zos across the event grid points. Filled markers are captured events, open markers missed: H = 28, M = 119, R_pos = 0.19 over the 147 combined positive events. Note the range — a few tenths of a metre — which is the surge signal alone, without the metre-scale astronomical tide that used to dominate this axis.',
    group: 'Event Capture',
    part: 'Step 2e',
  },
  {
    filename: 'tc5_summary/fig_TC5_E3_peak_scatter.png',
    title: 'TC5-E3 — Peak Hₛ vs Peak Tide-Free zos Scatter (selected pair q70/q99)',
    caption:
      'Scatter of peak Hₛ (x-axis) against peak tide-free zos (y-axis) within the causal window [D-2 … D+1] for all 147 combined positive events. Colour encodes coastal sector; filled markers are events captured at the selected pair q70/q99, open markers are missed. The two median threshold lines partition the plane into the four quadrants of the compound criterion. Capture also requires the level gate max(SWL) > HAT over the shared days, which this projection cannot show: an event can sit inside the upper-right quadrant and still be rejected because the still water level never cleared the local HAT.',
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
