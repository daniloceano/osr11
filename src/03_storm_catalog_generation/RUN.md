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

3. **FES2022 tide model** available at `data/tide_models_clipped_brasil/`.

4. **Unified metocean dataset** — either:
   - **Test (SC):** `data/test/metocean_sc_full_unified_waverys_grid.nc`
   - **Production (full Brazil):** `data/raw/metocean_brazil_unified_waverys_grid.nc` *(not yet available — see Action Plan below)*

---

## Run (test mode — SC domain)

From the **project root**:

```bash
python -m src.03_storm_catalog_generation.main --mode test
```

This processes the SC test fixture (~18×11 grid, 1993–2025 daily).

### Individual phases

```bash
# Phase 1 only — validate inputs
python -m src.03_storm_catalog_generation.main --phase load-validate --mode test

# Phases 1–2 — validate + compute tides
python -m src.03_storm_catalog_generation.main --phase tides --mode test

# Phases 1–3 — validate + tides + catalogs
python -m src.03_storm_catalog_generation.main --phase catalog --mode test

# Phase 4 only — QA figures (requires catalogs from a prior run)
python -m src.03_storm_catalog_generation.main --phase figures --mode test
```

### Debug logging

```bash
python -m src.03_storm_catalog_generation.main --mode test --log-level DEBUG
```

---

## Run (production mode — full Brazil)

```bash
python -m src.03_storm_catalog_generation.main --mode production
```

> **Not yet operational.** Requires:
> 1. Full-domain CMEMS download (GLORYS12 + WAVERYS, ~5°S–34°S)
> 2. Step 1 preprocessing rerun to produce unified NetCDF
> 3. Verification that FES2022 model clip covers the full domain

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
| `logs/run_metadata.json` | Run provenance |

---

## Configuration

Edit `src/03_storm_catalog_generation/config/analysis_config.py` to change:
- `RUN_MODE` — `"test"` or `"production"`
- `EPISODE_MAX_GAP_DAYS` — gap tolerance for episode merging (default: 1)
- `COASTAL_MAX_DIST_KM` — max distance to coast for grid points (default: 50 km)
- `MIN_VALID_FRAC` — minimum non-NaN fraction to include a grid point (default: 0.80)
