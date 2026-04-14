# RUN.md — Step 3: Storm Catalog Generation

Quick-start guide for running Step 3.

## Prerequisites

1. **Conda environment** activated:
   ```bash
   conda activate osr11
   ```

2. **Step 2 complete:** The PU-optimal threshold file must exist at:
   ```
   outputs/threshold_calibration/tables/tab_TC5_optimal_pair_pu.csv
   ```

3. **Unified metocean dataset** — one of:
   - **Test (SC):** `data/test/metocean_sc_full_unified_waverys_grid.nc`
   - **Production (full Brazil):** `data/unified/metocean_brazil_unified_waverys_grid.nc`

4. **FES2022 tide model** at `data/tide_models_clipped_brasil/` (only needed for runtime tide mode).

---

## SSH_total / Tide Modes

Step 3 supports three modes for obtaining SSH_total:

| Mode | Flag | When to use |
|------|------|-------------|
| **auto** (default) | `--tide-mode auto` | Detects pre-computed fields; falls back to runtime |
| **precomputed** | `--tide-mode precomputed` | Production: requires SSH_total in dataset |
| **runtime** | `--tide-mode runtime` | Legacy: computes FES2022 on-the-fly (slow) |

**Recommended production workflow:**
1. Run preprocessing with `tides.enabled: true` → produces unified dataset with SSH_total
2. Run Step 3 with `--tide-mode auto` or `--tide-mode precomputed`

---

## Run: Test mode (SC domain, legacy tides)

```bash
python -m src.03_storm_catalog_generation.main --mode test --tide-mode runtime
```

This computes FES2022 tides on-the-fly (~8 min for 53 grid points).

---

## Run: Production mode (full domain, pre-computed tides)

```bash
# Sequential (suitable for small domains)
python -m src.03_storm_catalog_generation.main --mode production --tide-mode auto

# Parallel (recommended for 100+ grid points)
python -m src.03_storm_catalog_generation.main --mode production --tide-mode auto --workers 20
```

Or explicitly enforce pre-computed mode (fails if SSH_total is missing):
```bash
python -m src.03_storm_catalog_generation.main --mode production --tide-mode precomputed --workers 20
```

### Parallelization

The `--workers N` flag controls the number of processes for the catalog-building phase (Phase 3). Each worker processes one grid point independently.

| Workers | Use case |
|---------|----------|
| 1 (default) | Sequential, debugging, small domains |
| 4–16 | Local workstation |
| 20–50 | Remote server (balanced I/O vs CPU) |

**Note:** Workers > 50 may not improve performance due to serialization overhead for 200-grid-point domains. For the current SC-domain data (204 grid points), 20 workers cut runtime from ~60 s to ~16 s.

---

## Individual phases

```bash
# Phase 1 — validate inputs
python -m src.03_storm_catalog_generation.main --phase load-validate --mode test

# Phase 2 — resolve SSH_total (auto-detect method)
python -m src.03_storm_catalog_generation.main --phase tides --mode test

# Phase 3 — build catalogs
python -m src.03_storm_catalog_generation.main --phase catalog --mode test

# Phase 4 — QA figures
python -m src.03_storm_catalog_generation.main --phase figures --mode test
```

---

## Debug logging

```bash
python -m src.03_storm_catalog_generation.main --mode test --log-level DEBUG
```

---

## Outputs

All outputs go to `outputs/storm_catalog/`:

| Path | Description |
|------|-------------|
| `catalog_hs_storms.json` | Hₛ storm catalog (JSON, full detail) |
| `catalog_ssh_total_storms.json` | SSH_total storm catalog (JSON, full detail) |
| `tables/tab_SC3_hs_storms_summary.csv` | Hₛ storms flat table |
| `tables/tab_SC3_ssh_total_storms_summary.csv` | SSH_total storms flat table |
| `tables/tab_SC3_catalog_metadata.csv` | Per-grid-point metadata |
| `figures/fig_SC3_annual_storm_counts.png` | Annual counts plot |
| `figures/fig_SC3_duration_distribution.png` | Duration histogram |
| `figures/fig_SC3_seasonal_climatology.png` | Monthly climatology |
| `logs/run_metadata.json` | Run provenance (includes tide_mode_used) |

---

## Configuration

Edit `src/03_storm_catalog_generation/config/analysis_config.py` to change:
- `RUN_MODE` — `"test"` or `"production"`
- `TIDE_MODE` — `"auto"`, `"precomputed"`, or `"runtime"`
- `EPISODE_MAX_GAP_DAYS` — gap tolerance for episode merging (default: 1)
- `COASTAL_MAX_DIST_KM` — max distance to coast for grid points (default: 50 km)
- `MIN_VALID_FRAC` — minimum non-NaN fraction to include a grid point (default: 0.80)

---

## Full production pipeline (server)

```bash
# 1. Download full-domain data (if not done yet; skip if data/raw/ already populated)
python -m src.01_data_preparation.acquisition.download_cmems_parallel \
    --config config/download_config_brazil_full.yml \
    --workers 80 --resume

# 2. Preprocessing: open monthly files, regrid, compute tides, write unified dataset
#    No CDO or external tools required — the script reads directories of monthly NetCDFs directly.
python -m src.01_data_preparation.preprocessing.interpolate_glorys_to_waverys_grid \
    --config config/preprocessing/glorys_to_waverys_brazil_full.yaml \
    --workers 50

# 3. Run Step 3 (fast — tides already in the unified dataset)
python -m src.03_storm_catalog_generation.main \
    --mode production --tide-mode auto --workers 20
```
