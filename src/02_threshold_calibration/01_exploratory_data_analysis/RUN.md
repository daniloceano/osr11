# Step 2a — Exploratory Data Analysis: Quick-Start Guide

## Quick Start

From the **project root directory**:

```bash
# Run all analyses
python -m src.exploratory_data_analysis.main --all

# Run specific parts
python -m src.exploratory_data_analysis.main --maps
python -m src.exploratory_data_analysis.main --timeseries
python -m src.exploratory_data_analysis.main --reported-events
python -m src.exploratory_data_analysis.main --municipalities
python -m src.exploratory_data_analysis.main --sector-boxplots
python -m src.exploratory_data_analysis.main --statistics
python -m src.exploratory_data_analysis.main --write-readmes

# Get help
python -m src.exploratory_data_analysis.main --help
```

## Alternative: Direct Script Invocation

```bash
# Also works (direct path)
python src/02_threshold_calibration/01_exploratory_data_analysis/main.py --all
```

## Important Notes

1. **Always run from the project root directory** (`osr11/`)
2. The script automatically adds the project root to `sys.path`
3. All imports use absolute paths (`src.exploratory_data_analysis.*`)
4. No need to modify `PYTHONPATH` environment variable

## Troubleshooting

### ImportError: No module named 'scipy' (or other packages)

Install required dependencies:

```bash
conda activate osr11
conda install scipy pandas xarray matplotlib cartopy
# or
pip install scipy pandas xarray matplotlib cartopy
```

### ImportError: No module named 'src'

Make sure you're running from the **project root** directory:

```bash
cd /path/to/osr11
python -m src.exploratory_data_analysis.main --help
```

## File Structure

```
osr11/                                  # ← Run from here!
├── src/
│   └── 02_threshold_calibration/
│       └── 01_exploratory_data_analysis/
│           ├── main.py                 # Entry point
│           ├── boxplots.py
│           ├── io.py
│           ├── maps.py
│           ├── municipalities.py
│           ├── reported_events.py
│           ├── statistics.py
│           ├── timeseries.py
│           ├── utils.py
│           ├── metadata.py
│           └── config/
│               └── analysis_config.py
├── config/
│   └── plot_config.py                  # Shared plot configuration
├── data/
│   ├── test/                           # Test datasets
│   └── reported events/                # Events CSV
└── outputs/
    └── south_sc_test_data_exploratory/
        ├── figures/
        └── tables/
```
