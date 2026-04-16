"""
OSR11 source package.

Registers numbered analysis directories under their non-numbered import
aliases so that ``from src.xxx import`` statements continue to work after
directories are renamed to ``01_xxx``, ``02_xxx``, etc.

Directory structure (after March 2026 refactoring):
----------------------------------------------------
src/
├── 01_data_preparation/          # STEP 1 — Data Preparation
│   ├── acquisition/              #   Download CMEMS data
│   └── preprocessing/            #   Harmonization, interpolation
└── 02_threshold_calibration/     # STEP 2 — Threshold Calibration (umbrella)
    ├── 01_exploratory_data_analysis/   # Sub-step 2a — EDA
    ├── 02_preliminary_compound/        # Sub-step 2b — Preliminary analysis
    ├── 03_tidal_sensitivity/           # Sub-step 2c — Tidal sensitivity
    ├── 04_csi_grid_scan/               # Sub-step 2d — CSI grid scan
    └── 05_pu_composite_calibration/    # Sub-step 2e — PU composite calibration

Adding a new numbered module:
    1. Create the directory (or git mv).
    2. Add an entry to _MODULE_ALIASES below — that is all.
"""
import importlib.util
import sys
from pathlib import Path

_src_dir = Path(__file__).parent

# alias (importable name) → real directory path (relative to src/)
# Supports nested paths for Step 2 sub-modules.
_MODULE_ALIASES: dict[str, str] = {
    # STEP 1 — Data Preparation
    "data_preparation":           "01_data_preparation",
    "acquisition":                "01_data_preparation/acquisition",
    "preprocessing":              "01_data_preparation/preprocessing",

    # STEP 2 — Threshold Calibration (umbrella)
    "threshold_calibration_umbrella": "02_threshold_calibration",

    # STEP 2 sub-steps (legacy aliases for backward compatibility)
    # NOTE: "threshold_calibration" intentionally maps to 04_csi_grid_scan (not the
    # umbrella) because all existing `from src.threshold_calibration.*` imports are
    # inside 04_csi_grid_scan files and reference modules within that directory.
    "threshold_calibration":      "02_threshold_calibration/04_csi_grid_scan",
    "exploratory_data_analysis":  "02_threshold_calibration/01_exploratory_data_analysis",
    "explore_test_data_south_sc": "02_threshold_calibration/01_exploratory_data_analysis",  # legacy
    "preliminary_compound":       "02_threshold_calibration/02_preliminary_compound",
    "tidal_sensitivity":          "02_threshold_calibration/03_tidal_sensitivity",
    "csi_grid_scan":              "02_threshold_calibration/04_csi_grid_scan",
    "pu_composite_calibration":   "02_threshold_calibration/05_pu_composite_calibration",

    # STEP 3 — Storm Catalog Generation / Hazard Characterization
    "storm_catalog_generation":   "03_storm_catalog_generation",
    "storm_catalogs":             "03_storm_catalog_generation/01_storm_catalogs",
    "compound_detection":         "03_storm_catalog_generation/02_compound_detection",
    "duration_persistence":       "03_storm_catalog_generation/03_duration_persistence",
    "monthly_seasonality":        "03_storm_catalog_generation/04_monthly_seasonality",
    "trends":                     "03_storm_catalog_generation/05_trends",
    "univariate_eva":             "03_storm_catalog_generation/06_univariate_eva",
    "dependence":                 "03_storm_catalog_generation/07_dependence",
    "site_export":                "03_storm_catalog_generation/08_site_export",
    "shared":                     "03_storm_catalog_generation/shared",
}


def _register_numbered_modules() -> None:
    for alias, real_path in _MODULE_ALIASES.items():
        real_dir  = _src_dir / real_path
        init_file = real_dir / "__init__.py"
        if not init_file.exists():
            continue
        pkg_key = f"src.{alias}"
        if pkg_key in sys.modules:
            continue
        spec = importlib.util.spec_from_file_location(
            pkg_key,
            str(init_file),
            submodule_search_locations=[str(real_dir)],
        )
        if spec is None:
            continue
        mod = importlib.util.module_from_spec(spec)
        sys.modules[pkg_key] = mod
        spec.loader.exec_module(mod)  # type: ignore[union-attr]


_register_numbered_modules()
