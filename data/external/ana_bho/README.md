# ANA BHO river extract

The GeoJSON files contain only features selected by their `NORIOCOMP` value:

- `rio_apodi.geojson`: `Rio Apodi`;
- `rio_paraguacu.geojson`: `Rio Paraguaçu`.

Both were extracted on 2026-07-22 from the Brazilian National Water and
Sanitation Agency (ANA) hydrography service:

`https://portal1.snirh.gov.br/server/rest/services/dados_abertos/Hidrografia/MapServer/0`

The service describes the layer as the Base Hidrográfica Ottocodificada used
by ANA. The file is stored locally so the exploratory figure can be reproduced
without querying the web during plotting.
