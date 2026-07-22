# Article Risk Figures

This folder contains a reproducible workflow for generating manuscript-style figures for the OSR11 coastal compound flooding risk analysis.

## Run

From the repository root:

```bash
python -m src.figures_article.make_article_risk_figures
python -m src.figures_article.make_article_calibration_figures
```

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
- Original ocean-point compound hazard metrics:
  - preferred: `outputs/storm_catalog/compound/compound_metrics.csv`
  - fallback candidates:
    - `site/public/data/hazard_characterization_grid_metrics.json`
    - `site/public/data/storm_maps_grid_metrics.json`
- Coastline context:
  - `data/ne_10m_coastline/ne_10m_coastline.shp`

## Generated Figures

- `hazard_vulnerability_risk_multiplot.png`
  - Panel A: current `Hazard_Index = norm(compound_c)`
  - Panel B: `SVI_Coast_2022`
  - Panel C: current `Risk_Hazard`
- `final_integrated_risk.png`
  - Standalone final integrated risk map using current `Risk_Hazard`.
  - Includes a top-municipality ranking inset.
- `original_ocean_hazard_points.png`
  - Original oceanic compound-event count points before municipal transfer/spatial association.

## Alias Detection

The script does not assume exact shapefile DBF names. It detects aliases for:

- municipality name: `NM_MUN`, `municipio`, `municipali`
- state/UF: `SIGLA_UF`, `uf`
- `SVI_Coast_2022`: `SVI_Coast_2022`, `SVI_Coast_`, `SVI_Coast`, `SVI_Coa`, `SVI`
- `Hazard_Index`: `Hazard_Index`, `Haz_index`, `Hazard_In`, `Hazard`, `azard_Inde`
- `Risk_Comp`: `Risk_Comp`, `Risk_comp`, `Risk_Com`, `risk_index`
- `Risk_Hazard`: `Risk_Hazard`, `Risk_harza`, `Risk_Haza`, `Risk_Haz`, `risk_inde1`
- `compound_c`: `compound_c`, `compound`, `comp_c`
- `mean_overl`: `mean_overl`, `mean_ove`, `mean_overlap_duration`
- `mean_compo`: `mean_compo`, `mean_com`, `mean_compound_intensity_norm`

For Figure 3, the current scope visualizes compound-event count. If an oceanic `Hazard_Index`
field is absent, the script uses `compound_c` directly:

```text
compound_c
```

The plotting color scale remains relative to the available ocean-point values.

## Interpretation Caveat

The risk indices are comparative/relative across Brazilian coastal municipalities. They should not be interpreted as absolute expected damage or as the absence/presence of coastal hazards. For example, a state with relevant physical coastal hazards may rank lower in the integrated map if its relative social vulnerability is lower than municipalities elsewhere.

The generated summary file records the actual input files, aliases, ranges, and whether Figure 3 read or computed `Hazard_Index`:

```text
outputs/article_figures/metadata/article_risk_figure_summary.json
```

Figure filenames are descriptive `snake_case` names and never encode manuscript order. Apply figure numbers in LaTeX, captions, or the journal production workflow, not in generated filenames. The generator validates the PNG-only, semantic-name policy and all figure paths stored in metadata after every run.
