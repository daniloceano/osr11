# Article Figures

This directory contains publication-quality article figures for the OSR11 analysis. Figure images are exported only as PNG at 300 dpi; PDF and SVG versions are intentionally not generated.

Filenames use descriptive `snake_case` and describe scientific content, for example `final_integrated_risk.png`. They never contain manuscript order (`fig01_`, `figure_01_`, `01_`, or equivalent). Figure numbering belongs in LaTeX, captions, or journal production and may change without renaming these files.

Machine-readable summaries and manifests are stored in `metadata/`. Every figure path in those files must point to an existing semantic PNG filename.

Regenerate the current figures from the repository root:

```bash
python -m src.figures_article.make_article_coastal_hazard_components_map
python -m src.figures_article.make_article_hazard_vulnerability_risk_multiplot
python -m src.figures_article.make_article_top10_municipality_tables
python -m src.figures_article.make_article_calibration_map
python -m src.figures_article.make_article_calibration_heatmaps
python -m src.figures_article.make_article_supplementary_zos_mean_coastal_band_map
python -m src.figures_article.make_article_supplementary_integrated_risk_zooms
```

The command removes obsolete PDF, SVG, and ordinally named article images before generation, then validates the directory and metadata. A policy violation causes a clear error.

The PU calibration multiplot uses the original 12-colour sequence as **worse → better** for `R_pos`, while `B` and `F_soft/P` reverse it because lower is better. The `Score` panel has its own green-to-purple 12-colour sequence, applied in reverse as requested. These orientations are recorded in `metadata/article_calibration_figure_summary.json` so later palette changes preserve the scientific meaning.

The coastal-risk workflow writes `coastal_hazard_index_components.png` and
`hazard_vulnerability_risk_multiplot.png`. The first is a 2 × 2 coastline
panel of mean annual frequency (events yr⁻¹), mean overlap duration (days),
mean compound intensity (dimensionless), and their normalized equal-weight
Hazard Index. The first three panels show catalog values without an additional
cross-grid rescaling and have individual colorbars. They use the
reversed-magma palette of the former annual-rate map, while the Hazard panel
uses the integrated-risk green-to-red palette. The second figure shows
municipal Hazard, SVI, and the final 0–1 normalized integrated risk with
discrete green-to-red classes.
Associated top-10 CSV and LaTeX tables are stored in `tables/`.

The supplementary integrated-risk zooms are saved as
`supplementary_integrated_risk_zooms.png`. Panel A shows RS through RJ and
panel B shows PA through PI, with a shared discrete scale identical to the
0–1 integrated-risk panel of the main multiplot. Municipalities from
neighboring states are colored whenever they intersect the unchanged regional
map extents.

The supplementary `zos` map is saved as
`supplementary_temporal_mean_zos_within_200km_coast.png`. Its supporting
coastal-band fields and machine-readable generation metadata are stored in
`data/` and `metadata/`, respectively.
