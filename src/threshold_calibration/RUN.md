# Running the Threshold Calibration Analysis

## Environment

```bash
conda activate osr
```

## Run All Parts

```bash
# From project root
python src/threshold_calibration/main.py --all

# Equivalent (default when no flag given)
python src/threshold_calibration/main.py
```

## Run Individual Parts

```bash
# Part TC-1: per-event figures only
python src/threshold_calibration/main.py --event-figures

# Summary table + cross-event figures only
python src/threshold_calibration/main.py --summary
```

## As a Module

```bash
python -m src.threshold_calibration.main --all
```

## Output Locations

```
outputs/threshold_calibration/
├── figures/
│   ├── events/    ← one PNG per reported event
│   └── summary/   ← S1–S4 cross-event figures
└── tables/
    ├── tab_TC_event_metrics.csv
    └── tab_TC_thresholds.csv
```

## Notes

- The analysis requires the unified metocean dataset:
  `data/test/metocean_sc_sul_unified_waverys_grid.nc`
- If the Part E municipality–grid association table is available
  (`outputs/south_sc_test_data_exploratory/tables/tab_municipality_grid_association.csv`),
  it will be used for more accurate grid-point assignment. Otherwise, hardcoded
  approximate coastal coordinates are used.
- MagicA must be installed in the `osr` environment:
  ```bash
  pip install -e /path/to/MagicA
  ```
