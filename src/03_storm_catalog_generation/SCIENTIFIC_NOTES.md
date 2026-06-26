# SCIENTIFIC_NOTES — Step 3: Hazard Characterization of Extreme and Compound Coastal Events

## Research Questions

1. How are extreme ocean events (wave height, sea level) formally identified and cataloged along the entire Brazilian coast?
2. What is the spatial distribution of storm frequency and intensity for Hₛ and SSH_total independently?
3. How sensitive is the resulting catalog to the threshold definition, gap tolerance, and data quality requirements?
4. What fraction of extreme events are compound (simultaneous waves + sea level)? How do compound events differ from univariate events in intensity, duration, and spatial distribution?
5. Are there statistically significant trends in storm frequency, intensity, or duration over the 33-year record?
6. What are the return levels for extreme Hₛ and SSH_total at each coastal grid point?
7. How strongly are wave height and sea level extremes statistically dependent during compound events?

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

Step 3 deliberately produces **two separate, univariate catalogs** — one for Hₛ and one for SSH_total — in sub-module 3.1. The temporal intersection of these catalogs (compound event detection) is performed in a **separate sub-module, 3.2** (`02_compound_detection/`), operating on the two catalogs as inputs. (Historical note: in the pre-2025 numbering this intersection was called "Step 4"; the restructuring described below folded it into Step 3 as sub-module 3.2.) This separation preserves methodological clarity:

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

### Production Run — Storm Catalogs (2025-04-15)

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

### Hazard Characterization — Full Pipeline Run (2025-05-16)

All 7 submodules executed successfully in 90.6 seconds. 808/808 grid points processed for all modules. No grid points were dropped or had missing data in any module.

| Module | Runtime | Key Output |
|--------|---------|------------|
| 3.2 Compound | 14.5 s | 96,031 compound events (across 808 pts) |
| 3.3 Duration | 8.3 s | Duration statistics for 808 pts |
| 3.4 Seasonality | 8.3 s | Monthly climatology for 808 pts |
| 3.5 Trends | 31.8 s | Mann–Kendall for 8 series × 808 pts |
| 3.6 EVA | 22.4 s | GPD return levels for 808 pts |
| 3.7 Dependence | 1.3 s | τ, ρ, χ, χ̄ for 808 pts |
| 3.8 Site Export | 4.0 s | 2.4 MB unified JSON (87 fields/pt) |

### Spatial Patterns (qualitative)

- **Hₛ**: Annual storm frequency is highest along the southern Brazilian coast (25–35°S), decreasing equatorward. Peak intensities follow the same gradient, reflecting the dominance of extratropical cyclones as wave generators.
- **SSH_total**: Storm frequency shows a more complex spatial pattern influenced by shelf width, tidal amplitude, and exposure to both tropical and extratropical forcing. The widest continental shelves (Amazon mouth, southern Santa Catarina) show distinct regimes.
- **Compound events**: Higher compound rates in the south (~4–6 yr⁻¹) vs. northeast (~1–3 yr⁻¹). The dependence structure (τ, ρ) is moderate positive throughout, with stronger coupling in the south.

Detailed interactive maps are available on the results website (`/results/hazard-characterization`).

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

1. **Step 4 — Exposure, vulnerability & risk integration**: A first municipal-scale integration is **complete** (external workflow; see the "Step 4" section below) — SVI_Coast_2022, Hazard_Index, Risk_Comp, Risk_Hazard for the coastal municipalities. Open follow-ups: revisit the equal-weight aggregation in light of the negative frequency↔intensity correlation, and bring the index computation into a versioned script in this repo.
2. **Validation against reported events**: Cross-reference compound catalog with the Leal et al. (2024) SC disaster database and the expanded S2ID registry.
3. **Spatial clustering**: Group storm episodes across neighboring grid points into spatially coherent storm systems (track-like objects). Not yet implemented.
4. **Bivariate / copula EVA**: Fit copulas to compound (Hₛ, SSH_total) pairs for joint return period estimation. The dependence analysis (Step 3.7) provides empirical input for copula selection.

---

## Hazard Characterization — Extended Framework

### 2025-05 — Restructuring Step 3

Step 3 has been expanded from "Storm Catalog Generation" to **"Hazard Characterization of Extreme and Compound Coastal Events"**. The former Steps 4–8 (compound detection, trends, EVA, etc.) are now submodules within Step 3, reflecting the fact that all these analyses operate on the same storm catalogs and share the same per-grid-point spatial framework.

### Submodule 3.2 — Compound Event Detection

**Definition**: A compound event at grid point $(i,j)$ exists when an Hₛ storm and an SSH_total storm overlap in time (share at least one calendar day). The compound event spans the union of all overlapping storms. If multiple Hₛ storms overlap the same SSH_total storm (or vice-versa), the resulting compound event covers the union.

Classification:
- **Hₛ-only**: Hₛ storm with no temporal overlap with any SSH_total storm
- **SSH_total-only**: SSH_total storm with no temporal overlap with any Hₛ storm
- **Compound**: Group of Hₛ + SSH_total storms sharing at least one day

**Normalized compound intensity**:

$$
I_{\text{norm}}^{\text{compound}} = \frac{1}{2}\left(\hat{H}_s + \hat{S}\right), \quad \hat{H}_s = \text{clip}\!\left(\frac{H_s^{\text{peak}} - Q_{05}^{H_s}}{Q_{95}^{H_s} - Q_{05}^{H_s}},\, 0,\, 1\right)
$$

where $Q_{05}$, $Q_{95}$ are computed from all compound event peaks across the full domain (not per grid point). This ensures comparability across space.

**Overlap metrics**: overlap_duration_days, peak_lag_days.

`peak_lag_days` $= t^{\text{peak}}_{H_s} - t^{\text{peak}}_{\text{SSH}}$ (calendar days). Sign convention:
**positive ⇒ the Hₛ peak occurs *after* the SSH_total peak** (Hₛ lags); negative ⇒ Hₛ leads;
zero ⇒ same day. (The site layer "Mean peak lag" uses this same convention.)

**[CAVEAT — non-contiguous overlap]** `overlap_duration_days` is `len(hs_days ∩ ssh_days)`,
where `hs_days` and `ssh_days` are the *unions* of all storm days in the compound group. When
a group contains multiple Hₛ and/or SSH_total storms, this intersection can be **temporally
discontinuous** (e.g. overlap on days 1–2 and again on days 7–8 → `overlap_duration_days = 4`
but the event spans 8 days). `date_start`/`date_end` are the first/last overlap days, so the
reported span can exceed `overlap_duration_days`. The metric therefore counts *total* shared
days, not a single contiguous co-occurrence window; for multi-storm groups its physical
interpretation as a single "overlap duration" is weaker. `union_duration_days` records the
full event footprint for comparison.

### Submodule 3.3 — Duration & Persistence

Per-grid-point summary statistics for Hₛ, SSH_total, and compound events:
- storm_count_total, annual_mean
- mean/p95/max duration (days)
- mean integrated intensity
- mean inter-event time (days) — time between consecutive episodes, characterizing return frequency

### Submodule 3.4 — Monthly Seasonality

Monthly climatology without circular statistics (unnecessary for discrete monthly counts):
- monthly_counts (12 values) and monthly_share (fractions)
- peak_month (month with highest count)
- seasonal_counts: DJF, MAM, JJA, SON

Applied independently for Hₛ, SSH_total, and compound events.

### Submodule 3.5 — Trend Analysis (Mann–Kendall + Sen Slope)

**Mann–Kendall test** (Mann 1945, Kendall 1975) applied to annual time series:

$$
S = \sum_{i=1}^{n-1}\sum_{j=i+1}^{n} \text{sign}(x_j - x_i)
$$

**Z-score** with continuity correction and tie adjustment. **Modified Mann–Kendall** (Hamed & Rao 1998) applied when significant lag-1 autocorrelation is detected (criterion $|r_1| > 1.96/\sqrt{n}$, only for $n \ge 10$):

**[IMPLEMENTATION NOTE]** This implementation computes the variance-correction factor $n/S^*$ from the autocorrelation of the **raw (mean-removed) series across all lags** ($r_i$, $i=1\dots n-1$). The original Hamed & Rao (1998) procedure uses the autocorrelation of the **ranks** of the data and includes only the **statistically significant** $r_i$. The simplification here (all lags, raw values) is common in practice but tends to be slightly more conservative; the correction is clamped to $\ge 1$ so it can only inflate, never deflate, $\mathrm{Var}(S)$. See `trends.py:_modified_variance_correction`.

$$
\text{Var}^*(S) = \text{Var}(S) \times \frac{n}{S^*}, \quad \frac{n}{S^*} = 1 + \frac{2}{n}\sum_{i=1}^{n-1}(n-i)\,r_i
$$

**Sen slope estimator** (Sen 1968):
$$
b = \text{median}\left\{\frac{x_j - x_i}{j - i}\right\}_{i < j}
$$

**Eight annual series tested** (in `trends.py:TREND_METRICS`):
1. annual Hₛ storm count
2. annual SSH_total storm count
3. annual compound event count
4. annual mean Hₛ peak value
5. annual mean SSH_total peak value
6. annual mean Hₛ duration
7. annual mean SSH_total duration
8. annual mean overlap duration

**[NOT COMPUTED]** A ninth series — *annual mean compound normalized intensity* — is
declared in `build_annual_series` but is never populated (no aggregation loop) and is
intentionally **not** included in `TREND_METRICS`. Reason: per-grid-point annual means
of the domain-normalized compound intensity are dominated by the few compound events
per year and were judged too noisy for a robust Mann–Kendall slope. To add it, populate
`series["annual_mean_compound_intensity_norm"]` from the compound events' intensity and
register the metric in `TREND_METRICS`.

### Submodule 3.6 — Univariate EVA (POT–GPD)

**Peaks-Over-Threshold with Generalized Pareto Distribution** applied to declustered storm peaks from the catalogs.

Excesses: $y = x - u$ where $u$ is the local q90 threshold.

GPD density:
$$
f(y;\, \xi,\, \sigma) = \frac{1}{\sigma}\left(1 + \xi\frac{y}{\sigma}\right)^{-(1+1/\xi)}, \quad y > 0
$$

Return level for return period $T$ (years):
$$
x_T = u + \frac{\sigma}{\xi}\left[(T\lambda)^{\xi} - 1\right], \quad \xi \neq 0
$$

where $\lambda = n_{\text{exceed}} / n_{\text{years}}$ is the mean exceedance rate.

**Minimum sample**: 10 exceedances required for GPD fit. Return periods: 2, 5, 10, 20, 50 years.

**Confidence intervals**: Delta method (approximate), propagating the closed-form **asymptotic** (expected-information) variance–covariance matrix of the GPD MLE — $\mathrm{Var}(\sigma)=2\sigma^2/n$, $\mathrm{Var}(\xi)=(1+\xi)^2/n$, $\mathrm{Cov}(\sigma,\xi)=-\sigma(1+\xi)/n$ — through $\partial x_T/\partial\sigma$ and $\partial x_T/\partial\xi$. This is the expected (not the numerically observed) information; it is valid for $\xi > -0.5$ and is approximate for small samples. Profile-likelihood intervals are not implemented.

**Independence guarantee**: Storm peaks are algebraically independent — the POT clustering in the catalog (gap ≤ 1 day) ensures one peak per meteorological event.

### Submodule 3.7 — Dependence Analysis (Hₛ–SSH_total)

Paired samples: $(H_s^{\text{peak}},\, \text{SSH}_{\text{total}}^{\text{peak}})$ from each compound event at each grid point.

**Kendall's τ**: rank correlation, robust to outliers, non-parametric.

**Spearman's ρ**: monotone rank correlation.

**Extremal dependence coefficient χ** (Coles, Heffernan & Tawn, 1999):
$$
\chi = \lim_{u \to 1} P\bigl(F_Y(Y) > u \mid F_X(X) > u\bigr)
$$

Estimated empirically at quantile $u = 0.95$. If χ > 0, the variables are **asymptotically dependent** — their extremes tend to co-occur even in the limit. If χ = 0, they are **asymptotically independent**.

**Sub-asymptotic coefficient χ̄** (Ledford & Tawn, 1996; 1997; Coles et al., 1999):
$$
\bar{\chi} = \frac{2\log P(F_X(X) > u)}{\log P(F_X(X) > u,\, F_Y(Y) > u)} - 1
$$

**Interpretation — χ and χ̄ must be read jointly**:
- If **χ > 0**: asymptotic dependence; χ̄ = 1 by definition and is not informative.
- If **χ = 0** (asymptotic independence): χ̄ ∈ (−1, 1] measures the **residual strength** or **rate of decay** toward independence in the joint tail.
  - χ̄ close to 1: the joint tail decays slowly (strong sub-asymptotic association — "near-dependence").
  - χ̄ close to 0: faster decay toward independence.
  - χ̄ < 0: negative association in the tails (rare in metocean compound events).

In practice, with n ≈ 250–320 compound events per grid point and the empirical estimator at u = 0.95, the effective number of pairs above threshold is ~12–16. This makes the distinction between χ = 0 (asymptotic independence) and small positive χ unreliable. **The χ/χ̄ values reported here should be interpreted as screening diagnostics, not as definitive classifications of the tail dependence class.** Rigorous classification would require bootstrap confidence intervals or parametric tail models (e.g., bivariate threshold exceedances), which are deferred to future bivariate EVA.

**Minimum samples**: τ/ρ require ≥ 5 pairs; χ/χ̄ require ≥ 20 compound events for stable tail estimates.

Reference: Coles et al. (1999); Ledford & Tawn (1996, 1997); Camus et al. (2021).

---

## Step 4 — Exposure, Vulnerability & Risk Integration (municipal scale)

This section documents methodological decisions in the municipal risk integration so they
are explicit in the scientific record. **The Hazard_Index / Risk_Comp / Risk_Hazard formulas
are NOT computed by any script in this repository** — they are produced externally (QGIS /
Python workflow by Karine Bastos Leal, INPE) and delivered as a shapefile,
`outputs/risk_index/risk_index.shp`. The repository only *reads* the precomputed fields
(`Haz_index`, `Risk_comp`, `Risk_harza`, `SVI_Coast_`) via `src/site/export_risk_index_data.py`
and re-exports them as GeoJSON for the website. The formulas below were reproduced numerically
from the exported data (agreement to ≤ 5×10⁻⁴, i.e. rounding only):

$$
\text{Hazard\_Index} = \tfrac{1}{3}\bigl[\,\text{norm}(\text{compound\_c}) + \text{norm}(\text{mean\_overl}) + \text{norm}(\text{mean\_compo})\,\bigr]
$$
$$
\text{Risk\_Comp} = \tfrac{\text{SVI\_Coast\_2022}}{100}\,\text{norm}(\text{compound\_c}), \qquad
\text{Risk\_Hazard} = \tfrac{\text{SVI\_Coast\_2022}}{100}\,\text{Hazard\_Index}
$$

where `norm(·)` is Min–Max scaling to [0, 1] across the coastal municipalities.

**Provenance of the three hazard inputs** (per grid point, from sub-module 3.2):
- `compound_c` = `compound_count_total` — the **absolute** compound-event count over the full
  1993–2025 record (range 51–300 in the delivered set), **not** an annual rate.
- `mean_overl` = `mean_overlap_duration`.
- `mean_compo` = `mean_compound_intensity_norm`.

**[DECISION — same grid point per municipality]** Each municipality is assigned the single
oceanic grid point with the **highest `compound_c`** within its association (spatial join,
performed in the external workflow). The three inputs are therefore the *coincident* values of
that one grid point; the per-municipality `grid_lat`/`grid_lon` in the shapefile confirm a
single point per municipality. The selection/join code is external and not auditable in this repo.

**[DECISION — double / asymmetric normalization of `mean_compo`]** `mean_compo` is already a
domain-wide normalized quantity (each event's intensity is clipped to [0,1] via
$(\text{peak}-Q_{05})/(Q_{95}-Q_{05})$ in sub-module 3.2, then averaged per point). In
Hazard_Index it is Min–Max normalized **again** across municipalities. The other two inputs
(`compound_c`, `mean_overl`) are raw counts/durations normalized **once**. This makes the
intensity term's normalization asymmetric relative to the other two (it is re-stretched to the
full [0,1] municipal range). The effect is a rescaling, not an error, but it is **not an
intentional weighting choice** and should be noted when interpreting the index.

**[DECISION — equal 1/3 weights and the correlation structure]** The three components are
combined with equal weights. Empirically, in the delivered set (280 municipalities) they are
**not** mutually positively correlated:

| Pair | Pearson r |
|------|-----------|
| compound_c × mean_overl | −0.41 |
| compound_c × mean_compo | −0.39 |
| mean_overl × mean_compo | +0.28 |

Compound-event **frequency is negatively correlated with mean per-event duration and
intensity** — municipalities with many compound events tend to have individually shorter/weaker
ones. The simple 1/3 mean therefore partially averages opposing signals (hence the compressed
observed range, Hazard_Index ∈ [0.19, 0.67] rather than [0, 1]). The equal-mean choice is
defensible as a transparent, assumption-light aggregator, but the common justification "the
components co-vary" does **not** hold here. A PCA (as used for the SVI) would capture a
frequency↔intensity *trade-off* axis rather than a single "all high" gradient and is a
reasonable alternative to consider in future work.

**[DECISION — handling of municipalities with no compound events]** At grid-point level, points
with zero compound events return `None` for `mean_overlap_duration` and
`mean_compound_intensity_norm` (sub-module 3.2). In the delivered municipal set every selected
grid point has ≥ 51 compound events, so this case does not arise in the final index. Where a
municipality lacks hazard data it is left **null** (dropped from the hazard/risk layers, 280 of
282 features populated) and retains only its SVI — it is **not** coerced to 0, and no NaN is
propagated into the Min–Max normalization (computed over the populated municipalities only).

**Social Vulnerability Index (SVI_Coast_2022)**: built from 10 IBGE/SIDRA 2022 socioeconomic
and infrastructure variables, standardized (StandardScaler), reduced by PCA; PC1 is
sign-adjusted so higher = more vulnerable and Min–Max normalized to 0–100. Method after Lima
et al. (2024). This is the only part of the chain that uses PCA.

---

## References

- Camus, P., Haigh, I. D., Nasr, A. A., Wahl, T., Darby, S. E., & Nicholls, R. J. (2021). Regional analysis of multivariate compound flooding potential: sensitivity analysis and spatial patterns. *Natural Hazards and Earth System Sciences*, 21, 2021–2042. https://doi.org/10.5194/nhess-21-2021-2021
- Coles, S. (2001). *An Introduction to Statistical Modeling of Extreme Values*. Springer.
- Coles, S. G., Heffernan, J. E., & Tawn, J. A. (1999). Dependence measures for extreme value analyses. *Extremes*, 2(4), 339–365.
- Davison, A. C. & Smith, R. L. (1990). Models for exceedances over high thresholds. *JRSS-B*, 52, 393–442.
- Ferro, C. A. T. & Segers, J. (2003). Inference for clusters of extreme values. *JRSS-B*, 65, 545–556.
- Hamed, K. H. & Rao, A. R. (1998). A modified Mann-Kendall trend test for autocorrelated data. *J. Hydrology*, 204, 182–196.
- Kendall, M. G. (1975). *Rank Correlation Methods*. Griffin, London.
- Law-Chune, S., et al. (2021). WAVERYS: a CMEMS global wave reanalysis during the altimetry period. *Ocean Dynamics*, 71, 357–379. https://doi.org/10.1007/s10236-020-01433-w
- Ledford, A. W. & Tawn, J. A. (1996). Statistics for near independence in multivariate extreme values. *Biometrika*, 83(1), 169–187.
- Ledford, A. W. & Tawn, J. A. (1997). Modelling dependence within joint tail regions. *Journal of the Royal Statistical Society: Series B*, 59(2), 475–499.
- Lellouche, J.-M., Greiner, E., Bourdallé-Badie, R., Garric, G., Melet, A., Drévillon, M., et al. (2021). The Copernicus Global 1/12° Oceanic and Sea Ice GLORYS12 Reanalysis. *Frontiers in Earth Science*, 9, 698876. https://doi.org/10.3389/feart.2021.698876
- Lyard, F. H., Lefevre, F., Letellier, T., & Francis, O. (2021). FES2014 global ocean tide atlas: design and performance. *Ocean Science*, 17(3), 615–649. https://doi.org/10.5194/os-17-615-2021 *(Note: no peer-reviewed publication exists for FES2022; the FES2014 paper describes the model framework. FES2022 is documented in Carrere, L. et al. (2022), "A new barotropic tide model for global ocean: FES2022", Ocean Surface Topography Science Team Meeting, conference abstract.)*
- Mann, H. B. (1945). Nonparametric tests against trend. *Econometrica*, 13(3), 245–259.
- Petroliagkis, T. I. (2018). Estimations of statistical dependence as joint return period modulator of compound events — Part 1: Storm surge and wave height. *Natural Hazards and Earth System Sciences*, 18, 1937–1953. https://doi.org/10.5194/nhess-18-1937-2018
- Reguero, B. G., Losada, I. J., & Méndez, F. J. (2019). A recent increase in global wave power as a consequence of oceanic warming. *Nature Communications*, 10(1), 205. https://doi.org/10.1038/s41467-018-08066-0
- Sen, P. K. (1968). Estimates of the regression coefficient based on Kendall's tau. *JASA*, 63(324), 1379–1389.
- Wahl, T., Jain, S., Bender, J., Meyers, S. D., & Luther, M. E. (2015). Increasing risk of compound flooding from storm surge and rainfall for major US cities. *Nature Climate Change*, 5, 1093–1097. https://doi.org/10.1038/nclimate2736
- Yue, S., Pilon, P., Phinney, B., & Cavadias, G. (2002). The influence of autocorrelation on the ability to detect trend in hydrological series. *Hydrological Processes*, 16(9), 1807–1829.
- Zscheischler, J., et al. (2020). A typology of compound weather and climate events. *Nature Reviews Earth & Environment*, 1, 333–347. https://doi.org/10.1038/s43017-020-0060-z
