# `data/` — OSR11 Data Directory

This directory holds all input data for the OSR11 project.
Raw ocean reanalysis files are **not committed** to version control (see `.gitignore`).
Only small test subsets and static reference datasets are tracked.

---

## Directory structure

```
data/
├── test/                                    # Small NetCDF subsets — committed (~100–500 KB each)
│   ├── README.md
│   ├── waverys_sc_sul_test.nc               # WAVERYS: VHM0, VMDR · 3-hourly · south SC coast, 1993–2025
│   ├── glorys_sc_sul_test.nc                # GLORYS12: zos · daily · south SC coast, 1993–2025
│   ├── waverys_sc_full_test.nc              # WAVERYS: VHM0, VMDR · 3-hourly · full SC coast, 1993–2025
│   ├── glorys_sc_full_test.nc               # GLORYS12: zos · daily · full SC coast, 1993–2025
│   └── metocean_sc_full_unified_waverys_grid.nc  # Unified daily metocean · full SC coast, WAVERYS grid
│
├── ne_10m_coastline/                        # Natural Earth 10 m coastline shapefile — committed
│   ├── ne_10m_coastline.shp                 # Main shapefile geometry
│   ├── ne_10m_coastline.dbf                 # Attribute table
│   ├── ne_10m_coastline.shx                 # Shape index
│   ├── ne_10m_coastline.prj                 # CRS definition (WGS84)
│   ├── ne_10m_coastline.cpg                 # Encoding descriptor
│   ├── ne_10m_coastline.VERSION.txt
│   └── ne_10m_coastline.README.html         # Natural Earth source metadata
│
├── reported events/                         # Coastal disaster and event databases — committed
│   ├── README.md
│   ├── reported_events_Karine_sc.xlsx       # Leal et al. (2024) — original Excel file
│   ├── reported_events_Karine_sc.csv        # Leal et al. (2024) — CSV version (generated)
│   ├── ressaca_sc_eventos_sc_1998_2020_consolidated_expandido.csv  # Curated additional events (1998–2020)
│   └── ressaca_sc_eventos_sc_1998_2020_repository_methodology.md   # Curation methodology document
│
├── tide_models_clipped_brasil/              # Astronomical tide model constituents — committed
│   ├── EOT20/ocean_tides/                   # EOT20 model: 17 tidal constituents (NetCDF)
│   └── fes2022b/ocean_tide_20241025/        # FES2022b model: 45 tidal constituents (NetCDF)
│
└── raw/                                     # Full-resolution reanalysis downloads — NOT committed
    ├── glorys/                              # GLORYS12 sea-level NetCDF files
    └── waverys/                             # WAVERYS wave NetCDF files
```

---

## Test data

The `test/` directory contains small domain cutouts of the operational CMEMS datasets, committed to the repository for development and validation use. Two spatial domains are covered:

- **Southern SC** (`*_sc_sul_*`): approx. −29.4 to −27.6°S, −50 to −48°W — south portion of the coast only.
- **Full SC** (`*_sc_full_*`): full Santa Catarina coast extent.

The unified file (`metocean_sc_full_unified_waverys_grid.nc`) is a merged daily product covering both GLORYS12 (zos) and WAVERYS (VHM0, VMDR) variables, regridded to the WAVERYS spatial grid.

See `data/test/README.md` for detailed file metadata.

To regenerate the test fixtures from a local full download:

```bash
python src/01_data_preparation/acquisition/build_test_fixture.py
```

---

## Natural Earth coastline

`ne_10m_coastline/` contains the 1:10m resolution global coastline from [Natural Earth](https://www.naturalearthdata.com/).
It is used by the exploratory analysis module (`src/02_threshold_calibration/01_exploratory_data_analysis/coastal.py`) to identify which model grid cells are "coastal" — i.e., non-NaN AND within a configurable distance of the actual coastline.

**Source**: [Natural Earth — Physical — Coastline](https://www.naturalearthdata.com/downloads/10m-physical-vectors/)  
**Resolution**: 1:10,000,000 (10 m)  
**CRS**: WGS84 (EPSG:4326)

---

## Reported events

`reported events/` contains two complementary datasets of coastal impact episodes on the Santa Catarina coast.
They serve different roles in the threshold calibration workflow — see `data/reported events/README.md` for full documentation.

**Official disaster database** (`reported_events_Karine_sc.csv`):
Civil-defence-based compilation of 105 declared coastal disasters in SC (1998–2023), derived from the Leal et al. (2024) study.

**Curated additional events** (`ressaca_sc_eventos_sc_1998_2020_consolidated_expandido.csv`):
Supplementary table of coastal *ressaca* episodes assembled from documentary sources (academic theses, news archives, technical reports) through a systematic search covering 1998–2020.

> Leal, K.B., Robaina, L.E.S., Körting, T.S. et al. (2024).
> *Nat Hazards* **120**, 11465–11482. https://doi.org/10.1007/s11069-023-06150-3

---

## Tide models

`tide_models_clipped_brasil/` contains spatially clipped tidal constituent files (NetCDF) from two global ocean tide models, covering the Brazilian coastal domain.

| Model | Directory | Constituents | Description |
|-------|-----------|--------------|-------------|
| EOT20 | `EOT20/ocean_tides/` | 17 | Empirical Ocean Tide model, 2020 edition |
| FES2022b | `fes2022b/ocean_tide_20241025/` | 45 | Finite Element Solution tidal model, 2022b release |

These models are used in the tidal sensitivity analysis (`src/02_threshold_calibration/03_tidal_sensitivity/`) to separate astronomically forced tidal signal from storm-surge residuals in the GLORYS12 sea-surface height field.

---

## Raw data

`raw/` is listed in `.gitignore` and is never committed.
Download scripts are in `src/01_data_preparation/acquisition/`. See the project README for full setup instructions.
