# `01_explore_test_data_south_sc` — Exploratory Analysis of South SC Test Data

## Purpose

This module contains the exploratory data analysis (EDA) for the OSR11 project,
restricted to the **test datasets covering the southern Santa Catarina coast**.

It is a **first-pass, inspection-oriented analysis**, not the final methodology.
Its goals are:

- Verify the structure, extent, and quality of the test NetCDF files.
- Understand the spatial and temporal variability of Hs (WAVERYS) and SSH (GLORYS).
- Explore the reported coastal disaster database (Leal et al. 2024) for the South sector.
- Associate municipalities to the nearest model grid points.
- Generate diagnostic figures and summary tables to inform subsequent analysis design.

> **Scope**: This module analyses only the **South sector** municipalities and the
> corresponding nearshore grid points. This restriction matches the spatial coverage
> of the test datasets (approx. −29.4 to −27.6°S, −50 to −48°W).
> It does **not** represent the final methodology for the full OSR11 study.

---

## Scientific scope

| Item              | Value                                                                 |
|-------------------|-----------------------------------------------------------------------|
| Datasets          | WAVERYS (VHM0, VMDR, 3-hourly) · GLORYS12 (zos, daily)              |
| Temporal coverage | 1993–2025                                                             |
| Spatial domain    | Southern SC coast (~−29.4 to −27.6°S, ~−50 to −48°W)                |
| Events database   | Leal et al. (2024), South sector only (test domain restriction)       |
| Analysis phase    | Exploratory / sanity check — **not final**                            |

### Documented analytical assumptions

1. **Coastal point selection via NE coastline**: The nearshore grid point (Part A)
   and municipality–grid associations (Part E) use the Natural Earth 10 m coastline
   (`data/ne_10m_coastline/`) to identify model cells that are both non-NaN and within
   `max_coastal_dist_km` (default 50 km) of the actual coastline. The cell with minimum
   distance to any coastline vertex is selected.  The previous heuristic of "minimum
   longitude" was not scientifically valid for non-meridional coastlines and has been
   replaced.
2. **Separate wave and SSH domain flags**: `in_wave_domain` (WAVERYS) and
   `in_gl_domain` (GLORYS) are computed independently. GLORYS12 uses a finer ocean
   land-mask, so some coastal municipalities may have valid WAVERYS data but no valid
   GLORYS coastal cell. This is expected and not a data error.
3. **South sector only**: The events database is filtered to South sector municipalities
   to match the test domain extent. This is logged explicitly at runtime.
4. **Compound thresholds [EDA]**: Quantile-based thresholds in Part G are empirical
   exploratory values (q90 of domain means), not a final compound-event definition.
5. **IBGE coordinates**: Municipality centroids are derived from the outer polygon ring
   of IBGE Malhas v2 geometries. Composite names (e.g. "Içara/Balneário Rincão") are
   matched by trying each part after splitting on "/" or "|".

---

## Module structure

```
src/01_explore_test_data_south_sc/
├── __init__.py
├── main.py               Entry point; CLI orchestrator for all analysis parts
├── io.py                 Dataset loading (WAVERYS, GLORYS, reported events CSV)
├── metadata.py           Dataset inspection + data/test/README generation
├── coastal.py            NE coastline-based coastal grid point selection
├── maps.py               Part A: spatial maximum maps (Cartopy)
├── timeseries.py         Part B: time series at peak grid points
├── reported_events.py    Part D: reported events EDA (counts, boxplots, seasonality)
├── municipalities.py     Part E: IBGE coords + municipality–coastal-grid association
├── boxplots.py           Part F: per-sector map + Hs/SSH boxplot figures
├── statistics.py         Part G: per-municipality scatter, seasonal cycle, compound
├── utils.py              Shared helpers (save_fig, fmt_time_ax, vline, span, ...)
└── config/
    ├── __init__.py
    └── analysis_config.py  File paths, variable names, analysis parameters

# Project-level (shared with all future analyses)
config/
└── plot_config.py          Publication-quality figure style (FigureStyle dataclass)
```

### Design decisions

- **Analysis config local, figure style global**: File paths and analysis parameters
  live in `src/01_explore_test_data_south_sc/config/analysis_config.py` (analysis-specific).
  Figure style (`FigureStyle`, `apply_publication_style`, `SECTOR_COLORS`) lives in the
  project-level `config/plot_config.py`, shared by all future analyses in this project.
- **Style via dataclass**: `FigureStyle` is a frozen dataclass. Style variants can be
  derived with `dataclasses.replace(STYLE, ...)` without mutating the global default.
- **Coastal point selection via NE coastline**: `coastal.py` provides `find_coastal_points`
  and `nearest_coastal_point`. Both use the committed Natural Earth 10 m shapefile
  (`data/ne_10m_coastline/`) and cartopy's shapereader to extract coastline vertices.
  All nearshore-point and municipality–grid selections go through this module.
- **Separate wave and SSH domain flags**: `municipalities.py` produces `in_wave_domain`
  and `in_gl_domain` columns independently, because GLORYS12 uses a finer land mask
  than WAVERYS. A municipality can have a valid WAVERYS coastal cell while the nearest
  GLORYS cell is land-masked. This explains why fewer municipalities appear in the SSH
  boxplot panels than in the Hs panels.
- **Part E runs before Part D**: In `main.py`, the municipality–grid association is
  computed before the reported-events EDA so that `grid_table` is available for the
  D2 SSH panel.  `--reported-events` also triggers Part E automatically.
- **No circular imports**: `coastal` → none; `analysis_config` → none; `utils` →
  `analysis_config` + `config.plot_config`; `io` → `analysis_config`; analysis modules →
  `analysis_config` + `utils` + `config.plot_config`; `municipalities` → `coastal`;
  `maps` → `coastal`; `boxplots` → `maps` (for `_CRS`, `_ne`).
- **Cartopy helpers**: `_CRS` and `_ne()` live in `maps.py` and are imported by
  `boxplots.py`, the only other module that generates cartopy figures.

---

## Inputs

| File                                            | Description                                  |
|-------------------------------------------------|----------------------------------------------|
| `data/test/waverys_sc_sul_test.nc`              | WAVERYS test subset (VHM0, VMDR, 3-hourly)  |
| `data/test/glorys_sc_sul_test.nc`               | GLORYS12 test subset (zos, daily)            |
| `data/reported events/reported_events_Karine_sc.csv` | Reported coastal events (Leal et al. 2024) |

All paths are resolved from the project root via `config/analysis_config.py`.

---

## Outputs

All outputs are written to `outputs/south_sc_test_data_exploratory/`.

```
outputs/south_sc_test_data_exploratory/
├── figures/
│   ├── fig_A1_spatial_max_combined.png          (or fig_A1a / fig_A1b if non-coincident)
│   ├── fig_B1_timeseries_at_maxima.png
│   ├── fig_D1_events_by_municipality.png
│   ├── fig_D2_Hs_SSH_boxplot_by_municipality.png
│   ├── fig_D4_monthly_seasonality.png
│   ├── fig_F_<Sector>_sector.png                (one per coastal sector)
│   ├── fig_G2_scatter_Hs_SSH_per_municipality.png
│   ├── fig_G3_seasonal_cycle.png
│   ├── fig_G4_compound_quicklook.png
│   ├── fig_G5_timeseries_compound_highlights.png
│   └── fig_G6_distributions_Hs_SSH.png
├── tables/
│   ├── tab_events_by_municipality.csv
│   ├── tab_events_by_sector.csv
│   ├── tab_municipality_grid_association.csv
│   ├── tab_descriptive_stats_by_municipality.csv
│   └── tab_top_compound_events_eda.csv
└── logs/                                         (reserved for future use)
```

Additionally regenerates:
- `data/test/README.md`
- `data/reported events/README.md`

---

## How to run

```bash
conda activate osr11

# Run the full exploratory analysis
python -m src.explore_test_data_south_sc.main --all

# Run individual parts
python -m src.explore_test_data_south_sc.main --maps
python -m src.explore_test_data_south_sc.main --timeseries
python -m src.explore_test_data_south_sc.main --reported-events
python -m src.explore_test_data_south_sc.main --municipalities
python -m src.explore_test_data_south_sc.main --sector-boxplots
python -m src.explore_test_data_south_sc.main --statistics
python -m src.explore_test_data_south_sc.main --write-readmes
```

> **Note on imports:** The physical directory is `src/01_explore_test_data_south_sc/` but it
> is registered under `src.explore_test_data_south_sc` via a compatibility alias in
> `src/__init__.py`. All `from src.explore_test_data_south_sc.xxx import` statements work
> unchanged. Adding new numbered modules only requires updating the `_MODULE_ALIASES` dict
> in `src/__init__.py`.

Parts B (--timeseries) and F/G (--sector-boxplots, --statistics) automatically
run their prerequisites (Parts A and E respectively) when called in isolation.

---

## Conventions

- **File naming**: figures use the prefix `fig_<PartLetter><Number>_<description>`;
  tables use `tab_<description>`.
- **Figure format**: PNG at 300 dpi (configurable in project-level `config/plot_config.py`).
- **Municipality ordering**: south to north by latitude, consistent with the SC coastline.
- **Panel labels**: use `plot_config.panel_label(ax, "a")` for (a), (b), etc.
- **Logging**: all modules log at INFO level; structured as `Part X: ...`.

---

## Limitations of this phase

- Restricted to the test domain: northern and central-north SC municipalities are
  outside the bounding box and receive no grid-based statistics.
- Compound thresholds (Part G) are empirical and exploratory (q90 of domain-mean
  daily series). They will be replaced by a physically motivated definition in the
  final analysis.
- No spatial interpolation: municipality analyses use the nearest coastal grid point.
- Wave and surge are compared at daily resolution (GLORYS) even though WAVERYS is
  3-hourly (WAVERYS is resampled to daily mean before paired analysis).
- GLORYS12 has a finer ocean land-mask than WAVERYS; some municipalities may have Hs
  data but no SSH data (logged explicitly as `in_gl_domain=False`).
- IBGE API calls require internet access; if the API is unavailable, municipality
  coordinates will be NaN and association tables will be incomplete.
- The NE 10 m coastline (`data/ne_10m_coastline/`) uses the global 1:10m shoreline.
  For very small coastal features (<10 km), a higher-resolution coastline may be
  required to correctly classify grid cells.

---

## Reference

> Leal, K.B., Robaina, L.E.S., Körting, T.S. et al. Identification of coastal natural
> disasters using official databases to provide support for the coastal management:
> the case of Santa Catarina, Brazil.
> *Nat Hazards* **120**, 11465–11482 (2024).
> https://doi.org/10.1007/s11069-023-06150-3
