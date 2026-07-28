r"""Audit of the compound-intensity definition: superseded vs adopted.

Context
-------
Until 2026-07-27 the compound intensity rescaled the **absolute** peaks of each
event by the 5th/95th percentiles of all peaks pooled over the domain. That
metric was superseded because the absolute sea-level peak is almost entirely
determined by the local tidal regime — regressing the mean SSH_total peak of a
grid point on its own q90 threshold gives R^2 = 0.998, and in the northern
macrotidal sector 91% of the peak is that baseline. The sea-level term
therefore encoded the astronomical tide rather than event severity.

The adopted definition, implemented in
``src/03_storm_catalog_generation/02_compound_detection/detection.py``, keeps
the **global** normalization — so the metric stays comparable between grid
points and does not degenerate, as purely local rescalings do — but removes the
local baseline first, using the same q90 threshold that defined the event:

    superseded : 0.5 * [ clip((peak_Hs  - Q05_Hs ) / (Q95_Hs  - Q05_Hs ), 0, 1)
                       + clip((peak_SSH - Q05_SSH) / (Q95_SSH - Q05_SSH), 0, 1) ]

    adopted    : E_Hs  = peak_Hs  - thr_Hs(local)
                 E_SSH = peak_SSH - thr_SSH(local)
                 0.5 * [ clip((E_Hs  - Q05_E_Hs ) / (Q95_E_Hs  - Q05_E_Hs ), 0, 1)
                       + clip((E_SSH - Q05_E_SSH) / (Q95_E_SSH - Q05_E_SSH), 0, 1) ]

The pipeline writes the adopted metric to ``mean_compound_intensity_norm`` and
keeps the superseded one under ``mean_compound_intensity_norm_abspeak``. This
script reproduces both from the raw catalog, checks each against its published
column, and propagates them through the unchanged Hazard Index aggregation of
``src/04_risk_integration/hazard_index.py``:

    H_raw = [ norm_grid(compound_count_total)
            + norm_grid(mean_overlap_duration)
            + norm_grid(intensity) ] / 3
    H     = norm_grid(H_raw)

Figures
-------
Two 2 x 3 coastal panels, using the cartography and palettes of the article
figures. Difference panels are always **superseded − adopted**, so warm colors
mark where the superseded metric was larger.

    explore_intensity_definition_comparison_<date>.png
        (a) intensity, superseded   (d) Hazard Index, superseded
        (b) intensity, adopted      (e) Hazard Index, adopted (published)
        (c) intensity difference    (f) Hazard Index difference

    explore_intensity_component_decomposition_<date>.png
        (a-c) Hs term: superseded, adopted, difference
        (d-f) SSH_total term: superseded, adopted, difference
    Because the intensity is an unweighted mean of the two terms, the change
    splits exactly: dI = 0.5*d(Hs term) + 0.5*d(SSH term).

This is an **exploratory audit**. It does not modify the pipeline, the
published Hazard Index, or any article figure; it only writes to
``outputs/exploratory_intensity_definition_comparison/``.

Run from the repository root:

    python src/exploratory/make_exploratory_intensity_definition_comparison.py
"""
from __future__ import annotations

from datetime import date, datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import cartopy.crs as ccrs
import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.cm import ScalarMappable
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.ticker import FormatStrFormatter
import numpy as np
import pandas as pd
from shapely.geometry import MultiLineString
from shapely.ops import linemerge, unary_union

from src.figures_article.make_article_supplementary_integrated_risk_zooms import (
    COUNTRY_BORDER_COLOR,
    LAND_COLOR,
    OCEAN_COLOR,
    STATE_BORDER_COLOR,
    _natural_earth_context,
    _numeric_stats,
    _relative,
)
from src.risk_integration.coastal_projection import (
    COASTAL_MAP_EXTENT,
    line_parts,
    project_values_to_coastline,
    read_coastal_inputs,
)
from src.risk_integration.hazard_index import (
    NATIVE_GRID_SOURCE,
    _minmax,
    derive_native_hazard_index,
)
from src.risk_integration.palettes import (
    component_colors,
    diverging_colors,
    risk_colors,
)


COMPOUND_CATALOG = ROOT / "outputs" / "storm_catalog" / "compound" / "compound_catalog.json"
COMPOUND_SUMMARY = ROOT / "outputs" / "storm_catalog" / "compound" / "compound_summary.json"

OUTPUT_DIR = ROOT / "outputs" / "exploratory_intensity_definition_comparison"
FIGURE_DIR = OUTPUT_DIR / "figures"
DATA_DIR = OUTPUT_DIR / "data"
METADATA_DIR = OUTPUT_DIR / "metadata"
RUN_DATE = date.today().strftime("%Y%m%d")
FIGURE_PATH = FIGURE_DIR / f"explore_intensity_definition_comparison_{RUN_DATE}.png"
COMPONENT_FIGURE_PATH = (
    FIGURE_DIR / f"explore_intensity_component_decomposition_{RUN_DATE}.png"
)
GRID_DATA_PATH = DATA_DIR / "native_grid_intensity_definition_comparison.csv"
SEGMENT_DATA_PATH = DATA_DIR / "intensity_definition_comparison_segments.geojson"
METADATA_PATH = METADATA_DIR / "explore_intensity_definition_comparison_metadata.json"

EXPLORATORY_DPI = 200
GRID_COLOR = "#9aa9b0"
COAST_COLOR = "#334155"

# Shared class limits so the two definitions are directly comparable.
INTENSITY_BOUNDARIES = np.round(np.arange(0.0, 0.71, 0.1), 2)
HAZARD_BOUNDARIES = np.round(np.linspace(0.0, 1.0, 9), 3)
INTENSITY_DIFF_BOUNDARIES = np.round(np.arange(-0.4, 0.41, 0.1), 2)
HAZARD_DIFF_BOUNDARIES = np.round(np.arange(-0.5, 0.51, 0.1), 2)

FIELDS = (
    "intensity_abspeak",
    "intensity_adopted",
    "intensity_difference",
    "hazard_abspeak",
    "hazard_adopted",
    "hazard_difference",
    "hs_term_abspeak",
    "hs_term_adopted",
    "hs_term_difference",
    "ssh_term_abspeak",
    "ssh_term_adopted",
    "ssh_term_difference",
)

# Shared scales for the component decomposition. Both rows use the SAME
# difference limits so the two components can be compared by eye.
COMPONENT_BOUNDARIES = np.round(np.linspace(0.0, 1.0, 9), 3)
COMPONENT_DIFF_BOUNDARIES = np.round(np.arange(-0.8, 0.81, 0.1), 2)

PANELS = (
    {
        "field": "intensity_abspeak",
        "panel": "A",
        "title": "Intensity — superseded (absolute peaks)",
        "boundaries": INTENSITY_BOUNDARIES,
        "palette": "component",
        "label": "Mean compound intensity (dimensionless)",
        "tick_format": "%.1f",
    },
    {
        "field": "intensity_adopted",
        "panel": "B",
        "title": "Intensity — adopted (excess over local threshold)",
        "boundaries": INTENSITY_BOUNDARIES,
        "palette": "component",
        "label": "Mean compound intensity (dimensionless)",
        "tick_format": "%.1f",
    },
    {
        "field": "intensity_difference",
        "panel": "C",
        "title": "Intensity difference (superseded − adopted)",
        "boundaries": INTENSITY_DIFF_BOUNDARIES,
        "palette": "diverging",
        "label": "Δ intensity (warm: superseded is larger)",
        "tick_format": "%.1f",
    },
    {
        "field": "hazard_abspeak",
        "panel": "D",
        "title": "Hazard Index — superseded intensity",
        "boundaries": HAZARD_BOUNDARIES,
        "palette": "risk",
        "label": "Hazard Index (0–1)",
        "tick_format": "%.2f",
    },
    {
        "field": "hazard_adopted",
        "panel": "E",
        "title": "Hazard Index — adopted intensity (published)",
        "boundaries": HAZARD_BOUNDARIES,
        "palette": "risk",
        "label": "Hazard Index (0–1)",
        "tick_format": "%.2f",
    },
    {
        "field": "hazard_difference",
        "panel": "F",
        "title": "Hazard Index difference (superseded − adopted)",
        "boundaries": HAZARD_DIFF_BOUNDARIES,
        "palette": "diverging",
        "label": "Δ Hazard Index (warm: superseded is larger)",
        "tick_format": "%.1f",
    },
)


COMPONENT_PANELS = (
    {
        "field": "hs_term_abspeak",
        "panel": "A",
        "title": "Hₛ term — superseded (absolute peak)",
        "boundaries": COMPONENT_BOUNDARIES,
        "palette": "component",
        "label": "Normalized Hₛ term (dimensionless)",
        "tick_format": "%.2f",
    },
    {
        "field": "hs_term_adopted",
        "panel": "B",
        "title": "Hₛ term — adopted (excess over threshold)",
        "boundaries": COMPONENT_BOUNDARIES,
        "palette": "component",
        "label": "Normalized Hₛ term (dimensionless)",
        "tick_format": "%.2f",
    },
    {
        "field": "hs_term_difference",
        "panel": "C",
        "title": "Δ Hₛ term (superseded − adopted)",
        "boundaries": COMPONENT_DIFF_BOUNDARIES,
        "palette": "diverging",
        "label": "Δ Hₛ term (warm: superseded is larger)",
        "tick_format": "%.1f",
    },
    {
        "field": "ssh_term_abspeak",
        "panel": "D",
        "title": "SSH_total term — superseded (absolute peak)",
        "boundaries": COMPONENT_BOUNDARIES,
        "palette": "component",
        "label": "Normalized SSH_total term (dimensionless)",
        "tick_format": "%.2f",
    },
    {
        "field": "ssh_term_adopted",
        "panel": "E",
        "title": "SSH_total term — adopted (excess over threshold)",
        "boundaries": COMPONENT_BOUNDARIES,
        "palette": "component",
        "label": "Normalized SSH_total term (dimensionless)",
        "tick_format": "%.2f",
    },
    {
        "field": "ssh_term_difference",
        "panel": "F",
        "title": "Δ SSH_total term (superseded − adopted)",
        "boundaries": COMPONENT_DIFF_BOUNDARIES,
        "palette": "diverging",
        "label": "Δ SSH_total term (warm: superseded is larger)",
        "tick_format": "%.1f",
    },
)


def _palette(kind: str, class_count: int) -> ListedColormap:
    colors = {
        "component": component_colors,
        "diverging": diverging_colors,
        "risk": risk_colors,
    }[kind](class_count)
    return ListedColormap(colors, name=f"{kind}_{class_count}")


def build_intensity_variants() -> tuple[pd.DataFrame, dict[str, Any]]:
    """Recompute both intensity definitions from the compound catalog."""
    if not COMPOUND_CATALOG.exists():
        raise FileNotFoundError(COMPOUND_CATALOG)
    catalog = json.loads(COMPOUND_CATALOG.read_text(encoding="utf-8"))
    published = json.loads(COMPOUND_SUMMARY.read_text(encoding="utf-8"))
    refs = published["normalization_refs"]
    # Superseded absolute-peak references, kept in the summary for audit.
    hs_low, hs_high = refs["abspeak_hs_ref_low"], refs["abspeak_hs_ref_high"]
    ssh_low, ssh_high = refs["abspeak_ssh_ref_low"], refs["abspeak_ssh_ref_high"]

    # First pass: pooled Q05/Q95 of the excess over the local q90 threshold.
    hs_excess_all: list[float] = []
    ssh_excess_all: list[float] = []
    for point in catalog:
        for event in point["compound_events"]:
            hs_excess_all.append(event["peak_hs"] - point["thr_hs_abs"])
            ssh_excess_all.append(event["peak_ssh_total"] - point["thr_ssh_total_abs"])
    if not hs_excess_all:
        raise RuntimeError("The compound catalog contains no events")
    hs_excess_low, hs_excess_high = np.percentile(hs_excess_all, [5, 95])
    ssh_excess_low, ssh_excess_high = np.percentile(ssh_excess_all, [5, 95])
    # Independent check that the recomputation matches what the pipeline used.
    for computed, key in (
        (hs_excess_low, "hs_excess_ref_low"),
        (hs_excess_high, "hs_excess_ref_high"),
        (ssh_excess_low, "ssh_excess_ref_low"),
        (ssh_excess_high, "ssh_excess_ref_high"),
    ):
        if abs(float(computed) - refs[key]) > 1e-3:
            raise RuntimeError(
                f"Recomputed {key} = {float(computed):.6f} does not match the "
                f"published reference {refs[key]}"
            )

    rows: list[dict[str, Any]] = []
    for point in catalog:
        events = point["compound_events"]
        if not events:
            continue
        hs = np.asarray([e["peak_hs"] for e in events], dtype=float)
        ssh = np.asarray([e["peak_ssh_total"] for e in events], dtype=float)
        hs_excess = hs - point["thr_hs_abs"]
        ssh_excess = ssh - point["thr_ssh_total_abs"]

        current = 0.5 * (
            np.clip((hs - hs_low) / (hs_high - hs_low), 0, 1)
            + np.clip((ssh - ssh_low) / (ssh_high - ssh_low), 0, 1)
        )
        excess = 0.5 * (
            np.clip(
                (hs_excess - hs_excess_low) / (hs_excess_high - hs_excess_low), 0, 1
            )
            + np.clip(
                (ssh_excess - ssh_excess_low) / (ssh_excess_high - ssh_excess_low),
                0,
                1,
            )
        )
        hs_term_abspeak = np.clip((hs - hs_low) / (hs_high - hs_low), 0, 1)
        ssh_term_abspeak = np.clip((ssh - ssh_low) / (ssh_high - ssh_low), 0, 1)
        hs_term_adopted = np.clip(
            (hs_excess - hs_excess_low) / (hs_excess_high - hs_excess_low), 0, 1
        )
        ssh_term_adopted = np.clip(
            (ssh_excess - ssh_excess_low) / (ssh_excess_high - ssh_excess_low), 0, 1
        )
        rows.append(
            {
                "grid_lat": point["grid_lat"],
                "grid_lon": point["grid_lon"],
                "n_events": len(events),
                "thr_hs_abs": point["thr_hs_abs"],
                "thr_ssh_total_abs": point["thr_ssh_total_abs"],
                "intensity_abspeak": float(current.mean()),
                "intensity_adopted": float(excess.mean()),
                "hs_term_abspeak": float(hs_term_abspeak.mean()),
                "ssh_term_abspeak": float(ssh_term_abspeak.mean()),
                "hs_term_adopted": float(hs_term_adopted.mean()),
                "ssh_term_adopted": float(ssh_term_adopted.mean()),
                "clipped_high_abspeak": float(
                    ((hs > hs_high) | (ssh > ssh_high)).mean()
                ),
                "clipped_high_adopted": float(
                    ((hs_excess > hs_excess_high) | (ssh_excess > ssh_excess_high)).mean()
                ),
            }
        )

    variants = pd.DataFrame(rows)
    metadata = {
        "published_references_absolute_peaks": refs,
        "derived_references_excess_over_local_threshold": {
            "hs_excess_low": round(float(hs_excess_low), 4),
            "hs_excess_high": round(float(hs_excess_high), 4),
            "ssh_excess_low": round(float(ssh_excess_low), 4),
            "ssh_excess_high": round(float(ssh_excess_high), 4),
            "population": "all compound-event excesses pooled over the native grid",
        },
        "event_count": int(variants.n_events.sum()),
        "grid_point_count": int(len(variants)),
    }
    return variants, metadata


LATITUDE_BANDS = (
    ("N (>= 0)", 0.0, 90.0),
    ("NE (0 to -10)", -10.0, 0.0),
    ("E (-10 to -18)", -18.0, -10.0),
    ("SE (-18 to -25)", -25.0, -18.0),
    ("S (< -25)", -90.0, -25.0),
)


def _band_table(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Signed component contributions summarized by latitude band."""
    table: list[dict[str, Any]] = []
    for name, lower, upper in LATITUDE_BANDS:
        subset = frame[(frame.grid_lat >= lower) & (frame.grid_lat < upper)]
        if subset.empty:
            continue
        table.append(
            {
                "band": name,
                "grid_points": int(len(subset)),
                "hs_term_abspeak": round(float(subset.hs_term_abspeak.mean()), 4),
                "hs_term_adopted": round(float(subset.hs_term_adopted.mean()), 4),
                "ssh_term_abspeak": round(float(subset.ssh_term_abspeak.mean()), 4),
                "ssh_term_adopted": round(float(subset.ssh_term_adopted.mean()), 4),
                "hs_contribution": round(float(subset.hs_contribution.mean()), 4),
                "ssh_contribution": round(float(subset.ssh_contribution.mean()), 4),
                "intensity_difference": round(
                    float(subset.intensity_difference.mean()), 4
                ),
            }
        )
    return table


def build_comparison() -> tuple[pd.DataFrame, dict[str, Any]]:
    """Assemble both intensities and both Hazard Indices on the native grid."""
    published, published_metadata = derive_native_hazard_index()
    variants, variant_metadata = build_intensity_variants()

    key = ["grid_lat", "grid_lon"]
    published = published.copy()
    for frame in (published, variants):
        for column in key:
            frame[column] = frame[column].round(4)
    merged = published.merge(variants, on=key, how="inner", validate="one_to_one")
    if len(merged) != len(published):
        raise RuntimeError(
            f"Only {len(merged)} of {len(published)} grid points could be matched"
        )

    # Validation: each recomputed variant must reproduce its published column —
    # the absolute-peak variant the audit field, the excess-based variant the
    # canonical field that the pipeline now writes.
    reproduction_error = float(
        np.max(
            np.abs(
                merged["intensity_abspeak"]
                - merged["mean_compound_intensity_norm_abspeak"]
            )
        )
    )
    adopted_error = float(
        np.max(
            np.abs(
                merged["intensity_adopted"] - merged["mean_compound_intensity_norm"]
            )
        )
    )
    if max(reproduction_error, adopted_error) > 5e-4:
        raise RuntimeError(
            "The recomputed intensities do not reproduce the published catalog "
            f"(abspeak {reproduction_error:.6f}, adopted {adopted_error:.6f})"
        )

    # The aggregation below mirrors derive_native_hazard_index() exactly; only
    # the intensity input changes between the two variants.
    frequency = _minmax(merged["compound_count_total"])
    duration = _minmax(merged["mean_overlap_duration"])
    # The published Hazard Index already uses the adopted excess-based
    # intensity; the superseded variant is rebuilt from the audit field.
    merged["hazard_adopted"] = merged["Hazard_Index"]
    abspeak_raw = (frequency + duration + _minmax(merged["intensity_abspeak"])) / 3.0
    merged["hazard_abspeak_raw"] = abspeak_raw
    merged["hazard_abspeak"] = _minmax(abspeak_raw)
    merged["intensity_difference"] = (
        merged["intensity_abspeak"] - merged["intensity_adopted"]
    )
    merged["hazard_difference"] = merged["hazard_abspeak"] - merged["hazard_adopted"]

    # Component decomposition. Because the intensity is an unweighted mean of
    # the two terms, the change splits exactly:
    #     dI = 0.5 * d(Hs term) + 0.5 * d(SSH term)
    merged["hs_term_difference"] = merged["hs_term_abspeak"] - merged["hs_term_adopted"]
    merged["ssh_term_difference"] = (
        merged["ssh_term_abspeak"] - merged["ssh_term_adopted"]
    )
    merged["hs_contribution"] = 0.5 * merged["hs_term_difference"]
    merged["ssh_contribution"] = 0.5 * merged["ssh_term_difference"]
    identity_error = float(
        np.max(
            np.abs(
                merged["hs_contribution"]
                + merged["ssh_contribution"]
                - merged["intensity_difference"]
            )
        )
    )
    if identity_error > 1e-12:
        raise RuntimeError(
            "The component decomposition does not close "
            f"(max abs error {identity_error:.3e})"
        )

    from scipy.stats import pearsonr, spearmanr

    def _rank_overlap(a: pd.Series, b: pd.Series, size: int) -> int:
        top_a = set(np.argsort(-a.to_numpy())[:size])
        top_b = set(np.argsort(-b.to_numpy())[:size])
        return int(len(top_a & top_b))

    comparison = {
        "intensity": {
            "pearson_with_latitude_abspeak": round(
                float(pearsonr(merged.grid_lat, merged.intensity_abspeak)[0]), 4
            ),
            "pearson_with_latitude_adopted": round(
                float(pearsonr(merged.grid_lat, merged.intensity_adopted)[0]), 4
            ),
            "spearman_between_definitions": round(
                float(spearmanr(merged.intensity_abspeak, merged.intensity_adopted)[0]), 4
            ),
            "abspeak": _numeric_stats(merged.intensity_abspeak),
            "adopted": _numeric_stats(merged.intensity_adopted),
            "difference": _numeric_stats(merged.intensity_difference),
            "mean_clipped_high_abspeak": round(
                float(merged.clipped_high_abspeak.mean()), 4
            ),
            "mean_clipped_high_adopted": round(
                float(merged.clipped_high_adopted.mean()), 4
            ),
        },
        "hazard": {
            "pearson_with_latitude_abspeak": round(
                float(pearsonr(merged.grid_lat, merged.hazard_abspeak)[0]), 4
            ),
            "pearson_with_latitude_adopted": round(
                float(pearsonr(merged.grid_lat, merged.hazard_adopted)[0]), 4
            ),
            "spearman_between_variants": round(
                float(spearmanr(merged.hazard_abspeak, merged.hazard_adopted)[0]), 4
            ),
            "top_80_points_in_common": _rank_overlap(
                merged.hazard_abspeak, merged.hazard_adopted, 80
            ),
            "abspeak": _numeric_stats(merged.hazard_abspeak),
            "adopted": _numeric_stats(merged.hazard_adopted),
            "difference": _numeric_stats(merged.hazard_difference),
        },
        "component_decomposition": {
            "identity": "intensity_difference = 0.5*d(Hs term) + 0.5*d(SSH term)",
            "identity_max_abs_error": identity_error,
            "hs_term_abspeak": _numeric_stats(merged.hs_term_abspeak),
            "hs_term_adopted": _numeric_stats(merged.hs_term_adopted),
            "hs_term_difference": _numeric_stats(merged.hs_term_difference),
            "ssh_term_abspeak": _numeric_stats(merged.ssh_term_abspeak),
            "ssh_term_adopted": _numeric_stats(merged.ssh_term_adopted),
            "ssh_term_difference": _numeric_stats(merged.ssh_term_difference),
            "mean_absolute_contribution": {
                "hs": round(float(merged.hs_contribution.abs().mean()), 6),
                "ssh": round(float(merged.ssh_contribution.abs().mean()), 6),
                "ssh_share_of_total_change": round(
                    float(
                        merged.ssh_contribution.abs().mean()
                        / (
                            merged.hs_contribution.abs().mean()
                            + merged.ssh_contribution.abs().mean()
                        )
                    ),
                    4,
                ),
            },
            "spatial_variability_of_the_change": {
                "sd_hs_term_difference": round(
                    float(merged.hs_term_difference.std()), 6
                ),
                "sd_ssh_term_difference": round(
                    float(merged.ssh_term_difference.std()), 6
                ),
                "note": (
                    "The Hs term contributes a broadly uniform level shift; the "
                    "SSH term contributes most of the spatial contrast of the "
                    "change. Compare the mean absolute contributions (similar) "
                    "with these standard deviations (different)."
                ),
            },
            "by_latitude_band": _band_table(merged),
        },
        "validation": {
            "recomputed_abspeak_max_abs_error": round(reproduction_error, 8),
            "recomputed_adopted_max_abs_error": round(adopted_error, 8),
            "note": (
                "Both intensities are recomputed from the raw catalog and "
                "checked against their published columns: the superseded one "
                "against mean_compound_intensity_norm_abspeak and the adopted "
                "one against mean_compound_intensity_norm."
            ),
        },
    }
    metadata = {
        "native_hazard_index_published": published_metadata,
        "intensity_variants": variant_metadata,
        "comparison": comparison,
    }
    return merged, metadata


def _plot_panel(
    axis: plt.Axes,
    segments: gpd.GeoDataFrame,
    coastline: gpd.GeoDataFrame,
    spec: dict[str, Any],
    *,
    draw_left_labels: bool,
    draw_bottom_labels: bool,
) -> dict[str, Any]:
    crs = ccrs.PlateCarree()
    land, countries, states = _natural_earth_context()
    axis.set_facecolor(OCEAN_COLOR)
    axis.add_geometries(
        land, crs=crs, facecolor=LAND_COLOR, edgecolor="none", zorder=0.5
    )
    axis.set_extent(COASTAL_MAP_EXTENT, crs=crs)

    grid = axis.gridlines(
        crs=crs,
        draw_labels=True,
        linewidth=0.35,
        color=GRID_COLOR,
        alpha=0.55,
        linestyle="--",
        zorder=1.2,
    )
    grid.xlocator = matplotlib.ticker.FixedLocator(np.arange(-55.0, -29.9, 5.0))
    grid.ylocator = matplotlib.ticker.FixedLocator(np.arange(-35.0, 10.0, 5.0))
    grid.top_labels = False
    grid.right_labels = False
    grid.left_labels = draw_left_labels
    grid.bottom_labels = draw_bottom_labels
    grid.xlabel_style = {"size": 7.5, "color": "#374151"}
    grid.ylabel_style = {"size": 7.5, "color": "#374151"}

    axis.add_geometries(
        states, crs=crs, facecolor="none", edgecolor=STATE_BORDER_COLOR,
        linewidth=0.4, alpha=0.96, zorder=5,
    )
    axis.add_geometries(
        countries, crs=crs, facecolor="none", edgecolor=COUNTRY_BORDER_COLOR,
        linewidth=0.65, alpha=0.98, zorder=5.2,
    )
    axis.add_geometries(
        coastline.geometry, crs=crs, facecolor="none", edgecolor=COAST_COLOR,
        linewidth=0.4, zorder=5.4,
    )

    boundaries = spec["boundaries"]
    cmap = _palette(spec["palette"], len(boundaries) - 1)
    values = segments[spec["field"]].to_numpy(dtype=float)
    classes = np.digitize(values, boundaries[1:-1])
    for class_index in range(len(boundaries) - 1):
        geometries = segments.geometry[classes == class_index].tolist()
        if not geometries:
            continue
        dissolved = unary_union(geometries)
        merged = (
            linemerge(dissolved)
            if isinstance(dissolved, MultiLineString)
            else dissolved
        )
        axis.add_geometries(
            line_parts(merged),
            crs=crs,
            facecolor="none",
            edgecolor=cmap(class_index),
            linewidth=3.2,
            zorder=8,
        )

    axis.set_title(spec["title"], fontsize=9.5, fontweight="bold", pad=6)
    axis.text(
        0.02, 0.975, spec["panel"], transform=axis.transAxes, ha="left", va="top",
        fontsize=10, fontweight="bold",
        bbox={"boxstyle": "round,pad=0.25", "facecolor": "white",
              "edgecolor": "#cbd5e1", "alpha": 0.94},
        zorder=10,
    )
    axis.set_extent(COASTAL_MAP_EXTENT, crs=crs)
    return {
        "panel": spec["panel"],
        "field": spec["field"],
        "title": spec["title"],
        "boundaries": [float(b) for b in boundaries],
        "colors": [matplotlib.colors.to_hex(cmap(i)) for i in range(cmap.N)],
        "statistics": _numeric_stats(segments[spec["field"]]),
    }


def _add_colorbar(
    figure: plt.Figure,
    axis: plt.Axes,
    spec: dict[str, Any],
    vertical_offset: float,
) -> None:
    boundaries = spec["boundaries"]
    cmap = _palette(spec["palette"], len(boundaries) - 1)
    position = axis.get_position()
    colorbar_axis = figure.add_axes(
        [position.x0, position.y0 - vertical_offset, position.width, 0.010]
    )
    mappable = ScalarMappable(norm=BoundaryNorm(boundaries, cmap.N, clip=True), cmap=cmap)
    mappable.set_array([])
    colorbar = figure.colorbar(
        mappable, cax=colorbar_axis, orientation="horizontal",
        boundaries=boundaries, ticks=boundaries[::2], spacing="uniform", drawedges=True,
    )
    colorbar.set_label(spec["label"], fontsize=7.5, labelpad=2.0)
    colorbar.ax.xaxis.set_major_formatter(FormatStrFormatter(spec["tick_format"]))
    colorbar.ax.tick_params(labelsize=6.5, length=2.2)
    labels = colorbar.ax.get_xticklabels()
    if labels:
        labels[0].set_horizontalalignment("left")
        labels[-1].set_horizontalalignment("right")
    colorbar.outline.set_linewidth(0.6)


def _render_grid_figure(
    segments: gpd.GeoDataFrame,
    coastline: gpd.GeoDataFrame,
    specs: tuple[dict[str, Any], ...],
    output_path: Path,
) -> list[dict[str, Any]]:
    """Draw one 2 x 3 coastal panel figure and save it."""
    figure, axes = plt.subplots(
        2, 3, figsize=(13.2, 12.6),
        subplot_kw={"projection": ccrs.PlateCarree()},
    )
    figure.subplots_adjust(
        left=0.045, right=0.985, top=0.965, bottom=0.085, wspace=0.06, hspace=0.26
    )
    panels: list[dict[str, Any]] = []
    for index, (axis, spec) in enumerate(zip(axes.flat, specs)):
        panels.append(
            _plot_panel(
                axis, segments, coastline, spec,
                draw_left_labels=index % 3 == 0,
                draw_bottom_labels=index >= 3,
            )
        )
    figure.canvas.draw()
    for index, (axis, spec) in enumerate(zip(axes.flat, specs)):
        _add_colorbar(figure, axis, spec, 0.042 if index < 3 else 0.062)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(
        output_path, dpi=EXPLORATORY_DPI, bbox_inches="tight", facecolor="white"
    )
    plt.close(figure)
    return panels


def main() -> None:
    grid, metadata = build_comparison()
    municipalities, coastline = read_coastal_inputs()
    segments, assignment = project_values_to_coastline(
        grid, FIELDS, municipalities=municipalities, coastline=coastline
    )

    for directory in (FIGURE_DIR, DATA_DIR, METADATA_DIR):
        directory.mkdir(parents=True, exist_ok=True)
    panels = _render_grid_figure(segments, coastline, PANELS, FIGURE_PATH)
    component_panels = _render_grid_figure(
        segments, coastline, COMPONENT_PANELS, COMPONENT_FIGURE_PATH
    )

    grid.to_csv(GRID_DATA_PATH, index=False, float_format="%.6f")
    segments.to_file(SEGMENT_DATA_PATH, driver="GeoJSON")
    METADATA_PATH.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "purpose": (
                    "Exploratory comparison of two compound-intensity definitions "
                    "and their effect on the Hazard Index. Does not modify the "
                    "production pipeline or any article figure."
                ),
                "sources": {
                    "compound_catalog": _relative(COMPOUND_CATALOG),
                    "compound_summary": _relative(COMPOUND_SUMMARY),
                    "native_grid_metrics": _relative(NATIVE_GRID_SOURCE),
                },
                "outputs": {
                    "figure": _relative(FIGURE_PATH),
                    "component_figure": _relative(COMPONENT_FIGURE_PATH),
                    "grid_table": _relative(GRID_DATA_PATH),
                    "coastal_segments": _relative(SEGMENT_DATA_PATH),
                    "metadata": _relative(METADATA_PATH),
                },
                "coastal_assignment": assignment,
                "panels": panels,
                "component_panels": component_panels,
                **metadata,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    c = metadata["comparison"]
    print(_relative(FIGURE_PATH))
    print(_relative(COMPONENT_FIGURE_PATH))
    print(_relative(GRID_DATA_PATH))
    print(_relative(SEGMENT_DATA_PATH))
    print(_relative(METADATA_PATH))
    print()
    print("Validation: both recomputed intensities match their published columns "
          f"(max abs error {max(c['validation']['recomputed_abspeak_max_abs_error'], c['validation']['recomputed_adopted_max_abs_error']):.2e})")
    print("Intensity  pearson(lat): superseded "
          f"{c['intensity']['pearson_with_latitude_abspeak']:+.3f} -> adopted "
          f"{c['intensity']['pearson_with_latitude_adopted']:+.3f}   "
          f"spearman between definitions {c['intensity']['spearman_between_definitions']:+.3f}")
    print("Hazard     pearson(lat): superseded "
          f"{c['hazard']['pearson_with_latitude_abspeak']:+.3f} -> adopted "
          f"{c['hazard']['pearson_with_latitude_adopted']:+.3f}   "
          f"spearman {c['hazard']['spearman_between_variants']:+.3f}   "
          f"top-80 in common {c['hazard']['top_80_points_in_common']}/80")
    d = c["component_decomposition"]
    a = d["mean_absolute_contribution"]
    v = d["spatial_variability_of_the_change"]
    print()
    print("Component decomposition (identity closes to "
          f"{d['identity_max_abs_error']:.1e}):")
    print(f"  mean |contribution| : Hs {a['hs']:.4f}   SSH {a['ssh']:.4f}   "
          f"(SSH share {100*a['ssh_share_of_total_change']:.1f}%)")
    print(f"  sd of the change    : Hs {v['sd_hs_term_difference']:.4f}   "
          f"SSH {v['sd_ssh_term_difference']:.4f}")
    print("  signed contribution by latitude band:")
    print(f"    {'band':16s} {'d(Hs)/2':>9s} {'d(SSH)/2':>9s} {'dI':>9s}")
    for row in d["by_latitude_band"]:
        print(f"    {row['band']:16s} {row['hs_contribution']:+9.4f} "
              f"{row['ssh_contribution']:+9.4f} {row['intensity_difference']:+9.4f}")


if __name__ == "__main__":
    main()
