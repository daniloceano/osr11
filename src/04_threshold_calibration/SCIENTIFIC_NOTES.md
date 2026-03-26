# SCIENTIFIC_NOTES — Step 4: Threshold Calibration (CSI Grid Scan)

**Module**: `src/04_threshold_calibration/`
**Project**: OSR11 — Compound Coastal Flooding Hazard Assessment, Santa Catarina coast
**Authors**: Danilo Couto de Souza, Carolina Barnez Gramcianinov, Ricardo de Camargo, Karine Bastos Leal

---

## Research Questions

1. Which combination of Hₛ and SSH_total exceedance thresholds best detects the 91 reported
   SC coastal disaster events while minimising spurious compound episodes (false alarms)?

2. Does the optimal threshold pair vary systematically by coastal sector, or is a single
   domain-wide pair sufficient for the full Santa Catarina coast?

3. What is the empirical distribution of capture lags — i.e., how many events are captured
   via antecedent forcing (D-2, D-1) vs the event day (D) vs the operational tolerance (D+1)?

---

## Physical / Statistical Framework

### Compound event definition

A compound coastal flooding event is defined as a time step at which both:

- Hₛ (significant wave height, from WAVERYS) ≥ thr_hs
- SSH_total = SSH + tide (GLORYS12 + FES2022) ≥ thr_ssh_total

are simultaneously exceeded. This joint exceedance definition follows
Zscheischler et al. (2020) and is consistent with Steps 2 and 3 of this pipeline.

### Threshold calibration framework

Thresholds are evaluated as **local percentiles** of the climatological series at each
municipality's grid point. The calibration sweeps 9 × 9 = 81 threshold pairs:

    Hₛ:         q50, q55, q60, q65, q70, q75, q80, q85, q90
    SSH_total:  q50, q55, q60, q65, q70, q75, q80, q85, q90

For each pair, a standard 2×2 contingency table is computed:

|              | Detected | Not detected |
|--------------|----------|--------------|
| Observed     | H (hit)  | M (miss)     |
| Not observed | F (false alarm) | TN (not used) |

True negatives (TN) are not computed because the "non-event" population is very large and
poorly defined (the full 32-year daily series has ~12,000 days, but only 91 are labelled as
disaster events). Computing TN would require defining a representative background sample,
which introduces additional assumptions. CSI avoids this by focusing only on H, M, and F.

### Verification metrics

**POD** (Probability of Detection / Hit Rate):

    POD = H / (H + M)

Proportion of observed disasters captured by the method. High POD means few misses.
Maximising POD alone would favour very permissive (low) thresholds.

**FAR** (False Alarm Ratio):

    FAR = F / (H + F)

Proportion of compound episode detections that do not correspond to any reported disaster.
High FAR means many spurious detections. Minimising FAR alone would favour very restrictive
(high) thresholds that detect almost nothing.

**CSI** (Critical Success Index):

    CSI = H / (H + M + F)

The primary optimisation metric. CSI balances POD and FAR by penalising both misses and
false alarms in the denominator. It ranges from 0 (no skill) to 1 (perfect detection).

### Optimal pair selection hierarchy

1. **Highest CSI** — primary criterion.
2. **Lowest FAR** — tiebreaker. Between two pairs with equal CSI, prefer the one that
   generates fewer false alarms (more specific detection).
3. **Highest percentile sum** (thr_hs_pct + thr_ssh_pct) — second tiebreaker. Among pairs
   with equal CSI and FAR, prefer the more restrictive pair. This aligns with the goal of
   establishing a physically meaningful compound event threshold rather than a permissive
   one that captures background variability.

---

## Datasets and Variables

| Variable | Source | Resolution | Period | Notes |
|----------|--------|------------|--------|-------|
| VHM0 (Hₛ) | WAVERYS (CMEMS) | ~8 km, daily 00Z | 1993–2025 | Regridded to WAVERYS grid |
| zos (SSH) | GLORYS12 (CMEMS) | ~8 km, daily 00Z | 1993–2025 | Tidal-residual product |
| tide | FES2022 via eo-tides | Daily 00Z (at grid points) | 1993–2025 | Evaluated at each municipality's grid point |
| SSH_total | zos + tide | Daily 00Z | 1993–2025 | Computed per grid point |
| Observed events | Leal et al. (2024) | Daily (civil date) | 1998–2023 | 91 events, 22 municipalities, 5 SC sectors |

The unified dataset (`data/test/metocean_sc_full_unified_waverys_grid.nc`) contains VHM0
and zos on the same WAVERYS grid. FES2022 tides are computed at the same grid points using
the `eo-tides` Python library (see Step 3 documentation).

---

## Methodology

### Step 4.0 — Reuse of infrastructure from Steps 2–3

The following components are reused **without modification**:

- `src/02_preliminary_compound/events.build_event_records()`: resolves each of the 91
  reported events to its nearest valid grid point (municipality → WAVERYS/GLORYS12 cell)
  and extracts the full climatological Hₛ and SSH series at that point.
- `src/03_tidal_sensitivity/tides.build_tide_cache()`: computes FES2022 tidal predictions
  at daily 00:00 UTC for each unique grid point.
- `src/03_tidal_sensitivity/tides.add_tide_to_ssh()`: computes SSH_total = SSH + tide.

### Step 4.1 — Causal/antecedent matching window

For each observed event reported on civil date **D**, the admissible match timestamps are:

    match_times = [D-2, D-1, D, D+1]   (daily 00Z snapshots)

**Rationale for each offset**:
- **D-2, D-1**: The physical forcing (wave swell, storm surge) may arrive at the coast
  1–2 days before the damage is recorded and reported to Civil Defense.
- **D**: The reported event day itself.
- **D+1 00Z**: Operational tolerance. The dataset contains daily snapshots at 00:00 UTC
  (not daily means). If the compound peak occurred during the afternoon or evening of civil
  day D (e.g., at 18:00 UTC), it would appear in the D+1 00:00 UTC snapshot rather than
  the D snapshot. Including D+1 avoids penalising the method for a UTC vs local-time
  convention mismatch.

**Important**: the window is asymmetric. Compound episodes detected only on D+2 or later
are **not** considered matches, even if they coincide with a separate natural hazard event.

### Step 4.2 — Threshold grid scan (Layer 1: hits and misses)

For each threshold pair (thr_hs_pct, thr_ssh_pct):

    For each observed event (municipality M, date D):
        1. Retrieve Hₛ(t) and SSH_total(t) at the pre-associated grid point.
        2. Compute local thresholds:
               thr_hs    = quantile(Hₛ_clim,       thr_hs_pct)
               thr_ssh   = quantile(SSH_total_clim, thr_ssh_pct)
           using the full 1993–2025 climatological series at that grid point.
        3. Build match_times = [D-2, D-1, D, D+1] ∩ time_index
        4. Check: captured = any(Hₛ(t) ≥ thr_hs AND SSH_total(t) ≥ thr_ssh
                                  for t in match_times)
        5. Record hit (H) or miss (M).

Thresholds are computed locally (per grid point), not globally. This means the same
percentile level corresponds to different absolute values at different locations along
the coast, reflecting the local climatological context.

### Step 4.3 — Full-series false alarm detection (Layer 2)

For each unique grid point and each threshold pair:

    1. Find all compound days in the full 1993–2025 series:
           compound_mask(t) = (Hₛ(t) ≥ thr_hs) AND (SSH_total(t) ≥ thr_ssh)
    2. Cluster consecutive compound days (gap ≤ 1 day) into independent episodes.
    3. For each episode, check if any of its days falls within the causal window
       [D-2, D-1, D, D+1] of any observed event at the same grid point.
    4. If not paired with any event → false alarm episode.

**Episode clustering**: Two compound days are considered part of the same episode if the
gap between them is ≤ 2 calendar days (i.e., at most 1 gap day allowed). This is
consistent with the `pot_min_separation_days=1` setting used in Steps 2–3.

**False alarm domain**: False alarms are only counted at grid points where at least one
observed event exists. This restricts the evaluation to the validated domain and prevents
inflating F with unrelated coastal sectors.

### Step 4.4 — Metric computation and optimal pair selection

For each threshold pair:

    POD = H / (H + M)
    FAR = F / (H + F)
    CSI = H / (H + M + F)

The optimal pair is selected following the hierarchy: max CSI → min FAR → max percentile sum.

---

## Assumptions

1. **SSH_total = SSH + FES2022 (daily 00Z)**: The tidal component is the FES2022 daily
   prediction at midnight UTC, consistent with the GLORYS12 snapshot time. The Tidal
   Sensitivity Analysis (Step 3) established that daily resolution is the appropriate
   baseline given the current dataset. Hourly-resolution tidal effects will be considered
   in a future extension.

2. **Local percentile thresholds**: Thresholds are computed from the full annual
   climatological series at each municipality's grid point. No seasonal decomposition or
   block maxima approach is used. This is consistent with Steps 2–3 and keeps the
   comparison clean.

3. **Single global match window**: The same causal window [D-2, D-1, D, D+1] is applied
   uniformly to all municipalities and sectors. Sector-specific windows are not tested in
   the base implementation but are a natural sensitivity extension.

4. **Event independence**: Each of the 91 reported events is treated as an independent
   observation. Some municipalities appear multiple times (repeat disasters). The method
   does not account for temporal clustering of observed events, which could bias the
   contingency table if multiple events share overlapping causal windows.

5. **False alarm domain restriction**: False alarms are evaluated only at grid points with
   at least one observed event. This is a deliberate scope restriction, not a bug. It means
   CSI may be somewhat optimistic relative to a full-domain scan.

6. **NaN handling**: Grid points where either Hₛ or SSH_total has NaN throughout are
   silently skipped. Approximately 50% of northern SC municipalities have partial or complete
   NaN coverage due to GLORYS12/WAVERYS grid resolution near complex coastal geometries.
   These events are recorded as misses and logged.

---

## Results and Interpretation

**[PRELIMINARY — to be updated after running the full grid scan]**

Results will be documented here after the analysis is executed. Key outputs to interpret:

- **CSI heatmap** (fig_TC4_H1): the spatial pattern of CSI across threshold pairs reveals
  whether there is a clear optimal region or a broad plateau. A sharp peak indicates robust
  calibration; a broad plateau suggests the method is not highly sensitive to the exact
  threshold choice.

- **FAR heatmap** (fig_TC4_H2): low-percentile combinations tend to have high FAR (many
  false alarms). The FAR surface helps identify which threshold pairs are too permissive.

- **POD heatmap** (fig_TC4_H3): high-percentile combinations tend to have low POD (many
  misses). The POD surface helps identify pairs that are too restrictive.

- **Event-level hits** (tab_TC4_event_hits_optimal.csv): events consistently missed at the
  optimal pair may indicate physical mismatches (e.g., events driven by processes not well
  captured by WAVERYS/GLORYS12 at daily resolution, or events in sectors with poor grid
  coverage).

- **Capture lag** (tab_TC4_lag_summary.csv): the distribution of lags at which events are
  captured (D-2, D-1, D, D+1) reveals whether the compound forcing typically precedes or
  coincides with the reported impact.

---

## Caveats and Limitations

1. **Daily temporal resolution**: WAVERYS and GLORYS12 are daily datasets. The compound
   detection cannot resolve intra-day timing. The D+1 00Z tolerance partially compensates,
   but tidal phasing effects at sub-daily scales are not captured. This is the most
   significant limitation of the current implementation.

2. **Reanalysis representativeness**: WAVERYS and GLORYS12 are gridded reanalysis products
   with ~8 km resolution. Nearshore wave and surge dynamics (shoaling, refraction, coastal
   trapping) are not fully resolved. Grid points are representative of offshore or open-shelf
   conditions, not the immediate shoreline.

3. **Reported event quality**: The Leal et al. (2024) database is derived from Civil Defense
   records, which may have reporting delays, missing events, or spatially imprecise location
   assignments. The event dates are civil dates (not UTC datetimes), which introduces an
   additional ±12-hour uncertainty relative to the 00Z time convention.

4. **Single-sector scan for false alarms**: False alarms are only counted at the 22
   municipalities with observed events. The broader SC coast may have additional false alarm
   episodes not captured by this scope restriction.

5. **Threshold stationarity**: Percentile thresholds are computed over the full 1993–2025
   period without accounting for long-term trends (e.g., sea level rise). For climate
   projections, non-stationary thresholds would be required.

6. **Independent events assumption**: Some municipalities have multiple events within a few
   years. If the threshold that captures one event is the same as the one that misses another,
   the contingency table may not be fully independent across observations.

---

## Next Steps

- **Step 5**: Use the optimal threshold pair from Step 4 to build independent storm catalogs
  (Hₛ exceedance episodes + SSH_total exceedance episodes) for the full series at each
  grid point.
- **Step 6**: Detect compound events as temporal overlaps between the Hₛ and SSH_total catalogs.
- **Sensitivity**: Re-run with a sector-specific match window (e.g., wider window for northern
  sectors where grid coverage is sparser).
- **Extension**: Evaluate whether hourly-resolution tidal signal changes the CSI surface
  significantly (requires 3-hourly or hourly WAVERYS data).

---

## References

- Leal, K. B. et al. (2024) — SC Civil Defense coastal disaster database (internal, cited as
  reported_events_Karine_sc.csv)
- Zscheischler, J. et al. (2020) — A typology of compound weather and climate events.
  _Nature Reviews Earth & Environment_, 1, 333–347. https://doi.org/10.1038/s43017-020-0060-z
- Green, A. L. et al. (2025) — A comprehensive review of compound flooding literature.
  _Nat. Hazards Earth Syst. Sci._, 25, 747–805. https://nhess.copernicus.org/articles/25/747/2025/
- Donges, J. F. et al. — Event coincidence analysis for quantifying statistical
  interrelationships between event time series. https://arxiv.org/abs/1508.03534
- NOAA / Space Weather Prediction Center — Forecast Verification Glossary.
  https://www.swpc.noaa.gov/sites/default/files/images/u30/Forecast%20Verification%20Glossary.pdf
- CMEMS (2024) — Global Ocean Physics Reanalysis (GLORYS12, WAVERYS). Copernicus Marine.
- Lyard, F. H. et al. (2021) — FES2014 global ocean tide atlas.
  _Ocean Sci._, 17, 615–649. https://doi.org/10.5194/os-17-615-2021
