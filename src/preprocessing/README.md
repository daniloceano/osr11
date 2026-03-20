# src/preprocessing/

Data preprocessing scripts that convert raw or format-incompatible data into
analysis-ready inputs for the compound coastal-event pipeline.

---

## Scripts

### `convert_reported_events.py`

Converts the Excel file `reported_events_Karine_sc.xlsx` to CSV format.

**Usage:**

```bash
python src/preprocessing/convert_reported_events.py
```

**What it does:**

1. Reads the Excel file from `data/reported events/`
2. Skips the first row (table caption)
3. Strips whitespace from column names
4. Saves as UTF-8 CSV to the same directory

**Output:** `data/reported events/reported_events_Karine_sc.csv`

**Why CSV?**

- Faster to read (no Excel parsing overhead)
- Better for version control (text-based diffs)
- No external dependencies on Excel libraries for routine analysis
- Easier manipulation in most data science workflows

---

### `interpolate_glorys_to_waverys_grid.py`

Interpolates GLORYS sea surface height (`zos`) onto the WAVERYS spatial grid
and builds a single unified NetCDF dataset with sea level and wave variables on
a common grid, ready for compound-event analysis.

#### Why this step exists

GLORYS12 and WAVERYS come from different ocean/wave models with incompatible
spatial grids:

| Dataset  | Resolution | Temporal | Variables            |
|----------|-----------|----------|----------------------|
| GLORYS12 | ~1/12° (~0.083°) | Daily | `zos` — sea surface height |
| WAVERYS  | ~1/5° (0.2°)     | 3-hourly | `VHM0` — Hs, `VMDR` — wave direction |

Before any joint analysis of compound coastal events (simultaneous extremes in
sea level and wave height), both datasets must share a common spatial grid.

#### Why WAVERYS is the target grid

WAVERYS has the coarser resolution (~0.2° vs ~0.083°).  Interpolating the finer
GLORYS onto the coarser WAVERYS grid is the correct direction because:

- It avoids artificially inflating spatial detail in the output.
- The GLORYS domain fully contains the WAVERYS grid → no extrapolation needed.
- Wave analysis products are generally limited to the ~0.2° resolution anyway.

#### Temporal alignment strategy

GLORYS is daily.  WAVERYS is 3-hourly and is aggregated to daily before merging.
The aggregation method (`mean` or `max`) is configurable in the YAML:

- **`mean`** (default): preserves mean daily wave conditions; suited for
  climatological and correlation studies.
- **`max`**: captures peak daily wave height; preferred when the focus is on
  compound extremes.

Only days present in **both** datasets (temporal intersection) are retained.

#### Inputs

| File | Description |
|------|-------------|
| `data/test/glorys_sc_sul_test.nc` | GLORYS12 sea surface height, daily, 1993–2025 |
| `data/test/waverys_sc_sul_test.nc` | WAVERYS Hs + direction, 3-hourly, 1993–2025 |

#### Output

`data/test/metocean_sc_sul_unified_waverys_grid.nc`

A single NetCDF file on the WAVERYS grid (~0.2°, 10 lat × 11 lon) containing:

| Variable | Description | Source |
|----------|-------------|--------|
| `zos`    | Sea surface height (m) | GLORYS12, interpolated to WAVERYS grid |
| `VHM0`   | Significant wave height (m) | WAVERYS, resampled to daily |
| `VMDR`   | Mean wave direction (°) | WAVERYS, resampled to daily |

**Dimensions:** `(time: 12053, latitude: 10, longitude: 11)`
**Period:** 1993-01-01 → 2025-12-31

#### Limitations

- Spatial interpolation uses bilinear (`linear`) interpolation via
  `xarray.DataArray.interp`. Higher-order methods (e.g. cubic) are available
  via the config but not tested.
- GLORYS `zos` is daily; no sub-daily sea-level variability is captured.
- WAVERYS is resampled from 3-hourly to daily: intra-day extremes are smoothed
  unless `resample_method: max` is selected.
- The unified dataset is intended for exploratory and test use.  Final compound-
  event analyses should use the full operational domains.

#### Usage

```bash
python -m src.preprocessing.interpolate_glorys_to_waverys_grid \
    --config config/preprocessing/glorys_to_waverys_test.yaml
```

The config file `config/preprocessing/glorys_to_waverys_test.yaml` controls
all input/output paths, variable names, interpolation method, and temporal
resampling method.

#### Performance note

`xarray.Dataset.resample` is very slow for datasets with ~100 k time steps
(>20 min).  This script uses a numpy/pandas groupby approach instead (~10 s
for the test domain).

---

## When to run

| Script | Re-run when |
|--------|-------------|
| `convert_reported_events.py` | Original Excel file is updated |
| `interpolate_glorys_to_waverys_grid.py` | GLORYS or WAVERYS test files are updated, config changes, or output file is missing |
