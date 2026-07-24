r"""Generate top-10 municipality tables for Hazard, SVI, and integrated risk.

Suggested LaTeX commands (requires ``\usepackage{booktabs}``)
-----------------------------------------------------------------
\input{outputs/article_figures/tables/top10_municipalities_by_hazard.tex}
\input{outputs/article_figures/tables/top10_municipalities_by_svi.tex}
\input{outputs/article_figures/tables/top10_municipalities_by_integrated_risk.tex}

Each table contains rank, municipality, state name, state abbreviation, and
the corresponding original index value. CSV versions are generated alongside
the publication-ready LaTeX tables.

Run from the repository root:

    python src/figures_article/make_article_top10_municipality_tables.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.figures_article.make_article_risk_figures import (
    make_top10_municipality_tables,
    read_risk_data,
)


def main() -> None:
    municipalities, metadata = read_risk_data()
    outputs = make_top10_municipality_tables(
        municipalities,
        metadata["risk_panel_key"],
    )
    print("\n".join(outputs))


if __name__ == "__main__":
    main()
