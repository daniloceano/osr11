# data/test/

Test datasets for the OSR11 project, used for exploratory development and
validation of the coastal risk analysis pipeline.

These are small domain cutouts of the operational datasets, covering the southern
Santa Catarina coast (approx. −29.4 to −27.6°S, −50 to −48°W) for the full 1993–2025 period.

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

> ⚠️ **Important**: Municipalities in the northern and central-north sectors of SC
> (e.g. Itapoá, São Francisco do Sul, Balneário Camboriú, Navegantes) are **outside**
> this test domain. Grid-based statistics are therefore unavailable for those municipalities.

## Known limitations

- Test cutouts only — they do not replace the full operational datasets.
- The domain does not cover the entire Santa Catarina coastline.
- Results from these files are exploratory and should not be interpreted as final.

## Subdirectories

- `reported events/` — Excel table of declared coastal disasters in SC (1998–2023)
