# SCIENTIFIC_NOTES — Step 3: Storm Catalog Generation

## Research Questions

1. How are extreme ocean events (wave height, sea level) formally identified and cataloged along the entire Brazilian coast?
2. What is the spatial distribution of storm frequency and intensity for Hₛ and SSH_total independently?
3. How sensitive is the resulting catalog to the threshold definition, gap tolerance, and data quality requirements?

---

## Physical / Statistical Framework

### Peaks-Over-Threshold (POT) Detection

Storm detection follows the peaks-over-threshold (POT) approach: for each coastal grid point and each variable (Hₛ, SSH_total), days exceeding a locally calibrated percentile threshold are flagged as exceedance days. Consecutive exceedance days are merged into discrete storm episodes. A tolerance of **≤ 1 non-exceedance day** between exceedances is permitted within the same episode; i.e., a single calm day flanked by exceedances does not split the episode.

For a given grid point $(i, j)$ and variable $X \in \{H_s, \text{SSH}_{\text{total}}\}$, the threshold is:

$$
X^{*}_{ij} = Q_p\bigl(X_{ij}(t)\bigr), \quad p = 0.90
$$

where $Q_p$ denotes the $p$-th percentile computed from the full available record (1993-01-01 to 2025-12-31), excluding NaN values. The exceedance mask is:

$$
E_{ij}(t) = \begin{cases} 1, & X_{ij}(t) \geq X^{*}_{ij} \\ 0, & \text{otherwise} \end{cases}
$$

### Episode Clustering

The clustering algorithm scans the binary exceedance mask chronologically and groups contiguous True values into episodes, merging across gaps of at most $g_{\max} = 1$ day:

$$
\text{If } E(t) = 0 \;\text{ and }\; E(t-1) = 1 \;\text{ and }\; E(t+1) = 1 \implies \text{gap is bridged (same episode)}
$$

This gap tolerance follows the operational convention established in Step 2e (PU composite calibration), which itself follows common practice in coastal hazard studies where individual storm events may span 2–5 days with brief intermissions that do not represent distinct meteorological systems.

### Per-Episode Attributes

For each episode $k$ at grid point $(i, j)$, the following attributes are computed:

- **Peak value**: $X^{\text{peak}}_k = \max_{t \in [t_0^k, t_1^k]} X(t)$
- **Peak date**: $t^{\text{peak}}_k = \arg\max_{t \in [t_0^k, t_1^k]} X(t)$
- **Duration**: $d_k = t_1^k - t_0^k + 1$ (calendar days, inclusive)
- **Integrated intensity**: $I_k = \sum_{t = t_0^k}^{t_1^k} \max\bigl(X(t) - X^{*}_{ij},\; 0\bigr)$

The integrated intensity captures both the magnitude and persistence of the exceedance and is analogous to the degree-day concept in climate science.

### SSH_total Definition

Total sea surface height is a composite variable combining the ocean dynamic sea level from GLORYS12 and the astronomical tidal signal from the FES2022 model:

$$
\text{SSH}_{\text{total}}(i, j, t) = \text{zos}(i, j, t)\big|_{00\text{UTC}} + \max_{h \in [0,24)} \text{tide}(i, j, t, h)
$$

where `zos` is sampled at the daily GLORYS12 time step (00:00 UTC) and the tide is the daily maximum computed from hourly FES2022 predictions. This definition follows the canonical form established in Step 2c and is mandatory for all subsequent analyses.

**[CAVEAT]** The `zos` sample at 00:00 UTC will not in general coincide with the time of maximum tide. The composite therefore approximates the worst-case daily total sea level rather than an exact instantaneous superposition. See *Caveats and Limitations*.

---

## Datasets and Variables

| Dataset | Variable | Resolution | Period | Source |
|---------|----------|------------|--------|--------|
| WAVERYS | VHM0 (Hₛ) | 0.2° × 0.2°, daily | 1993-01-01 – 2025-12-31 | Copernicus Marine Service |
| GLORYS12 | zos (dynamic SSH) | 0.2° × 0.2° (regridded), daily | 1993-01-01 – 2025-12-31 | Copernicus Marine Service |
| FES2022 | Tidal constituents | Point prediction | 1993-01-01 – 2025-12-31 | via `eo-tides` library |
| Natural Earth | 10 m coastline shapefile | Vector | — | naturalearthdata.com |

The unified metocean dataset (`metocean_brazil_unified_waverys_grid.nc`) was pre-computed in Step 1 by regridding GLORYS12 onto the WAVERYS grid and merging both products into a single time–lat–lon cube.

---

## Methodology

### Algorithmic Summary

1. **Load unified dataset** — open the preprocessed NetCDF; select coastal grid points within 50 km of the coastline; discard grid points with < 80% temporal coverage.
2. **Load calibrated thresholds** — read the optimal threshold pair (q90/q90) from Step 2e output (`tab_TC5_optimal_pair_pu.csv`). Step 3 does not recalibrate thresholds; it inherits them.
3. **Compute tides** (if SSH_total is not pre-computed) — for each grid point, predict hourly FES2022 tides and compute the daily maximum; add to `zos` to form SSH_total.
4. **Threshold application** — compute local percentile values at each grid point over the full record.
5. **Exceedance masking** — build binary exceedance arrays for Hₛ and SSH_total independently.
6. **Episode clustering** — group consecutive exceedance days into storm episodes with gap tolerance = 1 day.
7. **Attribute extraction** — for each episode, compute peak value, peak date, duration, integrated intensity, and full daily time series.
8. **Catalog serialization** — export two independent JSON catalogs (Hₛ storms, SSH_total storms) plus metadata and summary CSVs.

### Two Independent Catalogs

Step 3 deliberately produces **two separate, univariate catalogs** — one for Hₛ and one for SSH_total. The temporal intersection of these catalogs (compound event detection) is deferred to Step 4. This separation preserves methodological clarity:

- Each catalog can be validated, analyzed, and visualized independently.
- Compound detection logic (overlap rules, intensity normalization) can evolve without re-running the storm detection.
- The catalogs serve as building blocks for multiple downstream analyses beyond compound events.

### Grid Filtering Criteria

| Criterion | Value | Rationale |
|-----------|-------|-----------|
| Maximum distance to coastline | 50 km | Exclude open-ocean grid points; focus on coastal-relevant cells |
| Minimum valid data fraction | 80% | Ensure statistical reliability of percentile estimates |

The 50 km coastal buffer was computed using geodesic distance from each WAVERYS grid-point center to the nearest Natural Earth 10m coastline segment. Points farther inland (over land in the WAVERYS mask) are automatically excluded by the ocean-only mask.

---

## Assumptions

1. **Stationarity**: The threshold percentile is computed from the entire 33-year record, implicitly assuming that the underlying distribution is stationary. No trend removal or detrending is applied. If long-term trends exist (e.g., increasing Hₛ due to climate change), the 90th percentile will be biased toward the distribution center and some early (late) events may be over-detected (under-detected).

2. **Local independence**: Thresholds are computed independently at each grid point. Spatial coherence of storm systems is not enforced — neighboring grid points may detect episodes of different durations or timing. This design choice is intentional: the catalog serves as a pointwise inventory; spatial aggregation is a downstream concern.

3. **Daily resolution sufficiency**: The analysis operates on daily data. Sub-daily storm intensification and decay are not resolved. Storm timing is accurate to ±1 day. This is a fundamental limitation of the WAVERYS/GLORYS12 daily products used.

4. **Additive SSH_total**: The total sea level is approximated as zos + tide_daily_max. Non-linear interactions between surge and tide (e.g., tide–surge interaction in shallow estuaries) are not captured. This approximation is standard for open-coast applications at 0.2° resolution.

5. **Threshold pair optimality**: The q90/q90 pair is taken as given from Step 2e's PU composite calibration. Step 3 does not question or re-evaluate this choice. If the calibration is revised, the catalogs must be regenerated.

---

## Results and Interpretation

### Production Run (2025-04-15)

| Metric | Value |
|--------|-------|
| Grid points processed | 808 |
| Grid points skipped (quality) | 176 |
| Hₛ storms detected | 404,535 |
| SSH_total storms detected | 324,929 |
| Period | 1993-01-01 to 2025-12-31 |
| Mean Hₛ storms per point | ~500 (≈ 15.2 yr⁻¹) |
| Mean SSH_total storms per point | ~402 (≈ 12.2 yr⁻¹) |

The Hₛ catalog contains more storms than the SSH_total catalog across the domain. This is consistent with the higher temporal autocorrelation of wave height (swell persistence) compared to sea level anomalies, which leads to more frequent but shorter SSH exceedance episodes when using the same gap tolerance.

### Spatial Patterns (qualitative)

- **Hₛ**: Annual storm frequency is highest along the southern Brazilian coast (25–35°S), decreasing equatorward. Peak intensities follow the same gradient, reflecting the dominance of extratropical cyclones as wave generators.
- **SSH_total**: Storm frequency shows a more complex spatial pattern influenced by shelf width, tidal amplitude, and exposure to both tropical and extratropical forcing. The widest continental shelves (Amazon mouth, southern Santa Catarina) show distinct regimes.

**[PRELIMINARY]** Detailed spatial analysis maps are available on the results website (`/results/storm-maps`).

---

## Caveats and Limitations

1. **Temporal resolution**: Daily data means sub-daily co-occurrence of wave and sea-level extremes is not resolved. A compound event detected at daily resolution may or may not involve simultaneous extremes within the same 24 h window.

2. **zos–tide timing mismatch**: The SSH_total formula uses zos at 00:00 UTC combined with the daily maximum tide. These do not share the same timestamp. The resulting SSH_total overestimates the true instantaneous total sea level by an amount proportional to the diurnal range of the surge.

3. **Nearshore processes**: WAVERYS at 0.2° resolution does not resolve nearshore wave transformation (shoaling, refraction, breaking). Coastal flooding assessments require wave downscaling beyond this catalog.

4. **Gap tolerance sensitivity**: The 1-day gap tolerance merges events that may be meteorologically distinct but temporally adjacent. Reducing the tolerance to 0 would increase the storm count and decrease mean duration. This has not been explored systematically.

5. **No minimum duration filter**: Single-day exceedances are included as storm episodes. Whether a 1-day exceedance constitutes a meaningful "storm" depends on the application. Filtering by minimum duration (e.g., ≥ 2 days) is a valid downstream choice.

6. **Stationarity assumption**: No test for trends is performed. The literature suggests increasing wave heights in the South Atlantic over recent decades (e.g., Reguero et al. 2019), which would affect the percentile-based threshold.

---

## Decisions Inherited from Step 2

| Decision | Origin | Step 3 Treatment |
|----------|--------|-----------------|
| Threshold pair (q90/q90) | Step 2e — PU composite calibration | Loaded directly; not recomputed |
| SSH_total = zos + tide_daily_max | Step 2c — canonical definition | Applied identically |
| Threshold period = full record | Step 2e — corrected from initial 1998–2020 | Used for percentile computation |
| Gap tolerance = 1 day | Step 2e — gap convention | Inherited without modification |
| NaN handling (log + skip) | Step 2 — transparency pattern | Grid points with < 80% valid data are logged and excluded |

---

## Next Steps

1. **Step 4 — Compound event detection**: Temporal intersection of Hₛ and SSH_total catalogs to identify compound events. Classification into Hₛ-only, SSH_total-only, and compound classes. Normalized intensity metric for compound events.
2. **Spatial clustering**: Group storm episodes across neighboring grid points into spatially coherent storm systems (track-like objects). Not yet implemented.
3. **Return period estimation**: Fit extreme value distributions (GEV, GPD) to the annual maxima or POT catalogs at each grid point. Requires catalog as input.
4. **Temporal trend analysis**: Test for trends in storm frequency and intensity over the 33-year record using Mann-Kendall or equivalent non-parametric tests.

---

## References

- Reguero, B. G., Losada, I. J., & Méndez, F. J. (2019). A recent increase in global wave power as a consequence of oceanic warming. *Nature Communications*, 10(1), 205. https://doi.org/10.1038/s41467-018-08066-0
- Cavaleri, L., et al. (2024). Wave climate variability in the South Atlantic. *Ocean Modelling*, 191, 102415.
- Lellouche, J.-M., et al. (2021). The Copernicus Global 1/12° Oceanic and Sea Ice GLORYS12 Reanalysis. *Front. Earth Sci.*, 9, 698876. https://doi.org/10.3389/feart.2021.698876
- Law-Chune, S., et al. (2021). WAVERYS: a CMEMS global wave reanalysis during the altimetry period. *Ocean Dynamics*, 71, 357–379. https://doi.org/10.1007/s10236-020-01433-w
- Lyard, F. H., et al. (2021). FES2014 global ocean tide atlas: design and performance. *Ocean Science*, 17(3), 615–649. https://doi.org/10.5194/os-17-615-2021
