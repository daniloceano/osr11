# How to Run the South SC Test Data Explorer

## Quick Start

From the **project root directory**:

```bash
# Run all analyses
python src/explore_test_data_south_sc/main.py --all

# Run specific parts
python src/explore_test_data_south_sc/main.py --maps
python src/explore_test_data_south_sc/main.py --timeseries
python src/explore_test_data_south_sc/main.py --reported-events
python src/explore_test_data_south_sc/main.py --municipalities
python src/explore_test_data_south_sc/main.py --sector-boxplots
python src/explore_test_data_south_sc/main.py --statistics
python src/explore_test_data_south_sc/main.py --write-readmes

# Get help
python src/explore_test_data_south_sc/main.py --help
```

## Alternative: Run as a Module

```bash
# From anywhere, as long as project root is accessible
python -m src.explore_test_data_south_sc.main --all
```

## Important Notes

1. **Always run from the project root directory** (`osr11/`)
2. The script automatically adds the project root to `sys.path`
3. All imports use absolute paths (`src.explore_test_data_south_sc.*`)
4. No need to modify `PYTHONPATH` environment variable

## Troubleshooting

### ImportError: No module named 'scipy' (or other packages)

Install required dependencies:

```bash
conda activate osr
conda install scipy pandas xarray matplotlib cartopy
# or
pip install scipy pandas xarray matplotlib cartopy
```

### ImportError: No module named 'src'

Make sure you're running from the **project root** directory:

```bash
cd /path/to/osr11
python src/explore_test_data_south_sc/main.py --help
```

## File Structure

```
osr11/                                  # ← Run from here!
├── src/
│   └── explore_test_data_south_sc/
│       ├── main.py                     # Entry point
│       ├── boxplots.py
│       ├── io.py
│       ├── maps.py
│       ├── municipalities.py
│       ├── reported_events.py
│       ├── statistics.py
│       ├── timeseries.py
│       ├── utils.py
│       ├── metadata.py
│       └── config/
│           └── analysis_config.py
├── config/
│   └── plot_config.py                  # Shared plot configuration
├── data/
│   ├── test/                           # Test datasets
│   └── reported events/                # Events CSV
└── outputs/
    ├── figures/testdata_exploration/
    └── tables/testdata_exploration/
```
