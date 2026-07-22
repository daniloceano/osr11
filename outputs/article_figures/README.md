# Article Figures

This directory contains publication-quality article figures for the OSR11 analysis. Figure images are exported only as PNG at 300 dpi; PDF and SVG versions are intentionally not generated.

Filenames use descriptive `snake_case` and describe scientific content, for example `final_integrated_risk.png`. They never contain manuscript order (`fig01_`, `figure_01_`, `01_`, or equivalent). Figure numbering belongs in LaTeX, captions, or journal production and may change without renaming these files.

Machine-readable summaries and manifests are stored in `metadata/`. Every figure path in those files must point to an existing semantic PNG filename.

Regenerate the current figures from the repository root:

```bash
python -m src.figures_article.make_article_risk_figures
python -m src.figures_article.make_article_calibration_figures
```

The command removes obsolete PDF, SVG, and ordinally named article images before generation, then validates the directory and metadata. A policy violation causes a clear error.

The PU calibration multiplot uses the original 12-colour sequence as **worse → better** for `R_pos`, while `B` and `F_soft/P` reverse it because lower is better. The `Score` panel has its own green-to-purple 12-colour sequence, applied in reverse as requested. These orientations are recorded in `metadata/article_calibration_figure_summary.json` so later palette changes preserve the scientific meaning.
