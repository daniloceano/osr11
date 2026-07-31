"""Export the Step 2e calibration tables to the site's JSON payloads.

These files back the calibration pages of the site and the article's
calibration heatmap figure, which reads ``tc5_score_decomposition.json``
through ``src.figures_article.calibration_common.load_score_frame``.

Until 2026-07-30 no script produced them: they had been written once and then
went stale. The recalibration of that date changed the sweep grid from 81 to
121 pairs and changed the score itself, so the published files described a
calibration that no longer existed and the article figure silently rendered the
superseded surface. This module closes that gap -- the site and the figure now
derive from the same tables the pipeline writes.

Usage:
    conda run -n osr11 python -m src.site.export_calibration_data

Input:
    outputs/threshold_calibration/tables/tab_TC5_score_decomposition.csv
    outputs/threshold_calibration/tables/tab_TC5_qi_decomposition.csv
    outputs/threshold_calibration/tables/tab_TC5_optimal_pair_pu.csv
    outputs/threshold_calibration/tables/tab_TC5_detection_census.csv

Output:
    site/public/data/tc5_score_decomposition.json
    site/public/data/tc5_qi_decomposition.json
    site/public/data/tc5_decomposition_summary.json
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
TAB_DIR = ROOT / "outputs" / "threshold_calibration" / "tables"
SCORE_TABLE = TAB_DIR / "tab_TC5_score_decomposition.csv"
QI_TABLE = TAB_DIR / "tab_TC5_qi_decomposition.csv"
OPTIMAL_TABLE = TAB_DIR / "tab_TC5_optimal_pair_pu.csv"
CENSUS_TABLE = TAB_DIR / "tab_TC5_detection_census.csv"

SITE_DATA_DIR = ROOT / "site" / "public" / "data"
SCORE_JSON = SITE_DATA_DIR / "tc5_score_decomposition.json"
QI_JSON = SITE_DATA_DIR / "tc5_qi_decomposition.json"
SUMMARY_JSON = SITE_DATA_DIR / "tc5_decomposition_summary.json"

#: The q_i table is one row per unmatched episode at the selected pair and can
#: run to thousands of rows. The site shows a distribution and a worst-offender
#: list, so it is capped; the cap is reported in the summary.
QI_MAX_ROWS = 6000


def _records(frame: pd.DataFrame) -> list[dict]:
    """JSON-safe records, with NaN as null rather than the literal NaN."""
    return json.loads(frame.to_json(orient="records", date_format="iso"))


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    for path in (SCORE_TABLE, QI_TABLE, OPTIMAL_TABLE):
        if not path.exists():
            raise FileNotFoundError(
                f"{path} not found. Run Step 2e first: python "
                "src/02_threshold_calibration/05_pu_composite_calibration/main.py --all"
            )

    score = pd.read_csv(SCORE_TABLE)
    qi = pd.read_csv(QI_TABLE)
    optimal = pd.read_csv(OPTIMAL_TABLE).iloc[0]

    SITE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    SCORE_JSON.write_text(json.dumps(_records(score), separators=(",", ":")))
    log.info("Saved: %s (%d pairs)", SCORE_JSON.name, len(score))

    qi_export = qi.nlargest(min(QI_MAX_ROWS, len(qi)), "penalty_component")
    QI_JSON.write_text(json.dumps(_records(qi_export), separators=(",", ":")))
    log.info(
        "Saved: %s (%d of %d episodes, ranked by penalty)",
        QI_JSON.name, len(qi_export), len(qi),
    )

    hs_levels = sorted(int(v) for v in score["hs_percentile"].unique())
    ssh_levels = sorted(int(v) for v in score["ssh_percentile"].unique())
    hs_optimal = int(round(float(optimal["thr_hs_pct"]) * 100))
    ssh_optimal = int(round(float(optimal["thr_ssh_pct"]) * 100))

    summary = {
        "score_grid_size": [len(hs_levels), len(ssh_levels)],
        "score_grid_hs_percentiles": hs_levels,
        "score_grid_ssh_percentiles": ssh_levels,
        "score_optimal": {
            "hs_percentile": hs_optimal,
            "ssh_percentile": ssh_optimal,
            "H": int(optimal["H"]),
            "M": int(optimal["M"]),
            "U": int(optimal["U"]),
            "R_pos": round(float(optimal["R_pos"]), 6),
            "B": round(float(optimal["B"]), 6),
            "F_soft": round(float(optimal["F_soft"]), 4),
            "Score": round(float(optimal["Score"]), 6),
        },
        "qi_episode_count": int(len(qi)),
        "qi_exported_count": int(len(qi_export)),
        "qi_mean_qi": round(float(qi["q_i"].mean()), 6),
        "qi_mean_penalty": round(float(qi["penalty_component"].mean()), 6),
        "qi_max_penalty": round(float(qi["penalty_component"].max()), 6),
        "qi_E1_pct": round(float(100.0 * qi["E_i"].mean()), 4),
        "qi_top5_penalty": [
            round(float(v), 6)
            for v in qi.nlargest(5, "penalty_component")["penalty_component"]
        ],
        "qi_top5_qi": [round(float(v), 6) for v in qi.nsmallest(5, "q_i")["q_i"]],
        "weights": {
            "w1": float(score["w1"].iloc[0]),
            "w2": float(score["w2"].iloc[0]),
            "w3": float(score["w3"].iloc[0]),
        },
        "alphas": {
            "alpha_E": float(qi["alpha_E"].iloc[0]),
            "alpha_I": float(qi["alpha_I"].iloc[0]),
            "alpha_C": float(qi["alpha_C"].iloc[0]),
        },
    }

    if "burden_mode" in score.columns:
        row = score[
            (score["hs_percentile"] == hs_optimal)
            & (score["ssh_percentile"] == ssh_optimal)
        ]
        summary["burden"] = {
            "mode": str(score["burden_mode"].iloc[0]),
            "target_per_muni_yr": float(score["burden_target_per_muni_yr"].iloc[0]),
            "rate_at_optimal_per_muni_yr": (
                round(float(row["rate_per_muni_yr"].iloc[0]), 4) if len(row) else None
            ),
        }

    if CENSUS_TABLE.exists():
        census = pd.read_csv(CENSUS_TABLE)
        selected = census[
            (census["thr_hs_pct"] == float(optimal["thr_hs_pct"]))
            & (census["thr_ssh_pct"] == float(optimal["thr_ssh_pct"]))
        ]
        joined = census.assign(
            hs_percentile=(census["thr_hs_pct"] * 100).round().astype(int),
            ssh_percentile=(census["thr_ssh_pct"] * 100).round().astype(int),
        ).merge(
            score[["hs_percentile", "ssh_percentile", "Score"]],
            on=["hs_percentile", "ssh_percentile"],
        )
        summary["detection_census"] = {
            "n_pairs": int(len(census)),
            "n_degenerate_pairs": int(census["degenerate"].sum()),
            "degeneracy_rule": (
                "fewer accepted compound episodes over the calibration domain "
                "than positive events to recall"
            ),
            "selected_pair_accepted_episodes": (
                int(selected["n_accepted_episodes"].iloc[0]) if len(selected) else None
            ),
            "selected_pair_degenerate": (
                bool(selected["degenerate"].iloc[0]) if len(selected) else None
            ),
            "spearman_score_vs_accepted_episodes": round(
                float(
                    joined["Score"].corr(
                        joined["n_accepted_episodes"], method="spearman"
                    )
                ),
                6,
            ),
        }

    SUMMARY_JSON.write_text(json.dumps(summary, indent=2) + "\n")
    log.info("Saved: %s", SUMMARY_JSON.name)
    log.info(
        "Grid %d x %d; optimal q%d/q%d",
        len(hs_levels), len(ssh_levels), hs_optimal, ssh_optimal,
    )


if __name__ == "__main__":
    main()
