"""
build_test_fixture.py
---------------------
Extract a small, versionable test fixture from existing GLORYS and WAVERYS
NetCDF files on disk (no re-download).

The output is written to data/test/ as compressed float32 NetCDF files
small enough to be committed directly to the repository (~100–500 KB each).

Two spatial selection modes:
  bbox   — extract all grid points within a bounding box
  points — extract the nearest grid point to each named location

Usage:
    # Use default config
    python src/acquisition/build_test_fixture.py

    # Use a custom config
    python src/acquisition/build_test_fixture.py --config config/test_fixture.yml

    # Override source patterns from CLI
    python src/acquisition/build_test_fixture.py \\
        --glorys-pattern "/remote/glorys/*.nc" \\
        --waverys-pattern "/remote/waverys/*.nc"

    # Dry run (inspect files and config without writing anything)
    python src/acquisition/build_test_fixture.py --dry-run

    # Override output directory
    python src/acquisition/build_test_fixture.py --output-dir data/test
"""

from __future__ import annotations

import argparse
import calendar
import json
import logging
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import NamedTuple

import numpy as np
import xarray as xr
import yaml

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("osr11.fixture")

DEFAULT_CONFIG = Path("config/test_fixture.example.yml")

# Known coordinate name aliases (to handle different conventions)
_TIME_ALIASES = ["time"]
_LAT_ALIASES  = ["latitude", "lat", "nav_lat", "y"]
_LON_ALIASES  = ["longitude", "lon", "nav_lon", "x"]


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def load_config(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"Config file not found: {path}\n"
            "Copy config/test_fixture.example.yml to config/test_fixture.yml and edit."
        )
    with open(path) as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

def find_files(pattern: str) -> list[Path]:
    """Expand a glob pattern and return sorted list of matching files."""
    files = sorted(Path(".").glob(pattern)) if not Path(pattern).is_absolute() \
        else sorted(Path("/").glob(pattern.lstrip("/")))
    # Also try as absolute path directly
    if not files:
        import glob as _glob
        files = sorted(Path(p) for p in _glob.glob(pattern))
    if not files:
        raise FileNotFoundError(
            f"No files matched pattern: {pattern}\n"
            "Check the 'sources' section in your config file."
        )
    log.info("Found %d file(s) matching: %s", len(files), pattern)
    return files


def filter_files_by_period(files: list[Path], start: str, end: str) -> list[Path]:
    """
    Pre-filter files by parsing YYYY-MM from their filename.
    This avoids opening every file when only a subset is needed.
    Falls back to returning all files if the filename pattern doesn't match.
    """
    import re
    rx      = re.compile(r"(\d{4})-(\d{2})")
    start_d = date.fromisoformat(start)
    end_d   = date.fromisoformat(end)

    filtered: list[Path] = []
    for f in files:
        m = rx.search(f.name)
        if not m:
            log.debug("Cannot parse date from filename '%s' — keeping all files.", f.name)
            return files  # unparseable → return all and let xarray filter
        year, month = int(m.group(1)), int(m.group(2))
        last_day    = calendar.monthrange(year, month)[1]
        file_start  = date(year, month, 1)
        file_end    = date(year, month, last_day)
        if file_end >= start_d and file_start <= end_d:
            filtered.append(f)

    if not filtered:
        raise ValueError(
            f"No files overlap with the test period {start} → {end}.\n"
            "Extend the period or check that the source files cover this range."
        )
    log.info("Filtered to %d file(s) covering %s → %s", len(filtered), start, end)
    return filtered


# ---------------------------------------------------------------------------
# Coordinate detection
# ---------------------------------------------------------------------------

class CoordNames(NamedTuple):
    time: str
    lat:  str
    lon:  str


def detect_coords(ds: xr.Dataset) -> CoordNames:
    """
    Detect actual coordinate names in the dataset.
    Raises ValueError with a helpful message if any are missing.
    """
    def _find(aliases: list[str], role: str) -> str:
        for name in aliases:
            if name in ds.coords or name in ds.dims:
                return name
        raise ValueError(
            f"Cannot detect '{role}' coordinate in dataset.\n"
            f"Available coordinates: {list(ds.coords)}\n"
            f"Tried aliases: {aliases}"
        )

    return CoordNames(
        time = _find(_TIME_ALIASES, "time"),
        lat  = _find(_LAT_ALIASES,  "latitude"),
        lon  = _find(_LON_ALIASES,  "longitude"),
    )


# ---------------------------------------------------------------------------
# Spatial selection
# ---------------------------------------------------------------------------

def subset_bbox(ds: xr.Dataset, coords: CoordNames, bbox: dict) -> xr.Dataset:
    """Subset dataset to a bounding box (inclusive)."""
    lon_min = bbox["lon_min"]
    lon_max = bbox["lon_max"]
    lat_min = bbox["lat_min"]
    lat_max = bbox["lat_max"]

    subset = ds.sel(
        {
            coords.lat: slice(lat_min, lat_max),
            coords.lon: slice(lon_min, lon_max),
        }
    )
    if subset[coords.lat].size == 0 or subset[coords.lon].size == 0:
        raise ValueError(
            f"Spatial selection returned an empty dataset.\n"
            f"bbox={bbox}\n"
            f"Dataset lat range: [{float(ds[coords.lat].min()):.2f}, "
            f"{float(ds[coords.lat].max()):.2f}]\n"
            f"Dataset lon range: [{float(ds[coords.lon].min()):.2f}, "
            f"{float(ds[coords.lon].max()):.2f}]"
        )
    return subset


def subset_points(
    ds: xr.Dataset,
    coords: CoordNames,
    points: list[dict],
) -> xr.Dataset:
    """
    Extract the nearest grid point to each named location and return a
    dataset with a new 'station' dimension.
    """
    slices = []
    for pt in points:
        name = pt["name"]
        lat  = pt["lat"]
        lon  = pt["lon"]
        pt_ds = ds.sel(
            {coords.lat: lat, coords.lon: lon},
            method="nearest",
        ).expand_dims({"station": [name]})
        slices.append(pt_ds)
        actual_lat = float(pt_ds[coords.lat])
        actual_lon = float(pt_ds[coords.lon])
        log.info(
            "Point '%s': requested (%.3f, %.3f) → nearest (%.3f, %.3f)",
            name, lat, lon, actual_lat, actual_lon,
        )

    combined = xr.concat(slices, dim="station")
    return combined


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

def downcast_and_compress(ds: xr.Dataset) -> tuple[xr.Dataset, dict]:
    """Return dataset with float64 → float32, plus NetCDF encoding dict."""
    ds = ds.copy()
    encoding: dict = {}

    for var in ds.data_vars:
        if ds[var].dtype == np.float64:
            ds[var] = ds[var].astype(np.float32)
        fill = float(np.finfo(np.float32).min) if np.issubdtype(ds[var].dtype, np.floating) else None
        enc: dict = {"zlib": True, "complevel": 4}
        if fill is not None:
            enc["_FillValue"] = fill
        encoding[var] = enc

    return ds, encoding


def save_fixture(ds: xr.Dataset, path: Path, dry_run: bool = False) -> int:
    """Save dataset as compressed NetCDF4. Returns file size in bytes."""
    ds, encoding = downcast_and_compress(ds)

    if dry_run:
        log.info("[dry-run] Would save: %s  shape=%s", path, dict(ds.sizes))
        return 0

    path.parent.mkdir(parents=True, exist_ok=True)
    ds.to_netcdf(str(path), encoding=encoding, format="NETCDF4")
    size = path.stat().st_size
    log.info("Saved: %s  (%.1f KB)", path, size / 1024)
    return size


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------

def write_provenance(
    output_dir: Path,
    config: dict,
    results: list[dict],
    dry_run: bool,
) -> None:
    if dry_run:
        return
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config":       config,
        "outputs":      results,
    }
    out = output_dir / "fixture_provenance.json"
    out.write_text(json.dumps(manifest, indent=2, default=str))
    log.info("Provenance: %s", out)


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def print_summary(results: list[dict]) -> None:
    print("\n" + "=" * 60)
    print("  TEST FIXTURE SUMMARY")
    print("=" * 60)
    for r in results:
        print(f"\n  Product  : {r['product']}")
        print(f"  Source   : {r['source_pattern']}")
        print(f"  Files    : {r['n_files']} opened")
        print(f"  Variables: {r['variables']}")
        print(f"  Period   : {r['time_start']} → {r['time_end']}  ({r['n_time']} steps)")
        print(f"  Domain   : lon [{r['lon_min']:.2f}, {r['lon_max']:.2f}]"
              f"  lat [{r['lat_min']:.2f}, {r['lat_max']:.2f}]")
        print(f"  Shape    : {r['shape']}")
        print(f"  Output   : {r['output_file']}  ({r['size_kb']:.1f} KB)")
    print("=" * 60 + "\n")


# ---------------------------------------------------------------------------
# Core pipeline per product
# ---------------------------------------------------------------------------

def build_one_fixture(
    *,
    product: str,
    pattern: str,
    variables: list[str],
    period: dict,
    spatial_mode: str,
    bbox: dict | None,
    points: list[dict] | None,
    output_path: Path,
    dry_run: bool,
) -> dict:
    """Full pipeline for one product (glorys or waverys). Returns summary dict."""
    # 1 — discover and pre-filter files
    files   = find_files(pattern)
    files   = filter_files_by_period(files, period["start"], period["end"])

    # 2 — open lazily
    log.info("Opening %d file(s) lazily for %s …", len(files), product)
    ds = xr.open_mfdataset(
        [str(f) for f in files],
        combine     = "by_coords",
        data_vars   = "minimal",
        coords      = "minimal",
        compat      = "override",
        engine      = "netcdf4",
    )

    # 3 — select only the requested variables
    available = list(ds.data_vars)
    missing   = [v for v in variables if v not in available]
    if missing:
        raise ValueError(
            f"Variable(s) {missing} not found in {product} dataset.\n"
            f"Available: {available}"
        )
    ds = ds[variables]

    # 4 — detect coordinates
    coords = detect_coords(ds)
    log.info("Coordinates detected: time=%s lat=%s lon=%s", coords.time, coords.lat, coords.lon)

    # 5 — temporal subset
    ds = ds.sel({coords.time: slice(period["start"], period["end"])})
    if ds[coords.time].size == 0:
        raise ValueError(
            f"Temporal selection returned empty dataset for {product}.\n"
            f"Period: {period['start']} → {period['end']}"
        )

    # 6 — spatial subset
    if spatial_mode == "bbox":
        if not bbox:
            raise ValueError("spatial_mode='bbox' but no bbox defined in config.")
        ds = subset_bbox(ds, coords, bbox)
    elif spatial_mode == "points":
        if not points:
            raise ValueError("spatial_mode='points' but no points defined in config.")
        ds = subset_points(ds, coords, points)
    else:
        raise ValueError(f"Unknown spatial_mode: '{spatial_mode}'. Use 'bbox' or 'points'.")

    # 7 — load into memory (only the subsetted data)
    log.info("Loading subset into memory for %s …", product)
    ds = ds.load()

    # 8 — build summary info before saving
    lat_coord = ds[coords.lat].values
    lon_coord = ds[coords.lon].values
    time_vals = ds[coords.time].values
    summary = {
        "product":        product,
        "source_pattern": pattern,
        "n_files":        len(files),
        "variables":      variables,
        "time_start":     str(time_vals[0])[:10],
        "time_end":       str(time_vals[-1])[:10],
        "n_time":         int(ds[coords.time].size),
        "lat_min":        float(lat_coord.min()),
        "lat_max":        float(lat_coord.max()),
        "lon_min":        float(lon_coord.min()),
        "lon_max":        float(lon_coord.max()),
        "shape":          dict(ds.sizes),
        "output_file":    str(output_path),
        "size_kb":        0.0,
    }

    # 9 — save
    size_bytes = save_fixture(ds, output_path, dry_run=dry_run)
    summary["size_kb"] = size_bytes / 1024

    return summary


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Build small test fixtures from existing GLORYS/WAVERYS NetCDF files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--config", "-c", type=Path, default=DEFAULT_CONFIG)
    p.add_argument("--glorys-pattern",  type=str, default=None,
                   help="Override glob pattern for GLORYS source files.")
    p.add_argument("--waverys-pattern", type=str, default=None,
                   help="Override glob pattern for WAVERYS source files.")
    p.add_argument("--output-dir", type=Path, default=None,
                   help="Override output directory.")
    p.add_argument("--product", "-p",
                   choices=["glorys", "waverys", "both"], default="both",
                   help="Which fixture to build.")
    p.add_argument("--dry-run", action="store_true",
                   help="Inspect and validate without writing files.")
    return p.parse_args()


def main() -> None:
    args   = parse_args()
    cfg    = load_config(args.config)

    period       = cfg["test_period"]
    spatial_mode = cfg.get("spatial_mode", "bbox")
    bbox         = cfg.get("bbox")
    points       = cfg.get("points")
    output_dir   = args.output_dir or Path(cfg.get("output_dir", "data/test"))

    if args.dry_run:
        log.info("DRY RUN — no files will be written.")

    results: list[dict] = []

    for product in ("glorys", "waverys"):
        if args.product not in (product, "both"):
            continue

        src_cfg  = cfg["sources"][product]
        pattern  = (
            args.glorys_pattern  if product == "glorys"  and args.glorys_pattern
            else args.waverys_pattern if product == "waverys" and args.waverys_pattern
            else src_cfg["pattern"]
        )
        variables    = src_cfg["variables"]
        output_path  = output_dir / f"{product}_sc_sul_test.nc"

        log.info("--- Building fixture: %s ---", product)
        try:
            summary = build_one_fixture(
                product      = product,
                pattern      = pattern,
                variables    = variables,
                period       = period,
                spatial_mode = spatial_mode,
                bbox         = bbox,
                points       = points,
                output_path  = output_path,
                dry_run      = args.dry_run,
            )
            results.append(summary)
        except Exception as exc:
            log.error("Failed to build fixture for %s: %s", product, exc)
            sys.exit(1)

    print_summary(results)
    write_provenance(output_dir, cfg, results, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
