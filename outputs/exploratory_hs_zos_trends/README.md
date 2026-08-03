# Exploratory Hs and zos trend analysis

This folder centralizes the exploratory daily time-series and trend analysis
for significant wave height (`Hs`) and sea-surface height (`zos`) along the
Brazilian coast, covering 1993--2025.

## Definitions

- `Hs` is the daily maximum of 3-hourly WAVERYS VHM0.
- `Hs′` and `zos′` are local-mean anomalies over 1993--2025.
- `Hs*` and `zos*` are the prime anomalies after subtracting each point's
  1993--2025 monthly climatology.
- Trends are Theil--Sen slopes fitted to annual means and reported in
  millimetres per year.

## Figures

- `hs_timeseries_1993_2025.png` and `hs_prime_timeseries_1993_2025.png`
- `hs_timeseries_2020_2025.png` and `hs_prime_timeseries_2020_2025.png`
- `zos_timeseries_1993_2025.png` and `zos_prime_timeseries_1993_2025.png`
- `zos_timeseries_2020_2025.png` and `zos_prime_timeseries_2020_2025.png`
- `hs_star_timeseries_1993_2025.png` and `zos_star_timeseries_1993_2025.png`
- `hs_zos_trend_maps.png`: full-coast trends at all 808 hazard-grid points.

Each time-series figure contains eight locations and a locator map. The
full-period figures include the Theil--Sen trend in each panel.

## Processed data and provenance

- `data/hs_points/`: daily Hs extracts for the eight displayed locations.
- `data/zos_points/`: daily zos extracts for the same locations.
- `data/coastal_trends_all_808_points.csv`: four trends and their 95% slope
  intervals for every coastal hazard-grid point.
- `zos_timeseries_metadata.json` and `trend_analysis_metadata.json`: detailed
  definitions, source paths, coordinates, outputs, and trend results.

The full raw GLORYS12 and WAVERYS cubes remain centralized on the remote
`swell` server. Only lightweight processed point extracts and trend summaries
are stored locally.
