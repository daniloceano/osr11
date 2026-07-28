# External provenance — SVI_Coast_2022

`build_svi_coast_2022.py` is the script that produced the Social Vulnerability
Index carried by `outputs/risk_index/risk_index.shp`. It was written and run by
**Karine Bastos Leal (INPE)** as a Google Colab notebook and is stored here
verbatim, as exported, so the index has a traceable origin.

It is **not runnable from this repository** and is not part of any pipeline: it
mounts Google Drive, installs packages with `!pip`, and reads and writes
spreadsheets under `/content/drive/MyDrive/OSR11/`. It is kept as the record of
how the delivered numbers were obtained, not as a step to re-execute.

## What it does

1. Extracts the list of coastal municipalities from a PDF (`municipios.pdf`).
2. Resolves each name to its IBGE code through the Localidades API.
3. Pulls ten indicators from the 2022 Census through the SIDRA API, one query
   per theme: water supply, sewage, waste collection, paving, income, poverty,
   age groups, colour or race, literacy, and residents per household.
4. Adds **Balneário Rincão (4220000)** separately. The municipality was created
   in 2013 and is absent from the standard SIDRA aggregates, so its ten
   variables are fetched individually. This is why the delivered file carries
   **282** municipalities where Lima et al. (2024) report 281.
5. Standardises the ten variables (z-score), runs PCA, keeps PC1, flips its sign
   if the mean correlation with the inputs is negative, and rescales PC1 to
   0–100 as `SVI_Coast_2022`.

## Audit, 2026-07-28

**The index is reproducible.** Recomputing PC1 and the SVI from the ten
delivered variables, following the script, reproduces the delivered values
exactly:

```
PC1 : r = +1.000000, max|difference| = 0.0000
SVI : r = +1.000000, max|difference| = 0.0000
PC1 explains 50.5 % of the variance of the ten standardised indicators
```

**`pop_house` is published pre-normalised, and this is harmless to the index
but wrong in the label.** The script computes residents per household, then
Min–Max rescales that column to [0, 1] and overwrites it before the z-score
step. Two consequences, and only the second matters:

- *For the index: none.* Min–Max and the z-score are both affine, so the second
  absorbs the first. Verified: the standardised matrices computed with and
  without the intermediate Min–Max are identical to 5.7e-15. An earlier
  suspicion in this repository — that the variable might have entered the PCA
  with a different weight from the other nine — was **wrong**.
- *For the published table: real.* The value distributed as `pop_house` is the
  rescaled one (0–1), while the manuscript's Table of SVI variables defines it
  as "total population divided by the number of occupied permanent households",
  which is the raw 2.40–4.45 residents per household. The shapefile carries the
  raw value separately as `pop_house_`. Either the manuscript definition or the
  published column should be changed so they agree.

**What this script does not cover.** It contains no geoprocessing at all — no
`geopandas`, no shapefile, no `grid_lat`/`grid_lon`. The association between the
808 ocean grid points and the municipalities, which is what supplies
`grid_lat`/`grid_lon` in the delivered file, was produced elsewhere and remains
unaudited. That is the one reproducibility gap still open in Step 4.

## Data availability

For the manuscript, this script plus the ten variables in the delivered file are
enough to declare the SVI reproducible. The point-to-municipality association is
not, and should either be requested as code or reimplemented here.
