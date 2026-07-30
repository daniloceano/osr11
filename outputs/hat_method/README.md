# Instantâneo versionado — braço HAT

Métricas nativas do braço experimental HAT, preservadas fora de
`outputs/storm_catalog/` e `outputs/risk_index/` porque esses caminhos são
ignorados pelo Git.

- `compound_metrics_hat.csv`: métricas nos 808 pontos;
- `compound_summary_hat.json`: definição, Q05/Q95 próprios do braço, validação
  serial×paralela, fidelidade de `thr_hs` e teste de aceitação.

O HAT é `max(tide_daily_max)` em 1993–2025 por ponto. Ele é usado tanto no
portão `max(SWL) > HAT` quanto no excesso diário `SWL_d − HAT`.

Pontos sem evento têm `compound_count_total = 0` e
`mean_integrated_severity = 0`. Duração e intensidade de pico permanecem
ausentes nesses pontos, exceto quando explicitamente zeradas para os mapas
diagnósticos da comparação.

Este é um braço comparativo. Não substitui o método MHWS vigente.
