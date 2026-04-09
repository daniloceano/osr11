"""
Utility helpers for Step 2e — PU Composite Calibration.

Provides data loading, output directory management, and logging helpers.
All functions are self-contained and do not depend on other Step 2e modules.

Loading the expanded events database
-------------------------------------
The expanded events CSV (`ressaca_sc_eventos_sc_1998_2020_consolidated_expandido.csv`)
uses a different schema than the legacy Leal et al. database. The column "city"
maps to "municipality" throughout this codebase. Synthetic integer disaster_ids
(1, 2, …, N) are assigned so that build_event_records() from the preliminary_compound
module can be called without modification.

Loading the legacy events database
------------------------------------
The legacy CSV is loaded with minimal cleaning for use as a corroborating evidence
source in the E_i calculation (audit.py). Only disaster_id, municipality, date, and
coastal_sector are required from the legacy database.

Combined positive-event framework (Step 2e v2)
----------------------------------------------
Step 2e uses BOTH databases as its positive set P. load_combined_events() produces
the union of expanded (56 events, 14 cities) and legacy (91 events, 22 cities),
deduplicated on exact (municipality, date) matches, yielding 147 unique
(municipality, date) pairs from 27 unique municipalities.

  N_union_cities = 27
  B_target_effective = 12 × 27 = 324 ep/yr (from combined)

Near-matches (within ±3 days at the same municipality across databases) are retained
as separate events and flagged in the provenance table. Two near-matches were found
at Florianópolis (see tab_TC5_event_provenance.csv).

Note on unmapped municipalities
---------------------------------
Four cities from the expanded database (Biguaçu, Imbituba, Joinville, Laguna)
are not present in municipality_grid_ref.csv and therefore have no valid grid
associations. Events at these cities are included in the provenance table but
will be dropped by build_event_records() and cannot contribute to hits. They
represent structural misses — real events that the current grid coverage cannot
detect. P for scoring is set to len(records) (evaluable events only).
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

log = logging.getLogger(__name__)


# ── Output directory management ──────────────────────────────────────────────

def make_output_dirs(cfg: dict) -> None:
    """Create all Step 2e output directories if they don't exist.

    Parameters
    ----------
    cfg : dict
        Configuration dictionary from analysis_config.CFG.
    """
    dirs = [
        cfg["output_root"],
        cfg["fig_dir"],
        cfg["fig_summary_dir"],
        cfg["tab_dir"],
        cfg["log_dir"],
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    log.debug("Output directories ready: %s", cfg["output_root"])


# ── Threshold grid ────────────────────────────────────────────────────────────

def build_percentile_levels(start: float, stop: float, step: float) -> list[float]:
    """Generate a list of percentile levels from start to stop (inclusive).

    Parameters
    ----------
    start, stop : float
        First and last percentile (e.g., 0.50 and 0.90).
    step : float
        Step size (e.g., 0.05 for 5 percentile-point increments).

    Returns
    -------
    list of float, each rounded to 10 decimal places to avoid float drift.
    """
    levels = np.arange(start, stop + step * 0.5, step)
    return [round(float(v), 10) for v in levels]


# ── Data loading: expanded events (Step 2e primary) ──────────────────────────

def load_expanded_events(path: Path) -> pd.DataFrame:
    """Load the expanded documentary coastal-impact database.

    Source file: ressaca_sc_eventos_sc_1998_2020_consolidated_expandido.csv
    Schema: city, date, coastal_sector, source_title, source_url, notes

    Returns a DataFrame with columns:
        disaster_id   – synthetic int (row index + 1, for compatibility with
                        build_event_records() which reads int(row["disaster_id"]))
        municipality  – string, renamed from "city"
        date          – pd.Timestamp
        coastal_sector
        source_title
        source_url
        notes

    Raises
    ------
    FileNotFoundError
        If the CSV does not exist.
    ValueError
        If required columns are absent or no valid rows remain after cleaning.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Expanded events database not found: {path}\n"
            "Expected: data/reported events/"
            "ressaca_sc_eventos_sc_1998_2020_consolidated_expandido.csv"
        )

    df = pd.read_csv(path)

    # Rename "city" → "municipality" for consistency with the rest of the codebase
    if "city" in df.columns:
        df = df.rename(columns={"city": "municipality"})
    elif "municipality" not in df.columns:
        raise ValueError(
            f"Expanded events CSV must have a 'city' or 'municipality' column. "
            f"Found columns: {list(df.columns)}"
        )

    # Require date
    if "date" not in df.columns:
        raise ValueError(
            f"Expanded events CSV must have a 'date' column. "
            f"Found columns: {list(df.columns)}"
        )

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["municipality", "date"]).reset_index(drop=True)

    if df.empty:
        raise ValueError(
            "Expanded events database is empty after removing rows with missing "
            "municipality or date."
        )

    # Assign synthetic disaster_id (row index + 1, 1-based)
    df.insert(0, "disaster_id", range(1, len(df) + 1))

    # Optional columns — fill with empty string if absent
    for col in ["coastal_sector", "source_title", "source_url", "notes"]:
        if col not in df.columns:
            df[col] = ""

    log.info(
        "Expanded events loaded: %d records | %d municipalities | %s to %s",
        len(df),
        df["municipality"].nunique(),
        df["date"].min().date(),
        df["date"].max().date(),
    )
    return df


# ── Data loading: legacy events (used as E_i evidence source) ────────────────

def load_legacy_events(path: Path) -> pd.DataFrame:
    """Load the legacy Leal et al. (2024) Civil Defense database.

    Used exclusively as a corroborating evidence source for E_i in audit.py.
    Only returns disaster_id, municipality, date, and coastal_sector.

    The legacy CSV uses English column headers with spaces. This loader performs
    minimal cleaning (column rename, date parse, string strip).

    Parameters
    ----------
    path : Path
        Path to reported_events_Karine_sc.csv.

    Returns
    -------
    DataFrame with columns [disaster_id, municipality, date, coastal_sector].
    """
    path = Path(path)
    if not path.exists():
        log.warning(
            "Legacy events file not found: %s — E_i will be 0 for all episodes "
            "(no legacy corroboration available).",
            path,
        )
        return pd.DataFrame(columns=["disaster_id", "municipality", "date", "coastal_sector"])

    df = pd.read_csv(path)

    rename = {
        "Disaster ID":                      "disaster_id",
        "Dates of occurrence (mm/dd/yyyy)": "date",
        "Municipalities":                   "municipality",
        "Coastal Sectors":                  "coastal_sector",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})

    for col in ["municipality", "coastal_sector"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().replace("nan", pd.NA)

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["disaster_id", "municipality", "date"]).reset_index(drop=True)

    # Keep only needed columns
    keep = ["disaster_id", "municipality", "date", "coastal_sector"]
    df = df[[c for c in keep if c in df.columns]]

    log.info(
        "Legacy events loaded: %d rows | %d unique disaster IDs | %d municipalities",
        len(df),
        df["disaster_id"].nunique() if "disaster_id" in df.columns else 0,
        df["municipality"].nunique(),
    )
    return df


# ── Data loading: combined positive-event set ────────────────────────────────

def load_combined_events(
    expanded_path: Path,
    legacy_path: Path,
    near_match_window_days: int = 3,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load and combine the expanded and legacy event databases into a unified positive set.

    The combined positive set is the UNION of both databases, deduplicated on
    exact (municipality, date) matches. Near-matches within ±near_match_window_days
    at the same municipality but across databases are retained as separate events
    and flagged in the provenance table.

    Parameters
    ----------
    expanded_path : Path
        Path to ressaca_sc_eventos_sc_1998_2020_consolidated_expandido.csv (56 events).
    legacy_path : Path
        Path to reported_events_Karine_sc.csv (91 events).
    near_match_window_days : int
        Window in days for near-match flagging (default 3, matching the causal window).

    Returns
    -------
    combined_df : pd.DataFrame
        Union of both databases. Columns:
            disaster_id  — new sequential integer (1-based, re-assigned after merge)
            municipality — string
            date         — pd.Timestamp
            coastal_sector
            source       — "expanded" | "legacy" | "both"
        Rows with source="both" indicate exact (municipality, date) duplicates;
        only one copy is retained (the expanded-database row takes priority).
    provenance_df : pd.DataFrame
        Audit table with columns:
            municipality, date, source, near_match_flag (bool)
        near_match_flag is True if another event from the OTHER database exists
        at the same municipality within ±near_match_window_days.

    Notes
    -----
    With 0 exact (municipality, date) overlaps between the two databases
    (confirmed by prior analysis), the combined set has 56 + 91 = 147 events
    across 27 unique municipalities (union of 14 expanded + 22 legacy).
    Four expanded cities (Biguaçu, Imbituba, Joinville, Laguna) lack grid
    associations and will be dropped by build_event_records().
    """
    # ── Load both databases ────────────────────────────────────────────────────
    exp_df = load_expanded_events(expanded_path)
    leg_df = load_legacy_events(legacy_path)

    # Tag source before merge
    exp_sub = exp_df[["municipality", "date", "coastal_sector"]].copy()
    exp_sub["source"] = "expanded"

    leg_sub = leg_df[["municipality", "date", "coastal_sector"]].copy()
    leg_sub["source"] = "legacy"

    combined = pd.concat([exp_sub, leg_sub], ignore_index=True)

    # ── Deduplicate on exact (municipality, date) ─────────────────────────────
    # Mark both copies of duplicates as "both", then drop the second (legacy) copy.
    # expanded takes priority so that source_title/notes from expanded are kept
    # if we later join back. For now we only care about municipality, date, source.
    dup_mask = combined.duplicated(subset=["municipality", "date"], keep=False)
    combined.loc[dup_mask, "source"] = "both"
    combined = combined.drop_duplicates(
        subset=["municipality", "date"], keep="first"
    ).reset_index(drop=True)

    # ── Near-match detection ───────────────────────────────────────────────────
    # For each pair of events at the same municipality but from different databases,
    # flag those within ±near_match_window_days (exclusive of 0 = exact match).
    near_match = [False] * len(combined)
    # Only cities that appear in BOTH databases can have cross-database near-matches
    exp_cities = set(exp_sub["municipality"].unique())
    leg_cities = set(leg_sub["municipality"].unique())
    shared_cities = exp_cities & leg_cities

    combined["_date_int"] = (combined["date"] - pd.Timestamp("2000-01-01")).dt.days
    for city in shared_cities:
        city_rows = combined[combined["municipality"] == city]
        exp_rows = city_rows[city_rows["source"] == "expanded"]
        leg_rows = city_rows[city_rows["source"] == "legacy"]

        for i_exp in exp_rows.index:
            d_exp = combined.loc[i_exp, "_date_int"]
            for i_leg in leg_rows.index:
                d_leg = combined.loc[i_leg, "_date_int"]
                diff = abs(d_exp - d_leg)
                if 0 < diff <= near_match_window_days:
                    near_match[i_exp] = True
                    near_match[i_leg] = True

    combined["near_match_flag"] = near_match
    combined = combined.drop(columns=["_date_int"])

    # ── Assign new sequential disaster_ids ────────────────────────────────────
    combined.insert(0, "disaster_id", range(1, len(combined) + 1))

    # ── Build provenance table (for audit export) ─────────────────────────────
    provenance_df = combined[
        ["municipality", "date", "source", "near_match_flag"]
    ].copy()

    # ── Remove near_match_flag from the returned combined_df ─────────────────
    combined_out = combined.drop(columns=["near_match_flag"])

    # ── Logging ───────────────────────────────────────────────────────────────
    n_muni    = combined_out["municipality"].nunique()
    n_nm      = int(sum(near_match))
    n_exp     = int((combined_out["source"].isin(["expanded", "both"])).sum())
    n_leg     = int((combined_out["source"].isin(["legacy",   "both"])).sum())
    n_both    = int((combined_out["source"] == "both").sum())
    log.info(
        "Combined events: %d total "
        "(exp=%d, leg=%d, exact-both=%d) | %d municipalities | "
        "%s to %s | %d near-matches flagged (±%dd)",
        len(combined_out), n_exp, n_leg, n_both,
        n_muni,
        combined_out["date"].min().date(),
        combined_out["date"].max().date(),
        n_nm, near_match_window_days,
    )

    return combined_out, provenance_df


# ── Data loading: unified metocean dataset ────────────────────────────────────

def load_unified_dataset(path: Path) -> xr.Dataset:
    """Load the unified daily metocean dataset and validate key variables.

    Parameters
    ----------
    path : Path
        Path to metocean_sc_full_unified_waverys_grid.nc.

    Returns
    -------
    xr.Dataset with at least VHM0 and zos variables.

    Raises
    ------
    FileNotFoundError, ValueError
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Unified metocean dataset not found: {path}\n"
            "Run src/01_data_preparation/preprocessing first."
        )

    ds = xr.open_dataset(path)

    required = {"VHM0", "zos"}
    missing = required - set(ds.data_vars)
    if missing:
        raise ValueError(
            f"Unified dataset is missing required variable(s): {missing}. "
            f"Available: {list(ds.data_vars)}"
        )

    log.info(
        "Unified dataset: %d days | %d lat × %d lon | %s to %s",
        ds.sizes["time"],
        ds.sizes.get("latitude", ds.sizes.get("lat", "?")),
        ds.sizes.get("longitude", ds.sizes.get("lon", "?")),
        str(ds.time.values[0])[:10],
        str(ds.time.values[-1])[:10],
    )
    return ds


# ── Logging ───────────────────────────────────────────────────────────────────

def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logger with a human-readable formatter.

    Safe to call multiple times; only adds a handler if none is present.
    """
    root = logging.getLogger()
    if root.handlers:
        return  # already configured
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s  %(levelname)-8s  %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    root.setLevel(level)
    root.addHandler(handler)
