# Article Figures

This directory contains publication-quality article figures for the OSR11 analysis. Figure images are exported only as PNG at 300 dpi; PDF and SVG versions are intentionally not generated.

Filenames use descriptive `snake_case` and describe scientific content, for example `final_integrated_risk.png`. They never contain manuscript order (`fig01_`, `figure_01_`, `01_`, or equivalent). Figure numbering belongs in LaTeX, captions, or journal production and may change without renaming these files.

Machine-readable summaries and manifests are stored in `metadata/`. Every figure path in those files must point to an existing semantic PNG filename.

Regenerate the current figures from the repository root:

```bash
python -m src.figures_article.make_article_coastal_compound_event_rate_map
python -m src.figures_article.make_article_hazard_vulnerability_risk_multiplot
python -m src.figures_article.make_article_top10_municipality_tables
python -m src.figures_article.make_article_calibration_map
python -m src.figures_article.make_article_calibration_heatmaps
python -m src.figures_article.make_article_supplementary_zos_mean_coastal_band_map
```

The command removes obsolete PDF, SVG, and ordinally named article images before generation, then validates the directory and metadata. A policy violation causes a clear error.

The PU calibration multiplot uses the original 12-colour sequence as **worse → better** for `R_pos`, while `B` and `F_soft/P` reverse it because lower is better. The `Score` panel has its own green-to-purple 12-colour sequence, applied in reverse as requested. These orientations are recorded in `metadata/article_calibration_figure_summary.json` so later palette changes preserve the scientific meaning.

The coastal-risk workflow writes `coastal_compound_event_rate_per_year.png`
and `hazard_vulnerability_risk_multiplot.png`. The first divides native-grid
total event counts by the 33-year record length and projects the resulting
annual frequencies onto short coastline segments; the second shows municipal
Hazard, SVI, and integrated risk with discrete green-to-red classes.
Associated top-10 CSV and LaTeX tables are stored in `tables/`.

The supplementary `zos` map is saved as
`supplementary_temporal_mean_zos_within_200km_coast.png`. Its supporting
coastal-band fields and machine-readable generation metadata are stored in
`data/` and `metadata/`, respectively.
