# DOWNLOAD_LOG.md — CMEMS Data Acquisition: Issues and Solutions

Log of problems encountered during data download and the fixes applied.

---

## Production download: full Brazil (April 2026)

**Config**: `config/download_config_brazil_full.yml`  
**Domain**: [-35°S, +6°N] × [-55°W, -28°W]  
**Period**: 1993-01 to 2025-12  
**Products**: GLORYS (zos) + WAVERYS (VHM0, VMDR)  
**Total**: 792 monthly files (396 per product)  
**Final size**: 14.38 GB  

---

### Issue 1: `ModuleNotFoundError: No module named 'src.acquisition'`

**When**: First attempt to run `download_cmems_parallel.py`

**Cause**: The script had `sys.path.insert(0, str(Path(__file__).resolve().parents[2]))` which pointed to `src/`, then imported `from src.acquisition.download_cmems import load_config`. This tried to resolve `src/src/acquisition/` which doesn't exist. The path math was wrong because the script moved from `src/acquisition/` to `src/01_data_preparation/acquisition/` during a restructure but the `sys.path` insert wasn't updated.

**Fix**: Changed to:
```python
sys.path.insert(0, str(Path(__file__).resolve().parent))
from download_cmems import load_config
```
Direct sibling import — works regardless of how the script is invoked.

---

### Issue 2: `force_download` deprecated in copernicusmarine >= 2.x

**When**: Download start, visible in logs as:
```
WARNING - 'force_download' has been deprecated.
```

**Cause**: The `copernicusmarine.subset()` call used `force_download=True`, which was the old parameter name. In the current version, it's been replaced by `overwrite=True`.

**Impact**: Without `overwrite=True`, re-downloading the same month creates a new file with suffix `_(1).nc` instead of overwriting. This is also the root cause of the 3 duplicate files found in the SC download.

**Fix**: Replaced `force_download=True` → `overwrite=True` in both:
- `download_cmems_parallel.py`
- `download_cmems.py`

---

### Issue 3: No logs appearing in `nohup.out`

**When**: After launching with `nohup ... &`

**Cause**: Python buffers stdout/stderr when not connected to a terminal (i.e., when redirected to a file). The logging handler writes to `sys.stdout`, but the buffer is never flushed until it fills up (~8 KB) or the process exits.

**Fix**: Added line-buffering at script startup:
```python
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(line_buffering=True)
```
Also set explicit flush on the logging handler:
```python
_handler = logging.StreamHandler(sys.stdout)
_handler.flush = sys.stdout.flush
```

**Alternative**: Run with `python -u` flag (unbuffered), or use `PYTHONUNBUFFERED=1`.

---

### Issue 4: 55 immediate failures with empty error string (rate limiting)

**When**: First run with `--workers 100`

**Cause**: Launching 100 concurrent `copernicusmarine.subset()` calls simultaneously overwhelmed the CMEMS server (Cloudferro S3 backend). The server returned errors or empty responses for ~55 of the first batch. The `except` clause captured the exception but `str(exc)` was empty.

**Symptoms**:
- Tasks marked "failed" with `"error": ""` in status JSON
- Tasks completed in 8–10 seconds (too fast for a real download)
- No files created on disk

**Fix** (two-part):

1. **Reduced workers to 15**: CMEMS handles 15 concurrent connections well without throttling. Even at 15, the download rate was ~13 files/min for GLORYS (~10 MB each) and ~4 files/min for WAVERYS (~26 MB each).

2. **Added retry logic with exponential backoff** (5 retries, base delay 10s):
```python
MAX_RETRIES = 5
RETRY_BASE_DELAY = 10  # seconds

for attempt in range(1, MAX_RETRIES + 1):
    # ... try download ...
    if out.exists() and out.stat().st_size > 100_000:
        # success
    else:
        # retry with backoff
    delay = RETRY_BASE_DELAY * (2 ** (attempt - 1)) + random.uniform(0, 5)
    time.sleep(delay)
```

Also added **output validation**: after `subset()` returns, check that the file exists and is > 100 KB. This catches silent failures where the library returns without error but creates a truncated file.

---

### Issue 5: Connection pool warnings (non-fatal)

**When**: During parallel downloads

**Symptoms**:
```
WARNING - urllib3.connectionpool — Connection pool is full, discarding connection: s3.waw3-1.cloudferro.com. Connection pool size: 10
```

**Cause**: Each `copernicusmarine.subset()` call creates its own HTTP connections. With 15 workers, the shared connection pool hits its size limit and drops idle connections.

**Impact**: None — downloads proceed normally. This is purely cosmetic noise.

**Mitigation**: Not addressed. Could be suppressed by setting the urllib3 logger to ERROR level, but the warnings are harmless and sometimes useful for diagnosing actual connection problems.

---

### Issue 6: Stale temp files from killed downloads

**When**: After killing the process while downloads were in progress

**Symptoms**: Files like `glorys_zos_1993-06.nc.4q14qay_` (~17 KB) in `data/raw/glorys/`. These are partial HDF5 files created by `copernicusmarine` before the atomic rename.

**Fix**: Manually removed with:
```bash
rm -f data/raw/glorys/*.nc.* data/raw/waverys/*.nc.*
```
These temp files are not valid NetCDF and would be ignored by the preprocessing script's `open_mfdataset` glob anyway (it only matches `*.nc`).

---

## Performance reference

| Metric | Value |
|--------|-------|
| Workers | 15 |
| GLORYS files | 396 |
| GLORYS size | 3.87 GB (9–10 MB/file) |
| WAVERYS files | 396 |
| WAVERYS size | 10.51 GB (24–27 MB/file) |
| Total download | 14.38 GB |
| Total retries | 2 (both succeeded) |
| Permanent failures | 0 |
| Total time | ~75 min |
| Effective rate | ~3.2 GB/hr |

**Recommended workers**: 10–20 for reliable throughput without CMEMS throttling.

---

## SC-domain files (reference)

The initial SC-domain download ([-30,−20°S] × [-50,−40°W]) produced data that was
later moved to `data/raw/glorys_sc/` and `data/raw/waverys_sc/`. These files are
preserved for test fixture generation and reference but are not part of the
production pipeline.

See `PIPELINE_SETUP.md` for the full context.
