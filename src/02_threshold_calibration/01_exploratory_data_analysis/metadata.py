"""
Dataset inspection and data-directory documentation utilities.

Two responsibilities:
- ``inspect_datasets``: log structural metadata (dimensions, coordinates,
  variables, value ranges) for quick sanity checks.
- ``write_data_readmes``: regenerate the README.md files in data/test/ and
  data/reported events/ with accurate dataset metadata.
"""
from __future__ import annotations

import logging

import xarray as xr

from src.explore_test_data_south_sc.config.analysis_config import CFG, ROOT

log = logging.getLogger(__name__)


def inspect_datasets(ds_wave: xr.Dataset, ds_gl: xr.Dataset) -> None:
    """Log structural metadata for WAVERYS and GLORYS test datasets."""
    log.info("== Dataset inspection ==")
    for label, ds in [("WAVERYS", ds_wave), ("GLORYS", ds_gl)]:
        log.info("-- %s --", label)
        log.info("  Dimensions : %s", dict(ds.sizes))
        log.info("  Variables  : %s", list(ds.data_vars))
        log.info("  Coordinates: %s", list(ds.coords))
        for dim in ds.dims:
            coord = ds[dim].values
            log.info(
                "  %s range: %s to %s (%d values)",
                dim, coord[0], coord[-1], len(coord),
            )


def write_data_readmes() -> None:
    """Write README.md files for data/test/ and data/reported events/."""
    log.info("== Writing data directory README files ==")
    _write_test_readme()
    _write_events_readme()


# ── Internal ──────────────────────────────────────────────────────────────────

def _write_test_readme() -> None:
    path = ROOT / "data/test/README.md"
    path.write_text(
        """\
# data/test/

Test datasets for the OSR11 project, used for exploratory development and
validation of the coastal risk analysis pipeline.

These are small domain cutouts of the operational CMEMS datasets, covering the
southern Santa Catarina coast (approx. −29.4 to −27.6°S, −50 to −48°W) for
the full 1993–2025 period.

## Files

### `waverys_sc_sul_test.nc`

| Field               | Value                                          |
|---------------------|------------------------------------------------|
| Source              | WAVERYS (Copernicus Marine — GLOBAL_MULTIYEAR_WAV_001_032) |
| Variables           | `VHM0` — spectral significant wave height (m) · `VMDR` — mean wave direction (°) |
| Temporal resolution | 3-hourly                                       |
| Period              | 1993-01-01 to 2025-12-31                       |
| Grid                | 10 latitude × 11 longitude points (~0.2° spacing) |
| Purpose             | Exploratory analysis of wave conditions, southern SC coast |

### `glorys_sc_sul_test.nc`

| Field               | Value                                          |
|---------------------|------------------------------------------------|
| Source              | GLORYS12 (Copernicus Marine — GLOBAL_MULTIYEAR_PHY_001_030) |
| Variables           | `zos` — sea surface height (m, relative to mean sea level) |
| Temporal resolution | Daily                                          |
| Period              | 1993-01-01 to 2025-12-31                       |
| Grid                | 25 latitude × 25 longitude points (~1/12° ≈ 0.083° spacing) |
| Purpose             | Exploratory analysis of sea level variability, southern SC coast |

## Spatial domain

```
Latitude:  −29.4°S to −27.6°S
Longitude: −50.0°W to −48.0°W
```

This domain covers the southern portion of the Santa Catarina coast, roughly from
the Florianópolis–Palhoça area southward to near the border with Rio Grande do Sul.

> **Important**: Municipalities in the northern and central-north sectors of SC
> (e.g. Itapoá, São Francisco do Sul, Balneário Camboriú, Navegantes) are **outside**
> this test domain. Grid-based statistics are therefore unavailable for those municipalities.

> **Analysis scope**: The exploratory module `explore_test_data_south_sc` filters the
> reported events dataset to **South sector municipalities only**, to match this
> limited domain. This is documented in `io.py` and logged at runtime.

## Known limitations

- Test cutouts only — they do not replace the full operational datasets.
- The domain does not cover the entire Santa Catarina coastline.
- Exploratory analyses (Parts A–B) use a single nearshore point (closest to coast)
  for co-located Hs and SSH evaluation, rather than independent spatial maxima.
- Results from these files are exploratory and should not be interpreted as final.

## Subdirectories

- `reported events/` — Excel table of declared coastal disasters in SC (1998–2023)
""",
        encoding="utf-8",
    )
    log.info("  -> data/test/README.md")


def _write_events_readme() -> None:
    path = ROOT / "data/reported events/README.md"
    path.write_text(
        """\
# data/reported events/

## `reported_events_Karine_sc.csv`

Table of 105 coastal disasters declared by municipalities in Santa Catarina (SC), Brazil,
covering the period 1998–2023.

**Note**: This CSV file is generated from the original `reported_events_Karine_sc.xlsx`
using the preprocessing script `src/preprocessing/convert_reported_events.py`.

## Source

> Leal, K.B., Robaina, L.E.S., Körting, T.S. et al. Identification of coastal natural
> disasters using official databases to provide support for the coastal management:
> the case of Santa Catarina, Brazil.
> *Nat Hazards* **120**, 11465–11482 (2024).
> <https://doi.org/10.1007/s11069-023-06150-3>

The database was constructed from Brazilian official civil defence records and public
registers to identify coastal natural disasters associated with wave and meteorological
forcing events.

## File structure

The original Excel spreadsheet has two header rows:
- **Row 0**: full table caption (long string)
- **Row 1**: actual column names

The CSV file is generated with `skiprows=1` to use row 1 as the header.

Correct reading: `pd.read_csv(path)`.

## Column descriptions

| Original name                          | Internal name (snake_case) | Description                                                        |
|----------------------------------------|----------------------------|--------------------------------------------------------------------|
| Disaster ID                            | disaster_id                | Event identifier (integer; may repeat across municipalities for the same event) |
| Dates of occurrence (mm/dd/yyyy)       | date                       | Date of disaster declaration                                       |
| Months                                 | month                      | Month name (text)                                                  |
| Municipalities                         | municipality               | Municipality name (Portuguese)                                     |
| Coastal Sectors                        | coastal_sector             | Coastal sector: North, Central-north, Central, Central-south, South |
| EM or SPC                              | disaster_type              | Disaster classification code; `*` = not available                 |
| hgt                                    | hgt_m                      | Geopotential height at 500 hPa (m)                                 |
| Wspd (m/s)                             | wspd_ms                    | Wind speed (m/s)                                                   |
| Wdir (m/s)                             | wdir_deg                   | Wind direction (°) — column label says "m/s" but values are degrees |
| Hs (m)                                 | hs_m                       | Significant wave height at event date (m), extracted from reanalysis |
| Hsdir (°)                              | hsdir_deg                  | Mean wave direction (°)                                            |
| HsPp (s)                               | hspp_s                     | Peak period (s)                                                    |
| WP                                     | weather_pattern            | Weather pattern classification (integer code)                      |
| Number of Human Damage                 | n_human_damage             | Number of people affected; `*` = not available                     |
| Material Damage (BRL)                  | material_damage_brl        | Material damage in BRL; `*` = not available                        |
| Environmental Damage (BRL)             | env_damage_brl             | Environmental damage in BRL; `*` = not available                   |
| Public Economic Losses (BRL)           | public_losses_brl          | Public economic losses in BRL; `*` = not available                 |
| Private Economic Losses (BRL)          | private_losses_brl         | Private economic losses in BRL; `*` = not available                |

## Missing data

The asterisk (`*`) in the original file indicates information not available in source records.
The loading script converts `*` to `NaN`.

## Limitations

1. **Geographic scope**: SC coastal municipalities only; not the full Brazilian coastline.
2. **Temporal coverage**: 1998–2023 (non-continuous; depends on official declarations).
3. **Non-unique Disaster ID**: one event may affect multiple municipalities under the same ID.
4. **Undeclared events**: physically significant events not officially declared are absent.
5. **Unit inconsistency**: the `Wdir` column is labelled "m/s" in the original file,
   but values are in degrees (°). Preserved as observed — no automatic correction applied.
6. **Monetary values**: expressed in BRL at year of occurrence; no inflation adjustment.
7. **Hs and atmospheric variables**: extracted from reanalysis at the event date —
   they are not direct observations.
""",
        encoding="utf-8",
    )
    log.info("  -> data/reported events/README.md")
