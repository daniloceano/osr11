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

The project implements an 8-step execution algorithm aligned with the conceptual risk chain:

### **STEP 1 — Data Preparation**

Compile, harmonize, and quality-check all datasets. Standardize spatial reference systems and temporal coverage. Remove inconsistent records and document data quality limitations.

**Status:** ✅ Partially complete (test domain only)  
**Implementation:** `src/acquisition/`, `src/preprocessing/`

---

### **STEP 2 — Threshold Calibration**

Select candidate extreme thresholds for sea level (N) and significant wave height (Hₛ). For each threshold combination, detect storms in Santa Catarina and compare with reported coastal disasters from the SC Civil Defense database. Compute matching statistics (hit rate, false alarm rate, critical success index). Select the threshold combination with the best performance.

**Rationale:** Threshold definition is inherently subjective. Validation against observed disasters provides an empirical, pragmatic calibration strategy that grounds the analysis in real-world impacts. Although this introduces regional bias (SC-based thresholds extrapolated to other sectors), it represents the most defensible approach given uneven disaster record availability along the Brazilian coast.

**Status:** 🔄 In progress — initial visual calibration complete (full SC domain)
**Implementation:** `src/02_threshold_calibration/`
**Current scope:** q90 thresholds applied to 91 reported events across 5 SC sectors and 22 municipalities. Results show low concurrent exceedances (2%) at q90 — systematic threshold grid scan is the next step.
**Limitation:** Many northern SC municipalities have NaN data due to reanalysis grid coverage gaps over complex coastal geometries.

---

### **STEP 3 — Storm Catalog Generation**

For each coastal grid point, construct independent storm catalogs by identifying threshold exceedances and merging consecutive exceedances into single storm events. For each identified storm, record:

- Start time
- End time  
- Duration
- Peak value
- Full time series of values during the event
- Integrated intensity (time-integrated magnitude)

Generate separate catalogs for sea-level storms and wave storms. Save catalogs in structured JSON format for reproducibility and downstream analysis.

**Status:** 🔄 Planned (Phase 2)  
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

**Status:** 🔄 Planned (Phase 3)  
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

### **STEP 8 — Optional Physical Interpretation**

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

✅ **Phase 0 — Data acquisition pipeline** (complete)
- CMEMS download scripts (`src/acquisition/`)
- Test fixture generation for south SC sector and full SC coast
- Reported events preprocessing (Excel → CSV)

✅ **Step 1 — Exploratory data analysis** (complete for south SC test domain)
- Implemented in `src/01_explore_test_data_south_sc/`
- Spatial maximum maps of Hₛ and SSH (Part A)
- Time series at peak grid points (Part B)
- Reported events EDA: counts, boxplots, seasonality (Part D)
- Municipality–grid association via IBGE API (Part E)
- Per-sector overview figures (Part F)
- Descriptive statistics, scatter plots, seasonal cycle, compound quick-look (Part G)

**Important:** The exploratory analysis is **not** the full compound event detection framework described in Steps 2–7. It is a preliminary sanity-check and data familiarization phase. The exploratory "compound quick-look" uses empirical q90 thresholds as a placeholder.

🔄 **Step 2 — Threshold calibration** (in progress — full SC coast)
- Implemented in `src/02_threshold_calibration/`
- Domain extended from south SC to full SC (5 sectors, 22 municipalities, 91 events)
- Initial visual calibration at q90 complete
- Key finding: 2/91 concurrent exceedances at q90; systematic threshold optimisation planned
- Limitation: ~50% of events have NaN data due to reanalysis grid gaps over complex coasts

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
│   │   └── metocean_sc_full_unified_waverys_grid.nc # Unified daily · full SC (Step 2 input)
│   ├── reported events/
│   │   ├── README.md                         # Reported events database documentation
│   │   └── reported_events_Karine_sc.csv     # SC Civil Defense disaster database (Leal et al. 2024)
│   ├── ne_10m_coastline/                     # Natural Earth 10m coastline shapefile
│   └── raw/                                  # Full CMEMS downloads (not committed, .gitignore)
├── src/
│   ├── __init__.py                           # Import alias registry for numbered analysis dirs
│   ├── acquisition/
│   │   ├── download_cmems.py                 # Main CMEMS download script
│   │   ├── download_cmems_parallel.py        # Parallel download variant
│   │   ├── catalog_inspect.py                # CMEMS catalog inspection utility
│   │   └── build_test_fixture.py             # Build test-domain NetCDF subsets
│   ├── preprocessing/
│   │   ├── README.md                         # Preprocessing pipeline documentation
│   │   ├── convert_reported_events.py        # Excel → CSV conversion for reported events
│   │   └── interpolate_glorys_to_waverys_grid.py  # Spatial regridding pipeline
│   ├── 01_explore_test_data_south_sc/        # Step 1: Exploratory EDA (south SC test domain)
│   │   ├── main.py                           # CLI orchestrator (--all, --maps, --timeseries, etc.)
│   │   ├── io.py                             # Dataset loaders and South sector filtering
│   │   ├── coastal.py                        # Coastal grid point selection (Natural Earth)
│   │   ├── maps.py                           # Part A: Spatial maxima maps
│   │   ├── timeseries.py                     # Part B: Time series at peak grid points
│   │   ├── reported_events.py                # Part D: Reported events EDA
│   │   ├── municipalities.py                 # Part E: Municipality–grid association (IBGE API)
│   │   ├── boxplots.py                       # Part F: Sector boxplot figures
│   │   ├── statistics.py                     # Part G: Statistical analyses and distributions
│   │   ├── utils.py                          # Shared utilities (logging, I/O helpers)
│   │   ├── config/analysis_config.py         # Configuration: file paths, parameters, output dirs
│   │   ├── README.md                         # Detailed module documentation
│   │   └── RUN.md                            # Quick-start command reference
│   └── 02_threshold_calibration/             # Step 2: Threshold calibration (full SC coast)
│       ├── main.py                           # CLI orchestrator (--all, --event-figures, --summary)
│       ├── io.py                             # Data loaders (all SC sectors, target_sector=None)
│       ├── events.py                         # Event records (municipality→grid, all SC coords)
│       ├── thresholds.py                     # q90 computation + per-event metrics
│       ├── event_figures.py                  # Per-event visualisations (MagicA POT shading)
│       ├── summary.py                        # Consolidated table + S1–S4 summary figures
│       ├── utils.py                          # save_fig, make_output_dirs, muni_slug
│       ├── config/analysis_config.py         # Configuration: paths, parameters, target_sector
│       ├── README.md                         # Module documentation
│       └── RUN.md                            # Quick-start command reference
├── outputs/                                  # Analysis outputs (not committed, .gitignore)
│   └── south_sc_test_data_exploratory/
│       ├── figures/                          # PNG figures (300 dpi, publication-ready)
│       └── tables/                           # CSV summary tables
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

### 2. Run Exploratory Analysis (Step 1 — South SC test domain)

The test fixtures (`data/test/`) are already committed. No download required.

```bash
# Full exploratory analysis (all parts)
python -m src.explore_test_data_south_sc.main --all

# Individual parts
python -m src.explore_test_data_south_sc.main --maps           # Part A: Spatial maxima
python -m src.explore_test_data_south_sc.main --timeseries     # Part B: Time series
python -m src.explore_test_data_south_sc.main --events         # Part D: Reported events EDA
python -m src.explore_test_data_south_sc.main --municipalities # Part E: Municipality–grid
python -m src.explore_test_data_south_sc.main --boxplots       # Part F: Sector overview
python -m src.explore_test_data_south_sc.main --statistics     # Part G: Statistical analyses
```

Outputs written to: `outputs/south_sc_test_data_exploratory/`

See `src/01_explore_test_data_south_sc/RUN.md` for complete command reference.

### 3. Run Threshold Calibration (Step 2 — Full SC coast)

The full SC unified dataset (`data/test/metocean_sc_full_unified_waverys_grid.nc`) is committed.

```bash
# Full analysis (per-event figures + summary)
python src/02_threshold_calibration/main.py --all

# Individual parts
python src/02_threshold_calibration/main.py --event-figures   # TC-1: per-event figures
python src/02_threshold_calibration/main.py --summary         # Summary: S1–S4 + tables
```

Outputs written to: `outputs/threshold_calibration/`

See `src/02_threshold_calibration/RUN.md` for complete command reference.

### 4. Download Full-Domain Data (Optional)

**Note:** Full GLORYS12 and WAVERYS downloads are large (~100 GB+ for full Brazilian coast, 1993–2025). Test fixtures are sufficient for exploratory work.

```bash
# Inspect CMEMS catalog (recommended before downloading)
python src/acquisition/catalog_inspect.py GLOBAL_MULTIYEAR_PHY_001_030
python src/acquisition/catalog_inspect.py GLOBAL_MULTIYEAR_WAV_001_032

# Configure download parameters
cp config/download_config.example.yml config/download_config.yml
# Edit config/download_config.yml with desired spatial/temporal extent

# Download GLORYS12 and/or WAVERYS
python src/acquisition/download_cmems.py --product glorys
python src/acquisition/download_cmems.py --product waverys
# Or both: python src/acquisition/download_cmems.py
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

- **Phase 0 (Data preparation):** Complete for south SC test domain; full-domain downloads require large storage and processing time.

- **Step 1 (Exploratory analysis):** Implemented for south SC test domain (`src/01_explore_test_data_south_sc/`). This is **not** the final compound event detection framework—it is a preliminary EDA phase using empirical thresholds (q90) for data familiarization and pipeline validation.

- **Step 2 (Threshold calibration):** Initial visual calibration complete for the full SC coast (`src/02_threshold_calibration/`). The analysis covers all 5 Leal et al. (2024) sectors (91 events, 22 municipalities) but has data gaps for many northern municipalities due to reanalysis grid coverage limitations. Systematic threshold optimisation (hit rate, CSI grid scan) is the immediate next step.

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

**Last updated:** March 2026
