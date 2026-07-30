# Animações exploratórias de `zos` — Maranhão–Pará–Amapá, 2024

Este produto mostra a anomalia diária de `zos` do GLORYS12 na plataforma entre
Maranhão, Pará e Amapá. Foram produzidas três animações: janeiro de 2024, julho
de 2024 e o ano de 2024 completo, todas com um quadro por dia.

## Definição do campo

Para cada data de 2024, subtrai-se a média de `zos` do mesmo dia do calendário
no período 1993–2023. A remoção da climatologia torna mais visíveis estruturas
anômalas e sua possível propagação ao longo da plataforma. A escala de cores é
discreta e específica para cada animação. Valores negativos formam uma única
classe cinza e 0–0,1 m usa `#4E4B65`; as nove cores restantes são distribuídas
entre 0,1 m e o máximo do campo dentro do domínio e período. O limite direito da
barra é obrigatoriamente o máximo observado naquela animação, sem arredondamento
ou saturação acima dele.

`zos` é a altura dinâmica da superfície do mar acima do geoide no GLORYS12,
livre de maré e disponível como média diária. Neste produto ela é usada como
**proxy de sobrelevação dinâmica**, mas não é um resíduo meteorológico puro. Na
plataforma amazônica, sinais estéricos, de circulação de baixa frequência e de
descarga fluvial também podem contribuir. Assim, padrões propagantes devem ser
tratados como hipótese a testar, não como evidência isolada de storm surge.

## Reprodução no servidor `swell`

```bash
cd /p1-swell/danilocs/osr11
conda activate osr11
PATH=/home/danilocs/.conda/envs/cgfd-usp-mpas/bin:$PATH \
  python -m src.exploratory.animate_zos_surge_marapa
```

O prefixo apenas expõe o `ffmpeg` já instalado no servidor; o processamento
científico continua sendo executado pelo ambiente `osr11`.

Entradas:

- `data/raw/glorys/glorys_zos_YYYY-MM.nc`
- `data/ne_10m_coastline/ne_10m_coastline.shp`

Saídas:

- `animations/zos_anomaly_marapa_january_2024_daily.mp4`
- `animations/zos_anomaly_marapa_july_2024_daily.mp4`
- `animations/zos_anomaly_marapa_year_2024_daily.mp4`
- `metadata/animation_metadata.json`

Script: `src/exploratory/animate_zos_surge_marapa.py`.
