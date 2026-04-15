# PREPROCESSING_LOG.md — Preprocessing Issues and Solutions

Log of problems encountered during the preprocessing step (GLORYS + WAVERYS → unified dataset) and the fixes applied.

---

## Production run: full Brazil (April 2026)

**Config**: `config/preprocessing/glorys_to_waverys_brazil_full.yaml`  
**Input**: 396 GLORYS + 396 WAVERYS monthly files (14.38 GB)  
**Output**: `data/unified/metocean_brazil_unified_waverys_grid.nc` (1.6 GB)  
**Grid**: 206 lat × 136 lon (0.2° WAVERYS grid)  
**Domain**: [-35°S, +6°N] × [-55°W, -28°W]  
**Period**: 1993-01-01 → 2025-12-31 (12,053 days)  
**Variables**: VHM0, VMDR, zos, tide_daily_max, SSH_total  
**Coastal points**: 984 (within 50 km of coastline)  

---

### Issue 1: `index 51 is out of bounds for axis 1 with size 51` (tide cache grid mismatch)

**When**: First production run, at the tide computation phase.

**Error message**:
```
Pipeline failed: index 51 is out of bounds for axis 1 with size 51
```

**Cause**: The tide cache file `data/cache/tide_daily_max_cache.nc` was created during the previous SC-domain run (grid: 51 lat × 51 lon). When the full-Brazil run loaded this cache, it used the full Brazil grid indices (206 lat × 136 lon) to index into the 51×51 cache array. Index 51 was out of bounds for axis 1 with size 51 (0-indexed, so max valid index is 50).

The root issue: `compute_tides_parallel()` loaded the cache without checking that its dimensions match the current dataset grid.

**Fix**: Added grid dimension validation after loading the cache:
```python
cache_ok = (
    da_cache.sizes.get("latitude") == len(lat_vals)
    and da_cache.sizes.get("longitude") == len(lon_vals)
    and da_cache.sizes.get("time") == n_days
)
if not cache_ok:
    log.warning("Cache grid mismatch (...). Discarding stale cache.")
    da_cache = None
    remaining = list(coastal_points)
```

**File**: `src/01_data_preparation/preprocessing/compute_tides_parallel.py`

**Lesson**: Caches must always validate dimensions against the current run's grid before use. A cache from a different domain run is invalid.

---

### Issue 2: `Permission denied` on save (corrupted output from previous run)

**When**: After tide computation completed (984/984 ok), at the `to_netcdf()` write step.

**Error message**:
```
Pipeline failed: [Errno 13] Permission denied: '.../metocean_brazil_unified_waverys_grid.nc'
```

**Cause**: A previous failed run (started via `head -30` pipe which killed the process mid-execution) left a partially-written 828 MB file at the output path. This file was an incomplete HDF5 file (not readable by xarray/netCDF4). When the production run tried to overwrite it with `to_netcdf()`, the write failed with a misleading Permission denied error.

The misleading error message is a known issue: xarray/netCDF4 sometimes reports permission errors when the underlying HDF5 library cannot open/replace a corrupted file.

**Fix** (two-part):

1. **Removed the corrupted file**: `rm data/unified/metocean_brazil_unified_waverys_grid.nc`

2. **Added atomic write** to `save_dataset()` — writes to a `.nc.tmp` file first, then does an atomic rename:
```python
tmp_path = path.with_suffix(".nc.tmp")
ds.to_netcdf(tmp_path, encoding=encoding)
tmp_path.rename(path)   # atomic on POSIX
```
This prevents corrupted output files: if the process is interrupted, only the `.tmp` file is left (can be safely deleted), and the final `.nc` file is either complete or absent.

3. **Added `exc_info=True`** to the error handler for full stack traces in future failures.

**File**: `src/01_data_preparation/preprocessing/interpolate_glorys_to_waverys_grid.py`

---

### Issue 3: Slow NetCDF write (~35 min for 1.6 GB)

**When**: Save step, writing the unified dataset.

**Not a bug**, but worth documenting. The dataset has 5 variables × 12,053 timesteps × 206 lat × 136 lon. With zlib compression (complevel=4), the write took ~35 minutes. This is expected for the data size and compression level.

**Uncompressed size estimate**: ~5 × 12053 × 206 × 136 × 4 bytes ≈ 67 GB  
**Compressed output**: 1.6 GB (24:1 ratio — high because most of tide_daily_max and SSH_total are NaN outside the 984 coastal cells).

**Trade-off**: Lower `complevel` (e.g., 1) would be faster but produce a ~3–4 GB file. Level 4 is a good balance for storage vs write time.

---

## Performance reference

| Phase | Duration |
|-------|----------|
| Load GLORYS (396 files via `open_mfdataset`) | ~4 s |
| Load WAVERYS (396 files via `open_mfdataset`) | ~3 s |
| WAVERYS to memory + daily resample | ~40 s |
| Spatial interpolation (GLORYS → WAVERYS grid) | < 1 s |
| Tide computation (984 points × 12053 days, 100 workers) | ~8 min (first run); 0 s (cached) |
| SSH_total computation | ~10 s |
| Save to NetCDF (zlib-4, 1.6 GB) | ~35 min |
| **Total (first run)** | **~45 min** |
| **Total (with tide cache)** | **~36 min** |

---

## Tide cache

The tide cache is saved at `data/cache/tide_daily_max_cache.nc` and contains the pre-computed FES2022 daily-max tides for all 984 coastal grid points. This cache is valid **only** for the same grid dimensions and time range. If the input domain changes, the cache will be automatically discarded (see Issue 1 fix).

Cache size: ~62 MB (full Brazil grid).
