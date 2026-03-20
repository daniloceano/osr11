# `data/` — OSR11 Data Directory

This directory holds all input data for the OSR11 project.
Raw ocean reanalysis files are **not committed** to version control (see `.gitignore`).
Only small test subsets and static reference datasets are tracked.

---

## Directory structure

```
data/
├── test/                          # Small NetCDF subsets — committed (~100–500 KB each)
│   ├── waverys_sc_sul_test.nc     # WAVERYS test cutout: VHM0, VMDR — south SC coast, 1993–2025
│   ├── glorys_sc_sul_test.nc      # GLORYS12 test cutout: zos — south SC coast, 1993–2025
│   └── README.md                  # Auto-generated metadata (by src/explore_test_data_south_sc/main.py --write-readmes)
│
├── ne_10m_coastline/              # Natural Earth 10 m coastline shapefile — committed
│   ├── ne_10m_coastline.shp       # Main shapefile geometry
│   ├── ne_10m_coastline.dbf       # Attribute table
│   ├── ne_10m_coastline.shx       # Shape index
│   ├── ne_10m_coastline.prj       # CRS definition (WGS84)
│   ├── ne_10m_coastline.cpg       # Encoding descriptor
│   └── ne_10m_coastline.README.html  # Natural Earth source metadata
│
├── reported events/               # Reported coastal disaster database
│   ├── reported_events_Karine_sc.csv  # Leal et al. (2024) — SC coastal events, 1998–2023
│   └── README.md                  # Auto-generated metadata (by --write-readmes)
│
└── raw/                           # Full-resolution reanalysis downloads — NOT committed
    ├── glorys/                    # GLORYS12 sea-level NetCDF files (download via download_cmems.py)
    └── waverys/                   # WAVERYS wave NetCDF files (download via download_cmems.py)
```

---

## Test data

The `test/` cutouts cover the **southern Santa Catarina coast** (~−29.4 to −27.6°S, ~−50 to −48°W)
for the full reanalysis period (1993–2025). They are used by the exploratory analysis pipeline
without requiring a full data download.

To regenerate the test fixtures from a local full download:

```bash
python src/acquisition/build_test_fixture.py
```

## Natural Earth coastline

`ne_10m_coastline/` contains the 1:10m resolution global coastline from [Natural Earth](https://www.naturalearthdata.com/).
It is used by `src/explore_test_data_south_sc/coastal.py` to identify which model grid cells
are "coastal" — i.e., non-NaN AND within a configurable distance of the actual coastline.
This replaces the heuristic of using minimum longitude as a coastal proxy.

**Source**: [Natural Earth — Physical — Coastline](https://www.naturalearthdata.com/downloads/10m-physical-vectors/)
**Resolution**: 1:10,000,000 (10 m)
**CRS**: WGS84 (EPSG:4326)

## Reported events

`reported events/reported_events_Karine_sc.csv` is the Leal et al. (2024) database of
declared coastal disasters in Santa Catarina, Brazil (1998–2023). It is read and cleaned
by `src/explore_test_data_south_sc/io.py`.

> Leal, K.B., Robaina, L.E.S., Körting, T.S. et al. (2024).
> *Nat Hazards* **120**, 11465–11482. https://doi.org/10.1007/s11069-023-06150-3

## Raw data

`raw/` is listed in `.gitignore` and is never committed.
Download scripts are in `src/acquisition/`. See the project README for setup instructions.
