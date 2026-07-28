"""Exploratory: how the normalisation of the exposure term changes the risk map.

The integrated index adopted for the article is the conjunctive, IPCC-style
geometric mean of hazard, exposure and vulnerability,

    R = (A * E * V) ** (1/3),

with each component clipped to [0.01, 1] so that a municipality sitting at the
floor of a Min--Max scale does not receive zero risk as a scaling artefact.
``A`` is the compound-event Hazard Index renormalised over the municipalities
(``Hazard_Index_mun``) and ``V`` is ``SVI_Coast_2022 / 100``.

``E`` is the population within 10 km of the coastline. What is *not* settled is
how to bring that count onto [0, 1], and the choice is consequential rather
than technical, because Min--Max is an affine rescaling: it changes the range
of a variable and not its shape. The population count has skewness above 7, so
under Min--Max it stays that skewed inside [0, 1] and the term collapses —
nine municipalities in ten sit below 0.05 and the nominal weight of one third
buys almost no influence. A logarithm changes the shape but compresses real
differences; a percentile rank discards magnitude altogether.

This figure shows the three candidates side by side, and the risk map each one
produces, so the decision is made on evidence. Nothing here is an article
figure and nothing here is published.

Inputs
------
    outputs/exposure/municipal_exposure.csv
    site/public/data/risk_index_municipalities.geojson

Outputs
-------
    outputs/exploratory_exposure/exposure_normalization_comparison.png
    outputs/exploratory_exposure/exposure_normalization_summary.json

Run
---
    python -m src.exploratory.make_exploratory_exposure_normalization
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
from src.risk_integration.palettes import risk_colors  # noqa: E402


ROOT = Path(__file__).resolve().parents[2]
EXPOSURE_CSV = ROOT / "outputs" / "exposure" / "municipal_exposure.csv"
RISK_GEOJSON = ROOT / "site" / "public" / "data" / "risk_index_municipalities.geojson"
OUTPUT_DIR = ROOT / "outputs" / "exploratory_exposure"
OUTPUT_FIGURE = OUTPUT_DIR / "exposure_normalization_comparison.png"
OUTPUT_SUMMARY = OUTPUT_DIR / "exposure_normalization_summary.json"

EXPOSURE_FIELD = "pop_10km"
CLIP_FLOOR = 0.01
CLASS_BOUNDARIES = np.linspace(0.0, 1.0, 9)


def minmax(values: pd.Series) -> pd.Series:
    finite = values[np.isfinite(values)]
    lower, upper = float(finite.min()), float(finite.max())
    if np.isclose(lower, upper):
        return pd.Series(0.0, index=values.index)
    return (values - lower) / (upper - lower)


def normalisations(population: pd.Series) -> dict[str, pd.Series]:
    """The three candidate ways of bringing a population count onto [0, 1]."""
    return {
        "linear": minmax(population),
        "log10": minmax(np.log10(population + 1.0)),
        "rank": population.rank(pct=True),
    }


def load_components() -> gpd.GeoDataFrame:
    for path in (EXPOSURE_CSV, RISK_GEOJSON):
        if not path.exists():
            raise FileNotFoundError(path)

    risk = gpd.read_file(RISK_GEOJSON)
    exposure = pd.read_csv(EXPOSURE_CSV, dtype={"municipality_code": str})
    risk["municipality_code"] = risk["municipality_code"].astype(str)

    merged = risk.merge(
        exposure[["municipality_code", EXPOSURE_FIELD]],
        on="municipality_code",
        how="left",
        validate="one_to_one",
    )
    missing = int(merged[EXPOSURE_FIELD].isna().sum())
    if missing:
        raise RuntimeError(
            f"{missing} municipalities have no exposure value; the two layers "
            "do not describe the same set"
        )
    # Municipalities without a hazard association cannot enter a product.
    merged = merged[merged["Hazard_Index_mun"].notna()].copy()
    return merged


def build_frame(components: gpd.GeoDataFrame) -> tuple[gpd.GeoDataFrame, dict[str, Any]]:
    frame = components.copy()
    hazard = pd.to_numeric(frame["Hazard_Index_mun"], errors="coerce")
    vulnerability = pd.to_numeric(frame["SVI_Coast_2022"], errors="coerce") / 100.0
    population = pd.to_numeric(frame[EXPOSURE_FIELD], errors="coerce")

    frame["A"] = hazard
    frame["V"] = vulnerability

    clip = lambda s: s.clip(lower=CLIP_FLOOR, upper=1.0)  # noqa: E731
    summary: dict[str, Any] = {"normalisations": {}}
    for name, exposure in normalisations(population).items():
        risk = (clip(hazard) * clip(exposure) * clip(vulnerability)) ** (1.0 / 3.0)
        frame[f"E_{name}"] = exposure
        frame[f"R_{name}"] = risk
        summary["normalisations"][name] = {
            "E": {
                "mean": round(float(exposure.mean()), 6),
                "median": round(float(exposure.median()), 6),
                "share_below_0.05": round(float((exposure < 0.05).mean()), 4),
            },
            "spearman_R_with": {
                "A": round(float(spearmanr(risk, hazard).statistic), 4),
                "E": round(float(spearmanr(risk, exposure).statistic), 4),
                "V": round(float(spearmanr(risk, vulnerability).statistic), 4),
                "Risk_Hazard_published": round(
                    float(
                        spearmanr(
                            risk, pd.to_numeric(frame["Risk_Hazard"])
                        ).statistic
                    ),
                    4,
                ),
            },
            "top10": [
                f"{row.municipality_name}/{row.state}"
                for row in frame.assign(_r=risk).nlargest(10, "_r").itertuples()
            ],
        }

    pairs = [("linear", "log10"), ("linear", "rank"), ("log10", "rank")]
    summary["spearman_between_risk_maps"] = {
        f"{a}_vs_{b}": round(
            float(spearmanr(frame[f"R_{a}"], frame[f"R_{b}"]).statistic), 4
        )
        for a, b in pairs
    }
    return frame, summary


def draw(frame: gpd.GeoDataFrame, summary: dict[str, Any]) -> None:
    colors = risk_colors(len(CLASS_BOUNDARIES) - 1)
    cmap = ListedColormap(colors)
    norm = BoundaryNorm(CLASS_BOUNDARIES, cmap.N)

    names = ("linear", "log10", "rank")
    titles = {
        "linear": "Min–Max of the count",
        "log10": "Min–Max of log₁₀(count+1)",
        "rank": "Percentile rank",
    }
    fig, axes = plt.subplots(2, 3, figsize=(15, 13), constrained_layout=True)
    for column, name in enumerate(names):
        for row, prefix in enumerate(("E", "R")):
            ax = axes[row, column]
            frame.plot(
                column=f"{prefix}_{name}",
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
            if row == 0:
                ax.set_title(titles[name], fontsize=13, pad=8)
                label = f"E — {titles[name]}"
            else:
                stats = summary["normalisations"][name]["spearman_R_with"]
                label = (
                    f"R = (A·E·V)$^{{1/3}}$   ρ(R,A)={stats['A']:+.2f}  "
                    f"ρ(R,E)={stats['E']:+.2f}  ρ(R,V)={stats['V']:+.2f}"
                )
            ax.set_xlabel(label, fontsize=9)

    axes[0, 0].set_ylabel("Exposure term E", fontsize=12)
    axes[1, 0].set_ylabel("Integrated risk R", fontsize=12)

    mappable = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    bar = fig.colorbar(
        mappable,
        ax=axes,
        orientation="horizontal",
        fraction=0.035,
        pad=0.02,
        ticks=CLASS_BOUNDARIES,
    )
    bar.set_label("normalized value (dimensionless)", fontsize=11)
    fig.suptitle(
        "Exposure normalisation and its effect on the conjunctive risk index\n"
        f"E = resident population within 10 km of the coastline · "
        f"components clipped to [{CLIP_FLOOR}, 1] · exploratory, not published",
        fontsize=14,
    )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_FIGURE, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main() -> None:
    components = load_components()
    frame, summary = build_frame(components)
    draw(frame, summary)

    summary.update(
        {
            "generated_by": "src.exploratory.make_exploratory_exposure_normalization",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "exposure_field": EXPOSURE_FIELD,
            "clip_floor": CLIP_FLOOR,
            "formula": "R = (clip(A) * clip(E) * clip(V)) ** (1/3)",
            "municipality_count": int(len(frame)),
            "figure": str(OUTPUT_FIGURE.relative_to(ROOT)),
        }
    )
    with open(OUTPUT_SUMMARY, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    print(f"{len(frame)} municipalities")
    for name, block in summary["normalisations"].items():
        stats = block["spearman_R_with"]
        print(
            f"  E_{name:6s} mediana={block['E']['median']:.3f} "
            f"abaixo de 0.05={block['E']['share_below_0.05']:.0%} | "
            f"rho(R,A)={stats['A']:+.3f} rho(R,E)={stats['E']:+.3f} "
            f"rho(R,V)={stats['V']:+.3f}"
        )
    print("  entre mapas de R:", summary["spearman_between_risk_maps"])
    print(f"Figure: {OUTPUT_FIGURE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
