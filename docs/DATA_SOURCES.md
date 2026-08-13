# Data Sources — OSR11

Reproducible, external data sources actually used in the final products of the
project (hazard characterisation, threshold calibration, storm catalog,
exposure/vulnerability, and risk integration).

Columns: **ID/Name**, **Data type**, **Access** (where to download), **Documentation**
(paper, technical report, or methodological note describing the product/source).

---

## Ocean and wave reanalyses (CMEMS)

| ID/Name | Data type | Access | Documentation |
|---|---|---|---|
| **GLORYS12** (product `GLOBAL_MULTIYEAR_PHY_001_030`, dataset `cmems_mod_glo_phy_my_0.083deg_P1D-m`) | Global ocean physics reanalysis, 1/12° (~9 km), daily. Variable used: `zos` (sea surface height). | Copernicus Marine Service (CMEMS) — https://data.marine.copernicus.eu/product/GLOBAL_MULTIYEAR_PHY_001_030 (via the `copernicusmarine` Python toolbox) | Product User Manual (PUM) and Quality Information Document (QUID), available on the product page above |
| **WAVERYS** (product `GLOBAL_MULTIYEAR_WAV_001_032`, dataset `cmems_mod_glo_wav_my_0.2deg_PT3H-i`) | Global wave reanalysis (WaveWatch III model), ~0.2°, 3-hourly. Variables used: `VHM0` (significant wave height) and `VMDR` (mean wave direction). | Copernicus Marine Service (CMEMS) — https://data.marine.copernicus.eu/product/GLOBAL_MULTIYEAR_WAV_001_032 (via the `copernicusmarine` Python toolbox) | Product User Manual (PUM) and QUID, available on the product page above |

## Astronomical tide model

| ID/Name | Data type | Access | Documentation |
|---|---|---|---|
| **FES2022b** | Global astronomical tide atlas (finite element solution), 45 harmonic constituents. Used for the highest astronomical tide (HAT) and to separate the tidal signal from the storm-surge residual in GLORYS12 `zos`. | AVISO+ / LEGOS — https://www.aviso.altimetry.fr/en/data/products/auxiliary-products/global-tide-fes.html (registration required) | Carrère, L. et al. — FES2022 technical note (AVISO+); see also Lyard et al. (2021), *Ocean Dynamics*, for the FES2014 predecessor methodology |


## Census-derived socioeconomic data (IBGE)

| ID/Name | Data type | Access | Documentation |
|---|---|---|---|
| **IBGE Grade Estatística 2022** (Statistical Grid, 2022 Census) | Gridded resident-population and occupied-household counts, 200 m cells in urban census tracts / 1 km cells in rural ones. Used for population exposure. | IBGE geoFTP — https://geoftp.ibge.gov.br/recortes_para_fins_estatisticos/grade_estatistica/censo_2022/ | IBGE, *Grade Estatística — Notas Metodológicas 01/2025* |
| **IBGE/SIDRA 2022 Census** | Ten municipal socioeconomic indicators (water supply, sewage, waste collection, paving, income, poverty, age groups, colour/race, literacy, residents per household), pulled via the SIDRA API. Combined into the Social Vulnerability Index (`SVI_Coast_2022`, PCA on the ten standardised indicators). | IBGE SIDRA API — https://sidra.ibge.gov.br/ (2022 Census aggregates) and IBGE Localidades API (municipality code resolution) | Lima et al. (2024) [SVI construction reference]; index provenance and reproducibility documented in `src/04_risk_integration/external_svi/README.md` |
