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

- **Compound hazard:** The simultaneous occurrence of sea-level extremes (associated with storm surge and meteorological tides) and extreme wave events, capable of amplifying coastal impacts beyond what isolated extremes would produce.

- **Exposure:** The people present where the hazard acts — here, the resident population within 10 km of the coastline, from the IBGE Grade Estatística 2022. It is a proximity criterion, not a modelled inundation extent, so it counts residents *near* the coast and never residents *affected*. (Until 2026-07-28 this repository used the word "exposure" for the spatial association between ocean grid points and municipalities, which is a cartographic step and not an exposure component; that usage was wrong and has been removed.)

- **Vulnerability:** The physical susceptibility (geomorphology, land use, natural barriers) and social susceptibility (population, infrastructure, income) of coastal municipalities and sectors.

- **Risk:** The integration of hazard, exposure, and vulnerability to identify priority hotspots and inform adaptation interventions.

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
| MMA | Macrodiagnóstico da Zona<br>Costeira e Marinha | Geomorphology, erosion,<br>occupation, barriers | — | Coastal segments | Vulnerability layers |

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

FES2022 astronomical tide (eo-tides, hourly evaluation) added to GLORYS12 SSH to form SSH_total = zos(00:00 UTC) + tide(daily max). Detection at q90: 22 → 26 events (+7 new, −3 lost, 19 maintained). Establishes the canonical SSH_total definition.

**Status:** ✅ Complete  
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

**Theoretical basis:** Positive-unlabeled learning framework (Bekker and Davis, 2020); impact observation bias (Wyatt et al., 2023; Delforge et al., 2025).

**Status:** ✅ Complete  
**Implementation:** `src/02_threshold_calibration/05_pu_composite_calibration/`

---

### **STEP 3 — Hazard Characterization of Extreme and Compound Coastal Events**

The most comprehensive analysis step. Applies the PU-optimal thresholds from Step 2e to the full 1993–2025 record and runs the complete suite of hazard characterization analyses.

> **Mixed state since 2026-07-30.** Sub-step **3.2 is current**: it is regenerated
> at the recalibrated pair **q70/q99** with the HAT gate and datum, and it is the
> sole source of the published Hazard Index. Sub-steps **3.1 and 3.3–3.8 are
> NOT**: they read the Hₛ/`SSH_total` catalogs built at q90/q90, and re-running
> them unchanged would mix a superseded level variable into the published
> statistics. Rows below marked *(superseded inputs)* are in that state. See
> AUD-01 §14, remaining uncertainty (6).

| Submodule | Analysis | Key outputs |
|-----------|----------|-------------|
| **3.1 Storm Catalogs** *(superseded inputs)* | POT detection + episode clustering at q90/q90 on Hₛ and `SSH_total` | Per-grid-point JSON catalogs for Hₛ and `SSH_total` |
| **3.2 Compound Detection** | Temporal overlap of Hₛ and tide-free `zos` episodes, gated by `max(SWL) > HAT` | Compound events, integrated severity over the HAT datum (rescaled domain-wide), retained duration and peak-intensity diagnostics |
| **3.3 Duration & Persistence** *(superseded inputs)* | Per-grid-point persistence statistics | Mean/p95/max duration, inter-event times, integrated intensity |
| **3.4 Monthly Seasonality** *(superseded inputs)* | Monthly/seasonal climatology | Peak month, seasonal counts (DJF/MAM/JJA/SON) |
| **3.5 Trend Analysis** *(superseded inputs)* | Mann–Kendall + Sen slope (8 annual series) | Slope, p-value, direction, modified MK for autocorrelation |
| **3.6 Univariate EVA** *(superseded inputs)* | POT–GPD on storm peaks | Return levels (2, 5, 10, 20, 50 yr) with CI |
| **3.7 Dependence Analysis** *(superseded inputs)* | Hs–SSH_total statistical dependence | Kendall's τ, Spearman's ρ, χ, χ̄ |
| **3.8 Site Export** *(superseded inputs)* | Unified JSON for results website | All metrics merged per grid point |

**Status:** ⚠ Partial — 3.2 regenerated at q70/q99 with the HAT gate on 2026-07-30; 3.1 and 3.3–3.8 still carry the superseded q90/q90 `SSH_total` inputs  
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

Resident population and occupied households within 1, 2, 5 and 10 km of the
Natural Earth coastline, aggregated from the IBGE Grade Estatística 2022 by
cell centroid in EPSG:5880. The 10 km band feeds the risk index; the others
exist so the criterion can be varied. Across the 282 coastal municipalities,
**30.8 million** of the 37.4 million residents are within 10 km of the coast.

**Implementation:** `src/04_risk_integration/municipal_exposure.py` (aggregation),
`src/04_risk_integration/exposure_index.py` (normalisation),
`src/01_data_preparation/acquisition/download_ibge_grade.py` (acquisition).

#### Sub-step 4.3 — Social Vulnerability Index (SVI_Coast_2022)

The SVI was built from 10 socioeconomic and infrastructure variables from the 2022 IBGE Census (SIDRA) for 282 coastal municipalities:

| Variable | Description |
|----------|-------------|
| `pop_house` | Mean residents per household |
| `pop_rent` | Proportion in non-owned housing |
| `pop_poverty` | Proportion in poverty |
| `pop_agevul` | Proportion in vulnerable age groups (< 9 yr and 60+) |
| `pop_nonwhite` | Proportion non-white |
| `pop_illiterate` | Proportion illiterate |
| `pop_nowater` | Proportion without adequate water supply |
| `pop_nosewage` | Proportion without adequate sewage |
| `pop_nogarbage` | Proportion without adequate waste collection |
| `pop_nopaving` | Proportion on unpaved streets |

Variables were standardized with `StandardScaler` and submitted to PCA. PC1 was used as the main vulnerability axis; its sign was adjusted so that higher values represent higher social vulnerability. The final `SVI_Coast_2022` was normalized to 0–100 (Min–Max). Methodology based on Lima et al. (2024, *Nat. Hazards*, https://doi.org/10.1007/s11069-023-06246-w).

#### Sub-step 4.4 — Hazard Index and integrated risk

```
Hazard_Frequency = norm_native(compound_count_total)
Hazard_Severity  = norm_native(mean_integrated_severity)
Hazard_Index_raw = (Hazard_Frequency + Hazard_Severity) / 2
Hazard_Index     = norm_native(Hazard_Index_raw)
Hazard_Index_mun = norm_municipal(Hazard_Index)

Exposure_absolute = clip[(log10(pop_10km) - 2) / (6 - 2), 0, 1]
Exposure_relative = pop_10km / pop_municipality
Exposure_Index    = sqrt(clip(Exposure_absolute) * clip(Exposure_relative))

Risk_Hazard_raw = (clip(Hazard_Index_mun) * clip(Exposure_Index)
                   * clip(SVI_Coast_2022/100)) ^ (1/3)
Risk_Hazard     = norm_municipal(Risk_Hazard_raw)
```

Where:
- `clip()` floors a component at **0.01** before any product, so that a
  municipality sitting at the bottom of a Min–Max scale is not handed zero risk
  as a scaling artefact — Balneário Camboriú is exactly at `SVI = 0`
- `Hazard_Index_mun` — the hazard renormalized over the municipalities. The
  native-grid `Hazard_Index` reaches only 0.829 across municipalities, which
  would silently down-weight it in the product
- `Exposure_Index` — resident population within 10 km of the coastline, from the
  IBGE Grade Estatística 2022 (200 m urban / 1 km rural cells). Goalposts of
  10² and 10⁶ inhabitants are **fixed**, not taken from the data, so the scale
  does not move when the set of municipalities changes
- `Risk_Hazard` — the **geometric** mean of the three components. Conjunctive by
  construction: a component near zero pulls the index down, which is the
  property the IPCC risk framework implies. An arithmetic mean would let a large
  population compensate for the absence of a physical driver

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
- `Hazard_Index` — native-grid Min–Max normalization of `Hazard_Index_raw`, transferred to municipalities
- `Hazard_Index_mun` — `Hazard_Index` renormalized over the municipalities, so its amplitude matches SVI/100 in the equal-weight product
- `Exposure_Index`, `Exposure_absolute`, `Exposure_relative`
- `Risk_Hazard_raw` — geometric mean of `Hazard_Index_mun`, `Exposure_Index` and `SVI_Coast_2022/100` (each floored at 0.01)
- `Risk_Hazard` — `Risk_Hazard_raw` Min–Max normalized to [0, 1] — current integrated coastal risk

> **Notes.** (1) The hazard is implemented in `src/04_risk_integration/hazard_index.py` and reads the versioned `outputs/storm_catalog/compound/compound_metrics.csv`; the exposure in `src/04_risk_integration/exposure_index.py` and `municipal_exposure.py`; the external municipal file supplies only SVI, geometry and the pre-associated grid coordinates. (2) The export produces a single product; the delivered hazard/risk DBF columns are ignored. (3) The SVI script was obtained from its author and audited — the index reproduces exactly — but the point-to-municipality association remains external and unaudited; see `src/04_risk_integration/external_svi/README.md`. (4) Frequency is negatively correlated with mean duration and intensity, so the equal-weight average represents an explicit compensatory index rather than three mutually reinforcing signals. See `SCIENTIFIC_NOTES.md` → "Step 4 — Exposure, Vulnerability & Risk Integration".

**Status:** ✅ Complete  
**Website panels:** `/results/hazard-characterization` leads with the coastal Hazard Index map (four layers drawn on the Natural Earth coastline) and keeps the 87-metric explorer below it, transposed to the same coastline with the same graphic style. `/results/risk-integration` displays the current municipal product with every quantity available **before and after** its Min–Max normalization (`Hazard_Index_raw`, `Risk_Hazard_raw`). `/methodology/hazard-index` is the step-by-step reference for the index construction, and `/methodology/compound-detection` tells the same story as a continuous narrative from the storm catalogs to the composite index.

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
context). The map exposes four layers: `compound_count_annual_mean`
(events yr⁻¹), `mean_overlap_duration` (days), `mean_compound_intensity_norm`
(dimensionless), and `Hazard_Index` (0–1). The first three show the catalog
values themselves — the Min–Max scaling of the components is a methodological
step internal to the index and is not applied for display.

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
- **Steps 3.1 and 3.3–3.8 have NOT been regenerated** under the current method: they read the Hₛ/`SSH_total` catalogs built at q90/q90, and re-running them unchanged would mix a superseded level variable into the published statistics. See AUD-01 §14, remaining uncertainty (6)

✅ **STEP 4 — Exposure, Vulnerability & Risk Integration** (complete at municipal scale)
- SVI_Coast_2022 constructed from 10 IBGE Census 2022 variables via PCA (282 coastal municipalities)
- Exposure from resident population within 10 km of the coastline (IBGE Grade Estatística 2022), not a spatial join of oceanic hazard metrics
- Current Hazard_Index = norm_native{[norm_native(frequency) + norm_native(duration) + norm_native(intensity)]/3}; Risk_Hazard = norm_municipal[(clip(Hazard_Index_mun) × clip(Exposure_Index) × clip(SVI/100)) ^ (1/3)] — see Sub-step 4.4 for the full three-component formula


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
