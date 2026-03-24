# Running the Preliminary Compound Event Occurrence Analysis Analysis

## Environment

```bash
conda activate osr11
```

## Run All Parts

```bash
# From project root (recommended — uses import alias)
python -m src.preliminary_compound.main --all

# Direct script invocation also works
python src/02_preliminary_compound/main.py --all
```

## Run Individual Parts

```bash
# Part TC-1: per-event figures only
python -m src.preliminary_compound.main --event-figures

# Summary table + cross-event figures only
python -m src.preliminary_compound.main --summary
```

## Output Locations

```
outputs/preliminary_compound/
├── figures/
│   ├── events/    ← one PNG per reported event (91 events, full SC coast)
│   └── summary/   ← S1–S4 cross-event figures
└── tables/
    ├── tab_TC_event_metrics.csv
    └── tab_TC_thresholds.csv
```

## Notes

- The analysis requires the unified metocean dataset:
  `data/test/metocean_sc_full_unified_waverys_grid.nc`
- If the Part E municipality–grid association table is available
  (`outputs/south_sc_test_data_exploratory/tables/tab_municipality_grid_association.csv`),
  it will be used for more accurate grid-point assignment for South sector municipalities.
  For other sectors, hardcoded approximate coastal coordinates are used.
- MagicA must be installed from GitHub (not on PyPI):
  ```bash
  pip install git+https://github.com/daniloceano/MagicA.git
  ```
- The physical directory is `src/02_preliminary_compound/` but it is registered as
  `src.preliminary_compound` via the alias in `src/__init__.py`. Both invocation
  styles above work without any import changes.
