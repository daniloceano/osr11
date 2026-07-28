"""Exploratory: what changes when the exposure term enters the risk index.

Puts three maps side by side:

1. the published index, ``Risk_Hazard`` = norm(SVI/100 x Hazard_Index), which has
   no exposure term at all and is therefore a vulnerability-weighted hazard
   rather than risk in the IPCC sense;
2. the conjunctive index with exposure normalised by log10;
3. the same with exposure normalised by percentile rank.

The second row shows where each candidate moves a municipality relative to the
published index, in positions of the ranking. That is the diagnostic that
matters for a product meant to prioritise: not whether the colours look
different, but which places change place.

All three indices are Min--Max normalised over the municipalities before being
drawn, because the published one already is and because they are comparative
indices in any case. Min--Max is monotone, so it changes the colours and never
the ranking or the Spearman coefficients reported here.

Inputs
------
    outputs/exposure/municipal_exposure.csv
    site/public/data/risk_index_municipalities.geojson

Outputs
-------
    outputs/exploratory_exposure/risk_with_exposure_comparison.png
    outputs/exploratory_exposure/risk_with_exposure_summary.json

Run
---
    python -m src.exploratory.make_exploratory_risk_with_exposure
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import geopandas as gpd
import matplotlib
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import BoundaryNorm, ListedColormap  # noqa: E402

from src.risk_integration.coastal_projection import COASTAL_MAP_EXTENT  # noqa: E402
from src.risk_integration.exposure_index import (  # noqa: E402
    CLIP_FLOOR,
    exposure_inform,
    exposure_log10,
    exposure_rank,
)
from src.risk_integration.palettes import diverging_colors, risk_colors  # noqa: E402


ROOT = Path(__file__).resolve().parents[2]
EXPOSURE_CSV = ROOT / "outputs" / "exposure" / "municipal_exposure.csv"
RISK_GEOJSON = ROOT / "site" / "public" / "data" / "risk_index_municipalities.geojson"
OUTPUT_DIR = ROOT / "outputs" / "exploratory_exposure"
OUTPUT_FIGURE = OUTPUT_DIR / "risk_with_exposure_comparison.png"
OUTPUT_SUMMARY = OUTPUT_DIR / "risk_with_exposure_summary.json"

EXPOSURE_FIELD = "pop_10km"
RISK_BOUNDARIES = [round(value, 3) for value in np.linspace(0.0, 1.0, 9)]
#: Rank-shift classes, in positions. Symmetric, with a neutral middle class.
SHIFT_BOUNDARIES = [-280.0, -80.0, -40.0, -15.0, 15.0, 40.0, 80.0, 280.0]


def minmax(values: pd.Series) -> pd.Series:
    finite = values[np.isfinite(values)]
    lower, upper = float(finite.min()), float(finite.max())
    if np.isclose(lower, upper):
        return pd.Series(0.0, index=values.index)
    return (values - lower) / (upper - lower)


def load_frame() -> gpd.GeoDataFrame:
    for path in (EXPOSURE_CSV, RISK_GEOJSON):
        if not path.exists():
            raise FileNotFoundError(path)
    risk = gpd.read_file(RISK_GEOJSON)
    exposure = pd.read_csv(EXPOSURE_CSV, dtype={"municipality_code": str})
    risk["municipality_code"] = risk["municipality_code"].astype(str)
    merged = risk.merge(
        exposure[["municipality_code", EXPOSURE_FIELD, "pop_municipality"]],
        on="municipality_code",
        how="left",
        validate="one_to_one",
    )
    if int(merged[EXPOSURE_FIELD].isna().sum()):
        raise RuntimeError("Some municipalities have no exposure value")
    # Only municipalities with a hazard association can enter a product, and the
    # exposure normalisations are computed over that same reference population.
    return merged[merged["Hazard_Index_mun"].notna()].reset_index(drop=True)


def build(frame: gpd.GeoDataFrame) -> tuple[gpd.GeoDataFrame, dict[str, Any]]:
    result = frame.copy()
    hazard = pd.to_numeric(result["Hazard_Index_mun"], errors="coerce")
    vulnerability = pd.to_numeric(result["SVI_Coast_2022"], errors="coerce") / 100.0
    population = pd.to_numeric(result[EXPOSURE_FIELD], errors="coerce")
    clip = lambda series: series.clip(lower=CLIP_FLOOR, upper=1.0)  # noqa: E731

    municipal = pd.to_numeric(result["pop_municipality"], errors="coerce")
    exposures = {
        "inform": exposure_inform(population, municipal),
        "log10": exposure_log10(population),
        "rank": exposure_rank(population),
    }
    result["R_current"] = minmax(pd.to_numeric(result["Risk_Hazard"], errors="coerce"))
    for name, exposure in exposures.items():
        result[f"E_{name}"] = exposure
        result[f"R_{name}"] = minmax(
            (clip(hazard) * clip(exposure) * clip(vulnerability)) ** (1.0 / 3.0)
        )

    # Rank shift, in positions: positive means the candidate ranks the
    # municipality as more at risk than the published index does.
    position = lambda column: result[column].rank(ascending=False, method="min")  # noqa: E731
    for name in exposures:
        result[f"shift_{name}"] = position("R_current") - position(f"R_{name}")

    keys = ["R_current", "R_inform", "R_log10", "R_rank"]
    summary: dict[str, Any] = {
        "municipality_count": int(len(result)),
        "spearman": {
            f"{a}_vs_{b}": round(float(spearmanr(result[a], result[b]).statistic), 4)
            for i, a in enumerate(keys)
            for b in keys[i + 1 :]
        },
        "candidates": {},
    }
    for name in exposures:
        shift = result[f"shift_{name}"]
        movers_up = result.nlargest(5, f"shift_{name}")
        movers_down = result.nsmallest(5, f"shift_{name}")
        summary["candidates"][name] = {
            "spearman_with_current": round(
                float(spearmanr(result["R_current"], result[f"R_{name}"]).statistic), 4
            ),
            "median_absolute_shift": int(shift.abs().median()),
            "share_moving_more_than_15_positions": round(
                float((shift.abs() > 15).mean()), 4
            ),
            "largest_rise": [
                f"{row.municipality_name}/{row.state} +{int(getattr(row, f'shift_{name}'))}"
                for row in movers_up.itertuples()
            ],
            "largest_fall": [
                f"{row.municipality_name}/{row.state} {int(getattr(row, f'shift_{name}'))}"
                for row in movers_down.itertuples()
            ],
            "top10": [
                f"{row.municipality_name}/{row.state}"
                for row in result.nlargest(10, f"R_{name}").itertuples()
            ],
        }
    summary["top10_current"] = [
        f"{row.municipality_name}/{row.state}"
        for row in result.nlargest(10, "R_current").itertuples()
    ]
    return result, summary


def _panel(ax, frame, column, cmap, norm, title, subtitle) -> None:
    frame.plot(
        column=column,
        cmap=cmap,
        norm=norm,
        linewidth=0.1,
        edgecolor="#ffffff",
        ax=ax,
    )
    ax.set_xlim(COASTAL_MAP_EXTENT[0], COASTAL_MAP_EXTENT[2])
    ax.set_ylim(COASTAL_MAP_EXTENT[1], COASTAL_MAP_EXTENT[3])
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for side in ax.spines.values():
        side.set_edgecolor("#9ca3af")
    ax.set_title(f"{title}\n{subtitle}", fontsize=11, pad=6)


def draw(frame: gpd.GeoDataFrame, summary: dict[str, Any]) -> None:
    risk_cmap = ListedColormap(risk_colors(8))
    risk_norm = BoundaryNorm(RISK_BOUNDARIES, risk_cmap.N)
    shift_cmap = ListedColormap(diverging_colors(len(SHIFT_BOUNDARIES) - 1))
    shift_norm = BoundaryNorm(SHIFT_BOUNDARIES, shift_cmap.N)

    fig, axes = plt.subplots(2, 4, figsize=(20, 13), constrained_layout=True)

    _panel(
        axes[0, 0], frame, "R_current", risk_cmap, risk_norm,
        "Published index — no exposure",
        "norm(SVI/100 × Hazard_Index)",
    )
    for column, name, label in ((1, "inform", "INFORM"), (2, "log10", "log₁₀"), (3, "rank", "rank")):
        rho = summary["candidates"][name]["spearman_with_current"]
        _panel(
            axes[0, column], frame, f"R_{name}", risk_cmap, risk_norm,
            f"With exposure — E by {label}",
            f"(A·E·V)$^{{1/3}}$   ρ with published = {rho:+.3f}",
        )

    axes[1, 0].axis("off")
    # The diverging ramp is RdBu_r: low (negative) is blue, high (positive) is
    # red. A positive shift means the candidate ranks the municipality as more
    # at risk, so red is the rise and blue is the fall.
    axes[1, 0].text(
        0.5, 0.96,
        "Rank shift against the\npublished index\n\n"
        "red   = candidate ranks it\n          MORE at risk\n"
        "blue  = LESS at risk\n"
        "white = within 15 positions\n\n"
        f"{summary['municipality_count']} municipalities\n"
        "components clipped to\n"
        f"[{CLIP_FLOOR}, 1] before the product",
        ha="center", va="top", fontsize=11, color="#374151",
        linespacing=1.5,
        transform=axes[1, 0].transAxes,
    )
    for column, name, label in ((1, "inform", "INFORM"), (2, "log10", "log₁₀"), (3, "rank", "rank")):
        block = summary["candidates"][name]
        _panel(
            axes[1, column], frame, f"shift_{name}", shift_cmap, shift_norm,
            f"Rank shift — E by {label}",
            f"median |shift| = {block['median_absolute_shift']} positions · "
            f"{block['share_moving_more_than_15_positions']:.0%} move >15",
        )

    risk_bar = fig.colorbar(
        plt.cm.ScalarMappable(cmap=risk_cmap, norm=risk_norm),
        ax=axes[0, :], orientation="horizontal", fraction=0.045, pad=0.02,
        ticks=RISK_BOUNDARIES,
    )
    risk_bar.set_label("integrated index, Min–Max normalized (dimensionless)", fontsize=10)
    shift_bar = fig.colorbar(
        plt.cm.ScalarMappable(cmap=shift_cmap, norm=shift_norm),
        ax=axes[1, :], orientation="horizontal", fraction=0.045, pad=0.02,
        ticks=SHIFT_BOUNDARIES,
    )
    shift_bar.set_label(
        "change in ranking position — red = rises (more at risk), blue = falls",
        fontsize=10,
    )

    fig.suptitle(
        "Does the exposure term change the risk map?\n"
        "E = resident population within 10 km of the coastline · "
        "exploratory, not published",
        fontsize=14,
    )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_FIGURE, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main() -> None:
    frame, summary = build(load_frame())
    draw(frame, summary)
    summary.update(
        {
            "generated_by": "src.exploratory.make_exploratory_risk_with_exposure",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "exposure_field": EXPOSURE_FIELD,
            "clip_floor": CLIP_FLOOR,
            "published_formula": "R_current = norm_municipal((SVI/100) * Hazard_Index)",
            "candidate_formula": "R = norm_municipal((clip(A) * clip(E) * clip(V)) ** (1/3))",
            "figure": str(OUTPUT_FIGURE.relative_to(ROOT)),
        }
    )
    with open(OUTPUT_SUMMARY, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    print(f"{summary['municipality_count']} municipalities")
    print("  Spearman:", summary["spearman"])
    for name, block in summary["candidates"].items():
        print(
            f"  E_{name:6s} rho com o atual={block['spearman_with_current']:+.3f} | "
            f"|shift| mediano={block['median_absolute_shift']:>3d} posicoes | "
            f"{block['share_moving_more_than_15_positions']:.0%} movem >15"
        )
        print(f"    sobem : {', '.join(block['largest_rise'][:3])}")
        print(f"    descem: {', '.join(block['largest_fall'][:3])}")
    print(f"Figure: {OUTPUT_FIGURE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
