# SCIENTIFIC_NOTES — Step 3: Hazard Characterization of Extreme and Compound Coastal Events


> ### ⚠ Estado misto desde 2026-07-30
>
> O **Step 3.2** foi regenerado com o par recalibrado **q70/q99**, portão e datum
> em **HAT**, e é a única fonte do índice de perigo publicado. Os **Steps 3.1 e
> 3.3–3.8 não foram regenerados**: leem os catálogos de Hₛ e `SSH_total`
> construídos em q90/q90, e reexecutá-los sem alteração misturaria uma variável
> de nível superada às estatísticas publicadas. Ver AUD-01 §14, incerteza
> remanescente (6).
>
> **Detector vigente (3.2):**
>
> ```
> onda   Hs  >= q70 local
> nível  zos >= q99 local                 (livre de maré)
> portão max(SWL) > HAT na sobreposição
>
> SWL(d) = [zos(d) − média local de zos] + maré_máx_diária(d)
> HAT    = max(maré_máx_diária) em 1993–2025, por ponto
>
> severidade integrada = Σ_d 0,5·[norm(Hs_d − thr_hs) + norm(SWL_d − HAT)]
> ```
>
> **Pressupostos.** (1) Portão e datum são o mesmo nível — o excesso só tem
> interpretação como distância à condição que define o evento. (2) `zos` e
> FES2022 são modelos independentes; sua soma linear ignora a interação não
> linear maré–sobrelevação. (3) O HAT é máximo amostral de 33 anos, dependente
> da janela e não transferível a projeções. (4) Ponto sem evento aceito recebe
> frequência 0 e severidade 0, preservando os 808 pontos na normalização — são
> 208 pontos e 83 municípios.

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

1. **Step 4 — Exposure, vulnerability & risk integration**: Municipal-scale integration is **complete** (see the "Step 4" section below). The current Hazard Index is the normalized equal-weight combination of **two** components — compound-event frequency and mean integrated severity — on the 808-point native grid; the mean overlap duration was retired as a component on 2026-07-29 (AUD-06) and the peak-based intensity superseded by the integrated form, both remaining as published diagnostics. The index is transferred to municipalities and combined with `Exposure_Index` and `SVI_Coast_2022` as a conjunctive geometric mean, and the final `Risk_Hazard` is normalized to 0–1. Open follow-up: bring the external municipality–grid-point selection step into a versioned script in this repo.
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
are explicit in the scientific record. The external workflow (QGIS / Python workflow by
Karine Bastos Leal, INPE) delivered `outputs/risk_index/risk_index.shp` with SVI, compound
metrics, and the former risk fields (`Haz_index`, `Risk_comp`, `Risk_harza`,
`SVI_Coast_`). Of those, only the geometry, `SVI_Coast_`, the ten IBGE/SIDRA indicators,
`PC1` and the pre-associated `grid_lat`/`grid_lon` are read; the delivered hazard and risk
columns are ignored and recalculated from the versioned native-grid metrics.

The repository export produces **one** product,
`site/public/data/risk_index_municipalities.geojson`: the normalized native-grid
frequency-duration-intensity Hazard Index transferred to municipalities, and the risk
derived from it. Parallel scopes (`Legacy_*`, `CountOnly_*`, the
`risk_index_legacy_*` artefacts) were removed on 2026-07-28.

### 2026-07-28 — Exposure enters the published index; risk becomes conjunctive

**[DECISION — the integrated index is now the geometric mean of three components]**

$$
R_m=\left(A_m\,E_m\,V_m\right)^{1/3},\qquad
A=\mathrm{Hazard\_Index\_mun},\;
V=\frac{\mathrm{SVI\_Coast\_2022}}{100},
$$

each component floored at 0.01 before the product and the result Min--Max
normalized over the municipalities. This supersedes
$\mathrm{norm}\left[(\mathrm{SVI}/100)\times\mathrm{Hazard\_Index}\right]$,
which carried no exposure term and was therefore a vulnerability-weighted
hazard rather than risk in the IPCC sense.

**[DECISION — the exposure term follows INFORM]** $E$ is the resident
population within 10 km of the coastline, from the IBGE Grade Estatística 2022
(200 m urban / 1 km rural cells), brought onto $[0,1]$ as

$$
E=\left[
\mathrm{clip}\!\left(\frac{\log_{10}P-\log_{10}P_{\min}}
{\log_{10}P_{\max}-\log_{10}P_{\min}},0,1\right)
\cdot
\frac{P}{P_{\mathrm{mun}}}
\right]^{1/2},
\qquad P_{\min}=10^{2},\;P_{\max}=10^{6}.
$$

Three elements of that expression are taken from the Index for Risk Management
\citep{marinferrer2017inform}, which treats this exact problem for its physical
exposure indicators: the logarithm, applied because the indicator is a people
count (§6.2); **fixed goalposts instead of the observed extremes** (§6.3),
because outliers otherwise make the observed minimum and maximum
unrepresentative; and the pairing of an absolute with a relative reading
(Box 2), because "the absolute value of people exposed will favour more
populated countries while the value of population exposed relative to the total
population will reverse the problem".

**[VERIFICATION — why not the simpler candidates]** Three alternatives were
computed on the same data and rejected:

| $E$ | $\rho(R,A)$ | $\rho(R,E)$ | $\rho(R,V)$ |
|---|---|---|---|
| Min--Max of the count | +0.667 | +0.278 | +0.131 |
| Min--Max of $\log_{10}$ | +0.713 | **−0.043** | +0.413 |
| percentile rank | +0.568 | +0.593 | **−0.020** |
| **INFORM** | **+0.668** | **+0.198** | **+0.297** |

The raw Min--Max is degenerate: the count has skewness above 7 and the affine
rescaling leaves 89 % of the municipalities below 0.05. Under $\log_{10}$ the
exposure term is present but inert. Under the rank it drives the index but
annihilates the vulnerability signal. Only the INFORM form gives all three
components ordered, non-trivial influence.

**[VERIFICATION — the goalposts barely matter]** Risk maps built with
$10^2$–$10^6$, $10^2$–$10^7$ and $10^3$–$10^6$ agree at Spearman $\geq 0.99$;
the arithmetic and geometric pairings of the absolute and relative halves agree
at $0.995$. What the fixed goalposts do buy is stability: removing Rio de
Janeiro from the set shifts the median of $E$ by $0.0000$, against $0.0281$
under a data-driven Min--Max. And $E=0.5$ denotes 10,000 inhabitants in any
study using the same goalposts, whereas under a data-driven scale it denotes
4,677 inhabitants and only in this dataset.

**[CAVEAT — six municipalities saturate]** One reaches the floor and five the
ceiling, leaving 274 of 280 on the continuous scale. Rio de Janeiro (4.37 M) and
São Luís (1.04 M) both take 1.000 on the absolute half; the relative half
separates them again (0.706 against 1.000). This is the same trade the Human
Development Index makes with its own goalposts, and it is deliberate.

**[CAVEAT — proximity, not impact]** No water level is propagated over land
anywhere in this workflow. $E$ counts residents *near* the coast under a stated
distance criterion, never residents *affected*. The count is of *de jure*
residents on 2022-07-31, a single instant against 33 years of metocean record,
and the seasonal population of the resort municipalities of the South and
Southeast is not represented.

**[EFFECT]** Against the superseded index, Spearman $+0.801$; the median
municipality moves 23 positions and 62 % move more than 15. The largest rises
are São Luís (+88), Salvador (+84) and Maceió (+75) — capitals that combine a
large coastal population with high vulnerability. The largest falls are
Calçoene/AP (−276) and Santa Rita/MA (−269), which the previous index ranked
high on vulnerability alone: Calçoene has 101 residents within 10 km of the
coast out of 10,554.

### 2026-07-28 — The SVI script was obtained and audited

**[VERIFICATION — the index is reproducible]** The Colab notebook that produced
`SVI_Coast_2022` was obtained from its author (Karine Bastos Leal, INPE) and is
stored verbatim at `src/04_risk_integration/external_svi/`. Recomputing PC1 and
the index from the ten delivered variables reproduces the delivered values
exactly (`r = +1.000000`, max difference 0.0000); PC1 explains 50.5 % of the
variance of the ten standardised indicators.

**[CORRECTION — an earlier suspicion in this record was wrong]** The script
Min--Max rescales `pop_house` before the z-score step, and it was suspected here
that the variable might therefore have entered the PCA with a different weight
from the other nine. It does not: Min--Max and the z-score are both affine, so
the second absorbs the first. Verified to 5.7e-15.

**[CAVEAT — the published `pop_house` is not what the manuscript defines]** The
column distributed as `pop_house` is the rescaled one on [0,1]; the manuscript
table defines it as residents per household, which is the raw 2.40–4.45 value
carried separately as `pop_house_`. Either the definition or the published
column must change.

**[OPEN — the spatial association is still unaudited]** The notebook contains no
geoprocessing. The association between the 808 ocean grid points and the
municipalities, which supplies `grid_lat`/`grid_lon`, was produced elsewhere and
remains the one reproducibility gap in Step 4.

### 2026-07-28 — Exposure enters the framework; risk becomes conjunctive (superseded by the entry above)

**[DECISION — risk is the geometric mean of the three IPCC components]**
The integrated index is redefined as

$$
R_m=\left(A_m\,E_m\,V_m\right)^{1/3},
$$

where $A$ is the compound-event Hazard Index, $E$ a population-exposure index,
and $V=\mathrm{SVI\_Coast\_2022}/100$. The superseded form was the compensatory
product $(\mathrm{SVI}/100)\times\mathrm{Hazard\_Index}$ without any exposure
term.

The reason for the geometric mean is conceptual, not numerical. The IPCC
framework \citep{reisinger2020risk} defines risk as emerging from the
*interaction* of hazard, exposure and vulnerability, and supplies no formula.
What the framework does imply is that risk is **conjunctive**: with no hazard,
or with nobody exposed, there is no potential for adverse consequences. An
arithmetic mean $(A+E+V)/3$ violates that property — it lets a high population
compensate for the absence of a physical driver — whereas the geometric mean
preserves it. The same argument underlies the INFORM Risk Index of the European
Commission JRC, which aggregates its dimensions geometrically and deliberately
fuses exposure with hazard rather than treating exposure as a peer of
vulnerability.

**[DECISION — only the conjunctive index is published]** An additive
prioritisation variant was evaluated (Spearman $0.932$ against the geometric
form on the exploratory dataset) and is *not* published, to keep the article
focused. Only the geometric index may be called "risk".

**[DECISION — components are clipped at 0.01 before the product]** Min–Max
normalisation places at least one municipality at exactly zero on each
component; in a product that municipality would receive zero risk as an
artefact of the scaling, not as a physical statement. Balneário Camboriú (SC)
sits at $\mathrm{SVI}=0$ for this reason. All components are therefore clipped
to $[0.01,1]$ before the geometric mean. The clip is a floor on the scale, not
on the underlying quantity, and it must be reported in the manuscript.

**[DECISION — the hazard is renormalised over the municipalities for this
aggregation only]** `Hazard_Index` keeps the native-grid scale, so its municipal
range is $[0.003439, 0.829072]$ while $\mathrm{SVI}/100$ spans $[0,1]$. In an
equal-weight aggregation that difference in amplitude silently down-weights the
hazard. `Hazard_Index_mun` = Min–Max of `Hazard_Index` over the municipalities
is therefore introduced as the hazard input to $R$. It is a pure rescaling
(Spearman $1.000000$ against `Hazard_Index`) and no other published field uses
it. The native-grid scale is retained for `Hazard_Index` so that the municipal
layer and the coastal-line figure remain on one field.

**[PENDING — the exposure component]** $E$ will be built from the population
within 10 km of the coastline, from the IBGE Grade Estatística 2022
(200 m urban / 1 km rural cells; `TOTAL`). The **normalisation of $E$ is not yet
decided** and is the subject of an exploratory comparison, because Min–Max on a
raw population count is degenerate: the count has skewness $7.5$, 90 % of the
municipalities fall below $0.05$, and removing a single municipality (Rio de
Janeiro) shifts the median of $E$ by a factor of $1.7$. The candidates are
$\log_{10}$-then-Min–Max and the percentile rank. **[CAVEAT]** The choice is
consequential rather than technical: the ratio between Rio de Janeiro and the
median municipality is $188\times$ under Min–Max, $1.5\times$ under $\log_{10}$
and $2\times$ under ranks, and the exposure term only drives the ranking under
the rank normalisation. Whichever is adopted, the alternatives must be reported
as a sensitivity analysis.

**[CAVEAT — $E$ is proximity, not affected population]** No inundation extent is
modelled anywhere in this workflow. The 10 km band is a proximity criterion, and
the manuscript must say so explicitly; "potentially exposed population under the
10 km criterion" is admissible, "affected population" is not.

### 2026-07-28 — The municipal export has no fallback

**[DECISION]** `src/site/export_risk_index_data.py` previously fell back to the
previously exported `risk_index_legacy_municipalities.geojson` when
`outputs/risk_index/risk_index.shp` was absent. That path re-simplified already
simplified geometry and could publish a product rebuilt from a stale export
while reporting success. The externally delivered shapefile is now the only
accepted source and a missing component raises `FileNotFoundError`.

**[STATUS]** The shapefile is currently absent from both the workstation and the
`swell` server, so the export cannot be regenerated until the file is obtained
from the co-author. The last generated products remain committed under
`site/public/data/`.

**[CORRECTION]** The municipal maximum of `Hazard_Index` recorded in the
2026-07-27 entry below (0.782047) is superseded: the value in the current
product is **0.829072** (São Sebastião, SP), with a minimum of 0.003439.

### 2026-07-27 — Multimetric Hazard Index promoted to the current workflow *(SUPERSEDED 2026-07-29)*

> **Superseded by the 2026-07-29 entry below**, which retired duration from the
> index and replaced peak intensity with integrated severity. The index now
> carries **two** components. This entry is preserved as the dated record of the
> decision that was taken at the time, not as a description of the current
> workflow.

**[DECISION — frequency, duration, and intensity enter the hazard, as of 2026-07-27]**
The count-only decision previously recorded in this section is superseded.
Each component is Min–Max normalized across all 808 native ocean grid points,
their arithmetic mean is retained as `Hazard_Index_raw`, and the mean is
Min–Max normalized again so that the published physical Hazard Index spans
[0,1] on the native grid. The index is calculated before municipal transfer,
ensuring that the coastal-line figure and municipal hazard layer originate
from the same physical field. The authoritative implementation is
`src/04_risk_integration/hazard_index.py`; the site exporter and article
figures import this module rather than reimplementing the formula.

For interpretation, panels A--C of
`coastal_hazard_index_components.png` display the catalog values before this
cross-grid scaling: annual frequency in events per year, mean overlap duration
in days, and mean compound intensity as the dimensionless event-level metric.
Only panel D displays the final normalized Hazard Index.

$$
\begin{aligned}
H_F &= \text{norm}_{grid}(\text{compound\_count\_total}),\\
H_D &= \text{norm}_{grid}(\text{mean\_overlap\_duration}),\\
H_I &= \text{norm}_{grid}(\text{mean\_compound\_intensity\_norm}),\\
H_{raw} &= \tfrac{1}{3}(H_F + H_D + H_I),\\
\text{Hazard\_Index} &= \text{norm}_{grid}(H_{raw}).
\end{aligned}
$$
$$
\text{Risk\_Hazard}_{raw} =
\tfrac{\text{SVI\_Coast\_2022}}{100}\,\text{Hazard\_Index},
\qquad
\text{Risk\_Hazard} =
\text{norm}_{municipal}\left(\text{Risk\_Hazard}_{raw}\right).
$$

*(Superseded on 2026-07-28: the `Risk_Comp_raw`/`Risk_Comp` compatibility
aliases were removed; `Risk_Hazard_raw` and `Risk_Hazard` are the only names.)*

For the native grid, $H_{raw}\in[0.181936,0.661876]$ and the published
$\text{Hazard\_Index}\in[0,1]$. The 280 municipalities with a valid
pre-associated point inherit values in [0,0.782047] and are not renormalized
after transfer. The current municipal
$\text{Risk\_Hazard}_{raw}\in[0,0.613210]$ and
$\text{Risk\_Hazard}\in[0,1]$.

The former count-only repository product is retained as:

$$
\text{CountOnly\_Hazard\_Index}
=\text{norm}_{municipal}(\text{compound\_c}).
$$

*(Superseded on 2026-07-28: the `CountOnly_*` and `Legacy_*` fields and the
dedicated legacy GeoJSON were removed; the count-only index is now rebuilt
inside the exploratory comparison script that uses it.)*

### 2026-07-24 — Normalization of the final integrated index

The vulnerability–hazard product is retained as `Risk_Hazard_raw` for
traceability and then Min–Max normalized over municipalities with finite SVI
and hazard values:

$$
R_i = \frac{R^{raw}_i - \min_j(R^{raw}_j)}
{\max_j(R^{raw}_j) - \min_j(R^{raw}_j)}.
$$

At the time of this 2026-07-24 entry, the count-only product had
$R^{raw}\in[0,0.331630]$. After the 2026-07-27 multimetric promotion, the same
normalization rule is retained but the current raw range is [0,0.613210].
The published final index satisfies $R\in[0,1]$. Municipalities with missing
hazard values remain null and are excluded from both extrema.

**Provenance of the three current hazard inputs** (per native grid point, from sub-module 3.2):
- `compound_count_total` — the **absolute** compound-event count over the full
  1993–2025 record (43–322 over the 808-point grid), **not** an annual rate.
- `mean_overlap_duration` — mean temporal overlap (1.26–2.51 days).
- `mean_compound_intensity_norm` — mean dimensionless compound intensity
  (0.0659–0.6946) after event-level domain normalization.

**[DECISION — same grid point per municipality]** Each municipality is assigned the single
oceanic grid point with the **highest `compound_c`** within its association (spatial join,
performed in the external workflow). The three inputs are therefore the *coincident* values of
that one grid point; the per-municipality `grid_lat`/`grid_lon` in the shapefile confirm a
single point per municipality. The selection/join code is external and not auditable in this repo.

**[DECISION — second scaling of the mean-intensity component]**
`mean_compound_intensity_norm` is already a domain-normalized event quantity
(each event intensity is clipped to [0,1] via
$(\text{peak}-Q_{05})/(Q_{95}-Q_{05})$ in sub-module 3.2 and then averaged per
point). In the current Hazard Index, the per-point mean is Min–Max scaled
across the native grid so that its range is comparable with frequency and
duration before equal-weight aggregation. This second scaling is an
intentional component-standardization step, not a second physical definition
of intensity.

**[DECISION — equal 1/3 weights and correlation structure]** The three components are
combined with equal weights. Empirically, over the 808 native points they are
**not** mutually positively correlated:

| Pair | Pearson r |
|------|-----------|
| frequency × duration | −0.443 |
| frequency × intensity | −0.332 |
| duration × intensity | +0.318 |

Compound-event **frequency is negatively correlated with mean per-event duration and
intensity** — municipalities with many compound events tend to have individually shorter/weaker
ones. The simple 1/3 mean therefore partially averages opposing signals. The
equal-mean choice is retained as a transparent compensatory index, but it must
not be justified by claiming that the components co-vary. The final Min–Max
step expands the observed composite range to [0,1] without changing the
grid-point ranking.

**[DECISION — handling of missing hazard associations]** All 808 native points
have finite compound metrics in the current dataset (minimum count: 43).
Fernando de Noronha (PE) and Içara (SC) lack `grid_lat`/`grid_lon` in the
delivered municipal association and therefore remain **null** in the
hazard/risk municipal layers (280 of 282 features populated). Missing values
are not coerced to zero and are excluded from the municipal risk
normalization.

### 2026-07-27 — Compound intensity redefined as excess over the local threshold

**[DECISION — the intensity now measures the event, not the setting]** The
event-level compound intensity previously rescaled the **absolute** peaks by
the 5th/95th percentiles of all peaks pooled over the domain. That definition
is superseded. Each driver now contributes how far its peak rose **above its
own local q90 detection threshold** — the same threshold that defined the
event — and that excess is rescaled by the domain-wide Q05/Q95 of the excesses:

$$
\begin{aligned}
E_{H_s} &= \text{peak}_{H_s} - \text{thr}_{H_s}^{local}, \qquad
E_{SSH}  = \text{peak}_{SSH} - \text{thr}_{SSH}^{local},\\
I &= \tfrac{1}{2}\Big[\text{clip}\Big(\tfrac{E_{H_s}-Q_{05}(E_{H_s})}{Q_{95}(E_{H_s})-Q_{05}(E_{H_s})},0,1\Big)
   + \text{clip}\Big(\tfrac{E_{SSH}-Q_{05}(E_{SSH})}{Q_{95}(E_{SSH})-Q_{05}(E_{SSH})},0,1\Big)\Big].
\end{aligned}
$$

Reference values on the current dataset: $E_{H_s}\in[0.020,\,1.380]$ m and
$E_{SSH}\in[0.0153,\,0.4273]$ m. The normalization population remains global,
so the metric stays comparable between grid points.

**[EVIDENCE — the superseded metric encoded the astronomical tide]** Because
$SSH_{total} = zos + \text{tide}_{daily\,max}$, the absolute sea-level peak is
almost entirely set by the local tidal regime. Regressing the mean SSH_total
peak of a grid point on its own q90 threshold gives

$$\overline{\text{peak}}_{SSH} = 1.060\,\text{thr}_{SSH}^{local} + 0.089,
\qquad R^2 = 0.998 .$$

Decomposing the peak into baseline and storm excess by latitude band: the
threshold accounts for 91% of the peak in the north and 78% in the south, while
the storm excess itself varies only 1.7-fold along the coast (0.126–0.217 m)
against a 3.1-fold variation of the absolute peak (0.794–2.472 m). In the north
the peaks are also nearly identical between events (sd/peak = 0.05), i.e. the
sea-level term contributed a fixed regional offset rather than discriminating
events. Under the superseded definition the intensity therefore increased
**northward** ($r=+0.463$ with latitude), opposite to the wave-energy gradient.

**[VERIFICATION — effect of the change]** Diagnosed before adoption in
`src/exploratory/make_exploratory_intensity_definition_comparison.py`:

- the intensity reverses sign with latitude, $r=+0.463 \rightarrow -0.410$;
  the two definitions rank the grid almost independently (Spearman $0.280$);
- the Hazard Index becomes moderately southward,
  $r=-0.203 \rightarrow -0.523$, but its ranking is largely preserved
  (Spearman $0.883$; 53 of the top 80 grid points in common);
- the municipal integrated risk keeps Spearman $0.885$; the Norte/Nordeste
  hotspots persist because the municipal hazard is essentially flat with
  latitude ($r=+0.014$) and the pattern of `Risk_Hazard` is driven by the SVI
  ($r=+0.828$ with latitude; mean SVI 67.5 in the north against 23.1 in the
  south);
- the worst regional clipping falls from **30%** of northern events saturating
  the sea-level term to **10.5%**, and from 15% to 5.4% at the lower bound in
  the south.

**[DECOMPOSITION — which driver caused the change]** The intensity is an
unweighted mean, so the change splits exactly as
$\Delta I = \tfrac{1}{2}\Delta(H_s\text{ term}) + \tfrac{1}{2}\Delta(SSH\text{ term})$
(closes to $3\times10^{-16}$). The mean absolute contributions are nearly equal
(0.0856 for $H_s$, 0.0831 for SSH), but the two act differently: the $H_s$ term
shifts by a nearly uniform offset (positive at every point, sd 0.127) whereas
the SSH term changes sign, from $+0.73$ at the Amazon mouth to $-0.43$ in the
far south (sd 0.205). Since the intensity is Min–Max normalized again inside
the Hazard Index, a uniform offset has **no effect** (verified: adding a
constant leaves the index rank identical, Spearman $1.000000$). Isolating the
two terms confirms that the SSH term carries the whole spatial change:
substituting only the SSH term gives $r(H,\text{lat})=-0.615$, whereas
substituting only the $H_s$ term gives $+0.065$.

**[CAVEAT — accepted cost]** The $H_s$ term loses spatial contrast
(sd $0.227 \rightarrow 0.127$; range $0.00$–$0.91 \rightarrow 0.02$–$0.58$).
This is partly genuine information loss: the southern wave climate really is
more energetic. It is accepted because a more energetic setting also requires a
larger swell to cause damage there, so the excess over the local threshold
remains the impact-relevant quantity.

**[AUDIT]** The superseded values are preserved per grid point as
`mean_compound_intensity_norm_abspeak`, `p95_*_abspeak` and `max_*_abspeak`,
and both reference sets are recorded in
`outputs/storm_catalog/compound/compound_summary.json`. The exploratory script
reproduces both definitions from the raw catalog and checks each against its
published column at every run.

---

### 2026-07-27 — Repository-wide audit of the official Hazard Index

**[VERIFICATION — the canonical formula is consistent across the repository]**
A full audit was carried out on the code, exported products, methodological
documentation, and website, checking for duplicated calculations of the index,
residual references to the superseded count-only method, normalizations
performed in the municipal domain, and text describing duration or intensity as
diagnostic-only fields. Verified numerically on the current dataset:

- 808 native ocean grid points enter the calculation;
- $H_F$, $H_D$, and $H_I$ each span exactly $[0,1]$ on that grid;
- $H_{raw}$ equals the arithmetic mean of the three components at every point
  (agreement to machine precision);
- $\text{Hazard\_Index}\in[0,1]$ on the native grid;
- the municipal transfer reproduces the native-grid value at all 280
  municipalities with a valid association (zero mismatches), confirming that no
  renormalization occurs after the transfer;
- $\text{Risk\_Hazard}\in[0,1]$ across municipalities, and
  $\text{Risk\_Hazard}_{raw}$ equals $(\text{SVI}/100)\times\text{Hazard\_Index}$.

Because the most hazardous native grid point is not the point associated with
any municipality, the municipal `Hazard_Index` maximum is 0.782 rather than 1.
This is the expected consequence of transferring without renormalizing and is
not an error.

**[CORRECTION — duration and intensity were still described as diagnostics]**
The compound-detection methodology page and the municipal map tooltip still
labelled `mean_overlap_duration` and `mean_compound_intensity_norm` as
diagnostic or legacy fields that no longer feed the index. Both are equally
weighted physical inputs to the current Hazard Index; the descriptions were
corrected and the fields now carry their units (days; dimensionless).

**[CORRECTION — invalid JSON in the municipal metadata]** The municipalities
without a grid association were serialized with `NaN` coordinates, which Python
accepts but `JSON.parse` rejects. `risk_index_metadata.json` was therefore
unparseable and the current municipal risk page failed to load in the browser
while the legacy page still worked — i.e. the audit product was reachable and
the current product was not. Non-finite values are now mapped to `null` and the
metadata is written with `allow_nan=False` so the failure cannot recur silently.

**[DECISION — the coastal projection is a shared cartographic step]** The
grid-to-coastline transposition existed in two near-identical copies (the
article figure script and the exploratory comparison). It was extracted to
`src/04_risk_integration/coastal_projection.py`, which now serves the article
figure, the exploratory audit, and the website exporter. The step clips the
Natural Earth 10-m coastline to a 30-km buffer around the coastal
municipalities, splits it into segments of at most 5 km in EPSG:5880, and
assigns to each segment the values of its nearest native grid point. It is a
**visualization** of the native-grid field: no value is recalculated, rescaled,
or renormalized. On the current dataset this produces 6,743 segments drawing on
297 distinct grid points, with a median segment-to-point distance of 18.7 km
(99th percentile 83.1 km, maximum 119.9 km). This distance is a caveat of the
coastal display, not of the index.

**[DECISION — component maps show catalog values]** The website coastal map and
panels A–C of the article figure present the components in their own units
(events yr⁻¹, days, dimensionless) with no additional Min–Max scaling for
display. The cross-grid normalization is documented as a methodological step
internal to the index construction, so a reader can compare a map value
directly against the catalog.

---

### 2026-07-27 — Coastal presentation unified across all result maps

**[DECISION — the characterization metrics are shown on the coast]** The
per-grid-point explorer that accompanies the Hazard Index previously drew the
808 ocean points as a dot cloud, while the Hazard Index itself was drawn on the
coastline. The two panels now share one presentation: the same clipped Natural
Earth coastline, the same ≤5 km segmentation in EPSG:5880, the same
nearest-grid-point assignment, and the same discrete class colors. Each coastal
feature stores `metrics_index`, the array position of its source grid point in
the Step 3.8 metric catalog, so all 87 metrics are rendered from the existing
catalog without duplicating it. No metric is interpolated or recalculated along
the coast; the transposition remains purely cartographic.

Class limits for the 87 metrics are computed from the observed range with
rounded breaks: sequential (magma) for positive quantities, diverging (RdBu)
for signed quantities such as Sen slopes and peak lags, and a cyclic palette
for peak months. The palettes are defined once in
`src/04_risk_integration/palettes.py` and exported into the website metadata,
so figures and site legends cannot drift apart.

**[DECISION — nearest municipality attached to every coastal segment]** Each
segment now carries the nearest coastal municipality
(`sjoin_nearest` on the municipal polygons in EPSG:5880; 281 distinct
municipalities, maximum centroid distance 29.9 km, median 0 km because the
coastline is clipped to a 30-km municipal buffer). This makes the hand-off to
the risk integration explicit when reading any hazard map, and is attached for
interpretation only — it takes no part in the Hazard Index calculation.

**[DECISION — raw stages published next to the normalized ones]** The municipal
risk panel now publishes `Hazard_Index_raw` and `Risk_Hazard_raw` alongside
`Hazard_Index` and `Risk_Hazard`. Verified on the current dataset: the Spearman
rank correlation between each raw quantity and its normalized counterpart is
exactly 1, confirming that Min–Max rescaling changes the numeric range and not
the ranking of municipalities. Class limits are chosen so that every observed
value falls inside the published legend.

**[DECISION — the delivered legacy product is no longer a website page]** The
`/results/risk-integration/legacy` page was removed. *(Superseded on 2026-07-28:
the `Legacy_*` and `CountOnly_*` fields and the two
`risk_index_legacy_*` artefacts were removed altogether — see the
2026-07-28 entry above.)*

---

**Social Vulnerability Index (SVI_Coast_2022)**: built from 10 IBGE/SIDRA 2022 socioeconomic
and infrastructure variables, standardized (StandardScaler), reduced by PCA; PC1 is
sign-adjusted so higher = more vulnerable and Min–Max normalized to 0–100. Method after Lima
et al. (2024). This is the only part of the chain that uses PCA.

---

### 2026-07-29 — Compound detector redesigned; duration retired from the hazard index

**[DECISION — the tide becomes a conditioning variable, and the index carries
two components]** This supersedes the decision recorded on 2026-07-27 above,
which promoted frequency, duration and intensity as three equally weighted
components.

Two independent problems were established by the scientific audit (records
AUD-01 and AUD-06) and turned out to be inseparable.

*Detection.* The level driver was `SSH_total = zos + tide`. Where the tide is
macrotidal it carries 96–98 % of the variance of that sum, so a local q90 on it
became the spring-tide envelope and exceedances recurred fortnightly by
construction. A Rayleigh test of compound start dates against the 14.765-day
spring-neap period found significant phase locking at 88.5 % of the 808 grid
points and at 100 % of those north of 20° S, against 5 % in Rio Grande do Sul.
The variance ratio var(tide)/var(SSH_total) correlates with that statistic at
Spearman 0.837, confirming the mechanism.

The detector now uses the **dynamic sea level alone** for the level driver, and
the tide re-enters as a **conditioning variable**: an event additionally
requires the still water level, referenced to local mean sea level, to exceed
the local **mean high water springs** datum, computed as the sum of the M2 and
S2 amplitudes from FES2022. The tide no longer decides whether an event
occurred; it decides whether the water rose above the level the coast routinely
experiences. No wave-setup term is included: waves already act as a driver and
as half of the severity term, and a defensible setup parameterisation would
require wave period and beach slope, neither available across the domain.

*Index.* The duration component measured the number of days on which two
percentile tests happened to agree — a statistical coincidence rather than a
physical duration — over a domain-wide range of about one day imposed by the
daily resolution of the sea-level field, and it anticorrelated with frequency
(Spearman −0.550), so the two cancelled inside the equal-weight mean. It is
replaced by the **integrated severity**: the compound severity summed over the
days on which all detection criteria hold, so magnitude and persistence enter as
one quantity. That quantity correlates with frequency at **+0.599**, i.e. the
components now reinforce rather than cancel.

    Hazard_Index_raw = [ norm(compound_count_total) + norm(mean_integrated_severity) ] / 2
    Hazard_Index     = norm(Hazard_Index_raw)

Duration and the peak-based intensity remain computed and published as
diagnostics; they simply no longer enter the index.

*Outcome.* The hazard field acquired a monotonic south-to-north gradient
(Spearman with absolute latitude +0.584), consistent with the extratropical
cyclone climatology of the South Atlantic. In the municipal risk ranking, the
share of the top ten located north of 20° S fell from 70 % to 50 %. Neither
change is defensible alone: applying the detector revision while retaining the
duration raises that share to 90 %.

*Preserved.* The superseded products are archived under
`outputs/legacy_ssh_total_method/`, and the two methods are compared under
`outputs/method_comparison_ssh_total_vs_mhws/`.


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

---

## 2026-07-30 — Portão e datum em HAT, e o par recalibrado

### Definição vigente

O detector composto passa a usar o **HAT como portão de nível e como datum da
severidade**, os dois no mesmo nível. Substitui o MHWS, vigente entre
2026-07-29 e 2026-07-30, cujos produtos estão preservados em
`outputs/legacy_mhws_method/`.

$$
\text{onda: } H_s(d) \ge q_{70}^{\,\text{local}}
\qquad
\text{nível: } \eta(d) \ge q_{99}^{\,\text{local}}
$$

$$
\mathrm{SWL}(d) = \bigl(\eta(d) - \overline{\eta}\bigr) + \tau_{\max}(d)
\qquad
\mathrm{HAT} = \max_{1993 \le t \le 2025} \tau_{\max}(t)
$$

Um evento composto é um episódio de onda e um episódio de nível que
compartilham ao menos um dia de excedência (agrupamento por componentes conexas,
gap $\le 1$ dia), **condicionado a**

$$
\max_{d \in \mathcal{O}} \mathrm{SWL}(d) > \mathrm{HAT}
$$

onde $\mathcal{O}$ é o conjunto de dias de sobreposição. A severidade integrada
soma, sobre os dias de critério pleno,

$$
S = \sum_{d \in \mathcal{F}} \tfrac{1}{2}\left[
  \mathcal{N}\bigl(H_s(d) - \mathrm{thr}_{hs}\bigr) +
  \mathcal{N}\bigl(\mathrm{SWL}(d) - \mathrm{HAT}\bigr)
\right]
$$

com $\mathcal{N}$ reescalando pelos percentis Q05/Q95 do excesso agrupados no
domínio inteiro, **recalculados dentro deste braço**.

### Por que HAT, e por que portão e datum no mesmo nível

O portão MHWS mostrou-se pouco informativo em toda a costa: a maré astronômica
sozinha já o cruzaria em 73,0 % dos eventos ao norte de 15°S e em 79,6 % ao sul
de 25°S. Pior, o **conteúdo físico da severidade variava com a latitude** — 56 %
do excesso de nível no Amapá era astronômico, contra 26 % no Rio Grande do Sul —
de modo que um mesmo valor do índice significava astronomia no Norte e
sobrelevação no Sudeste.

Como $\tau \le \mathrm{HAT}$ por definição, o termo astronômico do excesso

$$
\mathrm{SWL} - \mathrm{HAT} = \underbrace{(\eta - \overline{\eta})}_{\text{meteorológico}} + \underbrace{(\tau_{\max} - \mathrm{HAT})}_{\le\, 0}
$$

é sempre não positivo, e a severidade fica sendo a sobrelevação descontada do
déficit de maré.

**Portão e datum não podem divergir.** O híbrido portão-HAT com datum-MHWS foi
avaliado e é indefensável: a constante herdada $\mathrm{HAT} - \mathrm{MHWS}$
responderia por 94–99 % do excesso no Norte, tornando a severidade um número
fixado pela estrutura harmônica local. O excesso só tem interpretação como
distância da condição que define o evento.

### Par de limiares

**q70 (onda) / q99 (nível)**, recalibrado no Step 2e de 2026-07-30 sobre este
mesmo detector — ver `src/02_threshold_calibration/05_pu_composite_calibration/SCIENTIFIC_NOTES.md`.
O par anterior, q90/q90, fora otimizado sobre `SSH_total`, variável que este
método não lê.

### Pressupostos

1. **HAT como estatística de ordem extrema.** É o máximo de uma amostra de 33
   anos, dependente do comprimento e da janela do registro, ao contrário de
   $A_{M2} + A_{S2}$, que é analítico. **[INCERTO]** O conjunto de eventos passa
   a depender de 1993–2025 e não é transferível diretamente a projeções. 33 anos
   cobrem o ciclo nodal de 18,6 anos, o que limita mas não elimina o problema.
2. **Soma linear de maré e `zos`.** GLORYS12 (sem forçante de maré) e FES2022
   são modelos independentes; a soma ignora a supressão não linear de
   sobrelevação em preamar em águas rasas, efeito potencialmente relevante na
   plataforma amazônica.
3. **Incoerência de fase.** `zos` é instantâneo às 00:00 UTC e $\tau_{\max}$ é
   máximo diário; os dois termos de SWL não compartilham timestamp, de modo que
   SWL superestima o nível instantâneo (AUD-03).
4. **Política de ponto sem evento.** Ausência de evento aceito implica
   frequência $=0$ e severidade integrada $=0$, nunca ausente. Preserva os 808
   pontos na população de normalização Min–Max.

### Resultados

| Quantidade | MHWS | HAT q90/q90 | **HAT q70/q99** |
|---|---:|---:|---:|
| eventos no domínio | 79 639 | 37 225 | **16 768** |
| pontos sem evento (de 808) | 0 | 248 | **208** |
| municípios sem evento (de 280) | 0 | 96 | **83** |
| $\rho(\lvert\text{lat}\rvert, \text{Índice})$ | +0,584 | +0,658 | **+0,710** |
| $\rho(\lvert\text{lat}\rvert, \text{Severidade})$ | +0,345 | +0,653 | **+0,699** |
| severidade média no AP | 0,429 | 0,112 | **0,048** |
| severidade média em SC/PR | 0,438 | 0,497 | **0,486** |

O empate entre Amapá e Santa Catarina na severidade, que motivou a mudança,
desaparece. A cobertura **melhora** frente ao braço q90/q90 (208 pontos zerados
contra 248) porque o limiar de onda mais baixo compensa o portão de nível mais
estrito.

### Caveats e limitações

1. **[BLOQUEANTE] AUD-02 piorou.** O `thr_hs` mínimo nos 808 pontos cai de
   0,20 m para **0,14 m**; pontos abaixo de 1,5 m sobem de 129 para **256**. Um
   "evento de onda extrema" com $H_s = 0{,}14$ m não é defensável.
2. **[BLOQUEANTE] O critério falsificável (c) reprovou.** O ranking municipal
   move-se de forma relevante: Spearman de 0,695 no domínio, 4 de 10 municípios
   mantidos no topo, deslocamento mediano de 36 posições no Sul/Sudeste. A
   adoção seguiu assim, por decisão do pesquisador responsável, contra a
   conclusão do §6 de `outputs/method_comparison_mhws_vs_hat/README.md`.
3. **[PENDENTE] Steps 3.1 e 3.3–3.8 não foram regenerados.** Eles leem os
   catálogos de $H_s$ e `SSH_total` produzidos pelo Step 3.1 em q90/q90.
   Reexecutá-los sem alterar o Step 3.1 produziria um híbrido incoerente —
   estatísticas de persistência, sazonalidade, tendência, EVA e dependência
   calculadas sobre `SSH_total`, variável que o método vigente não usa.
4. **[INCERTO]** O teste de Rayleigh não foi reexecutado sobre o catálogo final.
5. A remoção de eventos no Norte é **exclusão implícita de domínio**, não
   correção física demonstrada: o portão próximo do máximo astronômico observado
   esvazia o setor macromareal em vez de reponderá-lo.
