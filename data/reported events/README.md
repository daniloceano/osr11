# `data/reported events/` — Coastal Disaster and Event Databases

This directory contains two complementary datasets of coastal impact episodes on the Santa Catarina (SC) coast, covering different temporal and methodological perspectives. They are used in the threshold calibration workflow to provide observational ground-truth against which modeled compound-event detections can be evaluated.

---

## Overview

| File | Type | Period | N records (approx.) | Role |
|------|------|--------|---------------------|------|
| `reported_events_Karine_sc.csv` | Official civil-defence database | 1998–2023 | 105 | Primary calibration target |
| `reported_events_Karine_sc.xlsx` | Same — original Excel format | 1998–2023 | 105 | Source file for CSV generation |
| `ressaca_sc_eventos_sc_1998_2020_consolidated_expandido.csv` | Curated documentary archive | 1998–2020 | ~100+ | Supplementary auditing and event discovery |
| `ressaca_sc_eventos_sc_1998_2020_repository_methodology.md` | Methodology document | — | — | Curation protocol for the curated archive |

---

## `reported_events_Karine_sc.csv` — Official disaster database

### Description

Table of 105 coastal disasters declared by municipalities in Santa Catarina, Brazil, covering 1998–2023. This is the **primary observational reference** for the threshold calibration workflow.

Records are derived from Brazilian official civil-defence registers and public disaster databases, compiled and published by Leal et al. (2024). Events represent officially declared coastal disasters with marine forcing (wave and/or storm-tide component).

### Source

> Leal, K.B., Robaina, L.E.S., Körting, T.S. et al.
> Identification of coastal natural disasters using official databases to provide support for the coastal management: the case of Santa Catarina, Brazil.
> *Nat Hazards* **120**, 11465–11482 (2024).
> <https://doi.org/10.1007/s11069-023-06150-3>

### Generation

`reported_events_Karine_sc.csv` is generated from the original Excel file (`reported_events_Karine_sc.xlsx`) by the preprocessing script:

```
src/01_data_preparation/preprocessing/convert_reported_events.py
```

The original spreadsheet has two header rows (row 0 = table caption; row 1 = column names). The CSV is produced with `skiprows=1` so that row 1 becomes the header. Correct reading: `pd.read_csv(path)`.

### Column descriptions

| Original name | Internal name | Type | Description |
|---|---|---|---|
| Disaster ID | disaster_id | int | Event identifier; may repeat across municipalities sharing the same declared disaster |
| Dates of occurrence (mm/dd/yyyy) | date | date | Date of disaster declaration |
| Months | month | str | Month name (text) |
| Municipalities | municipality | str | Municipality name (Portuguese) |
| Coastal Sectors | coastal_sector | str | Coastal sector: North, Central-north, Central, Central-south, South |
| EM or SPC | disaster_type | str | Disaster classification code; `*` = not available |
| hgt | hgt_m | float | Geopotential height at 500 hPa (m) |
| Wspd (m/s) | wspd_ms | float | Wind speed (m/s) |
| Wdir (m/s) | wdir_deg | float | Wind direction (°) — column label says "m/s" but values are degrees |
| Hs (m) | hs_m | float | Significant wave height at event date (m), extracted from reanalysis |
| Hsdir (°) | hsdir_deg | float | Mean wave direction (°) |
| HsPp (s) | hspp_s | float | Peak period (s) |
| WP | weather_pattern | int | Weather pattern classification (integer code) |
| Number of Human Damage | n_human_damage | int | Number of people affected; `*` = not available |
| Material Damage (BRL) | material_damage_brl | float | Material damage in BRL; `*` = not available |
| Environmental Damage (BRL) | env_damage_brl | float | Environmental damage in BRL; `*` = not available |
| Public Economic Losses (BRL) | public_losses_brl | float | Public economic losses in BRL; `*` = not available |
| Private Economic Losses (BRL) | private_losses_brl | float | Private economic losses in BRL; `*` = not available |

### Missing data

The asterisk (`*`) in the original file indicates information not available in source records. The loading script (`io.py`) converts `*` to `NaN`.

### Limitations

1. **Geographic scope**: SC coastal municipalities only; not the full Brazilian coastline.
2. **Temporal coverage**: 1998–2023 (non-continuous; depends on official declarations).
3. **Non-unique Disaster ID**: one event may affect multiple municipalities under the same ID.
4. **Undeclared events**: physically significant events not officially declared are absent.
5. **Unit inconsistency**: the `Wdir` column is labelled "m/s" in the original file but values are in degrees (°). Preserved as observed — no automatic correction applied.
6. **Monetary values**: expressed in BRL at year of occurrence; no inflation adjustment.
7. **Hs and atmospheric variables**: extracted from reanalysis at the event date — they are not direct observations.

---

## `ressaca_sc_eventos_sc_1998_2020_consolidated_expandido.csv` — Curated additional events

### Description

A supplementary table of coastal *ressaca* and marine-inundation episodes on the Santa Catarina coast, assembled through a systematic **documentary search** covering the period 1998–2020.

This dataset is **not** an official disaster database. It was assembled through a forensic-style search of heterogeneous documentary sources — academic theses, regional news archives, civil-defence materials, technical reports, institutional bulletins — with the goal of recovering traceable evidence of marine-forced coastal impacts that may not have entered the official civil-defence register.

Each record corresponds to one municipality-date pair for which explicit evidence of a coastal *ressaca*-type episode was found in one or more traceable documentary sources.

### Intended use

This dataset is intended to complement the official Leal et al. database, not replace it. Appropriate uses include:

- **Event discovery**: identifying candidate coastal impact dates not present in the official record;
- **Auditing**: cross-checking whether modeled compound-event detections coincide with documentary evidence;
- **Calibration support**: augmenting the event sample used in threshold calibration, particularly for sectors or periods with few official declarations;
- **Historical reconstruction**: building a municipality-level chronology of impact episodes for subsequent instrumental verification.

### Column descriptions

| Column | Type | Description |
|--------|------|-------------|
| `city` | str | Municipality name (Portuguese), harmonized to a canonical form |
| `date` | date (ISO 8601, YYYY-MM-DD) | Representative date of the episode; for multi-day events, typically the onset date |
| `coastal_sector` | str | Coastal sector: North, Central-north, Central, Central-south, South |
| `source_title` | str | Title of the documentary source in which the event is recorded |
| `source_url` | str | URL to the documentary source (academic repository, news archive, technical report) |
| `notes` | str | Free-text field documenting date-interpretation choices, episode-start logic, or other curation decisions |

### Curation methodology

The full documentary search and screening protocol is described in:

```
data/reported events/ressaca_sc_eventos_sc_1998_2020_repository_methodology.md
```

Key protocol features:

- **Event definition**: marine-forced coastal disturbance — *ressaca do mar*, strong-wave coastal impact, seawater intrusion, storm-tide inundation, overtopping, or wave-associated shoreline erosion. Rainfall-only flooding, inland flash flooding, and wind damage without coastal inundation are excluded.
- **Source families**: academic theses and dissertations (university repositories), state and municipal civil-defence publications, technical coastal-monitoring reports, regional news archives, conference proceedings with explicit event references.
- **Staged screening**: four stages — (A) documentary relevance, (B) event-level evidence, (C) municipality resolution, (D) temporal resolution.
- **Deduplication**: primary key is `(city, date)`; conservative episode-level review avoids double-counting consecutive-day reports of the same event.
- **Quality philosophy**: traceability over exhaustiveness — ambiguous cases are excluded; every retained record is linked to a source title and URL.

### Limitations

1. **Not a complete census**: the historical documentary record is fragmented. This table should be interpreted as a curated supplement, not an exhaustive inventory.
2. **Uneven spatial and temporal coverage**: documentation density varies by coastal sector and time period; event density partly reflects source availability rather than true impact frequency.
3. **Narrative reconstruction**: much evidence comes from retrospective academic sources that synthesized earlier reporting — these may inherit biases from the documents they compiled.
4. **Representative dates**: multi-day events are reduced to a single onset date. This simplification may slightly shift timing relative to hydrodynamic peaks; see `notes` field for per-record documentation.
5. **Documentary, not instrumental**: the table evidences occurrence but does not quantify hydrodynamic magnitude. Pairing with tide-gauge records or wave reanalyses is recommended before physical interpretation.
6. **Sector inferred for some municipalities**: where sector attribution was not explicit in source documentation, it was inferred from coastal geography and flagged in `notes`.

### Recommended scientific use

Use this dataset alongside the official Leal et al. database as a complementary observational layer. Do not use it alone as the sole ground-truth for calibration or validation, and do not assume completeness through time or homogeneous detectability across municipalities.

---

## Relationship between the two datasets

The two datasets are **independent in provenance** and **complementary in purpose**:

| Aspect | Official database (Leal et al.) | Curated additional events |
|--------|---------------------------------|--------------------------|
| Source | Brazilian civil-defence registers | Heterogeneous documentary sources |
| Coverage | 1998–2023 | 1998–2020 |
| Selection basis | Official disaster declarations | Documentary evidence of coastal marine impact |
| Meteo/wave variables | Included | Not included |
| Traceability | Published, citable | Source URL provided per record |
| Role in workflow | Primary calibration target | Supplementary auditing and event discovery |

Events may overlap between the two datasets. Where the same municipality-date pair appears in both, this constitutes independent corroborating evidence of an impact episode. Where an event appears only in the curated archive, it is a candidate for further verification against the official record and instrumental data.
