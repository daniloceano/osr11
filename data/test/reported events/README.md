# data/test/reported events/

## `reported_events_Karine_sc.xlsx`

Table of 105 coastal disasters declared by municipalities in Santa Catarina (SC), Brazil,
covering the period 1998–2023.

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

The spreadsheet has two header rows:
- **Row 0**: full table caption (long string)
- **Row 1**: actual column names

Correct reading: `pd.read_excel(path, header=1)`.

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
