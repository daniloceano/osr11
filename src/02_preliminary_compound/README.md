# Preliminary Compound Event Occurrence Analysis — OSR11 Step 3

**Directory:** `src/02_preliminary_compound/`
**Analysis step:** Step 3 in the OSR11 8-step pipeline
**Domain:** Full Santa Catarina coast — all 5 Leal et al. (2024) sectors

---

## Purpose

This module implements the **initial preliminary compound event occurrence** phase of the OSR11
compound coastal hazard analysis. It uses the Leal et al. (2024) reported coastal
disaster database as ground-truth references to evaluate whether a q90 threshold
for significant wave height (Hₛ) and sea surface height (SSH) captures the
observed hazardous conditions.

This is a **preliminary, visual calibration**. For each reported event, the local
time series behaviour in a ±3-day window is inspected and compared against a
stationary q90 threshold computed from the full 1993–2025 climatological series.

---

## Scientific Scope

| Item | Description |
|------|-------------|
| **Input dataset** | `data/test/metocean_sc_full_unified_waverys_grid.nc` (VHM0, zos, daily, WAVERYS grid) |
| **Events database** | Leal et al. (2024) — all SC sectors (91 events, 22 municipalities) |
| **Sectors** | North, Central-north, Central, Central-south, South |
| **Threshold** | q90 of the full daily series at the nearest ocean grid point |
| **Window** | ±3 days centred on the reported event date (7-day total) |
| **Variables** | Hₛ (m) and SSH (m) |
| **Key question** | Does the q90 threshold capture events simultaneously in both variables? |

---

## Module Structure

```
src/02_preliminary_compound/
├── __init__.py
├── README.md                  # This file
├── RUN.md                     # Quick-start command reference
├── main.py                    # CLI entry point
├── io.py                      # Data loaders (supports target_sector=None for all sectors)
├── events.py                  # Event record construction (municipality→grid→window)
├── thresholds.py              # q90 threshold computation + per-event metrics
├── event_figures.py           # Per-event visualisations (MagicA POT shading)
├── summary.py                 # Consolidated table + cross-event summary figures
├── utils.py                   # save_fig, make_output_dirs, muni_slug
└── config/
    ├── __init__.py
    └── analysis_config.py     # File paths and analysis parameters (target_sector=None)
```

> **Note on imports:** This directory is registered as `src.preliminary_compound` via
> a compatibility alias in `src/__init__.py`. All existing `from src.preliminary_compound.xxx import`
> statements continue to work unchanged. Adding new numbered modules only requires updating
> the `_MODULE_ALIASES` dict in `src/__init__.py`.

---

## Analysis Parts

### Part TC-1 — Per-event figures

One figure per reported event (91 total), with two panels (Hₛ top, SSH bottom):

- 7-day time series in the event window
- q90 threshold as a horizontal dashed line
- Contiguous exceedance periods shaded (MagicA `peaks_over_threshold(event_wise=True)`)
- Reported event date marked with a vertical black line
- Maximum value in the window marked with a circle
- Text box: normalised maxima and concomitance summary

**Output:** `outputs/preliminary_compound/figures/events/fig_TC_event_{id}_{municipality}_{date}.png`

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

## Key Results (Preliminary)

- **91 events** across **22 municipalities** and **5 sectors** processed.
- **47 events** have valid Hₛ data; **10 events** have valid joint Hₛ + SSH data.
- Data gaps are concentrated in the North sector: many municipalities have the
  nearest ocean grid cell over land or in unresolved coastal embayments.
- **2 events** show concurrent q90 exceedances (both in Barra Velha: May 2001,
  March 2019). This 2% rate at q90 is expected and serves as the baseline for
  systematic threshold optimisation in the next phase.
- Mean normalised Hₛ maximum: **1.74×** the climatological mean.
- Mean normalised SSH maximum: **2.93×** the climatological mean.

---

## MagicA Usage

MagicA is not on PyPI. Install from GitHub:

```bash
pip install git+https://github.com/daniloceano/MagicA.git
```

Usage in this module:

```python
import magica as ma

processor = ma.read_data(series)          # pd.Series with DatetimeIndex
ea        = processor.get_extremes_analyzer()
peaks, peak_times = ea.peaks_over_threshold(
    threshold  = q90,
    event_wise = True,    # one peak per contiguous exceedance block
)
```

The `event_wise=True` option returns one peak per consecutive exceedance episode,
consistent with the storm-segmentation philosophy adopted throughout OSR11.

---

## Municipality Coordinate Resolution

Grid-point assignment follows a priority cascade:

1. **Part E table** (`outputs/south_sc_test_data_exploratory/tables/
   tab_municipality_grid_association.csv`) — most accurate (IBGE centroids + KD-tree).
   Currently covers only South sector municipalities.
2. **Hardcoded coordinates** (approximate coastal positions for all 5 sectors, see `events.py`).
3. **Domain-centre fallback** — last resort, logged as a warning.

---

## Domain expansion (from South SC to Full SC)

| Item | South SC (previous) | Full SC (current) |
|------|--------------------|--------------------|
| Input dataset | `metocean_sc_sul_unified_waverys_grid.nc` | `metocean_sc_full_unified_waverys_grid.nc` |
| Sectors | South only | North, Central-north, Central, Central-south, South |
| Municipalities | ~7 | 22 |
| Events | ~9 | 91 |
| target_sector | `"South"` | `None` (all sectors) |
| Grid lat range | −29.4° to −27.6° | −29.4° to −26.0° |

---

## Assumptions and Limitations

- Thresholds are computed from the full annual series (no seasonal decomposition).
- Municipality–grid assignment uses the nearest ocean grid cell; no spatial interpolation.
- Many northern SC municipalities have grid points over land → NaN thresholds and metrics.
- Events from outside the dataset time range are skipped with a warning.
- q90 is an exploratory initial choice; systematic threshold optimisation (hit rate,
  false-alarm rate, CSI over a threshold grid) is the immediate next step.

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Single unified dataset | Avoids temporal resampling inconsistencies between WAVERYS and GLORYS |
| ±3-day window | Covers typical extratropical wave/surge event duration; centred on reported date to account for reporting lag |
| q90 from full series | Simple, reproducible, comparable across locations |
| `target_sector=None` | All SC sectors included to match the full test domain extent |
| MagicA `event_wise=True` | One peak per consecutive exceedance block; consistent with storm-segmentation philosophy |
| Normalisation by mean | Makes Hₛ and SSH comparable across different units and climatological regimes |

---

## Inputs

| File | Description |
|------|-------------|
| `data/test/metocean_sc_full_unified_waverys_grid.nc` | Unified daily Hₛ + SSH dataset, full SC |
| `data/reported events/reported_events_Karine_sc.csv` | Coastal disaster events (Leal et al. 2024) |

## Outputs

```
outputs/preliminary_compound/
├── figures/
│   ├── events/          # Per-event PNG figures (91 files)
│   └── summary/         # Cross-event summary figures (S1–S4)
└── tables/
    ├── tab_TC_event_metrics.csv
    └── tab_TC_thresholds.csv
```
