# OSR11 — Compound Flooding Events in the South Atlantic Eastern Coast

**The Joint Effect of Meteorological Tides and Extreme Wave Events**

**Authors:** Danilo Couto de Souza, Carolina Barnez Gramcianinov, Ricardo de Camargo, Karine Bastos Leal  
**Institution:** Institute of Astronomy, Geophysics and Atmospheric Sciences (IAG-USP)  
**Status:** Hazard characterization, population exposure and municipal risk integration complete
**Current implementation:** Full Brazilian coast (808 grid points, 1993–2025; all Step 3 submodules complete; municipal risk indices produced)

---


> ### Method status — 2026-07-30
>
> The compound-event detector was revised twice in 2026. On **2026-07-29** the
> astronomical tide stopped being a forcing and became a conditioning variable:
> detection moved to tide-free `zos`, with a level gate and a severity datum at
> MHWS. On **2026-07-30** gate and datum both moved to **HAT**, and the Step 2e
> threshold calibration was redone on the production detector, selecting
> **q70 (Hₛ) / q99 (`zos`)** in place of q90/q90.
>
> Superseded products are preserved and versioned:
> [`outputs/legacy_ssh_total_method/`](outputs/legacy_ssh_total_method/),
> [`outputs/legacy_mhws_method/`](outputs/legacy_mhws_method/) and
> [`outputs/legacy_threshold_calibration_ssh_total/`](outputs/legacy_threshold_calibration_ssh_total/).
>
> **Two audit issues block publication.** **AUD-01** — the HAT adoption went
> ahead with one of its three pre-registered falsifiable criteria *failed*
> (municipal ranking stability), against the explicit conclusion of the method
> comparison; the decision and the dissent are recorded in
> [AUD-01 §14](docs/scientific_audit/issues/AUD-01_compound_detector_tidal_phase_locking.md).
> **AUD-02** — the recalibration *worsened* the local wave-threshold floor, which
> now reaches 0.14 m at sheltered points, with 256 of 808 points below 1.5 m.
> Neither is resolved.

---

## Abstract

Coastal communities and infrastructure along Brazil's South Atlantic Eastern Coast are increasingly exposed to compound coastal flooding, where meteorological tides (storm surges) coincide with extreme wave events. These compound hazards can amplify inundation, overtopping, erosion, and port disruption, producing severe socioeconomic impacts that are still poorly quantified at regional scale in Brazil. 

This project assesses the joint behavior of sea-level surges and significant wave height using CMEMS multiyear reanalyses (GLORYS12 for sea level and WAVERYS for waves), complemented by ERA5 atmospheric forcing to characterize synoptic drivers and seasonality. We identify compound events through a storm-based threshold approach whose detection thresholds (q70 for Hₛ, q99 for tide-free sea level) are empirically calibrated against reported SC coastal disaster records, and which requires the still water level over the shared days to exceed the local highest astronomical tide (HAT). Hazard characterization is complete for the full Brazilian coast (808 grid points, 1993–2025) and is integrated with population exposure from the census grid and social vulnerability to produce compound coastal risk indices and identify priority hotspots for adaptation planning.

---

## Stakeholders

The expected outcomes of this research are designed to support:

- **Port Authorities** — Risk assessment for port infrastructure and operations
- **Local Governments** — Coastal adaptation planning and emergency preparedness
- **Brazilian Navy** — Maritime operations and coastal zone management
- **Academia** — Compound hazard research and climate services development
- **Civil Protection Agencies** — Early warning systems and disaster risk reduction

---

## Conceptual Framework

The project follows the standard risk assessment chain:

```
COMPOUND HAZARD → EXPOSURE → VULNERABILITY → RISK
```

**Definitions:**

- **Compound hazard:** The simultaneous occurrence of a sea-level extreme (associated with storm surge and meteorological tides) and a **local significant-wave-height exceedance**, capable of amplifying coastal impacts beyond what isolated extremes would produce. Both criteria are **local percentiles**, so the wave term measures local rarity rather than absolute severity — see the calibration-domain note in Sub-step 2e.

- **Exposure:** The people present where the hazard acts — here, a weighted **resident** (*de jure*) population from cumulative 1, 2, 5 and 10 km coastline bands, counted by the IBGE Grade Estatística on the single reference date of 2022-07-31. It is a proximity criterion, not a modelled inundation extent, so it counts residents *near* the coast and never residents *affected*; and being *de jure*, it does not see the seasonal population of the resort municipalities (AUD-14). (Until 2026-07-28 this repository used the word "exposure" for the spatial association between ocean grid points and municipalities, which is a cartographic step and not an exposure component; that usage was wrong and has been removed.)

- **Vulnerability:** The **social** susceptibility of the resident population — income, education, race, age structure, housing tenure, crowding and basic sanitation — measured by `SVI_Coast_2022` (Sub-step 4.3). **No physical susceptibility layer is implemented.** Geomorphology, beach-face slope, dune and mangrove barriers, terrain elevation, coastal defences and drainage capacity are absent from this product; two stretches with the same income profile and the same hazard therefore receive the same vulnerability regardless of the ground they stand on. This is a declared limitation of the current cycle, not an omission from the description — see "Notes and Limitations". (Tracked as AUD-10.)

- **Risk:** The integration of hazard, exposure, and vulnerability to identify priority areas and inform adaptation interventions.

- **Hotspot:** A municipality whose **90 % rank interval stays within the first N positions** under a bootstrap over the 33 years of record — that is, one that does not leave the band when the record is resampled. Seven municipalities qualify at N = 10 and fourteen at N = 20. The term is used **only** in that sense. It does **not** mean a discrete cluster: among the 196 municipalities with any accepted compound event the risk distribution is continuous and unimodal (Silverman critical-bandwidth test, *p* = 0.56), and Fisher–Jenks goodness of variance fit rises smoothly with no elbow at any class count. The one genuine break in the distribution is the point mass of 84 municipalities at exactly zero, which is a statement about the record and not the lowest class of a gradient. (Tracked as AUD-16.)

---

## Research Objectives

**General Objective:**

Quantify the joint occurrence, intensity, and temporal structure of sea-level extremes and significant wave height extremes along the eastern coast of Brazil using multiyear CMEMS reanalyses (GLORYS12 and WAVERYS). Reported coastal disaster records support threshold calibration through a CSI grid scan and PU composite framework. Integrate hazard characterization with population exposure and social vulnerability to produce compound coastal risk indices and identify priority hotspots for adaptation planning.

**Specific Objectives:**

1. Compile, harmonize, and quality-check CMEMS oceanographic reanalyses, ERA5 atmospheric forcing, and Brazilian coastal disaster databases (S2ID, Atlas Digital, SC Civil Defense).

2. Calibrate extreme event thresholds for sea level and significant wave height using historically reported disasters in Santa Catarina as supporting evidence, establishing an empirically grounded detection framework through CSI grid scan (diagnostic) and PU Composite Calibration (final).

3. Construct independent storm catalogs for sea-level extremes and wave extremes, recording event characteristics (start, end, duration, peak intensity, integrated intensity) in structured JSON format.

4. Identify compound wave–surge events based on temporal overlap of independent storms, quantifying co-occurrence statistics, peak time lags, and overlap durations.

5. Produce spatial exposure maps of compound event frequency, intensity, and temporal trends along the Brazilian coast.

6. Construct a Social Vulnerability Index (SVI_Coast_2022) from 2022 IBGE Census data for 282 coastal municipalities using PCA on 10 socioeconomic and infrastructure variables, and quantify population exposure from the IBGE Grade Estatística 2022.

7. Generate coastal risk maps by combining hazard, exposure, and vulnerability components, identifying priority hotspots for targeted adaptation measures.

8. Characterize the synoptic and mesoscale atmospheric conditions (ERA5) associated with the most severe compound events, linking statistical hazard products to physical drivers.

---

## Data Sources

| Source | Product | Variables | Period | Resolution | Purpose |
|--------|---------|-----------|--------|------------|---------|
| CMEMS | WAVERYS<br>`GLOBAL_MULTIYEAR_WAV_001_032` | VHM0 (Hₛ), VMDR | 1993–2025 | ~0.2°, 3-hourly | Wave extremes |
| CMEMS | GLORYS12<br>`GLOBAL_MULTIYEAR_PHY_001_030` | zos (SSH) | 1993–2025 | 1/12°, daily | Sea-level extremes |
| ECMWF | ERA5 | MSLP, 10 m wind, SST | 1993–2025 | ~0.25°, hourly | Synoptic drivers |
| SC Civil Defense | Reported coastal disasters<br>(Leal et al. 2024) | Event date, municipality, impacts | 1998–2020 | Event-level | Threshold calibration support |
| S2ID / Atlas Digital | Brazilian disaster registry | Declared disasters, affected population, damages | 1991–present | Municipal | Threshold calibration support |
| IBGE | Localidades / Malhas APIs | Coordinates, boundaries | Current | Municipal | Municipal geometry |
| IBGE | Censo 2022 via SIDRA | 10 socioeconomic indicators | 2022 | Municipal | Social vulnerability |
| IBGE | Grade Estatística 2022 | Population, occupied households | 2022 | 200 m urban / 1 km rural | Population exposure |
| ~~MMA~~ | ~~Macrodiagnóstico da Zona<br>Costeira e Marinha~~ | ~~Geomorphology, erosion,<br>occupation, barriers~~ | — | — | **Not used.** Listed in earlier versions as a physical-vulnerability source; it was never acquired, and no physical layer exists in this product (AUD-10) |

**Data acknowledgments:**  
CMEMS products are accessed via the `copernicusmarine` Python toolbox. Disaster records from S2ID and SC Civil Defense are used exclusively to support threshold calibration (Step 2); they are not used as a separate downstream validation product, given systematic under-reporting acknowledged in both databases. IBGE Census 2022 data accessed via SIDRA for 282 coastal municipalities (281 in Lima et al. 2024, plus Balneário Rincão, created in 2013 and absent from the standard SIDRA aggregates). Population exposure from the IBGE Grade Estatística 2022.

---

## Methodological Framework

The project implements a multi-step execution algorithm aligned with the conceptual risk chain:

### **STEP 1 — Data Preparation**

Compile, harmonize, and quality-check all datasets. Download CMEMS reanalyses (WAVERYS, GLORYS12), preprocess reported events databases, standardize spatial reference systems and temporal coverage, and generate unified metocean datasets on a common grid.

**Status:** ✅ Complete (test domain)  
**Implementation:** `src/01_data_preparation/`
- `acquisition/` — CMEMS download scripts, test fixture generation
- `preprocessing/` — Excel → CSV conversion, spatial regridding (GLORYS → WAVERYS grid)

---

### **STEP 2 — Threshold Calibration** (umbrella step)

Umbrella step that empirically establishes the compound event detection framework. Encompasses four sub-steps (2a–2d) that progressively refine the detection thresholds by comparing against the 91-event SC coastal disaster database.

#### Sub-step 2a — Exploratory Data Analysis

First-look inspection of WAVERYS and GLORYS12 spatial distributions, temporal variability, and the events database. Coastal grid-point selection via Natural Earth coastline. Municipality–grid association via IBGE API. Per-sector boxplots, seasonal cycles, and compound quick-look at empirical q90.

**Status:** ✅ Complete  
**Implementation:** `src/02_threshold_calibration/01_exploratory_data_analysis/`

#### Sub-step 2b — Preliminary Compound Event Occurrence Analysis

First-pass inspection of joint Hₛ and SSH (zos) exceedances at q90 during each of the 91 reported coastal disasters in the Leal et al. (2024) SC database (full coast, 5 sectors, 22 municipalities). Per-event ±3-day windows; MagicA peaks-over-threshold; concomitance metrics. 2 of 91 events show concurrent Hₛ + SSH q90 exceedances (South sector, Barra Velha: May 2001, March 2019). Establishes the baseline from which subsequent calibration steps (2c–2e) progressively refine detection.

**Status:** ✅ Complete  
**Implementation:** `src/02_threshold_calibration/02_preliminary_compound/`

#### Sub-step 2c — Tidal Sensitivity Analysis

FES2022 astronomical tide (eo-tides, hourly evaluation) added to GLORYS12 SSH to form SSH_total = zos(00:00 UTC) + tide(daily max). Detection at q90: 22 → 26 events (+7 new, −3 lost, 19 maintained). Established the SSH_total definition **that has since been superseded**.

> **Phase incoherence of the summed level, and where it still applies (AUD-03).**
> `zos` is a single daily sample at 00:00 UTC; `tide_daily_max` is the largest
> tide of the day, at an arbitrary hour. Their sum is therefore not realised at
> any real instant. GLORYS12 provides no sub-daily sea level, so no correction is
> possible with the available inputs — this is a limitation of the data, not of
> the analysis.
>
> **`SSH_total` is no longer segmented.** Since 2026-07-31 level episodes are
> detected on tide-free `zos` at the local q99, so no tide enters the detection
> threshold and the phase mismatch does **not** affect it. The mismatch survives
> only in the two places where the tide legitimately re-enters: the acceptance
> gate `max(SWL) > HAT` and the level term of the integrated severity, with
> `SWL = (zos − mean zos) + tide_daily_max`.
>
> **Measured magnitude.** Bounding the true high-water `zos` by linear
> interpolation between consecutive daily samples gives a phase error with a
> domain median of **1.2 cm** per day (p95 3.2 cm), and it runs opposite to what
> a tidal argument predicts: ≈1 cm in the macrotidal North (17–19 % of the local
> `zos` standard deviation; rank correlation ρ ≥ 0.9996 against a phase-coherent
> alternative) against **5–10 cm in the micro-tidal South** (50–66 %;
> ρ = 0.93–0.98), where day-to-day `zos` variability is three times larger and
> HAT is low enough that SWL crosses it often. The effect is noise rather than
> bias — 89,922 currently-passing days would be lost and 91,274 currently-failing
> days gained at the two ends of the interval. Reproduce with
> `python -m src.exploratory.audit_AUD_03_ssh_phase_coherence`.

**Status:** ✅ Complete — superseded as the production level definition on 2026-07-31; retained as the historical Step 2c record
**Implementation:** `src/02_threshold_calibration/03_tidal_sensitivity/`

#### Sub-step 2d — CSI Grid Scan (Diagnostic)

81 threshold pairs (q50–q90 × q50–q90) evaluated with causal window [D-2, D-1, D, D+1 00Z]. Optimal CSI pair: Hₛ=q90, SSH_total=q90 (H=21, M=70, F=1 298, CSI=0.0151, FAR=0.984). The extremely high FAR (98.4%) revealed that classical verification metrics are unsuitable for this application due to systematic under-reporting in the Civil Defense database.

**Purpose:** Diagnostic exploration — demonstrated the need for a PU-based approach.  
**Note:** CSI thresholds are NOT used by subsequent steps; Step 2e performs independent calibration.

**Status:** ✅ Complete  
**Implementation:** `src/02_threshold_calibration/04_csi_grid_scan/`

#### Sub-step 2e — PU Composite Calibration (Final Calibration)

**Final threshold calibration** using a positive-unlabeled (PU) composite score that addresses systematic under-reporting. Uses a **combined positive-event set** (expanded documentary database of 56 events + legacy Civil Defense database of 91 events = 147 unique municipality×date pairs, 27 municipalities) curated from news archives, academic theses, technical reports, and Civil Defense records.

**Methodology:** The composite score balances three components:
- **Positive recall** R_pos(θ) = H(θ) / P — fraction of reported events captured
- **Annual burden** B(θ) — normalized detection rate (prevents excessive alerts)
- **Soft unmatched penalty** F_soft(θ) — penalizes unmatched episodes weighted by their plausibility

Each unmatched episode receives a confidence weight q_i based on:
- **External evidence** (E_i): Civil Defense bulletins, municipal reports, news sources
- **Physical intensity** (I_i): Percentile exceedance of detected peaks
- **Context coherence** (C_i): Seasonal timing, neighboring detections, exposure status

The optimal threshold pair is selected by maximizing Score(θ) = w₁·R_pos − w₂·B − w₃·F_soft/P, with default weights (0.60, 0.20, 0.20). Step 2e performs its own **independent threshold sweep** — it does NOT use thresholds from Step 2d. B_target_effective = 12 × 27 = 324 ep/yr.

> **Calibration domain, and what the wave threshold is (AUD-02, AUD-18).** All
> 147 municipality×date pairs are from **Santa Catarina**; the selected pair is
> then applied unchanged across 27° of latitude, from 35°S to 7°N. The wave
> criterion is a **local percentile of significant wave height**, not an absolute
> one, so the quantity detected is a **local Hₛ exceedance** — a measure of local
> rarity — and not an "extreme wave" in any absolute sense. Its absolute value
> varies by an order of magnitude along the coast (0.14 m to 2.40 m; median 0.90 m
> in Maranhão against 1.71 m in Rio Grande do Sul). The composite score does not
> determine this axis: the six best-scoring pairs lie within 1 % of each other and
> span q50–q80, while the level percentile q99 is selected in 14 of 14 sensitivity
> variants. Per-sector and per-state tables are supplementary material
> (`outputs/audit/AUD-02_threshold_exposure/`).

> **Detector performance against reported events, and how to read it (AUD-18).**
> On the calibrated pair q70/q99 the detector captures **R_pos = 0.19** of the
> 147 reported municipality×date pairs (H = 28, M = 119, U = 831,
> `outputs/threshold_calibration/tables/tab_TC5_optimal_pair_pu.csv`), up from
> **R_pos = 0.10** on the superseded q90/q90 pair. The Step 2d diagnostic on that
> earlier pair recorded **FAR = 0.984** and CSI = 0.015. Neither number should be
> read as accuracy. The positive-unlabeled framing exists precisely because the
> "negatives" are **unlabelled, not negative**: a detection with no matching
> record may be a real event that was never reported, and the SC databases are
> acknowledged by their own authors to under-report. A recall of 0.19 against an
> incomplete reference is a lower bound on true recall, and a false-alarm rate
> computed against that same reference is not interpretable as a false-alarm rate
> at all. This is also why the disaster records support calibration only and are
> not used as a downstream validation product.

**Theoretical basis:** Positive-unlabeled learning framework (Bekker and Davis, 2020); impact observation bias (Wyatt et al., 2023; Delforge et al., 2025).

**Status:** ✅ Complete  
**Implementation:** `src/02_threshold_calibration/05_pu_composite_calibration/`

---

### **STEP 3 — Hazard Characterization of Extreme and Compound Coastal Events**

The most comprehensive analysis step. Applies the PU-optimal thresholds from Step 2e to the full 1993–2025 record and runs the complete suite of hazard characterization analyses.

> **Whole step regenerated on 2026-07-31.** Every sub-step now runs on the
> recalibrated pair **q70 (Hₛ) / q99 (tide-free `zos`)**. Sub-step 3.1 rebuilt the
> catalogs on `zos` in place of `SSH_total` (`outputs/storm_catalog/logs/run_metadata.json`:
> `level_var: "zos"`, `level_is_tide_free: true`, `thr_hs_pct: 0.7`,
> `thr_level_pct: 0.99`), and 3.3–3.8 were rerun from those catalogs, so their
> columns are now `zos_*` rather than `ssh_total_*`. The 3.1 and 3.2 thresholds
> agree at all 808 points (maximum absolute difference 0.0 m).
> `outputs/storm_catalog/catalog_ssh_total_storms.json` is the retired
> `SSH_total` catalogue, kept for the record and read by nothing.

| Submodule | Analysis | Key outputs |
|-----------|----------|-------------|
| **3.1 Storm Catalogs** | POT detection + episode clustering at q70 on Hₛ and q99 on tide-free `zos` | Per-grid-point JSON catalogs for Hₛ and `zos` (707 453 and 42 455 episodes) |
| **3.2 Compound Detection** | Temporal overlap of Hₛ and tide-free `zos` episodes, gated by `max(SWL) > HAT` | Compound events, integrated severity over the HAT datum (rescaled domain-wide), retained duration and peak-intensity diagnostics |
| **3.3 Duration & Persistence** | Per-grid-point persistence statistics | Mean/p95/max duration, inter-event times, integrated intensity |
| **3.4 Monthly Seasonality** | Monthly/seasonal climatology | Peak month, seasonal counts (DJF/MAM/JJA/SON) |
| **3.5 Trend Analysis** | Mann–Kendall + Sen slope (8 annual series) | Slope, p-value, direction, modified MK for autocorrelation |
| **3.6 Univariate EVA** | POT–GPD on storm peaks | Return levels (2, 5, 10, 20, 50 yr) with CI |
| **3.7 Dependence Analysis** | Hₛ–`zos` statistical dependence | Kendall's τ, Spearman's ρ, χ, χ̄ |
| **3.8 Site Export** | Unified JSON for results website | All metrics merged per grid point |

**Status:** ✓ Complete — all sub-steps regenerated at q70/q99 on tide-free `zos` with the HAT gate (3.1 on 2026-07-31 01:48, 3.2–3.8 on 2026-07-31 02:08–02:09)
**Implementation:** `src/03_storm_catalog_generation/`  
**Run:**
```bash
# Generate storm catalogs (3.1)
python -m src.03_storm_catalog_generation.01_storm_catalogs.main --mode production --tide-mode auto --workers 20

# Run hazard characterization submodules (3.2–3.8)
python -m src.03_storm_catalog_generation.hazard_characterization --module all
```

---

### **STEP 4 — Exposure, Vulnerability & Risk Integration**

Integration of the compound hazard with population exposure and social vulnerability. The delivered municipal file carries 282 municipalities with SVI; 280 of them have a hazard association and therefore a risk value.

#### Sub-step 4.1 — Transfer of the hazard to municipalities

Compound-event frequency (`compound_count_total`) and mean integrated severity
(`mean_integrated_severity`) are combined first on the 808-point native ocean
grid. The resulting normalized Hazard Index is then transferred to each
municipality at its associated grid point. This is a cartographic transfer, not
an exposure component.

**The association is an input dataset, not a derived one.** It was established
by visual inspection in a GIS, municipality by municipality, weighing proximity
to the municipality against compound-event activity at the candidate point.
Both criteria were arbitrated together by eye; there is no script, and none can
be recovered. The association is therefore archived as versioned data at
`data/external/municipal_grid_association/`, with provenance, and the exporter
reads it from there and verifies it against the delivered shapefile.

Properties of the association, which should be reported with any result derived
from it:

| | |
|---|---|
| Municipalities with an associated point | 280 of 282 |
| Distinct grid points used | **178** |
| Maximum municipalities sharing one point | **9** |
| Distance municipality → point, median | 13.1 km |
| Distance municipality → point, maximum | 89.2 km |
| Assignments beyond 30 km | 20 |

Two consequences follow. Hazard values are **not spatially independent**
between neighbouring municipalities, since 178 points serve 280 units. And
municipalities at the head of Guanabara Bay (Magé, Guapimirim) have **no ocean
grid point within 30 km at all**: their hazard necessarily refers to the open
shelf and does not represent conditions inside the bay. That is a limitation of
grid coverage rather than of the association — no assignment rule resolves it,
as five candidate rules were tested and all return the same value there
(see `docs/scientific_audit/issues/AUD-04_grid_to_municipality_transfer.md`).

#### Sub-step 4.2 — Population exposure

Resident population and occupied households within cumulative 1, 2, 5 and 10 km
bands from the Natural Earth coastline, aggregated from the IBGE Grade Estatística
2022 by cell centroid in EPSG:5880. All four population bands feed the weighted
effective population used by the risk index. Across the 282 coastal municipalities,
**30.8 million** of the 37.4 million residents are within 10 km of the coast.

> **The count is *de jure* and instantaneous.** The census enumerates residents
> at their usual address on 2022-07-31, a single instant set against 33 years of
> metocean record. The seasonal population of the resort municipalities — which
> in Balneário Camboriú, Bombinhas, Guarujá, Ubatuba and Cabo Frio multiplies the
> people present in summer — is therefore invisible, and the bias is directional:
> it **under**states exposure in exactly the SC/PR/SP/RJ sector that carries the
> highest physical hazard in the domain. No seasonal-population proxy is applied,
> because none is available on a homogeneous basis for all 282 municipalities.
> The index measures risk to **residents**, not to visitors or to tourism assets.
> (AUD-14.)
>
> Four delivered records were checked because their `pop_10km` is very small:
> Santa Rita/MA (4 residents), Calçoene/AP (101), Oiapoque/AP (518) and
> Terra de Areia/RS (765). Santa Rita/MA and Calçoene/AP have exposure zero
> because their weighted population remains below the fixed 100-person goalpost;
> this is not a 0.01 floor. Removing
> all four leaves the published ranking unchanged (Spearman ρ = 1.000, maximum
> rank shift 0), so they anchor no normalisation. (AUD-15.)

**Implementation:** `src/04_risk_integration/municipal_exposure.py` (aggregation),
`src/04_risk_integration/exposure_index.py` (normalisation),
`src/01_data_preparation/acquisition/download_ibge_grade.py` (acquisition).

#### Sub-step 4.3 — Social Vulnerability Index (SVI_Coast_2022)

The SVI was built from 10 socioeconomic and infrastructure variables from the 2022 IBGE Census (SIDRA) for 282 coastal municipalities. Variables were standardized with `StandardScaler` and submitted to PCA. PC1 was retained as the vulnerability axis, its global sign checked so that higher values mean higher social vulnerability, and the result rescaled to 0–100 (Min–Max). Methodology based on Lima et al. (2024, *Nat. Hazards*, https://doi.org/10.1007/s11069-023-06246-w).

**PC1 explains 50.5 % of the variance of the ten standardized indicators; PC2 explains 16.5 %.** The mean correlation of PC1 with its inputs came out **positive (+0.468)**, so the global sign flip in the build script did **not** fire: the component was already oriented towards higher deprivation. The loadings are:

| Variable | Description | PC1 loading | *r* with SVI |
|----------|-------------|------------:|-------------:|
| `pop_poverty` | Proportion of households up to ½ minimum wage per capita | **+0.418** | +0.940 |
| `pop_illiterate` | Illiteracy rate (15+) | +0.371 | +0.833 |
| `pop_house` | Mean residents per occupied household (2.40–4.45) | +0.350 | +0.787 |
| `pop_nogarbage` | Proportion of households without waste collection | +0.349 | +0.783 |
| `pop_nonwhite` | Proportion not self-declared white | +0.347 | +0.780 |
| `pop_nosewage` | Proportion without adequate sewage | +0.320 | +0.719 |
| `pop_nowater` | Proportion without a general water network | +0.254 | +0.570 |
| `pop_nopaving` | Proportion on unpaved streets | +0.152 | +0.342 |
| `pop_agevul` | Proportion in vulnerable age groups (0–9 and 60+) | **−0.137** | −0.309 |
| `pop_rent` | Proportion of households **not owned** by a resident | **−0.338** | −0.760 |

> **The two negative loadings are empirical results, not coding errors.** Every
> one of the ten columns was traced back to its SIDRA query and tested against
> municipalities whose real-world standing is not in dispute; all ten passed, so
> no column is reversed. `pop_rent` loads negatively because non-ownership in
> Brazil is a trait of urban affluence — rental and second-home stock concentrate
> in the wealthy southern resort towns (Balneário Camboriú, 50.3 %) while
> self-built owner occupancy dominates the poor rural coast (Chaves/PA, 9.8 %).
> `pop_agevul` loads weakly negatively because it sums two age tails that move in
> opposite directions with income: the 0–9 share falls with development while the
> 60+ share rises, so their sum is nearly flat across the deprivation gradient.
> Forcing the sign of either input before the PCA is a mathematical no-op — it
> reflects the loading and leaves the component identical (ρ = 1.000, zero rank
> shifts). See AUD-09 for the full audit.

> **What the index is.** `SVI_Coast_2022` correlates *r* = **+0.940** with
> `pop_poverty` and ρ = **−0.491** with log municipal population: it is an axis of
> **material deprivation**, tracking Brazil's north–south development gradient. It
> is *not* a measure of susceptibility to coastal flooding specifically, and it
> contains no physical susceptibility at all (AUD-10). Two artefacts of the final
> Min–Max are worth naming: Balneário Camboriú/SC receives exactly **0** and
> Chaves/PA exactly **100**, because each anchors one end of the scale.

#### Sub-step 4.4 — Hazard Index and integrated risk

```
Hazard_Frequency = min(compound_count_total / 99, 1)
Hazard_Severity  = min(fillna(mean_integrated_severity, 0) / 1, 1)
Hazard_Index = Hazard_Index_mun = (Hazard_Frequency + Hazard_Severity) / 2

pop_eff = 0.4*pop_1km + 0.3*pop_2km + 0.2*pop_5km + 0.1*pop_10km
Exposure_absolute = clip[(log10(pop_eff) - 2) / (6 - 2), 0, 1]
Exposure_relative = pop_eff / pop_municipality
Exposure_Index = sqrt(Exposure_absolute * Exposure_relative)

V = Phi(PC1 / sd(PC1, ddof=0))
Risk_Hazard = (Hazard_Index_mun * Exposure_Index * V) ^ (1/3)
```

Where:
- no floor, municipal hazard Min–Max, or final risk Min–Max is applied
- `V` preserves the original SVI ordering (ρ = 1.0000) while avoiding exact
  sample-extreme anchors; the original `SVI_Coast_2022` remains published
- `Exposure_Index` — effective/weighted population, not a literal inhabitant
  count. Because the bands are cumulative, the equivalent ring weights are
  1.0 (0–1 km), 0.6 (1–2 km), 0.3 (2–5 km), and 0.1 (5–10 km), from the
  IBGE Grade Estatística 2022 (200 m urban / 1 km rural cells). Goalposts of
  10² and 10⁶ inhabitants are **fixed**, not taken from the data, so the scale
  does not move when the set of municipalities changes
- `Risk_Hazard` — the **geometric** mean of the three components. Conjunctive by
  construction: a component near zero pulls the index down, which is the
  property the IPCC risk framework implies. An arithmetic mean would let a large
  population compensate for the absence of a physical driver

An exact zero caused by hazard means **no compound event met the acceptance
criteria in 1993–2025**; it does not mean that physical coastal risk is
impossible. Missing association is a separate, explicit coverage category.

> **How `Risk_Hazard` may and may not be read (AUD-11).** It is a **relative
> prioritisation index among the Brazilian coastal municipalities analysed
> here** — not absolute risk, not a probability, and **not comparable with other
> studies or with a future revision of this one**. Hazard and exposure now use
> fixed anchors and therefore do not depend on which municipalities are in the
> set. **One dependence survives**: `sd(PC1)` in the vulnerability factor is
> estimated from the delivered sample, so restricting the domain rescales it for
> everyone. The two scales of that residual differ sharply. Removing a single
> municipality moves any other by at most **0.0036** — the worst case is
> Chaves/PA, which alone shifts `sd(PC1)` by 1 % — against **0.0945** under the
> superseded Min–Max chain, a **26-fold reduction**, and no removal changes any
> rank by more than three positions. But excluding a whole region is a different
> matter: dropping the North and Northeast changes `sd(PC1)` by **−57 %** and
> reorders the remaining 104 municipalities at **ρ = 0.70**, with a maximum
> displacement of 0.29 in the index. The published values are conditional on the
> 282-municipality domain, and any subset analysis must recompute the scale
> rather than slice these values.
> *(`src/exploratory/audit_AUD_11_scale_anchoring.py`)*

The exposure recipe follows the Index for Risk Management
([INFORM, JRC](https://drmkc.jrc.ec.europa.eu/inform-index/INFORM-Risk/Methodology)),
which treats the same problem for its physical-exposure indicators: log for a
people count (§6.2), fixed goalposts rather than observed extremes (§6.3), and
an absolute reading paired with a relative one (Box 2), because the count
favours the metropolitan municipalities while the share favours the small,
entirely coastal ones.

**Products generated:**
- `SVI_Coast_2022` — Social Vulnerability Index (external; audited, see below)
- `Hazard_Frequency`, `Hazard_Severity` — native-grid normalized hazard components
- `mean_overlap_duration`, `mean_compound_intensity_norm` — diagnostics, published but no longer index components (see AUD-06)
- `Hazard_Index_raw` — equal-weight mean of the three normalized components
- `Hazard_Index` / `Hazard_Index_mun` — fixed-anchor index, transferred without municipal renormalization
- `Exposure_Index`, `Exposure_absolute`, `Exposure_relative`
- `Risk_Hazard_raw` / `Risk_Hazard` — identical geometric mean of `Hazard_Index_mun`, `Exposure_Index` and `V`; no floor or final Min–Max

> **Notes.** (1) The hazard is implemented in `src/04_risk_integration/hazard_index.py` and reads the versioned `outputs/storm_catalog/compound/compound_metrics.csv`; the exposure in `src/04_risk_integration/exposure_index.py` and `municipal_exposure.py`; the external municipal file supplies only SVI, geometry and the pre-associated grid coordinates. (2) The export produces a single product; the delivered hazard/risk DBF columns are ignored. (3) The SVI script was obtained from its author and audited — the index reproduces exactly — but the point-to-municipality association remains external and unaudited; see `src/04_risk_integration/external_svi/README.md`. (4) Frequency is negatively correlated with mean duration and intensity, so the equal-weight average represents an explicit compensatory index rather than three mutually reinforcing signals. See `SCIENTIFIC_NOTES.md` → "Step 4 — Exposure, Vulnerability & Risk Integration".

**Status:** ✅ Complete  
**Website panels:** `/results/hazard-characterization` leads with the coastal Hazard Index map (three current layers drawn on the Natural Earth coastline) and keeps the metric explorer below it. `/results/risk-integration` displays the fixed-anchor hazard, weighted exposure, transformed vulnerability and their geometric-mean risk; the `*_raw` aliases are retained for audit but equal their published counterparts because no second Min–Max is applied. `/methodology/hazard-index` is the step-by-step reference for the index construction, and `/methodology/compound-detection` tells the same story as a continuous narrative from the storm catalogs to the composite index.

**Risk-index shapefile export:**
Karine's shapefile outputs are stored in `outputs/risk_index/` as `risk_index.shp`, `.shx`, `.dbf`, `.prj`, and `.cpg`. Convert them to the web data format with:

```bash
python -m src.site.export_risk_index_data
```

The exporter writes:
- `site/public/data/risk_index_municipalities.geojson`
- `site/public/data/risk_index_metadata.json`

Only one quantity is read from the shapefile by name, and DBF truncation means it
can arrive under several spellings; the resolved alias is recorded in the metadata:
- `SVI_Coast_2022` maps to `SVI_Coast_`

`Hazard_Index` is calculated on the native grid from compound-event frequency
and mean integrated severity, and transferred by `grid_lat`/`grid_lon`
**without renormalization**. `Risk_Hazard_raw` and the normalized `Risk_Hazard`
are then derived from that hazard together with the exposure and vulnerability
components. The delivered `Haz_index`/`Risk_comp`/`Risk_harza` columns are
not read at all — they were computed with a superseded definition. If
`outputs/risk_index/risk_index.shp` is absent the export raises
`FileNotFoundError`; there is no fallback to a previous export.

#### Sub-step 4.5 — Coastal representation of the Hazard Index

The Hazard Index lives on ocean grid points but is communicated along the
shoreline. `src/04_risk_integration/coastal_projection.py` is the single
implementation of that cartographic step:

1. the Natural Earth 10-m coastline is clipped to a 30-km buffer around the
   union of the coastal municipalities;
2. the linework is reprojected to SIRGAS 2000 / Brazil Polyconic (EPSG:5880)
   and split into segments of at most 5 km;
3. each segment is assigned the values of its nearest native ocean grid point,
   measured between the segment midpoint and the point in the metric projection.

The operation **never recalculates or renormalizes the index**. The same module
backs the article figure `coastal_hazard_index_components.png`, the exploratory
comparison, and the website layer, so all three are geometrically identical.
Discrete class colors are shared through `src/04_risk_integration/palettes.py`.

Generate the website layers with:

```bash
python -m src.site.export_coastal_hazard_data
```

which writes `site/public/data/coastal_hazard_segments.geojson`,
`coastal_hazard_metadata.json` (source file, native point count, segment count,
projection, maximum segment length, association method, nearest-distance
statistics, per-layer fields, units, class limits and palettes), and
`coastal_basemap.geojson` (Natural Earth land, country, and Brazilian state
context). The main map exposes three current layers: `compound_count_annual_mean`
(events yr⁻¹), `mean_integrated_severity` (dimensionless), and `Hazard_Index`
(0–1). The component layers show catalog values in their own units; the index
uses fixed anchors of 99 events and severity 1, not sample Min–Max.

Each coastal segment also carries:

- `municipality_name` / `municipality_state` / `municipality_distance_km` — the
  nearest coastal municipality, computed with `sjoin_nearest` in EPSG:5880.
  This is the unit that receives the hazard in Step 4; it is attached for
  interpretation and takes no part in the index calculation.
- `metrics_index` — the array position of the source grid point inside
  `hazard_characterization_grid_metrics.json`, so the website can draw any of
  the 87 Step 3 characterization metrics on the same coastline without
  duplicating the metric catalog.

The website therefore renders both the Hazard Index and the full metric
explorer with one geometry, one basemap, and one palette catalog.

---


## Current Implementation Status

The repository currently contains:

✅ **STEP 1 — Data Preparation** (complete for test domain)
- Implemented in `src/01_data_preparation/`
- CMEMS download scripts (`acquisition/`)
- Test fixture generation for south SC sector and full SC coast
- Reported events preprocessing (Excel → CSV)
- Spatial regridding: GLORYS → WAVERYS grid (`preprocessing/`)

✅ **STEP 2 — Threshold Calibration** (all sub-steps 2a–2e complete)

- **Sub-step 2a** — Exploratory Data Analysis
- **Sub-step 2b** — Preliminary Compound Analysis
- **Sub-step 2c** — Tidal Sensitivity
- **Sub-step 2d** — CSI Grid Scan (diagnostic)
- **Sub-step 2e** — PU Composite Calibration (final)

✅ **STEP 3 — Hazard Characterization** (complete for full Brazilian coast)
- Compound detection (Step 3.2) under the current HAT-gated method: **16,768 events** over 808 grid points, 1993–2025; 208 points and 83 municipalities carry no accepted event
- **All sub-steps regenerated on 2026-07-31** under the current method: 3.1 rebuilt the catalogs on tide-free `zos` at q70/q99, and 3.3–3.8 were rerun from those catalogs. No published statistic still derives from `SSH_total`

✅ **STEP 4 — Exposure, Vulnerability & Risk Integration** (complete at municipal scale)
- SVI_Coast_2022 constructed from 10 IBGE Census 2022 variables via PCA (282 coastal municipalities)
- Exposure from the weighted cumulative 1, 2, 5 and 10 km populations (IBGE Grade Estatística 2022), not a spatial join of oceanic hazard metrics
- Current `Hazard_Index = [min(compound_count_total/99,1) + min(fillna(mean_integrated_severity,0)/1,1)]/2`; `Risk_Hazard = (Hazard_Index_mun × Exposure_Index × Φ(PC1/sd(PC1)))^(1/3)`, with no floor or sample-dependent Min–Max — see Sub-step 4.4
- **Vulnerability is social only.** No physical susceptibility layer exists (AUD-10); 2 of 282 municipalities carry no risk value (AUD-15)


---

## Repository Structure

```
osr11/
├── README.md                                 # This file: project overview and scientific framework
├── environment.yml                           # Conda environment specification
├── config/
│   ├── plot_config.py                        # Shared figure styling (FigureStyle dataclass)
│   ├── download_config.example.yml           # Template for CMEMS download configuration
│   └── test_fixture.example.yml              # Template for test fixture generation
├── data/
│   ├── README.md                             # Data directory documentation
│   ├── test/                                 # Committed test-domain NetCDF subsets
│   │   ├── README.md                         # Test data description and limitations
│   │   ├── waverys_sc_sul_test.nc            # VHM0, VMDR · 3-hourly · south SC
│   │   ├── glorys_sc_sul_test.nc             # zos · daily · south SC
│   │   ├── metocean_sc_sul_unified_waverys_grid.nc  # Unified daily · south SC
│   │   ├── waverys_sc_full_test.nc           # VHM0, VMDR · 3-hourly · full SC
│   │   ├── glorys_sc_full_test.nc            # zos · daily · full SC
│   │   └── metocean_sc_full_unified_waverys_grid.nc # Unified daily · full SC
│   ├── reported events/
│   │   ├── README.md                         # Reported events database documentation
│   │   └── reported_events_Karine_sc.csv     # SC Civil Defense disaster database (Leal et al. 2024)
│   ├── ne_10m_coastline/                     # Natural Earth 10m coastline shapefile
│   └── raw/                                  # Full CMEMS downloads (not committed, .gitignore)
├── src/
│   ├── __init__.py                           # Import alias registry for numbered analysis dirs
│   │
│   ├── 01_data_preparation/                  # STEP 1 — Data Preparation
│   │   ├── acquisition/                      #   Download CMEMS data
│   │   │   ├── download_cmems.py             #     Main CMEMS download script
│   │   │   ├── download_cmems_parallel.py    #     Parallel download variant
│   │   │   ├── catalog_inspect.py            #     CMEMS catalog inspection utility
│   │   │   └── build_test_fixture.py         #     Build test-domain NetCDF subsets
│   │   └── preprocessing/                    #   Harmonization, interpolation
│   │       ├── README.md                     #     Preprocessing pipeline documentation
│   │       ├── convert_reported_events.py    #     Excel → CSV conversion
│   │       └── interpolate_glorys_to_waverys_grid.py  # Spatial regridding
│   │
│   └── 02_threshold_calibration/             # STEP 2 — Threshold Calibration (umbrella)
│       ├── 01_exploratory_data_analysis/     #   Sub-step 2a — EDA
│       │   ├── main.py                       #     CLI orchestrator
│       │   ├── io.py, coastal.py, maps.py    #     Analysis modules
│       │   ├── config/analysis_config.py     #     Configuration
│       │   └── README.md, RUN.md             #     Documentation
│       ├── 02_preliminary_compound/          #   Sub-step 2b — Preliminary analysis
│       │   ├── main.py                       #     CLI orchestrator
│       │   ├── events.py, thresholds.py      #     Analysis modules
│       │   ├── config/analysis_config.py     #     Configuration
│       │   └── README.md, RUN.md             #     Documentation
│       ├── 03_tidal_sensitivity/             #   Sub-step 2c — Tidal sensitivity
│       │   ├── main.py                       #     CLI orchestrator
│       │   ├── tides.py                      #     FES2022 integration
│       │   ├── config/analysis_config.py     #     Configuration
│       │   └── README.md                     #     Documentation
│       ├── 04_csi_grid_scan/                 #   Sub-step 2d — CSI grid scan (diagnostic)
│       │   ├── main.py                       #     CLI orchestrator
│       │   ├── calibration.py, metrics.py    #     Analysis modules
│       │   ├── config/analysis_config.py     #     Configuration
│       │   └── README.md, RUN.md, SCIENTIFIC_NOTES.md
│       └── 05_pu_composite_calibration/      #   Sub-step 2e — PU composite calibration (final)
│           ├── main.py                       #     CLI orchestrator
│           ├── scoring.py, audit.py          #     Core PU scoring + episode audit
│           ├── sensitivity.py, figures.py    #     Sensitivity analysis + visualizations
│           ├── config/analysis_config.py     #     Configuration
│           └── README.md, RUN.md, SCIENTIFIC_NOTES.md, INTEGRATION_NOTES.md
│
│   └── 03_storm_catalog_generation/          # STEP 3 — Hazard Characterization
│       ├── 01_storm_catalogs/                #   Submodule 3.1 — Catalog generation
│       │   ├── main.py                       #     CLI orchestrator
│       │   └── segmentation.py, metrics.py, io.py, tides.py, figures.py
│       ├── hazard_characterization.py        #   CLI orchestrator (submodules 3.2–3.8)
│       ├── config/analysis_config.py         #   Configuration
│       ├── shared/catalog_utils.py           #   Shared I/O utilities
│       ├── 02_compound_detection/            #   Submodule 3.2 — Compound events
│       ├── 03_duration_persistence/          #   Submodule 3.3 — Duration statistics
│       ├── 04_monthly_seasonality/           #   Submodule 3.4 — Seasonality
│       ├── 05_trends/                        #   Submodule 3.5 — Mann–Kendall trends
│       ├── 06_univariate_eva/                #   Submodule 3.6 — POT–GPD EVA
│       ├── 07_dependence/                    #   Submodule 3.7 — Hs–SSH dependence
│       ├── 08_site_export/                   #   Submodule 3.8 — Site JSON export
│       └── SCIENTIFIC_NOTES.md               #   Science documentation
│
│   ├── 04_risk_integration/                  # STEP 4 — Exposure, Vulnerability & Risk
│   │   ├── hazard_index.py                   #   Canonical native-grid Hazard Index
│   │   ├── exposure_index.py                 #   Canonical exposure term definitions
│   │   ├── municipal_exposure.py             #   Population aggregation by distance band
│   │   ├── coastal_projection.py             #   Canonical grid → coastline projection
│   │   ├── palettes.py                       #   Shared discrete class palettes
│   │   └── external_svi/                     #   Externally delivered SVI + audit
│   │
│   ├── figures_article/                      # Manuscript-quality figures and tables
│   │   ├── make_article_coastal_hazard_components_map.py
│   │   ├── make_article_hazard_vulnerability_risk_multiplot.py
│   │   ├── make_article_supplementary_integrated_risk_zooms.py
│   │   └── make_article_top10_municipality_tables.py
│   │
│   ├── site/                                 # Website data exporters
│   │   ├── export_risk_index_data.py         #   Municipal risk layers (current + legacy)
│   │   ├── export_coastal_hazard_data.py     #   Coastal Hazard Index layers + basemap
│   │   └── export_storm_maps_data.py         #   Storm map layers
│   │
│   └── exploratory/                          # Exploratory audits and diagnostics
│
├── outputs/                                  # Analysis outputs (not committed, .gitignore)
│   ├── south_sc_test_data_exploratory/       #   Step 2a outputs
│   ├── preliminary_compound/                 #   Step 2b outputs
│   ├── tidal_sensitivity/                    #   Step 2c outputs
│   ├── threshold_calibration/                #   Step 2d and 2e outputs
│   └── storm_catalog/                        #   Step 3 outputs
│       ├── catalog_hs_storms.json            #     Hₛ storm catalog
│       ├── catalog_ssh_total_storms.json     #     SSH_total storm catalog
│       ├── compound/                         #     Compound detection outputs
│       ├── duration_persistence/             #     Persistence metrics
│       ├── seasonality/                      #     Monthly climatology
│       ├── trends/                           #     Trend analysis
│       ├── eva/                              #     Return levels
│       └── dependence/                       #     Dependence metrics
├── logs/                                     # Execution logs (not committed, .gitignore)
└── site/                                     # Scientific results website (Next.js + Tailwind CSS)
    ├── README.md                             # Site documentation
    ├── DEPLOYMENT.md                         # Vercel deployment guide
    ├── app/                                  # Next.js App Router pages
    ├── components/                           # React components
    ├── content/                              # Project metadata and figure definitions
    ├── public/                               # Static assets (figures, etc.)
    └── ...
```

---

## Quick Start

### 1. Environment Setup

```bash
# Clone repository
git clone <repository-url>
cd osr11

# Create conda environment
conda env create -f environment.yml
conda activate osr11

# Authenticate with CMEMS (required for full-domain downloads)
copernicusmarine login
# Enter credentials (stored in ~/.copernicusmarine/)
```

### 2. Run Exploratory Analysis (Step 2a — South SC test domain)

The test fixtures (`data/test/`) are already committed. No download required.

```bash
# Full exploratory analysis (all parts)
python -m src.exploratory_data_analysis.main --all

# Individual parts
python -m src.exploratory_data_analysis.main --maps           # Part A: Spatial maxima
python -m src.exploratory_data_analysis.main --timeseries     # Part B: Time series
python -m src.exploratory_data_analysis.main --events         # Part D: Reported events EDA
python -m src.exploratory_data_analysis.main --municipalities # Part E: Municipality–grid
python -m src.exploratory_data_analysis.main --boxplots       # Part F: Sector overview
python -m src.exploratory_data_analysis.main --statistics     # Part G: Statistical analyses
```

Outputs written to: `outputs/south_sc_test_data_exploratory/`

See `src/02_threshold_calibration/01_exploratory_data_analysis/RUN.md` for complete command reference.

### 3. Run Preliminary Compound Analysis (Step 2b — Full SC coast)

The full SC unified dataset (`data/test/metocean_sc_full_unified_waverys_grid.nc`) is committed.

```bash
# Full analysis (per-event figures + summary)
python -m src.preliminary_compound.main --all

# Individual parts
python -m src.preliminary_compound.main --event-figures   # TC-1: per-event figures
python -m src.preliminary_compound.main --summary         # Summary: S1–S4 + tables
```

Outputs written to: `outputs/preliminary_compound/`

See `src/02_threshold_calibration/02_preliminary_compound/RUN.md` for complete command reference.

### 4. Run CSI Grid Scan — Diagnostic (Step 2d)

```bash
# Full diagnostic threshold scan
python -m src.csi_grid_scan.main --all
```

Outputs written to: `outputs/threshold_calibration/`

See `src/02_threshold_calibration/04_csi_grid_scan/RUN.md` for complete command reference.

> **Note:** Step 2d is diagnostic. Its thresholds are NOT used operationally. Step 2e (PU Composite Calibration) is the final calibration step.

### 5. Run PU Composite Calibration — Final Calibration (Step 2e)

```bash
# Full PU calibration pipeline
python src/02_threshold_calibration/05_pu_composite_calibration/main.py --all
```

Outputs written to: `outputs/threshold_calibration/` (tables prefixed `tab_TC5_*`, figures `fig_TC5_*`)

See `src/02_threshold_calibration/05_pu_composite_calibration/RUN.md` for complete command reference.

### 6. Download Full-Domain Data (Optional)

**Note:** Full GLORYS12 and WAVERYS downloads are large (~100 GB+ for full Brazilian coast, 1993–2025). Test fixtures are sufficient for exploratory work.

```bash
# Inspect CMEMS catalog (recommended before downloading)
python src/01_data_preparation/acquisition/catalog_inspect.py GLOBAL_MULTIYEAR_PHY_001_030
python src/01_data_preparation/acquisition/catalog_inspect.py GLOBAL_MULTIYEAR_WAV_001_032

# Configure download parameters
cp config/download_config.example.yml config/download_config.yml
# Edit config/download_config.yml with desired spatial/temporal extent

# Download GLORYS12 and/or WAVERYS
python src/01_data_preparation/acquisition/download_cmems.py --product glorys
python src/01_data_preparation/acquisition/download_cmems.py --product waverys
# Or both: python src/01_data_preparation/acquisition/download_cmems.py
```

Downloaded files saved to `data/raw/` (not committed to Git).

---

## Results Website

A scientific results website is available in `site/` (Next.js, deployable to Vercel).

```bash
cd site
npm install
npm run dev          # Local development server → http://localhost:3000
npm run build        # Production build
vercel --prod        # Deploy to Vercel (requires Vercel account)
```

To regenerate the municipal risk-index web layer after Karine's shapefile changes:

```bash
python -m src.site.export_risk_index_data
```

See `site/DEPLOYMENT.md` for full deployment instructions and `site/README.md` for site documentation.

---

## Notes and Limitations

### Data Limitations

- **GLORYS12 and WAVERYS resolution:** Reanalysis products have finite spatial resolution (~0.2° for WAVERYS, 1/12° for GLORYS12). Nearshore processes at scales < 10 km may not be fully resolved.

- **Disaster records:** S2ID and Atlas Digital databases have incomplete and uneven reporting. Not all coastal flooding events are officially declared or documented. Reported impacts (damages, affected population) are minimum estimates and subject to underreporting bias.

- **SC Civil Defense database:** The Leal et al. (2024) database provides high-quality event-level data for Santa Catarina (1998–2020) but is geographically limited. Threshold calibration based on SC events introduces regional bias when extrapolated to other coastal sectors—an acknowledged methodological limitation justified by data availability constraints.

### Declared limitations for the manuscript

The twelve paragraphs below are written to be transferable, essentially as they
stand, into the Limitations section of the manuscript. Each closes an audit
issue in `docs/scientific_audit/`; the numbers are reproducible from the scripts
named at the end of each paragraph.

- **Daily phase mismatch in the still-water level (AUD-03).** GLORYS12 supplies a
  single `zos` sample per day, at 00:00 UTC, while the FES2022 term is the
  largest astronomical tide of that day, which occurs at an arbitrary hour. The
  still-water level `SWL = (zos − mean zos) + tide_daily_max` is therefore not
  realised at any real instant, and no correction is possible without sub-daily
  sea level, which the product does not provide. Since 2026-07-31 the mismatch
  no longer touches the level detection threshold — episodes are segmented on
  tide-free `zos`, with no tide added before the percentile is taken — but it
  does enter the acceptance gate `max(SWL) > HAT` and the level term of the
  integrated severity. Bounding the true high-water `zos` by linear
  interpolation between consecutive daily samples puts the phase error at a
  domain median of **1.2 cm** per day (p95 3.2 cm). It is strongly
  latitude-dependent, and **in the opposite direction to the one a tidal
  argument would suggest**: about 1 cm in the macrotidal north (17–19 % of the
  local `zos` standard deviation, rank correlation ρ ≥ 0.9996 against a
  phase-coherent alternative) against **5–10 cm in the micro-tidal south**
  (50–66 % of the local standard deviation, ρ = 0.93–0.98), because day-to-day
  `zos` variability there is three times larger and HAT is low enough that SWL
  crosses it on 3–9 % of days rather than 0.1–0.3 %. On roughly half of the
  southern days that currently pass the gate, the decision would flip at the
  unfavourable end of the interpolation interval. The effect is **noise, not
  bias**: across the domain 89,922 passing days would be lost and 91,274
  currently-failing days would be gained, so the count is not systematically
  inflated or deflated. The consequence to declare is that the attribution of
  *individual* events in the South carries day-level uncertainty, even though
  the aggregate hazard field is stable. No tide-gauge comparison was performed;
  no observed sea-level series is held in this repository, and acquiring one
  (GLOSS/IBGE or Marinha do Brasil) remains an open validation step.
  *(`src/exploratory/audit_AUD_03_ssh_phase_coherence.py`)*

- **Vulnerability is social only; there is no physical susceptibility layer
  (AUD-10).** Vulnerability enters the risk index exclusively through
  `SVI_Coast_2022`, built from ten IBGE/SIDRA 2022 socioeconomic and
  infrastructure indicators. No variable describes the ground itself:
  construction typology, terrain elevation, beach-face slope, dune, mangrove or
  reef barriers, hard coastal defences, and drainage capacity are all absent.
  Two municipalities with the same income profile and the same hazard therefore
  receive the same vulnerability whether the exposed frontage is a rocky cliff
  or a sand plain one metre above sea level — precisely the factor that
  translates a given forcing into a given impact. The earlier framing, which
  listed the MMA *Macrodiagnóstico da Zona Costeira e Marinha* as a
  vulnerability source, was never implemented and has been withdrawn from the
  data-source table. Exposure and vulnerability should also not be conflated:
  the population count is exposure, not a physical vulnerability proxy. Building
  the physical layer is the recommended next step, not a claim of this cycle.

- **Exposure is resident and instantaneous; seasonal population is invisible
  (AUD-14).** The exposure term counts residents *de jure* at their usual
  address on 2022-07-31, a single instant set against 33 years of metocean
  record. The floating population of the resort municipalities — which in
  Balneário Camboriú, Bombinhas, Guarujá, Ubatuba and Cabo Frio multiplies the
  people present during the summer — does not appear. The bias is systematic and
  directional: it **understates** exposure in exactly the SC/PR/SP/RJ sector that
  carries the highest physical hazard in the domain, so the risk of the southern
  resort municipalities is a lower bound. No seasonal proxy has been applied,
  because no defensible estimate is available on a homogeneous basis for all
  282 municipalities and any occupancy factor for second homes would be an
  unverifiable assumption. The index should be read as risk to **residents**, not
  to visitors or to tourism assets. A partial mitigating factor, not a
  correction: South Atlantic storm surge and extreme waves peak in austral autumn
  and winter, when the floating population is at its lowest.

- **Sample coverage and hazard-silent municipalities (AUD-15).** The municipal
  set is inherited from Lima et al. (2024) plus Balneário Rincão, created in 2013
  and absent from the standard SIDRA aggregates, giving **282** municipalities;
  the membership criterion is inherited rather than re-derived here. All 282
  carry an SVI, but only **280** carry a risk value, and **the two absences have
  different causes**. **Fernando de Noronha/PE** is an archipelago ~350 km
  offshore, but the grid does cover it: **19 points** lie over the archipelago,
  with ordinary oceanic wave thresholds (Hₛ ≈ 2.0 m) and HAT ≈ 1.5 m, the nearest
  1.5 km from the municipal polygon. Each carries 9–13 candidate events, **all
  rejected by the HAT gate**, so associating it would give it `Hazard_Index_mun`
  = 0 and place it among the 83 hazard-silent municipalities below: its absence
  is a **result**. **Içara/SC** is different, and an earlier reading of it was
  wrong. It lies **4.0 km from the coastline with no sea frontage at all**, and
  its three neighbours inside the set — Araranguá, Jaguaruna and Balneário Rincão
  — all sit between it and the water. The reason is dated: Balneário Rincão was
  created out of Içara by state law 12,668/2003 and installed in 2013, taking the
  shore with it. A municipality without frontage has no ocean grid point of its
  own, so the association did not fail — there was nothing to associate, and the
  absence is **correct by definition**. That also exposes a defect in the
  inherited roster: Lima et al. (2024) list 281 municipalities and do **not**
  include Balneário Rincão, which had to be added here by hand, so the roster
  appears to predate or ignore the 2013 split — carrying the now-landlocked
  parent and missing the child that kept the coast. Exactly one member of the set
  has no sea frontage, and it is that one. A frontage screening of all 282 against
  the Natural Earth 10 m coastline is versioned, but it is a **screening, not a
  classification**: that dataset reports no intersection for 25 municipalities,
  nearly all unambiguously coastal — Olinda, Itajaí, Navegantes among them — every
  one within 700 m of the drawn line, so only a case an order of magnitude outside
  that band is decidable. A definitive classification needs a coastline at survey
  resolution, which this repository does not hold. Four municipalities have a
  population within 10 km too small for the exposure metric to discriminate —
  **Santa Rita/MA (4 residents), Calçoene/AP (101), Oiapoque/AP (518),
  Terra de Areia/RS (765)**. Santa Rita/MA and Calçoene/AP have exposure zero
  because `pop_eff` is below the fixed 100-person absolute goalpost; there is no
  0.01 floor. Santa Rita/MA is nonetheless a **sea-fronting municipality**, with
  1.98 km of measured frontage: its problem is exposure measurement and hazard
  association — its point lies 77 km away — not membership, and excluding it on
  low `pop_10km` would use the very variable being measured. Removing all four
  leaves the published ranking unchanged (ρ = 1.000, maximum rank shift 0), so
  they anchor no normalisation.
  The coverage limitation that the current method newly creates is different in
  kind and larger: **83 of the 280 municipalities draw their hazard from a grid
  point that accepted no compound event at all**, so their `Hazard_Index_mun` and
  risk are exactly 0. They are
  concentrated in the North and Northeast (CE 18, AL 15, RN 14, PE 12, SE 7,
  BA 7, PB 3, MA 3, PA 3, AP 1) and they occupy ranks **191–280** — the whole
  bottom third of the ranking as tied exact zeros; they do not define a hazard
  gradient. Zero here means no accepted event in 1993–2025, not impossibility of
  physical coastal risk. In the published GeoJSON every case carries its own
  label — `coverage_status` separates the 197 municipalities with an accepted
  event, the 83 without and the 2 without an association, and `risk_zero_cause`
  separates a hazard zero from an exposure zero — and panel (d) of the article
  multiplot gives exact zeros a class of their own on the colour bar, labelled 0.
  **That boundary is itself sampling-dependent.** Resampling the 33 years of
  record (AUD-07) sends a further **94 municipalities to exactly zero in some
  draws** — 34 % of draws for Guimarães/MA, Alcântara/MA, Raposa/MA and Icatu/MA,
  which rank 21st, 22nd, 28th and 32nd — so only **102 of the 280 are robustly
  non-zero**. The zero category should be read as a property of a 33-year sample,
  not as a fixed partition of the coast.
  *(`src/exploratory/audit_AUD_15_sample_coverage.py`,
  `src/exploratory/audit_AUD_15_sea_frontage.py`)*

- **Deprivation axis, not coastal susceptibility (AUD-09).** `SVI_Coast_2022` is
  PC1 of the ten standardized indicators, explaining 50.5 % of their variance
  (PC2: 16.5 %). It correlates *r* = +0.940 with the poverty indicator and
  ρ = −0.491 with log municipal population: it measures **material deprivation**
  along Brazil's north–south development gradient, and it is not specific to
  coastal flooding. Two indicators carry negative PC1 loadings — `pop_rent`
  (−0.338) and `pop_agevul` (−0.137) — which the audit confirmed are empirical
  results rather than coding errors: all ten columns were traced to their SIDRA
  queries and tested against municipalities of undisputed standing, and all ten
  passed. Non-ownership is a trait of urban affluence in Brazil, and the
  vulnerable-age share sums two tails that move oppositely with income. Forcing
  the sign of either input before the PCA is a mathematical no-op. Redundancy is
  real: mean |r| among the ten is 0.42, and four of them measure basic
  sanitation. Two scales must be kept apart. What **enters the risk** is
  `Vulnerability_CDF_PC1 = Φ(PC1/sd(PC1))`, which spans 0.0122–0.9948 and has
  **no exact anchor**. What is **published as a map layer and in the article SVI
  table** is the original `SVI_Coast_2022`, the 0–100 Min–Max of the same PC1,
  preserved unchanged for traceability and provenance — and it still puts
  **Balneário Camboriú at exactly 0 and Chaves/PA at exactly 100**. Those two
  values are a **scale artefact of the Min–Max**, not a statement that one
  municipality has no social vulnerability and another has the maximum
  conceivable; they no longer propagate to the risk, but they are visible to a
  reader, and the article table prints 100.000 in its first row. The choice of
  scale is not critical to the ranking: substituting a percentile rank of PC1
  gives ρ = 0.991 on the published risk, an additive index with the conceptual
  direction imposed on all ten indicators gives ρ = 0.978, and the original
  Min–Max gives ρ = 0.976 — but only Φ avoids reintroducing an exact anchor.
  **No comparison against the reference SVI-Coast of Lima et al. (2024) was
  performed**: it is built on the 2010 census, is not held here, and obtaining it
  requires the supplementary material of that article. This is a declared gap in
  the external validation of the vulnerability layer, not an oversight.
  *(`src/exploratory/audit_AUD_09_svi_directionality.py`,
  `src/exploratory/audit_AUD_09_scale_alternatives.py`)*

- **The integrated index is hazard-led, and the hazard field is shaped by the
  acceptance gate (AUD-13).** Equal nominal weights of 1/3 do not imply equal
  contribution. On the 196 municipalities with positive risk — log quantities are
  undefined for the 84 that sit at exact zero — the hazard accounts for **84.7 %**
  of the variance of log risk, exposure for 35.0 % and vulnerability for
  **−19.7 %**, a negative share meaning that vulnerability *compresses* rather
  than expands the dispersion of the index. Removing the hazard from the formula
  leaves ρ = +0.092 against the published ranking: the integrated index is
  operationally the hazard index, modulated by the other two layers. This follows
  from the physics of the detector rather than from the algebra: the geometric
  mean weights by logarithmic dispersion, and the HAT gate made the hazard field
  nearly binary. Three consequences must be stated. **First**, the marginal rank
  correlation between vulnerability and risk is **negative** (−0.372), which does
  *not* mean that vulnerability reduces risk — the partial correlation,
  controlling hazard and exposure, is **+0.790**. This is suppression, and its
  cause is the strong hazard–vulnerability anticorrelation (ρ = −0.601), which
  compresses the variance of log risk by a factor of three, against 9 % for the
  exposure–vulnerability pair that earlier versions of this analysis identified.
  **Second**, that anticorrelation is a genuine and welcome finding — compound
  wave–surge hazard in Brazil concentrates in the S/SE, where social deprivation
  is lowest, because the forcing is extratropical — but **part of its magnitude is
  produced by the geography of the gate itself**: mean HAT rises from 0.49 m
  (35–28°S) to 2.61 m (2°S–7°N) for tidal reasons unrelated to storms, so the bar
  to clear grows fivefold in exactly the direction in which the meteorological
  forcing weakens. The direction of the finding is sound; its strength mixes a
  physical and a methodological gradient, and no fixed-amplitude-gate
  counterfactual has been run to separate them. **Third**, because ρ(hazard, risk)
  = 0.893, the index propagates in full any weakness of the quantities that define
  the hazard, including the local-percentile wave criterion described in the
  paragraph below. The conjunctive geometric aggregation is no longer a near-neutral choice:
  an arithmetic mean gives ρ = 0.550 and retains 4 of the top 10. It is retained
  on the IPCC rationale stated before the method changed, not on the ranking it
  produces. Individual absences such as Recife are discussed in the audit record;
  the shoreline signal there is documented as heterogeneous between adjacent
  sectors of the same urban beach (Gregório et al., 2017) and strongly
  anthropogenic in origin (Rocha, 2018), i.e. organised below the resolution of a
  ~0.2° wave grid, and the local damage threshold sits below HAT rather than above
  it. Zero means no accepted compound event in 1993–2025, never impossibility of
  physical coastal risk.
  *(`src/exploratory/audit_AUD_13_component_contributions.py`)*

- **The wave criterion measures local rarity, not absolute severity, and no
  absolute floor is derivable here (AUD-02).** The wave threshold is the local
  q70 of significant wave height, so its absolute value spans an order of
  magnitude along the coast: 0.14 m at the lowest grid point, a median of
  **0.90 m in Maranhão** and 0.905 m in Amapá against 1.71 m in Rio Grande do Sul.
  A detected event is therefore a **local Hₛ exceedance**, and the term "extreme
  wave" is not used for it anywhere in this repository. The exposure of the
  published result must be read with that in mind: **161 of the 280 municipalities
  carrying a risk value draw their hazard from a grid point whose wave threshold
  is below 1.5 m, 44 from points below 1.0 m, 8 of the top 20 — including the
  first, São José do Norte/RS at 1.20 m, where the regional median q90 is 2.48 m —
  and all 20 of the top 20 from points below 2.0 m.** No absolute floor was
  imposed, for two demonstrated reasons rather than by preference. The PU
  composite score does not determine the wave axis: its six best pairs lie within
  1 % of one another and span q50–q80, while the level percentile is selected
  identically in every sensitivity variant. And an external anchor would have to
  come from a setup/runup formulation driven by Hₛ, which requires beach-face
  slope — the physical susceptibility layer this project has already recorded as
  absent. Nor were sheltered points filtered out: coastline orientation shelters
  points that lie in no bay at all, and WAVERYS at ~0.2° is a **large-scale driver
  even at exposed points**, so "genuine shelter" and "doubtful cell" cannot be
  separated by any rule this repository can state, and any filter would be
  arbitration wearing the appearance of a criterion. Two consequences are named
  rather than hidden: **Mangaratiba/RJ**, ranked 4th nationally, draws its hazard
  from a point inside Sepetiba Bay with a 0.78 m threshold, and **Magé/RJ**,
  ranked 3rd, from the inner Guanabara Bay. Replacing the percentile criterion
  with a physically anchored one, via wave setup computed directly from Hₛ, is the
  named route past this limitation and is future work.
  *(`src/exploratory/audit_AUD_02_threshold_exposure.py`,
  `src/exploratory/audit_AUD_02_threshold_grid_floor.py`)*

- **The ranking is interpretable at the top and not below it (AUD-07).** Two
  robustness questions have to be separated. The **aggregation** is stable:
  scoring the hazard on frequency alone gives ρ = 0.940 against the published
  ranking and on severity alone 0.974, and sweeping the weight between the two
  components from 0 to 1 never drops ρ below **0.94**, so the equal 50/50 split is
  practically indifferent rather than an unjustified convention. What does move
  the result is the functional form: a compensatory arithmetic mean gives
  ρ = 0.551 and a percentile-rank version 0.638. The conjunctive geometric form is
  retained on the IPCC rationale stated before the method changed. The **rank**,
  by contrast, is only partly resolved. Resampling municipalities — the usual
  design — now measures exactly nothing, because fixed goalposts make each value
  independent of sample membership; the uncertainty that exists is in the hazard
  estimate, and a bootstrap over the 33 years of record (1000 draws, 90 %
  intervals) puts the median interval width at **4.5 rank positions inside the top
  10 and 7 for ranks 11–20**, with the first three positions degenerate, against
  **45 positions for ranks 101–196**. Eight municipalities have intervals covering
  rank 10, so ranks 4–11 are not distinguishable and "top ten" is a presentational
  cut, not a statistical class. Below roughly rank 20 the ordering should be read
  as priority bands, not as a ranking. One driver of that deserves naming: because
  the severity term is a **conditional mean that does not scale with rarity**,
  while frequency is anchored at 99 events, a single moderate event yields
  severity ≈ 0.28 against frequency 0.010, and the resulting hazard of 0.146
  combined with a high vulnerability places **Guimarães/MA at rank 21 on the
  strength of one event in 33 years**. Ninety-four of the 196 municipalities with
  positive risk rest on fewer than ten accepted events and ninety on fewer than
  five; in the bootstrap, 94 of them fall to exactly zero risk in some draws — 34 %
  of draws for Guimarães, Alcântara, Raposa and Icatu — so only **102 of the 280
  are robustly non-zero** and the zero/non-zero boundary is itself sampling-
  dependent. The bootstrap treats years as exchangeable and therefore ignores
  trend and interannual autocorrelation, which makes these intervals a floor on
  the uncertainty rather than a full estimate.
  *(`src/exploratory/audit_AUD_07_aggregation_sensitivity.py`)*

- **There are no discrete hotspots; the result is a gradient (AUD-16).** The
  stated aim of identifying "priority hotspots" presupposes that discrete
  high-risk clusters exist. They do not. Silverman's critical-bandwidth
  bootstrap rejects unimodality over all 280 municipalities (*p* = 0.002) but
  **fails to reject it over the 196 with any accepted compound event**
  (*p* = 0.56), which places the bimodality entirely in the point mass at zero
  rather than in any cluster of high values; Fisher–Jenks goodness of variance
  fit rises smoothly from 0.678 at two classes to 0.974 at eight, with no elbow
  at any class count. The single genuine break in the distribution is therefore
  the 84 municipalities at exactly zero, and that break is a statement about the
  record — no accepted compound event in 1993–2025 — not the lowest class of a
  gradient. The standard spatial route to a hotspot definition is unavailable
  here: **32.6 % of the 650 contiguity neighbour pairs share the same ocean grid
  point** and therefore carry an identical hazard by construction (178 points
  serve 280 municipalities, up to 9 municipalities per point), so a Getis-Ord
  Gi\* surface would measure the association geometry as much as the risk field,
  and the global Moran's I of 0.813 has to be read with that in mind. What is
  defensible is a definition based on the rank interval rather than the value: a
  municipality qualifies at level N when its 90 % interval stays inside the first
  N positions across resamples of the record. Seven municipalities qualify at
  N = 10 and fourteen at N = 20, and no municipality outside the published top-N
  qualifies — so the published list loses no one, it simply contains three
  members at N = 10 that do not hold up. Equal-interval map classes are retained
  and are no longer open to the objection that motivated this issue: since the
  Min–Max chain was removed the scale has fixed anchors, so class limits keep
  their meaning across regenerations, whereas Jenks would move them at every
  regeneration and has no preferred class count.
  *(`src/exploratory/audit_AUD_16_hotspot_definition.py`)*

- **Calibrated in one state, applied to twenty-seven degrees of latitude
  (AUD-18).** Every positive event used to calibrate the detection thresholds
  comes from **Santa Catarina**: 91 records from the state Civil Defense database
  (Leal et al., 2024) plus 56 curated from news archives, theses and technical
  reports, giving 147 unique municipality×date pairs across 27 municipalities.
  The selected pair is then applied unchanged from 35°S to 7°N. The **transfer
  assumption** is that a local percentile is portable even when its absolute value
  and its physical meaning are not — which is the point of using percentiles, and
  also the reason the detected quantity is a local exceedance rather than an
  absolute extreme. The assumption is not testable outside Santa Catarina with the
  data held here. A documented reconnaissance for a comparable reference in the
  North and Northeast returned a qualified negative: what exists is **not
  equivalent, but the gap is not irremediable either**. The national compilation
  *Panorama da Erosão Costeira no Brasil* (Muehe, org., MMA, 2018) covers every
  coastal state chapter by chapter, but it diagnoses **where** the shoreline is
  retreating, not **when** events occurred, so it cannot validate a dated event
  detector; it can support qualitative sanity checks only. The federal S2ID and
  its Atlas Digital do carry dates, but they are declaration-driven and are
  acknowledged in this repository as systematically under-reported, which is why
  they were excluded from downstream validation in the first place. At least one
  dated regional analysis exists for a single Northeastern city — storm-surge
  events at Fortaleza/CE (Paula, Morais, Ferreira & Dias, 2015) — but a single
  municipality cannot calibrate a coastline. The GLOSS-Brasil network operated
  through the Navy's CHM and the IBGE RMPG provide observed sea level at Northern
  and Northeastern stations, which would validate the **level** component
  directly; no tide-gauge comparison has been performed in this cycle, and it
  remains the single most tractable validation step available. The consequence to
  declare is therefore narrower than "no validation is possible": the detector is
  **empirically anchored only in the South/Southeast**, its behaviour elsewhere is
  an extrapolation whose physical meaning changes with the surge-to-tide ratio
  (which spans two orders of magnitude across the domain), and the sources that
  could partially test it have been identified but not yet used.
  *(reconnaissance recorded in `docs/scientific_audit/issues/AUD-18_independent_validation_gap.md` §3-bis)*

- **The municipal unit distorts exposure, and the denominator is where it shows
  (AUD-08).** Exposure pairs an absolute half against a relative half, following
  the INFORM recommendation that an index should reward both the number of people
  at risk and their weight within the unit. The relative half divides the
  effective coastal population by the **whole municipal population**, and that is
  a textbook modifiable-areal-unit problem: it partly measures how coastal a
  municipality happens to be, which is a property of the administrative outline
  rather than of risk. The **saturation** that earlier versions of this analysis
  reported has been removed rather than declared: under a single 10 km band the
  ratio reached its ceiling in **59 of 282** municipalities and exceeded 0.99 in
  92, so the relative half barely discriminated; under the effective population it
  reaches the ceiling **zero** times, with a median of 0.373. The effective
  population is also the only support tested that avoids both failure modes at
  once — a 1 km band leaves 14 municipalities with no counted residents at all,
  a 10 km band saturates a fifth of the sample, `pop_eff` does neither. **The
  MAUP itself remains**, and it is directional: dropping the relative half
  entirely would move **Itaboraí/RJ from 118th to 9th**, **Campos dos
  Goytacazes/RJ — which contains the Farol de São Tomé, one of the most
  documented erosion cases in the country — from 159th to 72nd**, Araruama/RJ
  from 67th to 11th and Linhares/ES from 188th to 164th. Those are large
  municipalities whose population sits inland: Campos has 483,486 residents but
  an effective coastal population of 8,825, giving a relative term of 0.018
  against an absolute term of 0.486. The relative half is nevertheless **kept**,
  because the counterfactual moves the index the other way into a different
  distortion — the city of Rio de Janeiro also gains 49 positions, and an index
  that ranks metropolises first by virtue of their size is the outcome the INFORM
  pairing exists to prevent. The reader should therefore treat the ranking of
  large, partly inland municipalities as a **lower bound**. One clarification on
  the spatial support, because it is often assumed to be the problem: the
  population is counted on the IBGE statistical grid at **200 m in urban and 1 km
  in rural areas**, which is finer than a census sector, so the count is not
  coarsely aggregated. The distortion is in the **reporting unit and the
  denominator**, not in the population data.
  *(`src/exploratory/audit_AUD_08_exposure_support.py`)*

- **Qualitative validation against reference cases: what the index recovers and
  what it does not (AUD-05).** Thirty-three municipalities with independent
  evidence were fixed as a reference list **before** the comparison was run, drawn
  only from sources predating every method change, and committed to version
  control first; hazard and integrated risk carry separate expectations, and
  cases where neither a high nor a low value would be an error — a wealthy
  municipality with real erosion, on an index whose vulnerability layer measures
  material deprivation — are reported rather than scored. **The index recovers the
  case that earlier versions of this analysis identified as disqualifying.**
  Balneário Camboriú, Itajaí and Navegantes, which the initial review placed at
  ranks 280, 275 and 273 of 280 with Balneário Camboriú at exactly 0.000, now sit
  at **rank 81 of 280 on hazard**, in the upper third; their integrated risk
  remains low, but for a stated reason rather than an artefact — they are among
  the wealthiest coastal municipalities in the country. **No municipality with
  documented disruption, severe erosion or recurrent coastal flooding remains in
  the bottom decile.** Thirteen of fourteen positive controls meet their hazard
  expectation, several strongly: São José do Norte 3rd, Laguna 4th, Bertioga 6th,
  São Sebastião 7th, Rio Grande 17th. The negative controls also behave: Macapá,
  Turiaçu, Chaves and Icatu, whose events the initial review attributed to
  astronomical tide rather than storms, now fall to hazard ranks 188, 167, 138 and
  121 — the middle of the distribution, no longer physical hotspots. **One
  divergence survives, and it is at the top of the ranking.** Magé ranks 3rd and
  Paraty 5th on integrated risk, and both sit inside sheltered bays: Magé, Duque
  de Caxias and Guapimirim share a single open-shelf grid point **35 km away**
  across Guanabara Bay, and Paraty draws from a point 15 km inside Baía da Ilha
  Grande. Swell of the magnitude recorded at those points does not reach the inner
  bays, and the flooding documented at all four is fluvial and pluvial rather than
  wave-driven. This is the point-to-municipality association limitation declared
  elsewhere in this section, surfacing where it matters most, and it is **declared
  rather than corrected**: the association is expert judgement, versioned as an
  input, and re-drawing it for one bay after seeing the ranking would be selection
  on the outcome. Readers and the top-ten table should treat those two entries as
  carrying imported hazard. A second, opposite divergence is equally worth stating:
  **Santa Vitória do Palmar ranks 1st on hazard and 131st on integrated risk**,
  with Osório at 40th and 156th and Itaboraí at 29th and 118th — physically
  exposed municipalities with low material deprivation, depressed by the same
  suppression structure described above. The index is a social-risk prioritisation,
  and these are the cases where that framing costs the most.
  *(`src/exploratory/audit_AUD_05_reference_cases.py`,
  `docs/scientific_audit/reference_cases.csv`)*

### Current Implementation Status

- **STEP 1 (Data Preparation):** Complete for south SC test domain; full-domain downloads require large storage and processing time. Implementation in `src/01_data_preparation/`.

- **STEP 2 (Threshold Calibration):** All sub-steps 2a–2e complete.
  - **2a** — Exploratory analysis complete (`src/02_threshold_calibration/01_exploratory_data_analysis/`)
  - **2b** — Preliminary compound analysis complete (`src/02_threshold_calibration/02_preliminary_compound/`)
  - **2c** — Tidal sensitivity complete (`src/02_threshold_calibration/03_tidal_sensitivity/`)
  - **2d** — CSI grid scan complete — diagnostic only (`src/02_threshold_calibration/04_csi_grid_scan/`)
  - **2e** — PU composite calibration complete — final calibrated thresholds (`src/02_threshold_calibration/05_pu_composite_calibration/`)

- **STEP 3 (Hazard Characterization):** Complete for the full Brazilian coast; interactive hazard panel available at `site/app/results/hazard-characterization/`.

- **STEP 4 (Exposure, Vulnerability & Risk Integration):** Complete at municipal scale from Karine's `outputs/risk_index/` shapefile outputs; interactive risk panel available at `site/app/results/risk-integration/`.


### Reproducibility

- All test fixtures (`data/test/`) are version-controlled and committed to the repository.
- Analysis outputs (`outputs/`, `logs/`) are regeneratable from test fixtures and are excluded from version control (`.gitignore`).
- Full-domain CMEMS downloads (`data/raw/`) are excluded from version control due to size.
- Python environment fully specified in `environment.yml`.

### Data Retention Policy

- **Committed to Git:** Configuration files, scripts, test fixtures, documentation, preprocessing outputs (CSVs).
- **Not committed:** Full CMEMS downloads (`data/raw/`), analysis outputs (`outputs/`), execution logs (`logs/`), site build artifacts (`site/.next/`, `site/node_modules/`).

---

## Citation and Acknowledgments

**Preliminary results.** This is an ongoing research project. Results presented are subject to revision and should not be cited without consulting the authors.

**Data sources:**
- CMEMS GLORYS12 and WAVERYS products: Copernicus Marine Environment Monitoring Service
- ERA5: ECMWF / Copernicus Climate Change Service
- Reported events (Santa Catarina): Leal, K. B., et al. (2024). Identification of coastal natural disasters using official databases to provide support for the coastal management: the case of Santa Catarina, Brazil.
- S2ID / Atlas Digital de Desastres: Brazilian Federal Government
- IBGE: Instituto Brasileiro de Geografia e Estatística
- Natural Earth coastline data: naturalearthdata.com
- Macrodiagnóstico da Zona Costeira e Marinha: Ministério do Meio Ambiente (MMA)

**Contact:**
Danilo Couto de Souza  
Institute of Astronomy, Geophysics and Atmospheric Sciences (IAG-USP)  
University of São Paulo, Brazil

---

**Last updated:** April 2026
