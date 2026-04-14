# Step 3 — Storm Catalog Generation

**Part of the OSR11 Pipeline**  
**Location:** `src/03_storm_catalog_generation/`  
**Status:** Planned — implementation not yet started  
**Preceded by:** Step 2 (Threshold Calibration, complete)  
**Followed by:** Step 4 (Compound Event Detection)

---

## 1. PURPOSE

### Scientific rationale

Step 3 applies the empirically calibrated compound event detection thresholds (from Step 2e) to the full 1993–2025 metocean record to produce independent storm catalogs for sea-level (SSH_total) and wave (Hₛ) extremes at each **coastal grid point along the entire eastern coast of Brazil**. A "storm" is defined as a continuous period during which a variable exceeds its local threshold. Consecutive exceedance days within a configurable gap tolerance are merged into a single storm episode.

The core output object is the **coastal grid-point catalog**, not a municipality-centered catalog. If a simple and robust API-based method exists to identify the nearest municipality for each coastal grid point, that information can be included as optional metadata, but municipality labeling is not a required dependency for Step 3.

Storm segmentation is the operationalization of the peaks-over-threshold (POT) philosophy adopted throughout Step 2. It converts a continuous time series of exceedance days into a structured list of discrete, bounded episodes, each characterized by its temporal extent and intensity.

### Connection to Step 2 outputs

Step 3 is the first step that uses the Step 2e output operationally. The PU-optimal threshold pair stored in `outputs/threshold_calibration/tables/tab_TC5_optimal_pair_pu.csv` is the sole authoritative source of detection thresholds. Step 3 must not use the Step 2d CSI-optimal thresholds (which were diagnostic only).

### Role as foundation for Step 4

Step 3 produces two independent catalogs — one for Hₛ storms and one for SSH_total storms — at each coastal grid point. Step 4 compares these catalogs temporally to identify compound events (episodes where both a wave storm and a sea-level storm overlap in time). The catalog schema and attribute definitions established in Step 3 directly determine what Step 4 can compute.

---

## 2. INHERITED DECISIONS FROM STEP 2

The following methodological commitments are fixed by the Step 2 implementation and must be inherited unchanged by Step 3.

### 2.1 Final threshold pair (from Step 2e)

| Variable | Threshold | Source file |
|----------|-----------|-------------|
| Hₛ (VHM0) | q90 of the local climatological series (full metocean record) | `outputs/threshold_calibration/tables/tab_TC5_optimal_pair_pu.csv` → column `thr_hs_pct` |
| SSH_total (zos_total) | q90 of the local climatological series (full metocean record) | `outputs/threshold_calibration/tables/tab_TC5_optimal_pair_pu.csv` → column `thr_ssh_pct` |

Thresholds are **local percentiles** — they are computed independently at each coastal grid point from the local time series, not as a single global value. This is mandatory for consistency with all Step 2 analyses.

**Threshold computation period (authoritative decision from Step 2e corrections):** Thresholds are computed from the **full metocean record** (1993–2025), not from the validated period. The validated period (1998–2020) restricts only the event-matching scan (where detected episodes are compared against reported events), not the climatological series from which percentile thresholds are derived. This ensures maximum statistical robustness and eliminates edge effects at the boundaries of the event-record period. The storm catalog is also generated from the full 1993–2025 series.

### 2.2 SSH_total mandatory definition

SSH_total must be computed as:

```
SSH_total(d) = zos(d, 00:00 UTC) + tide_daily_max(d)
```

Where:
- `zos` — GLORYS12 sea surface height above geoid (daily 00:00 UTC snapshot, variable name `zos` in the unified NetCDF)
- `tide_daily_max` — FES2022 astronomical tide evaluated at hourly resolution and resampled to daily maximum

This definition is canonical. Using raw `zos` alone (without the tidal component) is incorrect and inconsistent with all prior steps.

**Known limitation (propagated from Step 2c):** `zos` is a 00:00 UTC snapshot; `tide_daily_max` is the daily maximum which may occur at a different time. SSH_total therefore combines two non-simultaneous quantities. This is inherent to GLORYS12's daily-only output and is the accepted approximation throughout this project.

### 2.3 Tide integration code location

The tide integration functions already exist in Step 2c and are reused by Steps 2d and 2e:

- `src/02_threshold_calibration/03_tidal_sensitivity/tides.py` — contains:
  - `build_tide_cache(records, daily_max=True)` — computes FES2022 daily-max tidal series per grid point
  - `add_tide_to_ssh(ssh_series, tide_series)` — computes SSH_total = zos + tide
  - `_compute_daily_max_tides(lat, lon, time_index)` — hourly FES2022 evaluation → daily max (internal helper)
  - `compute_tides_for_point(lat, lon, time_index)` — low-level FES2022 evaluation at given timestamps

Step 3 must reuse these functions (not reimplement tide computation). The tide model directory is `data/tide_models_clipped_brasil/` (configured in Step 2e's `config/analysis_config.py`, constant `TIDE_MODELS_DIR`).

**Interface adaptation note:** In Step 2c–2e, `build_tide_cache()` accepts a `list[EventRecord]` and extracts `(grid_lat, grid_lon)` coordinates and the climatological time index from each record. Step 3 does not use EventRecord objects — it works with grid points from the metocean dataset. Step 3's tide wrapper should either (a) construct lightweight record-like objects compatible with `build_tide_cache()`, or (b) call the lower-level `_compute_daily_max_tides(lat, lon, time_index)` directly for each grid point. Option (b) is cleaner and avoids coupling to Step 2's data model. The `add_tide_to_ssh()` function has a simple `(pd.Series, pd.Series) → pd.Series` signature and requires no adaptation.

### 2.4 Episode clustering / gap convention

The episode merging convention from Steps 2d–2e is:

```
EPISODE_MAX_GAP_DAYS = 1
```

Two exceedance days belong to the same episode if the gap between them is at most `EPISODE_MAX_GAP_DAYS + 1` calendar days (i.e., at most 1 non-exceedance day may separate them within one episode). This is the `_cluster_episodes()` logic in `src/02_threshold_calibration/05_pu_composite_calibration/scoring.py`.

**Semantic difference from Step 2:** In Steps 2d–2e, `_cluster_episodes()` operates on a **compound mask** (days where *both* Hₛ ≥ threshold AND SSH_total ≥ threshold simultaneously). In Step 3, the same clustering algorithm is applied independently to **single-variable exceedance masks** — one for Hₛ and one for SSH_total — to produce two independent storm catalogs. The algorithmic logic (gap tolerance, merging rule) is identical; only the input mask semantics differ.

Step 3 must implement the same gap convention for consistency. This is an open design decision if a different value is more scientifically appropriate (see Section 7).

### 2.5 Matching window convention (for reference only)

The causal window [D-2, D-1, D, D+1 00Z] from Steps 2b–2e is specific to threshold validation against reported events. Step 3 does not perform event matching against the disaster database — it applies thresholds to the continuous series. The causal window is not directly used in storm segmentation. It is documented here only for context.

### 2.6 Propagated caveats

The following caveats from Step 2 propagate to Step 3 and must be acknowledged in Step 3 documentation:

1. **NaN grid points:** Some coastal grid points have partial or complete NaN coverage due to GLORYS12/WAVERYS resolution near complex coastal geometries. The municipality-grid matching (Step 2 preprocessing) assigns each municipality to its **nearest valid ocean grid point** from the combined GLORYS12+WAVERYS dataset, but some grid points still have degraded coverage. These grid points produce NaN thresholds and empty catalogs. They must be tracked and logged, not silently dropped.
2. **No seasonal decomposition:** Thresholds are computed from the annual series without seasonal block-maxima approaches. This means threshold values are climatological, not season-specific.
3. **Tidal asynchronism:** SSH_total = zos(00:00 UTC) + tide_daily_max is a physical approximation. This propagates into the SSH_total storm catalog.
4. **GLORYS12 daily resolution:** Sub-daily SSH information is not available. Storm timing from the SSH_total catalog is accurate only to ±1 day.
5. **Threshold period resolved:** Thresholds are now computed from the full metocean record (1993–2025), not the validated period. This eliminates the previous caveat about applying validated-period thresholds to years outside that range. The only remaining caveat is that the event-matching validation scan (used in Step 2e to compute recall and PU scores) was restricted to 1998–2020 by the event database coverage, so the detection performance metrics are strictly validated only for that period.

---

## 3. INPUTS

| Input | Path | Format | Notes |
|-------|------|--------|-------|
| Unified metocean dataset | `data/test/metocean_sc_full_unified_waverys_grid.nc` | NetCDF4, xarray-readable | Variables: `VHM0` (Hₛ, daily max, m), `zos` (SSH, 00:00 UTC daily, m). Dimensions: `time`, `latitude`, `longitude`. Time: 1993–2025 daily. Full domain runs require the production dataset in `data/raw/`. |
| Step 2e optimal threshold pair | `outputs/threshold_calibration/tables/tab_TC5_optimal_pair_pu.csv` | CSV | Columns: `thr_hs_pct`, `thr_ssh_pct` (float fractions, e.g. 0.90 = q90). Single-row file. |
| Municipality–grid reference | `outputs/preprocessing/municipality_grid_ref.csv` | CSV | Columns: `municipality`, `muni_lat`, `muni_lon`, `grid_lat`, `grid_lon`, `grid_dist_km`, `hs_valid_frac`, `ssh_valid_frac`, `data_quality`, `coord_source`. Maps 27 union municipalities (expanded + legacy event databases) to their nearest valid ocean grid point. **For the SC test domain:** this file defines the set of coastal grid points to process. **For the full-domain production run:** grid points should be extracted directly from the metocean dataset using a coastal mask (see Domain Expansion below). Municipality labels are always optional metadata — the core catalog object is grid-point-based. |
| FES2022 tide model | `data/tide_models_clipped_brasil/fes2022b/` | Model binary files | Accessed via `eo-tides` Python library. Same path used by Steps 2c–2e. |

### Notes on the unified dataset

The current committed test fixture (`metocean_sc_full_unified_waverys_grid.nc`) covers the full SC coast but is a test subset. The production run requires the full-domain CMEMS download stored in `data/raw/`. Step 3 implementation should support both configurations via the config file.

Variable names in the unified NetCDF:
- `VHM0` — significant wave height (m), daily maximum from 3-hourly WAVERYS
- `zos` — sea surface height above geoid (m), daily 00:00 UTC from GLORYS12

SSH_total is computed at runtime by adding FES2022 tide — it is not pre-stored in the unified dataset.

### Domain expansion: full eastern Brazil coast

Step 3 is designed to produce storm catalogs for the **entire eastern coast of Brazil**, not just the Santa Catarina test domain used in Step 2. This requires:

1. **Additional CMEMS data download:** GLORYS12 (zos) and WAVERYS (VHM0) covering the full eastern Brazilian coast (~5°S to ~34°S, ~52°W to ~30°W or as appropriate for the coastal strip). The current test fixture covers only SC. A production-scale download must be performed before the full-domain run.
2. **Unified dataset production:** Step 1 (data preparation) must be rerun to produce a unified NetCDF covering the extended domain. The same regridding approach (GLORYS12 → WAVERYS grid) applies.
3. **FES2022 tide model coverage:** The clipped tide model files in `data/tide_models_clipped_brasil/` must cover the full domain. If the current clip is SC-only, an extended clip is needed.
4. **Municipality-grid reference scope:** For the full domain, the coastal grid-point catalog is the primary object. Municipality labeling (if desired) requires an extended reference mapping or a reverse-geocoding API.
5. **Computational considerations:** The full domain will have ~1000+ coastal grid points (vs. ~10 for SC). Tide computation via `eo-tides` may become a bottleneck; consider caching or parallelization.

The test-domain run (SC coast) serves as the proof-of-concept. The full-domain run is the production target.

---

## 4. EXPECTED OUTPUTS

### 4.1 Storm catalogs

Step 3 should produce two independent catalogs — one for Hₛ storms and one for SSH_total storms. The catalog format should be structured JSON (consistent with the repository convention stated in Step 3 of the root README) or CSV.

**Recommended output format: JSON (primary) + CSV summary (secondary)**

The JSON catalog is the primary analytical artifact because it naturally accommodates variable-length event lists and nested time series. The CSV summary is for human inspection and downstream statistical analysis.

#### Hₛ storm catalog

**File:** `outputs/storm_catalog/catalog_hs_storms.json`

Per-entry schema:

```json
{
  "grid_lat": -27.6,
  "grid_lon": -48.6,
  "municipality": "Laguna",
  "thr_hs_pct": 0.90,
  "thr_hs_abs": 2.34,
  "storms": [
    {
      "event_id": "hs_-27.60_-48.60_19990815",
      "date_start": "1999-08-15",
      "date_end": "1999-08-17",
      "duration_days": 3,
      "peak_value": 2.91,
      "peak_date": "1999-08-16",
      "integrated_intensity": 6.87,
      "time_series": {
        "dates": ["1999-08-15", "1999-08-16", "1999-08-17"],
        "values": [2.45, 2.91, 2.68]
      }
    }
  ]
}
```

**Note:** `municipality` is optional metadata (nullable). When a grid point is not associated with a municipality (e.g., in the full-domain run), this field should be `null`.

#### SSH_total storm catalog

**File:** `outputs/storm_catalog/catalog_ssh_total_storms.json`

Same schema as Hₛ catalog, replacing `hs` references with `ssh_total`. The `municipality` field is likewise optional (nullable).

```json
{
  "grid_lat": -27.6,
  "grid_lon": -48.6,
  "municipality": "Laguna",
  "thr_ssh_pct": 0.90,
  "thr_ssh_abs": 1.12,
  "storms": [...]
}
```

### 4.2 Per-event attributes (required for each storm)

| Attribute | Description | Units |
|-----------|-------------|-------|
| `event_id` | Unique identifier: `<var>_<lat>_<lon>_<YYYYMMDD>` (e.g. `hs_-27.60_-48.60_19990815`) | string |
| `date_start` | First day of threshold exceedance | ISO date |
| `date_end` | Last day of threshold exceedance | ISO date |
| `duration_days` | Number of days in episode | days |
| `peak_value` | Maximum variable value within the episode | m |
| `peak_date` | Date of peak value | ISO date |
| `integrated_intensity` | Sum of exceedance above threshold across episode days: Σ(value − threshold) | m·day |
| `time_series.dates` | Chronological list of dates within the episode | list[ISO date] |
| `time_series.values` | Variable values on each episode day | list[float] |

### 4.3 Summary tables (CSV)

| File | Description |
|------|-------------|
| `outputs/storm_catalog/tables/tab_SC3_hs_storms_summary.csv` | One row per Hₛ storm event: all per-event attributes in flat tabular form |
| `outputs/storm_catalog/tables/tab_SC3_ssh_total_storms_summary.csv` | One row per SSH_total storm event |
| `outputs/storm_catalog/tables/tab_SC3_catalog_metadata.csv` | Per-grid-point metadata: n_storms, mean_duration, mean_peak, data coverage, NaN fraction |

**Naming convention:** The `SC3` prefix follows the project's step-based table naming (cf. `TC4_`, `TC5_` for Steps 2d/2e). Replace with an appropriate domain label for production runs if needed.

### 4.4 Run metadata

**File:** `outputs/storm_catalog/logs/run_metadata.json`

```json
{
  "run_date": "2026-...",
  "dataset": "metocean_sc_full_unified_waverys_grid.nc",
  "period_full_series": ["1993-01-01", "2025-12-31"],
  "period_threshold_computation": "full_record",
  "period_validation_scan": ["1998-01-01", "2020-12-31"],
  "thr_hs_pct": 0.90,
  "thr_ssh_pct": 0.90,
  "episode_max_gap_days": 1,
  "tide_model": "FES2022",
  "n_grid_points": ...,
  "n_hs_storms_total": ...,
  "n_ssh_total_storms_total": ...
}
```

---

## 5. PROPOSED ANALYTICAL WORK PLAN

The following is a granular step-by-step implementation plan. Each numbered item corresponds to a logically distinct code unit.

### 5.1 Load and validate inputs

1. Load `tab_TC5_optimal_pair_pu.csv` and extract `thr_hs_pct` and `thr_ssh_pct`. Validate that both are in [0.5, 1.0].
2. Load the unified metocean NetCDF dataset using `xarray`. Confirm presence of `VHM0` and `zos` variables and the expected `time`, `latitude`, `longitude` dimensions.
3. Load `municipality_grid_ref.csv`. Filter to grid points with `data_quality == "ok"` and `hs_valid_frac > 0` (or a configurable minimum coverage fraction).
4. Identify the unique set of coastal grid points to process. **SC test domain:** extract unique `(grid_lat, grid_lon)` pairs from `municipality_grid_ref.csv`. **Full-domain production:** extract all coastal ocean grid points from the unified dataset (grid cells adjacent to the land mask). The implementation should support both modes via the config file.

### 5.2 Threshold computation and catalog periods

5. Load the full 1993–2025 metocean series. Thresholds are computed from the **full record** (not a clipped validated period). This is consistent with the corrected Step 2e implementation, which computes percentile thresholds from the full metocean record and restricts only the event-matching scan to the validated period (1998–2020). The storm catalog is also generated from the full series.

### 5.3 Compute SSH_total per grid point

6. For each unique coastal grid point, compute the FES2022 daily-maximum tidal series by calling `_compute_daily_max_tides(lat, lon, time_index)` from Step 2c's `tides.py` (see §2.3 interface note). The `time_index` should span the full metocean record (1993–2025).
7. Compute SSH_total = zos + tide_daily_max using `add_tide_to_ssh()` from Step 2c.
8. Validate that SSH_total is not all-NaN for each grid point. Log a warning for grid points where tide computation fails or returns all-NaN.

### 5.4 Compute local percentile thresholds

9. For each grid point, extract the Hₛ series from the **full metocean record** (1993–2025) and compute the local q90 threshold using `series.quantile(thr_hs_pct)` on finite values only.
10. Repeat for SSH_total: extract the full-record series and compute the local q90 threshold.
11. Store thresholds in a per-grid-point lookup dict: `{(lat, lon): {"thr_hs": float, "thr_ssh": float}}`.
12. For grid points where the threshold is NaN (all-NaN series), log the point and mark it as skipped.

### 5.5 Generate binary exceedance masks (full series)

13. For each grid point, apply thresholds to the **full 1993–2025 series** (not the clipped validated series):
    ```
    hs_exceedance_mask(t)  = VHM0(t) >= thr_hs
    ssh_exceedance_mask(t) = SSH_total(t) >= thr_ssh
    ```
14. These are independent masks — the Hₛ catalog and SSH_total catalog are generated independently (not as joint exceedances).

### 5.6 Segment consecutive exceedances into storm episodes

15. For each grid point and each variable, apply the `_cluster_episodes()` logic (gap tolerance = `EPISODE_MAX_GAP_DAYS = 1`): consecutive exceedance days separated by at most 1 non-exceedance day are merged into a single episode.
16. Assign a unique `event_id` to each episode: `<var_prefix>_<lat>_<lon>_<YYYYMMDD>` where `<lat>/<lon>` are the grid-point coordinates (formatted to 2 decimal places) and `<YYYYMMDD>` is the episode start date. This grid-point-based ID is consistent with the catalog's spatial design and does not depend on municipality labeling.

### 5.7 Compute per-event attributes

17. For each episode, compute:
    - `date_start` and `date_end` (first and last exceedance day)
    - `duration_days` = number of days in episode
    - `peak_value` = maximum variable value within the episode
    - `peak_date` = date of peak value
    - `integrated_intensity` = sum of (value − threshold) for all episode days (values below threshold after merging are treated as 0 for integration purposes)
    - `time_series.dates` and `time_series.values` (all days within the episode)

### 5.8 Assemble and serialize catalogs

18. Assemble the Hₛ catalog as a list of per-grid-point entries (each with grid metadata + storm list).
19. Assemble the SSH_total catalog with the same structure.
20. Write both catalogs to JSON: `outputs/storm_catalog/catalog_hs_storms.json` and `outputs/storm_catalog/catalog_ssh_total_storms.json`.
21. Flatten to CSV summary tables: `tab_SC3_hs_storms_summary.csv` and `tab_SC3_ssh_total_storms_summary.csv`.

### 5.9 Generate diagnostic figures and QA tables

22. **Figure SC-1:** Time series of annual storm count per variable (domain-mean) to verify plausibility.
23. **Figure SC-2:** Spatial map of mean storm duration and mean peak intensity at each coastal grid point.
24. **Figure SC-3:** Distribution of storm durations (histogram) per variable.
25. **Figure SC-4:** Seasonal climatology of storm frequency (monthly mean count per grid point, domain-averaged).
26. **Table SC-QA:** Per-grid-point QA summary: n_storms, mean_duration, NaN fraction, threshold values.
27. Write `run_metadata.json` with all configuration parameters and aggregate statistics.

---

## 6. PROPOSED MODULE/FILE ORGANIZATION

```
src/03_storm_catalog_generation/
├── README.md                    # This planning file
├── main.py                      # CLI orchestrator
│                                  --all runs the full pipeline
│                                  --load-validate: Step 5.1–5.2
│                                  --tides: Step 5.3
│                                  --thresholds: Step 5.4
│                                  --catalog: Steps 5.5–5.8
│                                  --figures: Step 5.9
│                                  --summary: print summary
├── io.py                        # I/O helpers
│                                  load_optimal_thresholds()   — reads tab_TC5_optimal_pair_pu.csv
│                                  load_unified_dataset()      — reuses Step 2b pattern
│                                  load_municipality_ref()     — reads municipality_grid_ref.csv
│                                  save_catalog_json()         — serializes catalog to JSON
│                                  save_catalog_csv()          — flattens catalog to CSV summary
├── tides.py                     # Thin wrapper around Step 2c tides.py
│                                  get_tide_cache_for_grid_points() — calls _compute_daily_max_tides per point
│                                  compute_ssh_total_series()       — calls add_tide_to_ssh
│                                  NOTE: call Step 2c low-level functions directly (see §2.3 interface note)
├── segmentation.py              # Storm detection and episode segmentation
│                                  compute_local_threshold()  — percentile from finite values
│                                  build_exceedance_mask()    — boolean Series
│                                  cluster_episodes()         — gap-tolerance merging
│                                  compute_episode_attributes() — per-episode metrics
│                                  build_storm_catalog()      — assembles catalog for one grid point
├── metrics.py                   # Per-event attribute computation
│                                  compute_integrated_intensity()  — Σ(value − threshold) × dt
│                                  compute_peak()                  — (peak_value, peak_date)
│                                  compute_duration()              — n_days
├── figures.py                   # Diagnostic visualizations
│                                  plot_annual_counts()          — SC-1
│                                  plot_spatial_intensity()      — SC-2
│                                  plot_duration_distribution()  — SC-3
│                                  plot_seasonal_climatology()   — SC-4
└── config/
    ├── __init__.py
    └── analysis_config.py       # All user-editable parameters and paths
                                   UNIFIED_FILE, OPTIMAL_PAIR_FILE, MUNICIPALITY_GRID_REF
                                   TIDE_MODELS_DIR, TIDE_MODEL
                                   EPISODE_MAX_GAP_DAYS, THR_COMPUTATION_PERIOD
                                   OUTPUT_ROOT, CATALOG_DIR, FIG_DIR, TAB_DIR, LOG_DIR
                                   HS_VAR, SSH_VAR, SSH_TOTAL_VAR
                                   FULL_SERIES_START, FULL_SERIES_END
```

### Module roles summary

| File | Role |
|------|------|
| `main.py` | CLI entry point; orchestrates the pipeline in order |
| `io.py` | All I/O: loading inputs, saving JSON/CSV outputs |
| `tides.py` | Thin bridge to Step 2c tide infrastructure; computes SSH_total per grid point |
| `segmentation.py` | Core storm detection: threshold computation, exceedance masking, episode clustering, attribute assembly |
| `metrics.py` | Per-episode attribute calculation (intensity, duration, peak) |
| `figures.py` | Diagnostic plots for QA |
| `config/analysis_config.py` | All path and parameter configuration |

---

## 7. OPEN DESIGN DECISIONS

These are genuine open questions that require human review before coding begins.

### 7.1 Gap tolerance for episode merging

**Default inherited from Step 2:** `EPISODE_MAX_GAP_DAYS = 1` (at most 1 non-exceedance day within an episode).

**Open question:** Is 1 day the scientifically appropriate choice for storm catalog generation? Steps 2d–2e used this value during the threshold scan for false alarm identification. A gap of 0 days (strictly consecutive exceedances) would produce shorter, more fragmented catalogs; a gap of 2 days would merge more episodes into longer storms.

**Recommendation before implementation:** Danilo should decide whether to keep `EPISODE_MAX_GAP_DAYS = 1` (consistent with calibration) or use a different physically motivated value for the catalog. If changed, document the rationale in the config.

### 7.2 Threshold percentile computation period — RESOLVED

**Decision (authoritative, implemented in Step 2e corrections):** Thresholds are computed from the **full metocean record** (1993–2025). This corresponds to option (B) from the original question.

**Rationale:** The validated period (1998–2020) restricts only the event-matching scan where detected episodes are compared against reported events. The climatological percentile computation should use the longest available record for maximum statistical robustness. This distinction was implemented in the corrective pass for Steps 2d and 2e (see `build_event_records()` now called with `ds_full` before temporal clipping).

**This is no longer an open question.** Step 3 should compute thresholds from the full record.

### 7.3 NaN coverage threshold

**Current State (from municipality_grid_ref.csv):** Grid points with `data_quality == "ok"` are used. Some points have partial NaN coverage (`hs_valid_frac < 1.0` or `ssh_valid_frac < 1.0`).

**Open question:** What minimum valid data fraction should a grid point have to be included in the catalog? Suggestions:
- `hs_valid_frac >= 0.90` and `ssh_valid_frac >= 0.90` (10% tolerance)
- `hs_valid_frac >= 0.80` and `ssh_valid_frac >= 0.80` (20% tolerance)

Grid points below the threshold should be listed in the QA table with a `skipped_reason` column.

### 7.4 Integrated intensity definition

**Two candidate definitions:**
- (A) `Σ(value − threshold)` summed over all episode days — measures total exceedance above the threshold
- (B) `Σ(value)` summed over all episode days — measures absolute storm intensity

Option (A) is more informative for hazard assessment (it quantifies how much the event exceeds the detection threshold). Option (B) is simpler to interpret physically.

**Recommendation:** Option (A) is preferred for consistency with the exceedance framework. This should be confirmed before implementation.

### 7.5 Output format: JSON vs NetCDF

The root README and Step 3 description specify JSON as the catalog format. JSON is flexible and human-readable but not ideal for large spatial grids. For the full Brazilian coast (~1000+ grid points × 32 years), NetCDF or Parquet may be more efficient.

**Open question:** For the test domain (south SC, ~10 grid points), JSON is fine. For the full domain, a different format may be needed. This decision should be made before the full-domain implementation begins.

---

## 8. QA / VALIDATION CHECKLIST

A future implementation agent should verify the following before declaring Step 3 complete:

- [ ] **Threshold loaded correctly:** `thr_hs_pct` and `thr_ssh_pct` from `tab_TC5_optimal_pair_pu.csv` match the expected values (default: 0.90 / 0.90). Log the loaded values at startup.
- [ ] **SSH_total computed correctly:** At a known grid point, SSH_total values should be > zos values (tide is positive in the tidal mean). The difference (tide_daily_max) should have a mean of approximately +0.5 m based on Step 2c results (~+0.53 m mean SSH_total vs ~+0.05 m mean SSH from Step 2c).
- [ ] **Independent catalogs:** Hₛ storm catalog and SSH_total storm catalog are generated independently (not as joint exceedances). Verify: some storms appear in one catalog but not the other on the same dates.
- [ ] **Event counts are plausible:** For q90 thresholds, exceedances should occur approximately 10% of all days. With `EPISODE_MAX_GAP_DAYS = 1`, the number of independent storm episodes per grid point per year should be in the range of ~10–30 for both variables. Verify against historical intuition.
- [ ] **All per-event attributes computed:** Each storm entry in the catalog JSON has: `event_id`, `date_start`, `date_end`, `duration_days`, `peak_value`, `peak_date`, `integrated_intensity`, `time_series.dates`, `time_series.values`. Verify no missing keys.
- [ ] **No duplication artifacts:** Each episode appears exactly once per variable per grid point. Verify: no overlapping start/end date ranges within the same grid point catalog.
- [ ] **NaN grid points tracked:** Grid points with NaN thresholds or all-NaN series are listed in the QA table with a `skipped_reason` and do not appear in the JSON catalog.
- [ ] **Output schema documented:** The JSON schema (field names, types, units) is documented in the config or module docstring so that Step 4 can consume it without ambiguity.
- [ ] **Run metadata saved:** `run_metadata.json` exists and contains all key parameters used in the run (threshold percentiles, gap tolerance, validated period, tide model, dataset path, run date).

---

## 9. RELATION TO STEP 4

Step 4 (Compound Event Detection) identifies compound events as episodes where an Hₛ storm and an SSH_total storm overlap temporally at the same grid point. The Step 3 catalog design directly shapes what Step 4 can compute.

### Spatial alignment

Both the Hₛ catalog and the SSH_total catalog are built on the same WAVERYS grid (after GLORYS12 regridding to WAVERYS grid in Step 1). Step 4 can join the two catalogs by `(grid_lat, grid_lon)` — no spatial interpolation is needed.

### Temporal overlap logic

Step 4 compares the `[date_start, date_end]` intervals of Hₛ storms and SSH_total storms at each grid point. A compound event is defined when these intervals overlap by at least one day (or a configurable minimum overlap threshold — a Step 4 design decision).

The `time_series.dates` field in each catalog entry allows Step 4 to compute exact day-by-day overlap metrics rather than just start/end interval overlap. This supports:
- Exact overlap duration (number of co-exceedance days)
- Peak time lag (date of Hₛ peak minus date of SSH_total peak)

### Event attributes Step 4 derives from Step 3

Step 4 will use the following Step 3 attributes for each compound event:
- From the Hₛ storm: `peak_value`, `peak_date`, `duration_days`, `integrated_intensity`
- From the SSH_total storm: `peak_value`, `peak_date`, `duration_days`, `integrated_intensity`
- Derived in Step 4: overlap duration, peak time lag, joint peak (max of each variable during overlap period)

### Data model design recommendation

To facilitate Step 4, each catalog entry should be indexed by `(grid_lat, grid_lon, date_start)` in both the JSON and CSV formats. When implementing Step 4, catalogs should be loaded as flat DataFrames (from the CSV summary) keyed on these columns for efficient temporal join operations.

The JSON catalog with embedded `time_series` is the primary artifact for reproducing individual event traces. The CSV summary is the primary artifact for statistical analysis and compound event detection.

---

## References

- Leal, K. B. et al. (2024). Identification of coastal natural disasters using official databases. *Nat Hazards*, 120, 11465–11482.
- Bekker, J., and Davis, J. (2020). Learning from positive and unlabeled data: a survey. *Machine Learning*, 109, 719–760.
- Zscheischler, J. et al. (2020). A typology of compound weather and climate events. *Nat. Rev. Earth Environ.*, 1, 333–347.
- Green, J. et al. (2025). A comprehensive review of compound flooding literature. *NHESS*, 25, 747–816.
- CMEMS GLORYS12: Global Ocean Physics Reanalysis. Copernicus Marine Environment Monitoring Service.
- CMEMS WAVERYS: Global Ocean Waves Reanalysis. `GLOBAL_MULTIYEAR_WAV_001_032`.
