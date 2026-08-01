r"""Generate top-10 municipality tables for Hazard, SVI, and integrated risk.

Suggested LaTeX commands (requires ``\usepackage{booktabs}``)
-----------------------------------------------------------------
\input{outputs/article_figures/tables/top10_municipalities_by_hazard.tex}
\input{outputs/article_figures/tables/top10_municipalities_by_svi.tex}
\input{outputs/article_figures/tables/top10_municipalities_by_integrated_risk.tex}

Each table contains rank, municipality, state name, state abbreviation, and
the corresponding index value. CSV versions are generated alongside the
publication-ready LaTeX tables. The integrated-risk values use the normalized
0--1 product exported by ``src.site.export_risk_index_data``.

Run from the repository root:

    python src/figures_article/make_article_top10_municipality_tables.py
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import geopandas as gpd
import pandas as pd


RISK_PATH = ROOT / "site" / "public" / "data" / "risk_index_municipalities.geojson"
RISK_METADATA_PATH = ROOT / "site" / "public" / "data" / "risk_index_metadata.json"
TABLE_DIR = ROOT / "outputs" / "article_figures" / "tables"
METADATA_PATH = (
    ROOT
    / "outputs"
    / "article_figures"
    / "metadata"
    / "article_top10_municipality_tables_metadata.json"
)

TABLE_SPECS: dict[str, dict[str, str]] = {
    "hazard": {
        "field": "Hazard_Index",
        "value_label": "Hazard index",
        "stem": "top10_municipalities_by_hazard",
        "caption": (
            "Top 10 Brazilian coastal municipalities by "
            "fixed-anchor frequency–integrated-severity hazard index."
        ),
        "latex_label": "tab:top10-municipal-hazard",
    },
    "svi": {
        "field": "SVI_Coast_2022",
        "value_label": "SVI",
        "stem": "top10_municipalities_by_svi",
        "caption": (
            "Top 10 Brazilian coastal municipalities by Social "
            "Vulnerability Index (SVI)."
        ),
        "latex_label": "tab:top10-municipal-svi",
    },
    "integrated_risk": {
        "field": "Risk_Hazard",
        "value_label": "Risk index",
        "stem": "top10_municipalities_by_integrated_risk",
        "caption": (
            "Top 10 Brazilian coastal municipalities by the integrated "
            "compound-risk index. Ranks 1--3 are stable across a bootstrap over "
            "the 33 years of record, but the 90\\% intervals of ranks 4--11 "
            "overlap, so the ordering within that band is not resolved; see the "
            "rank-uncertainty and aggregation-sensitivity tables "
            "(AUD-07 supplementary). Two entries carry a declared spatial-support "
            "caveat: Mag\\'e and Paraty sit inside sheltered bays and draw their "
            "hazard from open-shelf grid points 35 and 15 km away, so their "
            "hazard is imported from outside the embayment that shelters them; "
            "the recurrent flooding documented at both is fluvial and pluvial "
            "rather than wave-driven (AUD-04, AUD-05)."
        ),
        "latex_label": "tab:top10-municipal-integrated-risk",
    },
}


def _relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _latex_escape(value: Any) -> str:
    text = str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    return text


def _rank_table(
    municipalities: gpd.GeoDataFrame,
    *,
    field: str,
    value_label: str,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    required = {
        "municipality_name",
        "state",
        "state_name",
        field,
    }
    missing = sorted(required.difference(municipalities.columns))
    if missing:
        raise RuntimeError(f"Missing table fields: {', '.join(missing)}")

    ranked = municipalities.dropna(subset=[field]).copy()
    ranked[field] = pd.to_numeric(ranked[field], errors="coerce")
    ranked = ranked.dropna(subset=[field]).sort_values(
        [field, "municipality_name"],
        ascending=[False, True],
        kind="mergesort",
    ).head(10)
    table = pd.DataFrame(
        {
            "Rank": range(1, len(ranked) + 1),
            "Municipality": ranked["municipality_name"].astype(str).to_numpy(),
            "State": ranked["state_name"].astype(str).to_numpy(),
            "UF": ranked["state"].astype(str).to_numpy(),
            value_label: ranked[field].astype(float).to_numpy(),
        }
    )
    return table, table.to_dict(orient="records")


def _write_latex(
    table: pd.DataFrame,
    *,
    value_label: str,
    caption: str,
    latex_label: str,
    path: Path,
) -> None:
    lines = [
        r"\begin{table}[htbp]",
        rf"\caption{{{_latex_escape(caption)}}}",
        rf"\label{{{latex_label}}}",
        r"\begin{tabular}{rlllr}",
        r"\toprule",
        rf"Rank & Municipality & State & UF & {_latex_escape(value_label)} \\",
        r"\midrule",
    ]
    for row in table.to_dict(orient="records"):
        lines.append(
            f"{int(row['Rank'])} & "
            f"{_latex_escape(row['Municipality'])} & "
            f"{_latex_escape(row['State'])} & "
            f"{_latex_escape(row['UF'])} & "
            f"{float(row[value_label]):.3f} \\\\"
        )
    lines.extend(
        [
            r"\bottomrule",
            r"\end{tabular}",
            r"\end{table}",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    if not RISK_PATH.exists():
        raise FileNotFoundError(RISK_PATH)
    municipalities = gpd.read_file(RISK_PATH)
    source_metadata = json.loads(RISK_METADATA_PATH.read_text(encoding="utf-8"))

    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    table_metadata: dict[str, Any] = {}
    outputs: list[str] = []
    for name, spec in TABLE_SPECS.items():
        table, rows = _rank_table(
            municipalities,
            field=spec["field"],
            value_label=spec["value_label"],
        )
        csv_path = TABLE_DIR / f"{spec['stem']}.csv"
        latex_path = TABLE_DIR / f"{spec['stem']}.tex"
        table.to_csv(csv_path, index=False, float_format="%.3f")
        _write_latex(
            table,
            value_label=spec["value_label"],
            caption=spec["caption"],
            latex_label=spec["latex_label"],
            path=latex_path,
        )
        table_metadata[name] = {
            "field": spec["field"],
            "value_label": spec["value_label"],
            "rows": rows,
            "csv": _relative(csv_path),
            "latex": _relative(latex_path),
        }
        outputs.extend([_relative(csv_path), _relative(latex_path)])

    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": _relative(RISK_PATH),
        "source_metadata": _relative(RISK_METADATA_PATH),
        "risk_key": "Risk_Hazard",
        "risk_normalization": source_metadata["integrated_risk_normalization"],
        "ranking": (
            "descending; municipality name ascending as deterministic tie-breaker"
        ),
        "tables": table_metadata,
    }
    METADATA_PATH.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("\n".join(outputs))


if __name__ == "__main__":
    main()
