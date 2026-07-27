# Exploratory hazard-index comparison

This folder contains a diagnostic comparison of:

1. the former count-only municipal Hazard Index;
2. the current official equal-weight Hazard Index based on compound-event
   frequency, mean overlap duration, and mean normalized intensity, with the
   aggregated result subsequently Min--Max normalized to 0--1; and
3. the difference `count-only - multimetric`.

The municipal comparison uses the official component and Hazard fields in
`site/public/data/risk_index_municipalities.geojson`. This exploratory product
audits the methodological change and does not modify the official hazard or
integrated-risk indices.

The same multimetric formula is also calculated for all 808 native ocean grid
points and transposed to the Natural Earth coastline. Coastline segments no
longer than 5 km are assigned the value at their nearest native grid point in
EPSG:5880. To preserve a complete 0--1 native-grid product, the component and
final Min--Max normalizations use the 808-point grid domain. The coastal
figure repeats the three-panel comparison: former count-only index, current
normalized multimetric index, and `count-only - multimetric`.

Run from the repository root:

```bash
python src/exploratory/make_exploratory_hazard_index_comparison.py
```

Generated products are organized into `figures/`, `data/`, and `metadata/`.
