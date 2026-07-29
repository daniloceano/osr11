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

The two sea-level panels use ten discrete classes. The `zos` display is capped
at 0.4 m, with values above this limit retained in the data and represented by
the upper color class.

The Hs panel uses 0.2-m classes between 0 and 3 m. The ten user-provided Hs
color anchors are linearly interpolated to the 15 required classes; values
above 3 m remain in the data and use the upper display class.

A second three-panel figure replaces Hs with the empirical visual proxy
`0.2 * Hs`, while retaining the same `zos` and FES2022 panels. Its class
interval is 0.04 m, exactly 20% of the Hs interval, and its display maximum is
0.6 m. Because multiplication by 0.2 is a positive linear transformation,
`q90(0.2 * Hs) = 0.2 * q90(Hs)`. This proxy is not a hydrodynamic wave-setup
calculation and does not represent bathymetry, beach slope, breaking, wave
period, direction, or dissipation.

An additional two-panel figure shows:

1. `q90(Hs)` only where the native-point value is at least 0.5 m; lower-value
   source points are retained in the data table but their coastline segments
   are left uncolored.
2. A conditional sea-level q90. Where
   `q = [q90(zos) + 0.2 q90(Hs)] / q90(FES tide)` is below one, the displayed
   field is `q90(zos)`. Where `q >= 1`, it is the production q90 of the daily
   `SSH_total = zos + tide_daily_max` series (`thr_ssh_total_abs` in the
   compound-metrics table).

The second panel is therefore a pointwise hybrid selected from two q90 fields,
not the q90 of one homogeneous daily time series.

The package also contains a two-panel coastal ratio figure. Panel A shows
`q90(zos) / q90(FES2022 daily-maximum tide)`, while panel B shows
`[q90(zos) + 0.2 q90(Hs)] / q90(FES2022 daily-maximum tide)`. The panels use
one shared discrete scale with an explicit class boundary and reference line
at one. These dimensionless fields combine temporal quantiles already
calculated at each native point; they are not temporal quantiles of daily
ratios or a time-synchronous summed water level. Values below one indicate a
larger astronomical-tide q90, while values above one indicate that the
corresponding numerator exceeds the astronomical-tide q90.

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
