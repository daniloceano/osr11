# Article Risk Figures

This folder contains a reproducible workflow for generating manuscript-style figures for the OSR11 coastal compound flooding risk analysis.

## Run

From the repository root:

```bash
python src/figures_article/make_article_coastal_hazard_components_map.py
python src/figures_article/make_article_hazard_vulnerability_risk_multiplot.py
python src/figures_article/make_article_top10_municipality_tables.py
python src/figures_article/make_article_calibration_map.py
python src/figures_article/make_article_calibration_heatmaps.py
python src/figures_article/make_article_supplementary_zos_mean_coastal_band_map.py
python src/figures_article/make_article_supplementary_integrated_risk_zooms.py
```

The map command writes `santa_catarina_study_area_and_grid_points.png`; the
heatmap command writes `pu_composite_calibration_heatmaps.png`. Regenerate both
with the two commands above. The equivalent module commands also remain supported:

```bash
python -m src.figures_article.make_article_coastal_hazard_components_map
python -m src.figures_article.make_article_hazard_vulnerability_risk_multiplot
python -m src.figures_article.make_article_top10_municipality_tables
python -m src.figures_article.make_article_calibration_map
python -m src.figures_article.make_article_calibration_heatmaps
python -m src.figures_article.make_article_supplementary_zos_mean_coastal_band_map
python -m src.figures_article.make_article_supplementary_integrated_risk_zooms
```

The supplementary-map command writes
`supplementary_temporal_mean_zos_within_200km_coast.png`. It shows the
1993--2025 temporal mean of raw GLORYS `zos` over valid ocean cells within
200 km of the Natural Earth coastline. It intentionally has no title, river
labels, or in-map legend; those explanations belong in the supplementary
caption embedded in the script header. Natural Earth 10-m lines delineate
countries and first-order administrative divisions (states or provinces).

For the calibration map, the visible coastline is extracted from the same
municipal polygons used for the shaded areas, ensuring exact geometric
alignment. The local Natural Earth 10 m coastline is used only to classify
which municipal-boundary segments are maritime. The visible SC–PR and SC–RS
borders likewise use shared edges from the municipal geometry.

Outputs are written to:

```text
outputs/article_figures/
```

The script saves publication-quality PNG files at 300 dpi. PDF and SVG article-figure exports are intentionally not generated.

Municipal geometries are reprojected to EPSG:4326 when needed and simplified for plotting with a topology-preserving tolerance of `0.001` degrees. Raw shapefiles in `outputs/risk_index/` are not modified.

## Expected Inputs

- Municipal risk shapefile from Karine:
  - `outputs/risk_index/risk_index.shp`
  - `outputs/risk_index/risk_index.shx`
  - `outputs/risk_index/risk_index.dbf`
  - `outputs/risk_index/risk_index.prj`
  - `outputs/risk_index/risk_index.cpg` if available
- Ocean-point compound hazard metrics:
  - current: `outputs/storm_catalog/compound_mhws/compound_metrics_mhws.csv`
  - superseded SSH_total product, archived for comparison:
    `outputs/legacy_ssh_total_method/hazard/compound_metrics.csv`
  - fallback candidates:
    - `site/public/data/hazard_characterization_grid_metrics.json`
    - `site/public/data/storm_maps_grid_metrics.json`
- Coastline context:
  - `data/ne_10m_coastline/ne_10m_coastline.shp`

## Generated Figures

- `coastal_hazard_index_components.png`
  - A 1 × 3 panel showing mean annual compound-event frequency
    (events yr⁻¹), mean integrated severity (dimensionless), and the resulting
    0--1 Hazard Index. Mean overlap duration is not part of the main figure.
  - Panels A--B display the native-grid catalog values in their own units. The integrated severity sums, over the days on
    which all detection criteria hold, the excess of each driver over its own
    local reference — the local q90 for waves and the mean high water springs
    datum for level — rescaled by the domain-wide Q05/Q95 of those daily
    excesses. Magnitude and persistence therefore enter as a single quantity.
  - For the Hazard calculation, frequency is divided by the fixed 99-event
    anchor and integrated severity by the fixed anchor 1, both capped at 1.
    Their equal-weight mean is the final index; no second Min--Max is applied.
    Duration was retired from the index on 2026-07-29; see AUD-06.
  - Every panel is projected onto Natural Earth coastline segments of at most
    5 km. Each segment receives the value at its nearest grid point in SIRGAS
    2000 / Brazil Polyconic (EPSG:5880).
- `hazard_vulnerability_risk_multiplot.png`
  - Uses a 2 × 2 layout for the four municipal risk components.
  - Panel A: `Hazard_Index_mun` — the fixed-anchor `Hazard_Index` transferred
    without municipal renormalization.
  - Panel B: `Exposure_Index` — geometric mean of the fixed-goalpost absolute
    component and municipal share, both calculated from the weighted effective
    population in the cumulative 1, 2, 5, and 10 km coastal bands.
  - Panel C: `Vulnerability_CDF_PC1 = Φ(PC1/sd(PC1,ddof=0))`.
  - Panel D: `Risk_Hazard = (Hazard_Index_mun × Exposure_Index × Vulnerability_CDF_PC1)^(1/3)`,
    without floor or final Min--Max.
  - Uses discrete green-to-red classes derived from the inverted Composite
    Score heatmap palette.
  - Includes Natural Earth country and Brazilian-state boundaries over gray
    land and a light-blue ocean.
- `supplementary_integrated_risk_zooms.png`
  - Panel A: integrated-risk detail for RS, SC, PR, SP, and RJ.
  - Panel B: integrated-risk detail from ES to Natal (RN).
  - Panel C: integrated-risk detail from Natal (RN) to PI.
  - Panel D: integrated-risk detail from PI to PA.
  - The 2 × 2 sequence provides continuous zoom coverage of the Brazilian
    coast, with slight overlap at the joins between regional windows.
  - Coastal municipalities from neighboring states are also colored wherever
    they intersect the fixed map extents.
  - Uses the same global 0–1 discrete limits as the integrated-risk panel in
    the main figure, so colors remain directly comparable.

## Generated Tables

The table script writes CSV and publication-ready LaTeX versions below
`outputs/article_figures/tables/` for the top 10 municipalities by:

- `Hazard_Index`;
- `SVI_Coast_2022`;
- `Risk_Hazard` (or the detected risk-field fallback).

Every table includes municipality, state name, and state abbreviation.

## Alias Detection

The script does not assume exact shapefile DBF names. It detects aliases for:

- municipality name: `NM_MUN`, `municipio`, `municipali`
- state/UF: `SIGLA_UF`, `uf`
- `SVI_Coast_2022`: `SVI_Coast_2022`, `SVI_Coast_`, `SVI_Coast`, `SVI_Coa`, `SVI`
- `compound_c`: `compound_c`, `compound`, `comp_c`
- `mean_overl`: `mean_overl`, `mean_ove`, `mean_overlap_duration`
- `mean_compo`: `mean_compo`, `mean_com`, `mean_compound_intensity_norm`

## Coastal-Line Map — Values and Shared Implementation

The coastal-line map displays panels A--B in the catalog's own units
(events yr⁻¹ and dimensionless) and panel C as the final composite index.
The index construction uses fixed anchors independent of sample extrema:

```text
Hazard_Frequency = min(compound_count_total / 99, 1)
Hazard_Severity  = min(fillna(mean_integrated_severity, 0) / 1, 1)
Hazard_Index_raw = (Hazard_Frequency + Hazard_Severity) / 2
Hazard_Index = Hazard_Index_raw
```

The formula itself lives in `src/04_risk_integration/hazard_index.py`; the
projection of grid values onto coastline segments lives in
`src/04_risk_integration/coastal_projection.py`; the discrete class colors live
in `src/04_risk_integration/palettes.py`. These figure scripts import all three
rather than reimplementing them, and the website exporter
(`src/site/export_coastal_hazard_data.py`) imports the same modules, so the
article figure and the site map are geometrically and chromatically identical.

The component panels use the discrete reversed-magma palette formerly used for
the annual-rate coastline map, but each panel has its own colorbar in the
catalog's displayed units. The Hazard Index uses the same discrete
green-to-red palette as the municipal integrated-risk figure.

## Interpretation Caveat

The risk indices are comparative/relative across Brazilian coastal municipalities. They should not be interpreted as absolute expected damage or as the absence/presence of coastal hazards. For example, a state with relevant physical coastal hazards may rank lower in the integrated map if its relative social vulnerability is lower than municipalities elsewhere.

Machine-readable files record the actual input files, aliases, ranges,
coastal-assignment diagnostics, discrete color boundaries, and table rows:

```text
outputs/article_figures/metadata/article_risk_figure_summary.json
outputs/article_figures/metadata/article_coastal_hazard_index_components_metadata.json
outputs/article_figures/metadata/article_hazard_vulnerability_risk_metadata.json
outputs/article_figures/metadata/article_top10_municipality_tables_metadata.json
```

Figure filenames are descriptive `snake_case` names and never encode manuscript order. Apply figure numbers in LaTeX, captions, or the journal production workflow, not in generated filenames. The generator validates the PNG-only, semantic-name policy and all figure paths stored in metadata after every run.
