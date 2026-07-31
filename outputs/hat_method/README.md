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

> **Atualizado em 2026-07-31 (AUD-17).** A última linha deste README dizia
> *"Este é um braço comparativo. Não substitui o método MHWS vigente."* — o que
> deixou de ser verdade. **O braço HAT foi adotado como método vigente** em
> 2026-07-31: o Step 3 inteiro foi regenerado sobre ele, e
> `outputs/storm_catalog/compound_hat/compound_metrics_hat.csv` é a fonte do
> Hazard Index publicado. O MHWS passou a ser o legado, preservado em
> `outputs/legacy_mhws_method/`.
>
> Atenção: **este instantâneo é do par q90/q90**, não do par calibrado q70/q99.
> Ele é lido por `src/exploratory/audit_AUD_01_final_criteria.py` sob a chave
> `hat_q90`, como termo de comparação. Para o produto vigente use
> `outputs/current_method_hat/`.
