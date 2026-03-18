# OSR11 — Compound Coastal Flooding on Brazil's Eastern Coast

Assessment of compound wave–surge events along the South Atlantic Eastern Coast of Brazil using CMEMS multiyear reanalyses.

**Authors:** Danilo Couto de Souza, Carolina Barnez Gramcianinov, Ricardo de Camargo, Karine Bastos Leal

---

## Objective

Quantify the joint occurrence and intensity of sea-level extremes (storm surges) and significant wave height events along the Brazilian coast, map compound hazard exposure, and integrate vulnerability indicators to identify coastal risk hotspots.

---

## Repository structure

```
osr11/
├── config/
│   └── download_config.example.yml   # Copy and edit to configure downloads
├── data/
│   └── raw/
│       ├── glorys/                   # GLORYS sea-level NetCDF files
│       └── waverys/                  # WAVERYS wave NetCDF files
├── src/
│   └── acquisition/
│       ├── download_cmems.py         # Main download script
│       └── catalog_inspect.py        # Catalog inspection utility
├── logs/
├── environment.yml                   # Conda environment
└── README.md
```

> `data/raw/` is listed in `.gitignore` and is never committed to version control.

---

## Setup

### 1. Create and activate the environment

```bash
conda env create -f environment.yml
conda activate osr11
```

### 2. Authenticate with Copernicus Marine

Run once to save credentials locally (`~/.copernicusmarine/`):

```bash
copernicusmarine login
```

Alternatively, set environment variables (useful for HPC/CI):

```bash
export COPERNICUSMARINE_SERVICE_USERNAME="your_username"
export COPERNICUSMARINE_SERVICE_PASSWORD="your_password"
```

> Register at [https://marine.copernicus.eu](https://marine.copernicus.eu) if you do not have an account.

### 3. Create your config file

```bash
cp config/download_config.example.yml config/download_config.yml
# Edit bbox, period, and output_dir as needed
```

---

## Data acquisition

### Inspect the CMEMS catalog

Before downloading, inspect available datasets and variables within each product:

```bash
# Using the standalone utility
python src/acquisition/catalog_inspect.py GLOBAL_MULTIYEAR_PHY_001_030
python src/acquisition/catalog_inspect.py GLOBAL_MULTIYEAR_WAV_001_032

# Or via the download script
python src/acquisition/download_cmems.py --inspect
python src/acquisition/download_cmems.py --inspect --product glorys
```

### Download test subset

```bash
# Download both GLORYS and WAVERYS (uses config/download_config.yml)
python src/acquisition/download_cmems.py

# Download only GLORYS
python src/acquisition/download_cmems.py --product glorys

# Download only WAVERYS
python src/acquisition/download_cmems.py --product waverys

# Use a specific config file
python src/acquisition/download_cmems.py --config config/my_config.yml
```

Output files are saved under `data/raw/glorys/` and `data/raw/waverys/` as NetCDF.

---

## CMEMS products used

| Product | ID | Variables |
|---|---|---|
| GLORYS (sea level) | `GLOBAL_MULTIYEAR_PHY_001_030` | `zos` (sea surface height above geoid) |
| WAVERYS (waves) | `GLOBAL_MULTIYEAR_WAV_001_032` | `VHM0` (Hs), `VMDR` (mean wave direction) |

> Variable names and `dataset_id` are resolved from the live catalog at runtime.
> Run `--inspect` to verify current names before downloading.

---

## Analytical framework (planned)

```
Data acquisition → QC → Threshold calibration → Storm catalog
→ Compound event detection → Exposure analysis
→ Vulnerability mapping → Risk integration → Hotspot ranking
```

See the working plan document for full methodology details.
