# OSR11 — Compound Flooding Events in the South Atlantic Eastern Coast

**The Joint Effect of Meteorological Tides and Extreme Wave Events**

**Authors:** Danilo Couto de Souza, Carolina Barnez Gramcianinov, Ricardo de Camargo, Karine Bastos Leal  
**Institution:** Institute of Astronomy, Geophysics and Atmospheric Sciences (IAG-USP)  
**Status:** Methodology development and exploratory analysis phase  
**Current implementation:** Full Santa Catarina coast (threshold calibration phase)

---

## Abstract

Coastal communities and infrastructure along Brazil's South Atlantic Eastern Coast are increasingly exposed to compound coastal flooding, where meteorological tides (storm surges) coincide with extreme wave events. These compound hazards can amplify inundation, overtopping, erosion, and port disruption, producing severe socioeconomic impacts that are still poorly quantified at regional scale in Brazil. 

This project assesses the joint behavior of sea-level surges and significant wave height using CMEMS multiyear reanalyses (GLORYS12 for sea level and WAVERYS for waves), complemented by ERA5 atmospheric forcing to characterize synoptic drivers and seasonality. We identify compound events through a storm-based threshold approach validated against official disaster records, evaluate spatial patterns and temporal trends, and integrate hazard exposure with coastal vulnerability layers to produce risk maps and identify priority hotspots for adaptation planning.

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

- **Exposure:** The spatial frequency, intensity, and duration of compound events at coastal locations, quantifying where and when hazards occur.

- **Vulnerability:** The physical susceptibility (geomorphology, land use, natural barriers) and social susceptibility (population, infrastructure, income) of coastal municipalities and sectors.

- **Risk:** The integration of hazard, exposure, and vulnerability to identify priority hotspots and inform adaptation interventions.

---

## Research Objectives

**General Objective:**

Quantify the joint occurrence, intensity, and temporal structure of sea-level extremes and significant wave height extremes along the eastern coast of Brazil using multiyear CMEMS reanalyses (GLORYS12 and WAVERYS), validate the compound event framework against observed coastal disaster events, and integrate hazard characterization with exposure and vulnerability data to produce coastal risk maps.

**Specific Objectives:**

1. Compile, harmonize, and quality-check CMEMS oceanographic reanalyses, ERA5 atmospheric forcing, and Brazilian coastal disaster databases (S2ID, Atlas Digital, SC Civil Defense).

2. Calibrate extreme event thresholds for sea level and significant wave height by comparing detected storms with historically reported disasters in Santa Catarina, establishing a validated detection framework.

3. Construct independent storm catalogs for sea-level extremes and wave extremes, recording event characteristics (start, end, duration, peak intensity, integrated intensity) in structured JSON format.

4. Identify compound wave–surge events based on temporal overlap of independent storms, quantifying co-occurrence statistics, peak time lags, and overlap durations.

5. Produce spatial exposure maps of compound event frequency, intensity, and temporal trends along the Brazilian coast.

6. Integrate exposure layers with coastal vulnerability data (social indicators from IBGE, physical-territorial variables from Macrodiagnóstico da Zona Costeira e Marinha, and historical damage records) to construct a Vulnerability Index.

7. Generate coastal risk maps by combining hazard, exposure, and vulnerability components, identifying priority hotspots for targeted adaptation measures.

8. Characterize the synoptic and mesoscale atmospheric conditions (ERA5) associated with the most severe compound events, linking statistical hazard products to physical drivers.

---

## Data Sources

| Source | Product | Variables | Period | Resolution | Purpose |
|--------|---------|-----------|--------|------------|---------|
| CMEMS | WAVERYS<br>`GLOBAL_MULTIYEAR_WAV_001_032` | VHM0 (Hₛ), VMDR | 1993–2025 | ~0.2°, 3-hourly | Wave extremes |
| CMEMS | GLORYS12<br>`GLOBAL_MULTIYEAR_PHY_001_030` | zos (SSH) | 1993–2025 | 1/12°, daily | Sea-level extremes |
| ECMWF | ERA5 | MSLP, 10 m wind, SST | 1993–2025 | ~0.25°, hourly | Synoptic drivers |
| SC Civil Defense | Reported coastal disasters<br>(Leal et al. 2024) | Event date, municipality, impacts | 1998–2023 | Event-level | Threshold validation |
| S2ID / Atlas Digital | Brazilian disaster registry | Declared disasters, affected population, damages | 1991–present | Municipal | Impact quantification |
| IBGE | Localidades / Malhas APIs | Coordinates, boundaries, census | Current | Municipal | Exposure indicators |
| MMA | Macrodiagnóstico da Zona<br>Costeira e Marinha | Geomorphology, erosion,<br>occupation, barriers | — | Coastal segments | Vulnerability layers |

**Data acknowledgments:**  
CMEMS products are accessed via the `copernicusmarine` Python toolbox. Disaster records from S2ID and Atlas Digital acknowledge incomplete reporting and serve as minimum-estimate indicators. The Macrodiagnóstico da Zona Costeira e Marinha is a key source for physical-territorial vulnerability components.

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

First-pass inspection of joint Hₛ and SSH exceedances at q90 during each of the 91 reported coastal disasters in the Leal et al. (2024) SC database (full coast, 5 sectors, 22 municipalities). Per-event ±3-day windows; MagicA peaks-over-threshold; concomitance metrics. 22 of 91 events show concurrent SSH-only exceedances at q90. Establishes the baseline from which sub-step 2d calibrates thresholds systematically.

**Status:** ✅ Complete  
**Implementation:** `src/02_threshold_calibration/02_preliminary_compound/`

#### Sub-step 2c — Tidal Sensitivity Analysis

FES2022 astronomical tide (eo-tides, hourly evaluation) added to GLORYS12 SSH to form SSH_total = zos(00:00 UTC) + tide(daily max). Detection at q90: 22 → 26 events (+7 new, −3 lost, 19 maintained). Establishes the canonical SSH_total definition.

**Status:** ✅ Complete  
**Implementation:** `src/02_threshold_calibration/03_tidal_sensitivity/`

#### Sub-step 2d — CSI Grid Scan

81 threshold pairs (q50–q90 × q50–q90) evaluated with causal window [D-2, D-1, D, D+1 00Z]. Optimal pair: Hₛ=q90, SSH_total=q90 (H=21, M=70, F=1 298, CSI=0.0151, FAR=0.984). High FAR likely reflects Civil Defense under-reporting.

**Status:** ✅ Complete  
**Implementation:** `src/02_threshold_calibration/04_csi_grid_scan/`

#### Sub-step 2e — False Alarm Attribution (planned)

Cross-reference the 1 298 flagged episodes with S2ID, Atlas Digital, and media archives to reclassify genuine under-reported events and revise effective CSI before advancing to Step 3.

**Status:** 🔄 Planned

---

### **STEP 3 — Storm Catalog Generation**

For each coastal grid point, construct independent storm catalogs by identifying threshold exceedances (using calibrated q90/q90 from Step 2d) and merging consecutive exceedances into single storm events. For each identified storm, record:

- Start time
- End time  
- Duration
- Peak value
- Full time series of values during the event
- Integrated intensity (time-integrated magnitude)

Generate separate catalogs for sea-level storms and wave storms. Save catalogs in structured JSON format for reproducibility and downstream analysis.

**Status:** 🔄 Planned  
**Implementation:** To be developed

---

### **STEP 4 — Compound Event Detection**

Compare sea-level storm catalogs and wave storm catalogs at each grid point. Classify a **compound event** when a sea-level storm and a wave storm overlap in time. Record:

- Overlap duration
- Peak time lag (time difference between Hₛ peak and SSH peak)
- Joint peak intensity

Optionally impose a minimum overlap duration threshold. From the resulting compound event catalog, compute:

- Annual frequency of compound events
- Mean and upper-percentile joint intensity
- Mean, minimum, and maximum overlap duration
- Time between successive compound events
- Seasonality (monthly climatology)
- Spatial distribution

**Status:** 🔄 Planned  
**Implementation:** To be developed

---

### **STEP 5 — Exposure Analysis**

Quantify compound hazard exposure using indicators derived from the compound event catalog:

- Mean annual frequency
- Temporal trend (linear or non-parametric)
- Mean compound peak intensity
- Mean overlap duration
- Upper percentile (p90, p95) of overlap duration
- Recurrence interval and intermittency characteristics

Normalize indicators to a common scale and optionally combine into a **Compound Exposure Hazard Index** for mapping purposes.

**Status:** 🔄 Planned (Phase 5)  
**Implementation:** To be developed

---

### **STEP 6 — Vulnerability Analysis**

Construct a coastal vulnerability index by integrating:

**Social vulnerability:**
- Population density
- Income and poverty indicators
- Infrastructure quality (housing, sanitation, access)
- IBGE census data and socioeconomic indices

**Physical-territorial vulnerability:**
- Low-lying terrain and inundation susceptibility
- Erosional sectors and shoreline retreat rates
- Natural barriers (dunes, mangroves, reefs)
- Coastal occupation and urbanization intensity
- Macrodiagnóstico da Zona Costeira e Marinha indicators

**Historical damage sensitivity:**
- S2ID and Atlas Digital reported impacts (material damages, affected population, economic losses) used as auxiliary layer where available, acknowledging incomplete reporting

Standardize variables, apply weighting schemes, and combine into a spatially explicit **Vulnerability Index** at municipal or coastal segment scale.

**Status:** 🔄 Planned (Phase 6)  
**Implementation:** To be developed

---

### **STEP 7 — Risk Integration**

Produce the main applied outcome: a **coastal risk map of compound wave–surge events** for Brazil.

**Procedure:**
1. Rescale exposure and vulnerability indices to the same range [0, 1]
2. Combine via weighted mean, multiplicative approach, or class-based matrix
3. Generate final risk classes (e.g., Low / Moderate / High / Very High)
4. Identify priority hotspots
5. Cross-reference hotspots with municipalities presenting reported impacts in S2ID/Atlas Digital
6. Produce maps, tables, and summary statistics for stakeholder communication

**Status:** 🔄 Planned (Phase 6)  
**Implementation:** To be developed

---

### **STEP 8 — Physical Interpretation (Optional)**

As an optional validation and interpretation stage:

- Select the most severe compound events from the catalog
- Analyze seasonality (monthly/seasonal distribution)
- Characterize synoptic conditions using ERA5 (MSLP, winds, atmospheric circulation patterns)
- Discuss dominant atmospheric mechanisms (extratropical cyclones, frontal systems, blocking patterns)
- Assess uncertainties in threshold choices, grid resolution effects, and reanalysis biases

This stage strengthens the physical interpretation and overall robustness of the study.

**Status:** 🔄 Planned (Phase 8)  
**Implementation:** To be developed

---

## Current Implementation Status

The repository currently contains:

✅ **STEP 1 — Data Preparation** (complete for test domain)
- Implemented in `src/01_data_preparation/`
- CMEMS download scripts (`acquisition/`)
- Test fixture generation for south SC sector and full SC coast
- Reported events preprocessing (Excel → CSV)
- Spatial regridding: GLORYS → WAVERYS grid (`preprocessing/`)

✅ **STEP 2 — Threshold Calibration** (sub-steps 2a–2d complete; 2e planned)

- **Sub-step 2a** — Exploratory Data Analysis (`src/02_threshold_calibration/01_exploratory_data_analysis/`):
  Spatial maximum maps, time series, reported events EDA, municipality–grid association, per-sector boxplots, statistical analyses

- **Sub-step 2b** — Preliminary Compound Analysis (`src/02_threshold_calibration/02_preliminary_compound/`):
  Domain: full SC (5 sectors, 22 municipalities, 91 events); key finding: 22/91 concurrent SSH-only exceedances at q90

- **Sub-step 2c** — Tidal Sensitivity (`src/02_threshold_calibration/03_tidal_sensitivity/`):
  SSH_total = SSH + FES2022 daily max tide; detection at q90: 22 → 26 events

- **Sub-step 2d** — CSI Grid Scan (`src/02_threshold_calibration/04_csi_grid_scan/`):
  81 threshold pairs evaluated; optimal pair q90/q90 (H=21, M=70, F=1 298, CSI=0.0151)

- **Sub-step 2e** — False Alarm Attribution: 🔄 planned (cross-reference flagged episodes with S2ID/Atlas Digital)

🔄 **Steps 3–8** — Planned, not yet implemented

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
│       └── 04_csi_grid_scan/                 #   Sub-step 2d — CSI grid scan
│           ├── main.py                       #     CLI orchestrator
│           ├── calibration.py, metrics.py    #     Analysis modules
│           ├── config/analysis_config.py     #     Configuration
│           └── README.md, RUN.md, SCIENTIFIC_NOTES.md
│
├── outputs/                                  # Analysis outputs (not committed, .gitignore)
│   ├── south_sc_test_data_exploratory/       #   Step 2a outputs
│   ├── preliminary_compound/                 #   Step 2b outputs
│   ├── tidal_sensitivity/                    #   Step 2c outputs
│   └── threshold_calibration/                #   Step 2d outputs
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

### 4. Run CSI Grid Scan (Step 2d)

```bash
# Full threshold calibration analysis
python -m src.csi_grid_scan.main --all
```

Outputs written to: `outputs/threshold_calibration/`

See `src/02_threshold_calibration/04_csi_grid_scan/RUN.md` for complete command reference.

### 5. Download Full-Domain Data (Optional)

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

See `site/DEPLOYMENT.md` for full deployment instructions and `site/README.md` for site documentation.

---

## Notes and Limitations

### Data Limitations

- **GLORYS12 and WAVERYS resolution:** Reanalysis products have finite spatial resolution (~0.2° for WAVERYS, 1/12° for GLORYS12). Nearshore processes at scales < 10 km may not be fully resolved.

- **Disaster records:** S2ID and Atlas Digital databases have incomplete and uneven reporting. Not all coastal flooding events are officially declared or documented. Reported impacts (damages, affected population) are minimum estimates and subject to underreporting bias.

- **SC Civil Defense database:** The Leal et al. (2024) database provides high-quality event-level data for Santa Catarina (1998–2023) but is geographically limited. Threshold calibration based on SC events introduces regional bias when extrapolated to other coastal sectors—an acknowledged methodological limitation justified by data availability constraints.

### Current Implementation Status

- **STEP 1 (Data Preparation):** Complete for south SC test domain; full-domain downloads require large storage and processing time. Implementation in `src/01_data_preparation/`.

- **STEP 2 (Threshold Calibration):** Sub-steps 2a–2d complete; sub-step 2e (False Alarm Attribution) planned.
  - **2a** — Exploratory analysis complete (`src/02_threshold_calibration/01_exploratory_data_analysis/`)
  - **2b** — Preliminary compound analysis complete (`src/02_threshold_calibration/02_preliminary_compound/`)
  - **2c** — Tidal sensitivity complete (`src/02_threshold_calibration/03_tidal_sensitivity/`)
  - **2d** — CSI grid scan complete (`src/02_threshold_calibration/04_csi_grid_scan/`)

- **Steps 3–8 (Storm catalogs, compound detection, risk mapping):** Methodology defined but not yet implemented. Future work will follow the 8-step algorithm described above.

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
