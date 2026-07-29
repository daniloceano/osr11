# Exploratory coastal q90 maps

This output compares the local temporal 90th percentile of three daily
metocean fields during 1993–2025:

- WAVERYS significant wave height (`VHM0`), represented by the daily maximum;
- GLORYS12 dynamic sea level (`zos`) at 00:00 UTC;
- the FES2022 astronomical tide evaluated hourly and represented by its daily
  maximum.

The quantiles are computed separately at every native coastal grid point used
by the production compound-event catalogue. The displayed coastline is only a
cartographic projection: each Natural Earth segment receives the value of its
nearest native point. Values are not spatially interpolated, normalized, or
combined.

Run from the repository root:

```bash
python src/exploratory/make_exploratory_q90_hs_zos_fes_coastal_map.py
```

The NetCDF calculation is intentionally exact and can take several minutes.
For layout-only changes, reuse the generated native-grid CSV:

```bash
python src/exploratory/make_exploratory_q90_hs_zos_fes_coastal_map.py --reuse-data
```

Generated artifacts are stored under `figures/`, `data/`, and `metadata/`.
