# Threshold Calibration — OSR11 Step 3

## Purpose

This module implements the **initial threshold calibration** phase of the OSR11
compound coastal hazard analysis. It uses the reported coastal disaster events
(Leal et al., 2024) as ground-truth references to evaluate whether a q90
threshold for significant wave height (Hₛ) and sea surface height (SSH) can
capture the observed hazardous conditions.

This is a **preliminary, visual calibration**. The approach is intentionally simple:
for each reported event, we inspect the local time series behaviour in a ±3-day
window and compare it against a stationary q90 threshold computed from the full
1993–2025 climatological series.

---

## Scientific Scope

| Item | Description |
|------|-------------|
| **Input** | `data/test/metocean_sc_sul_unified_waverys_grid.nc` (VHM0, zos, daily, WAVERYS grid) |
| **Events** | Leal et al. (2024) South sector reported coastal disasters |
| **Threshold** | q90 of the full daily series at the nearest coastal grid point |
| **Window** | ±3 days centred on the reported event date (7-day total) |
| **Variables** | Hₛ (m) and SSH (m) |
| **Key question** | Does the q90 threshold capture events simultaneously in both variables? |

---

## Module Structure

```
src/threshold_calibration/
├── __init__.py
├── README.md                  # This file
├── main.py                    # CLI entry point
├── io.py                      # Data loaders
├── events.py                  # Event record construction (municipality→grid→window)
├── thresholds.py              # q90 threshold computation + per-event metrics
├── event_figures.py           # Per-event visualisations (MagicA POT shading)
├── summary.py                 # Consolidated table + cross-event summary figures
├── utils.py                   # save_fig, make_output_dirs, muni_slug
└── config/
    ├── __init__.py
    └── analysis_config.py     # File paths and analysis parameters
```

---

## Analysis Parts

### Part TC-1 — Per-event figures

One figure per reported event, with two panels (Hₛ top, SSH bottom):

- 7-day time series in the event window
- q90 threshold as a horizontal dashed line
- Contiguous exceedance periods shaded (MagicA `peaks_over_threshold(event_wise=True)`)
- Reported event date marked with a vertical black line
- Maximum value in the window marked with a circle
- Text box: normalised maxima and concomitance summary

**Output:** `outputs/threshold_calibration/figures/events/fig_TC_event_{id}_{municipality}_{date}.png`

### Summary — Cross-event figures and table

| Output | Description |
|--------|-------------|
| `tab_TC_event_metrics.csv` | Per-event metrics (raw, normalised, concomitance) |
| `tab_TC_thresholds.csv` | q90 thresholds and climatological statistics per municipality |
| `fig_TC_S1` | Grouped bar chart: normalised Hₛ and SSH maxima per event |
| `fig_TC_S2` | Scatter: normalised Hₛ vs SSH, concurrent events highlighted |
| `fig_TC_S3` | Horizontal bar: concomitance fraction per event |
| `fig_TC_S4` | Heatmap: municipality × event date, colour = concomitance fraction |

---

## MagicA Usage

This analysis uses [MagicA](https://github.com/daniloceano/MagicA) for Peaks Over
Threshold (POT) identification within each event window:

```python
import magica as ma

processor = ma.read_data(series)          # pd.Series with DatetimeIndex
ea        = processor.get_extremes_analyzer()
peaks, peak_times = ea.peaks_over_threshold(
    threshold  = q90,
    event_wise = True,                    # one peak per contiguous exceedance block
)
```

The `event_wise=True` option returns one peak per consecutive exceedance episode,
consistent with the storm-segmentation philosophy adopted throughout OSR11.

If MagicA fails for a specific series, the error is logged and the figure is saved
without POT markers — it does not crash the pipeline.

---

## Municipality Coordinate Resolution

Grid-point assignment follows a priority cascade:

1. **Part E table** (`outputs/south_sc_test_data_exploratory/tables/
   tab_municipality_grid_association.csv`) — most accurate (IBGE centroids + KD-tree).
2. **Hardcoded coordinates** (approximate coastal positions, see `events.py`) — used
   when Part E has not been run.
3. **Domain-centre fallback** — last resort, with a warning.

---

## Assumptions and Limitations

- Thresholds are computed from the full annual series (no seasonal decomposition).
- Municipality–grid assignment uses the nearest grid cell; no spatial interpolation.
- The test domain covers only the South SC sector (~−29.4 to −27.6°S).
- Events from outside the dataset time range (before 1993 or after 2025) are skipped.
- Normalisation is ÷ climatological mean; negative SSH values require care in interpretation.
- q90 is an exploratory initial choice; systematic threshold optimisation (hit rate,
  false-alarm rate, CSI) is planned for the next calibration phase.

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Single unified dataset | Avoids temporal resampling inconsistencies between WAVERYS and GLORYS |
| ±3-day window | Covers the typical duration of extratropical wave/surge events; centred on the reported date to account for reporting lag |
| q90 from full series | Simple, reproducible, comparable across locations |
| MagicA `event_wise=True` | Treats consecutive days above threshold as one event; prevents multiple markers during a single storm |
| Normalisation by mean | Makes Hₛ and SSH comparable across different units and climatological regimes |
| Summary figures (S1–S4) | Covers different aspects: magnitude (S1), joint behaviour (S2), concomitance (S3), overview (S4) |

---

## Inputs

| File | Description |
|------|-------------|
| `data/test/metocean_sc_sul_unified_waverys_grid.nc` | Unified daily Hₛ + SSH dataset |
| `data/reported events/reported_events_Karine_sc.csv` | Coastal disaster events (Leal et al. 2024) |

## Outputs

```
outputs/threshold_calibration/
├── figures/
│   ├── events/          # Per-event PNG figures
│   └── summary/         # Cross-event summary figures
└── tables/
    ├── tab_TC_event_metrics.csv
    └── tab_TC_thresholds.csv
```
