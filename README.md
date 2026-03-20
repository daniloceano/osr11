# OSR11 — Compound Coastal Flooding on Brazil's Eastern Coast

**Joint wave–surge extreme events along the South Atlantic eastern coast of Brazil**

**Authors:** Danilo Couto de Souza, Carolina Barnez Gramcianinov, Ricardo de Camargo, Karine Bastos Leal
**Institution:** Institute of Astronomy, Geophysics and Atmospheric Sciences (IAG-USP)
**Status:** Research in progress · Current focus: southern Santa Catarina (test domain)

---

## Scientific Problem

Compound coastal flooding events — characterised by the simultaneous or near-simultaneous
occurrence of extreme significant wave heights (Hₛ) and elevated sea surface levels
associated with meteorological tides and storm surges — represent a disproportionate share
of observed coastal disasters along the Brazilian coast. Despite the documented socioeconomic
impact of these events, their joint statistical behaviour, physical drivers, and geographic
distribution remain poorly quantified at regional scales.

Isolated wave or surge extremes already impose severe hazards. When they co-occur, their
compound nature amplifies coastal flooding, erosion, and infrastructure damage in ways that
cannot be captured by single-variable analyses. A compound-event framework is therefore
essential for credible coastal risk assessment, hazard mapping, and climate-informed
adaptation planning along the Brazilian coast.

---

## Research Objectives

**General objective:** Quantify the joint occurrence, intensity, and temporal structure of
sea-level extremes and significant wave height extremes along the eastern coast of Brazil,
using multiyear CMEMS reanalyses (GLORYS12 and WAVERYS), and assess their association with
observed coastal disaster events.

**Specific objectives:**

1. Characterise the marginal distributions of Hₛ and SSH at nearshore grid points along the Brazilian coast.
2. Detect compound wave–surge events: joint exceedances within a temporal coincidence window.
3. Validate the compound event catalog against the Leal et al. (2024) Santa Catarina database and the S2ID national disaster registry.
4. Produce municipality-scale hotspot maps of compound event frequency and intensity.
5. Integrate exposure (IBGE) and vulnerability indicators to derive compound coastal risk products.
6. Interpret the synoptic and mesoscale atmospheric drivers (ERA5) of high-intensity compound events.

---

## Data Sources

| Source | Product | Variables | Period | Resolution |
|--------|---------|-----------|--------|------------|
| CMEMS | WAVERYS (`GLOBAL_MULTIYEAR_WAV_001_032`) | VHM0 (Hₛ), VMDR (direction) | 1993–2025 | ~0.2°, 3-hourly |
| CMEMS | GLORYS12 (`GLOBAL_MULTIYEAR_PHY_001_030`) | zos (sea surface height) | 1993–2025 | 1/12°, daily |
| ECMWF | ERA5 | MSLP, 10 m wind, SST, upper levels | 1993–2025 | ~0.25°, hourly |
| Leal et al. (2024) | SC coastal disaster database | Event date, municipality, Hₛ, damage | 1998–2023 | Event-level |
| S2ID / Atlas Digital | Brazilian disaster registry | Declared disasters, impact data | 1991–present | Municipal |
| IBGE | Localidades / Malhas APIs | Municipality coordinates, boundaries | Current | Municipal |

All CMEMS products are accessed via the `copernicusmarine` Python toolbox.

---

## Methodological Framework

The project follows a sequential pipeline from data acquisition to risk integration:

```
Phase 0  ·  Data acquisition, organisation, and QC
             └─ CMEMS downloads, test fixtures, preprocessing
             └─ STATUS: complete

Phase 1  ·  Exploratory data analysis (south SC test domain)
             └─ Spatial maps, time series, events EDA, statistics
             └─ STATUS: in progress  ← current stage

Phase 2  ·  Threshold calibration and storm event cataloging
             └─ POT/GPD thresholds, event segmentation

Phase 3  ·  Compound event detection
             └─ Joint exceedance framework, co-occurrence statistics

Phase 4  ·  Validation against observed disasters
             └─ Cross-referencing with Leal et al. (2024) and S2ID

Phase 5  ·  Regional scaling to full Brazilian coastal domain

Phase 6  ·  Exposure, vulnerability, and risk integration
```

**Compound event definition (exploratory):** an event is classified as compound if Hₛ and SSH
each exceed their respective extreme thresholds within a ±3-day coincidence window. Thresholds
are currently empirical (q90 of domain means) and will be replaced by physically motivated
estimates in Phase 2.

---

## Current Results

The currently implemented analysis is the **exploratory EDA for the southern SC test domain**
(`src/explore_test_data_south_sc/`), which covers:

- **Part A** — Spatial maximum maps of Hₛ and SSH (1993–2025)
- **Part B** — Time series at peak-value grid points (±15-day window)
- **Part D** — Reported events EDA: counts, Hₛ/SSH boxplots at event dates, monthly seasonality
- **Part E** — Municipality–grid association via IBGE API and Natural Earth coastline
- **Part F** — Sector overview figure: map + Hₛ + SSH boxplots per municipality
- **Part G** — Descriptive statistics, scatter plots, seasonal cycle, compound quick-look, distributions

Outputs (figures and tables) are written to `outputs/south_sc_test_data_exploratory/`.
See `src/explore_test_data_south_sc/README.md` for full documentation and `RUN.md` for
quick-start instructions.

---

## Repository Structure

```
osr11/
├── README.md
├── environment.yml                           # Conda environment
├── config/
│   ├── plot_config.py                        # Shared FigureStyle dataclass
│   ├── download_config.example.yml           # Template for CMEMS downloads
│   └── test_fixture.example.yml              # Template for test fixture builds
├── data/
│   ├── README.md
│   ├── test/                                 # Committed test-domain NetCDF subsets
│   │   ├── waverys_sc_sul_test.nc            # VHM0, VMDR · 3-hourly · 1993–2025
│   │   └── glorys_sc_sul_test.nc             # zos · daily · 1993–2025
│   ├── reported events/
│   │   └── reported_events_Karine_sc.csv     # Leal et al. (2024)
│   ├── ne_10m_coastline/                     # Natural Earth coastline shapefile
│   └── raw/                                  # Full CMEMS downloads (not committed)
├── src/
│   ├── acquisition/
│   │   ├── download_cmems.py                 # Main CMEMS download script
│   │   ├── download_cmems_parallel.py        # Parallel download variant
│   │   ├── catalog_inspect.py                # CMEMS catalog inspection utility
│   │   └── build_test_fixture.py             # Build test NetCDF subsets
│   ├── preprocessing/
│   │   └── convert_reported_events.py        # Excel → CSV for reported events
│   └── explore_test_data_south_sc/           # Phase 1: EDA of south SC test data
│       ├── main.py                           # CLI orchestrator
│       ├── io.py                             # Dataset loaders
│       ├── coastal.py                        # Coastal grid point selection (NE)
│       ├── maps.py                           # Part A: spatial maxima maps
│       ├── timeseries.py                     # Part B: time series
│       ├── reported_events.py                # Part D: events EDA
│       ├── municipalities.py                 # Part E: municipality–grid association
│       ├── boxplots.py                       # Part F: sector boxplot figure
│       ├── statistics.py                     # Part G: statistical analyses
│       ├── utils.py                          # Shared utilities
│       ├── config/analysis_config.py         # File paths and parameters
│       ├── README.md
│       └── RUN.md
├── outputs/                                  # Analysis outputs (not committed)
│   └── south_sc_test_data_exploratory/
│       ├── figures/                          # PNG figures (300 dpi)
│       └── tables/                           # CSV summary tables
└── site/                                     # Scientific results website (Next.js)
```

---

## Environment Setup

### 1. Create the Conda environment

```bash
conda env create -f environment.yml
conda activate osr11
```

### 2. Authenticate with Copernicus Marine (CMEMS)

```bash
copernicusmarine login
# Follow the prompt to enter credentials (stored in ~/.copernicusmarine/)
```

### 3. Run the exploratory analysis (test data — no download required)

The test fixtures are already committed to the repository. Run directly:

```bash
# Full analysis
python -m src.explore_test_data_south_sc.main --all

# Individual parts
python -m src.explore_test_data_south_sc.main --maps          # Part A
python -m src.explore_test_data_south_sc.main --timeseries    # Part B
python -m src.explore_test_data_south_sc.main --statistics    # Part G
```

See `src/explore_test_data_south_sc/RUN.md` for the complete command reference.

---

## Data Acquisition (Full Domain)

```bash
# Inspect CMEMS catalog (recommended before downloading)
python src/acquisition/catalog_inspect.py GLOBAL_MULTIYEAR_PHY_001_030
python src/acquisition/catalog_inspect.py GLOBAL_MULTIYEAR_WAV_001_032

# Configure download (copy and edit)
cp config/download_config.example.yml config/download_config.yml

# Download GLORYS and WAVERYS
python src/acquisition/download_cmems.py
python src/acquisition/download_cmems.py --product glorys
python src/acquisition/download_cmems.py --product waverys
```

---

## Results Website

A scientific results site is available in `site/` (Next.js + Tailwind CSS, deployable to Vercel).

```bash
cd site
npm install
npm run dev          # Local development server at http://localhost:3000
npm run build        # Production build
vercel --prod        # Deploy to Vercel
```

---

## Notes

- `data/raw/` is listed in `.gitignore` and is never committed to version control.
- All analysis outputs (`outputs/`) are regeneratable from the test fixtures and are not committed.
- Results are preliminary and subject to revision. Do not cite without consulting the authors.
