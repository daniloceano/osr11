# PIPELINE_SETUP.md — Production Pipeline: Initial Setup

This document describes the one-time steps required to go from a fresh clone to a
running production pipeline (Steps 1–3).  
Run these steps **in order** before executing Step 3.

---

## Current data state (April 2026)

| Directory | Contents | Domain | Status |
|-----------|----------|--------|--------|
| `data/raw/glorys_sc/` | 399 monthly GLORYS files (incl. 3 duplicates `_(1)`) | SC coast [-30,−20°S] × [-50,−40°W] | ✅ Downloaded |
| `data/raw/waverys_sc/` | 399 monthly WAVERYS files (incl. 3 duplicates `_(1)`) | SC coast [-30,−20°S] × [-50,−40°W] | ✅ Downloaded |
| `data/raw/glorys/` | 396 monthly GLORYS files (Jan 1993 – Dec 2025) | Full Brazil [-35°S,+6°N] × [-55°W,-28°W] | ✅ Downloaded (14.38 GB) |
| `data/raw/waverys/` | 396 monthly WAVERYS files (Jan 1993 – Dec 2025) | Full Brazil [-35°S,+6°N] × [-55°W,-28°W] | ✅ Downloaded (14.38 GB) |
| `data/unified/` | `metocean_brazil_unified_waverys_grid.nc` | Full Brazil, 206×136 grid, 12053 days | ✅ Preprocessed (1.6 GB) |
| `outputs/storm_catalog/` | Hs + SSH_total catalogs, 808 grid points | Full Brazilian coast | ✅ Step 3 complete |
| `site/public/data/` | `hazard_characterization_grid_metrics.json` (3.8, primary) + legacy `storm_maps_grid_metrics.json` | 808 grid points | ✅ Exported for site |

The SC-domain files were downloaded during an initial test phase.  
They are preserved for reference and for test fixture regeneration, but are
**not used by the production pipeline**.

`logs/download_status_sc_backup.json` — backup of the SC download run log.

---

## Step 0 — Environment setup

```bash
conda env create -f environment.yml
conda activate osr11
```

Verify the tide model is present:

```bash
ls data/tide_models_clipped_brasil/fes2022b/ocean_tide_20241025/
```

Expected: 45 `*.nc` constituent files covering the full Brazilian domain.  
If missing, contact the IAG data team or re-run `src/01_data_preparation/acquisition/build_test_fixture.py`.

---

## Step 1 — Download full-Brazil metocean data

### Config file

`config/download_config_brazil_full.yml`

Spatial domain defined in that file:

```
bbox: [-55°W → -28°W] × [-35°S → +6°N]
```

This covers the full Brazilian coast from Chuí (RS) to Amapá plus offshore margin.

### Run download

```bash
# Do NOT use --resume (would skip files incorrectly if output paths match old SC files)
python src/01_data_preparation/acquisition/download_cmems_parallel.py \
    --config config/download_config_brazil_full.yml \
    --workers 100
```

> **Why no `--resume`?**  
> The `--resume` flag marks a task as done if the output file already exists.
> In the previous SC run the files were saved to `data/raw/glorys/` and
> `data/raw/waverys/`. Those directories are now empty, so `--resume` is
> safe to use again once the download starts. For the very first run on a
> clean directory, `--resume` is harmless.

### Monitor progress (separate terminal)

```bash
watch -n 5 python src/acquisition/monitor.py
# or:
cat logs/download_status.json | python -m json.tool | grep -E '"completed"|"failed"|"pending"'
```

### Expected output

```
data/raw/glorys/
  glorys_zos_1993-01.nc
  glorys_zos_1993-02.nc
  ...
  glorys_zos_2025-12.nc     # 396 files (monthly, Jan 1993 – Dec 2025)

data/raw/waverys/
  waverys_VHM0_VMDR_1993-01.nc
  ...
  waverys_VHM0_VMDR_2025-12.nc  # 396 files
```

Total download size: ~40–80 GB (estimate; depends on CMEMS server).

---

## Step 2 — Preprocessing (GLORYS + WAVERYS → unified dataset)

### What this step does

1. Opens all 396 GLORYS monthly files via `xr.open_mfdataset` (no CDO required).
2. Opens all 396 WAVERYS monthly files the same way.
3. Interpolates GLORYS sea-level (`zos`) onto the WAVERYS spatial grid.
4. Computes astronomical tides via FES2022b at all coastal grid points.
5. Derives `SSH_total = zos + tide + MSL`.
6. Saves a single unified NetCDF to `data/unified/`.

### Config file

`config/preprocessing/glorys_to_waverys_brazil_full.yaml`

Key settings:

```yaml
input:
  glorys:  data/raw/glorys/    # directory → auto-discovers and concatenates all .nc files
  waverys: data/raw/waverys/

output:
  path: data/unified/metocean_brazil_unified_waverys_grid.nc

tides:
  enabled: true
  model: fes2022
  model_dir: data/tide_models_clipped_brasil
  workers: 50
```

### Run

```bash
conda run -n osr11 \
  python -m src.01_data_preparation.preprocessing.interpolate_glorys_to_waverys_grid \
  --config config/preprocessing/glorys_to_waverys_brazil_full.yaml \
  --workers 50
```

### Expected output

```
data/unified/metocean_brazil_unified_waverys_grid.nc
```

Approximate size: **600 MB – 1.5 GB** for full Brazil domain.  
Approximate runtime: **10–20 min** with 50 workers on the server.

### Verify

```python
import xarray as xr
ds = xr.open_dataset("data/unified/metocean_brazil_unified_waverys_grid.nc")
print(ds)
# Expected: dims (time, lat, lon), variables [VHM0, VMDR, zos, ssh_tide, SSH_total]
```

---

## Step 3 — Storm catalog generation

### Prerequisites

Step 2 output must exist:

```
data/unified/metocean_brazil_unified_waverys_grid.nc
```

Threshold calibration output must exist:

```
outputs/threshold_calibration/tables/tab_TC5_optimal_pair_pu.csv
```

### Run

```bash
python -m src.03_storm_catalog_generation.01_storm_catalogs.main \
  --mode production \
  --tide-mode auto \
  --workers 20
```

See `src/03_storm_catalog_generation/RUN.md` for full documentation (individual phases,
debug logging, parallelization guidelines).

### Expected outputs

```
outputs/storm_catalog/
  logs/run_metadata.json          # Run summary with storm counts
  catalog_hs_storms.json          # Hs storm catalog (29 MB, 404,535 storms)
  catalog_ssh_total_storms.json   # SSH_total storm catalog (25 MB, 324,929 storms)
  tables/tab_SC3_catalog_metadata.csv     # Per-grid-point QA metadata
  tables/tab_SC3_hs_storms_summary.csv    # Flat CSV: one row per Hs storm
  tables/tab_SC3_ssh_total_storms_summary.csv  # Flat CSV: one row per SSH storm
  figures/                        # QA figures (one per coastal grid point)
```

---

## Site exports — two distinct JSONs

There are **two** site-export paths, both currently live and consumed by different pages.
Do not confuse them.

### A. Full hazard-characterization export (current, primary)

Built by sub-module **3.8** (`08_site_export/export.py`), run as part of the hazard
characterization pipeline (`hazard_characterization --module all` / `--module site_export`).
It merges **all** sub-module outputs (compound, duration, seasonality, trends, EVA,
dependence) into one JSON consumed by **`/results/hazard-characterization`**.

```bash
python -m src.03_storm_catalog_generation.hazard_characterization --module site_export
```

Output:

```
site/public/data/hazard_characterization_grid_metrics.json   # ~2.4 MB, 808 grid points
```

### B. Legacy storm-maps export (compound-only, still consumed)

The older, narrower export in `src/site/export_storm_maps_data.py` produces a
compound/3-class-only JSON consumed by **`/results/storm-maps`**. The 3.8 export above
supersedes it for new work, but the `/results/storm-maps` page still reads this file, so
it is kept until that page is retired or repointed.

```bash
conda run -n osr11 python -m src.site.export_storm_maps_data
```

Output:

```
site/public/data/storm_maps_grid_metrics.json   # ~0.4 MB, 808 grid points
```

Compound detection itself lives in sub-module **3.2** (`02_compound_detection/`); both
exports read its results rather than re-detecting.

### Production results (April 2026)

- 306,256 Hs-only storms
- 228,426 SSH_total-only storms
- 96,031 compound events

---

## Summary of commands (clean full-Brazil run)

```bash
# 0. Environment
conda activate osr11

# 1. Download (run once, ~75 min with 15 workers)
python src/01_data_preparation/acquisition/download_cmems_parallel.py \
    --config config/download_config_brazil_full.yml \
    --workers 15

# 2. Preprocessing (~45 min with 100 tide workers)
python -m src.01_data_preparation.preprocessing.interpolate_glorys_to_waverys_grid \
    --config config/preprocessing/glorys_to_waverys_brazil_full.yaml \
    --workers 100

# 3a. Storm catalogs / sub-module 3.1 (~1-5 min with 20 workers)
python -m src.03_storm_catalog_generation.01_storm_catalogs.main \
    --mode production --tide-mode auto --workers 20

# 3b. Hazard characterization sub-modules 3.2–3.8 (incl. full site export)
python -m src.03_storm_catalog_generation.hazard_characterization --module all

# 4. (optional) Legacy compound-only export for the /results/storm-maps page
python -m src.site.export_storm_maps_data
```

---

## Troubleshooting

### `download_status.json` shows all tasks "done" but files are wrong domain

This happened during the initial SC test run. The fix is already applied:
- SC files are now in `data/raw/glorys_sc/` and `data/raw/waverys_sc/`
- `logs/download_status.json` has been reset to `pending` for all 792 tasks
- `logs/download_status_sc_backup.json` preserves the SC run record

### Duplicates `_(1).nc` in raw directories

CMEMS occasionally creates duplicate files when a download is retried.
The preprocessing script automatically excludes files with `_(N)` in their name.
To clean them up manually:

```bash
# List duplicates (do not delete before verifying)
find data/raw/glorys/ -name "*_(*.nc" 
find data/raw/waverys/ -name "*_(*.nc"

# Remove after verifying the canonical file exists
find data/raw/glorys/ -name "*_(*.nc" -delete
find data/raw/waverys/ -name "*_(*.nc" -delete
```

### FES2022 tide model missing or incomplete

Expected path: `data/tide_models_clipped_brasil/fes2022b/ocean_tide_20241025/`  
The model must cover the full Brazilian domain [-35, 6] × [-55, -28].
The `eo-tides` library will raise an error if constituent files are missing.
