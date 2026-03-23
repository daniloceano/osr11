# data/test/

Test datasets for the OSR11 project, used for exploratory development and
validation of the coastal risk analysis pipeline.

These are small domain cutouts of the operational CMEMS datasets covering the
Santa Catarina coast for the full 1993–2025 period. Two domains are maintained:

| Domain | Coverage | Purpose |
|--------|----------|---------|
| **South SC** (`*_sc_sul_test.nc`) | ~−29.4 to −27.6°S | Phase 1 exploratory analysis |
| **Full SC** (`*_sc_full_test.nc`) | ~−29.4 to −26.0°S | Threshold calibration, all sectors |

---

## South SC domain files (`*_sc_sul_test.nc`)

### `waverys_sc_sul_test.nc`

| Field               | Value                                          |
|---------------------|------------------------------------------------|
| Source              | WAVERYS (Copernicus Marine — GLOBAL_MULTIYEAR_WAV_001_032) |
| Variables           | `VHM0` — spectral significant wave height (m) · `VMDR` — mean wave direction (°) |
| Temporal resolution | 3-hourly                                       |
| Period              | 1993-01-01 to 2025-12-31                       |
| Grid                | 10 latitude × 11 longitude points (~0.2° spacing) |
| Purpose             | Phase 1 exploratory analysis (south SC coast) |

### `glorys_sc_sul_test.nc`

| Field               | Value                                          |
|---------------------|------------------------------------------------|
| Source              | GLORYS12 (Copernicus Marine — GLOBAL_MULTIYEAR_PHY_001_030) |
| Variables           | `zos` — sea surface height (m, relative to mean sea level) |
| Temporal resolution | Daily                                          |
| Period              | 1993-01-01 to 2025-12-31                       |
| Grid                | 25 latitude × 25 longitude points (~1/12° ≈ 0.083° spacing) |
| Purpose             | Phase 1 exploratory analysis (south SC coast) |

### `metocean_sc_sul_unified_waverys_grid.nc`

| Field               | Value                                          |
|---------------------|------------------------------------------------|
| Source              | GLORYS12 interpolated to WAVERYS grid          |
| Variables           | `VHM0`, `VMDR` (WAVERYS daily mean), `zos` (GLORYS interpolated) |
| Temporal resolution | Daily                                          |
| Period              | 1993-01-01 to 2025-12-31                       |
| Grid                | WAVERYS grid (10 lat × 11 lon, ~0.2°)          |
| Purpose             | Preprocessing output for south SC domain       |

---

## Full SC domain files (`*_sc_full_test.nc`)

### `waverys_sc_full_test.nc`

| Field               | Value                                          |
|---------------------|------------------------------------------------|
| Source              | WAVERYS (Copernicus Marine — GLOBAL_MULTIYEAR_WAV_001_032) |
| Variables           | `VHM0` — spectral significant wave height (m) · `VMDR` — mean wave direction (°) |
| Temporal resolution | 3-hourly                                       |
| Period              | 1993-01-01 to 2025-12-31                       |
| Grid                | 18 latitude × 11 longitude points (~0.2° spacing) |
| Lat range           | −29.4° to −26.0°S                              |
| Purpose             | Threshold calibration — full SC coast (all 5 sectors) |

### `glorys_sc_full_test.nc`

| Field               | Value                                          |
|---------------------|------------------------------------------------|
| Source              | GLORYS12 (Copernicus Marine — GLOBAL_MULTIYEAR_PHY_001_030) |
| Variables           | `zos` — sea surface height (m, relative to mean sea level) |
| Temporal resolution | Daily                                          |
| Period              | 1993-01-01 to 2025-12-31                       |
| Grid                | 44 latitude × 25 longitude points (~1/12°)     |
| Lat range           | −29.5° to −25.9°S                              |
| Purpose             | Threshold calibration — full SC coast (all 5 sectors) |

### `metocean_sc_full_unified_waverys_grid.nc`

| Field               | Value                                          |
|---------------------|------------------------------------------------|
| Source              | GLORYS12 interpolated to WAVERYS grid          |
| Variables           | `VHM0`, `VMDR` (WAVERYS daily mean), `zos` (GLORYS interpolated) |
| Temporal resolution | Daily                                          |
| Period              | 1993-01-01 to 2025-12-31 (12 053 days)         |
| Grid                | 18 lat × 11 lon, ~0.2°                         |
| Lat range           | −29.4° to −26.0°S                              |
| Purpose             | Main input for `02_threshold_calibration/`     |

---

## Spatial domains

```
South SC (sul):                  Full SC:
Latitude:  −29.4°S to −27.6°S   Latitude:  −29.4°S to −26.0°S
Longitude: −50.0°W to −48.0°W   Longitude: −50.0°W to −48.0°W
```

The full SC domain extends the south SC domain northward to cover the five
coastal sectors in the Leal et al. (2024) disaster database:
`South`, `Central-south`, `Central`, `Central-north`, `North`.

---

## Known limitations

- Test cutouts only — they do not replace the full operational datasets.
- At ~0.2° (WAVERYS) and 1/12° (GLORYS12) resolution, many municipalities
  have their nearest ocean grid point over land or in shallow embayments that
  the reanalysis grid does not resolve. This particularly affects northern SC
  municipalities (Araquari, Balneário Barra do Sul, Barra Velha, etc.) and
  results in NaN values in derived metrics.
- Results from these files are exploratory and should not be interpreted as final.
- Raw data used to generate these fixtures is at `data/raw/` (not committed to
  git due to size). Rebuild commands:
  ```bash
  # South SC fixtures
  python src/acquisition/build_test_fixture.py --config config/test_fixture.example.yml
  # Full SC fixtures
  python src/acquisition/build_test_fixture.py --config config/test_fixture_sc_full.yml
  # Unified datasets
  python -m src.preprocessing.interpolate_glorys_to_waverys_grid --config config/preprocessing/glorys_to_waverys_test.yaml
  python -m src.preprocessing.interpolate_glorys_to_waverys_grid --config config/preprocessing/glorys_to_waverys_sc_full.yaml
  ```
