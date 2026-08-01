# AUD-11 — Min–Max em cadeia, ancoragem da escala em municípios individuais e limites de interpretação do índice

| Campo | Valor |
|-------|-------|
| **ID** | AUD-11 |
| **Tipo** | `risco-interpretacao` |
| **Componente** | integração (transversal) |
| **Etapa do fluxo** | Step 4.4 |
| **Afeta** | código, interpretação, saídas, documentação |
| **Prioridade** | P1 |
| **Bloqueia publicação?** | Sim — satisfeito pela declaração do caráter relativo e da dependência residual |
| **Status** | `resolvido` |
| **Desfecho** | `mitigado-parcialmente` — a ancoragem amostral foi reduzida em 26× no nível do município, mas **não eliminada**: `sd(PC1)` continua estimado da amostra e é material em escala de domínio |
| **Depende de** | — |
| **Bloqueia** | AUD-05, AUD-16 |
| **Relacionado a** | AUD-06, AUD-07, AUD-09, AUD-13, AUD-15 |
| **Origem** | `baseline/2026-07-29_initial_review.md` §4.3, §4.4, §8 item 9, §9.2 item 8 |
| **Criado em** | 2026-07-29 |
| **Última atualização** | 2026-07-31 (verificação dos critérios e fechamento) |

---

> ### Nota de leitura — a decisão desta questão não cumpriu inteiramente o que prometeu
>
> A entrada de decisão da §14 afirma que, com âncoras fixas, "nenhum valor
> publicado passará a depender de qual município ou qual ponto está no conjunto".
> **Isso é verdade para perigo e exposição, e falso para a vulnerabilidade**:
> `V = Φ(PC1/sd(PC1))` estima `sd(PC1)` **da amostra entregue**
> ([`export_risk_index_data.py:158`](../../../src/site/export_risk_index_data.py)).
>
> A consequência tem duas escalas muito diferentes, e ambas foram medidas:
> remover **um** município move qualquer outro em no máximo **0,0036** — 26×
> menos que sob Min–Max —, mas excluir **uma região inteira** move até **0,292**
> e reordena o restante a **ρ = 0,70**. Ver §14, entrada de 2026-07-31.
>
> Fechada como `mitigado-parcialmente`, não como `metodologia-alterada`: o
> objeto da questão foi reduzido, não removido.

## 1. Problema

O produto aplica Min–Max **três vezes em cadeia** (componentes do perigo →
`Hazard_Index` → `Hazard_Index_mun`, e novamente em `Risk_Hazard`). Duas
consequências:

1. **Amplificação de contraste**: o mapa final apresenta contraste ~60 % maior do
   que existe no produto conjuntivo subjacente.
2. **Ancoragem em municípios individuais**: remover **um** município desloca todos
   os valores publicados em 0,043 em média, até 0,094. O índice é estritamente
   relativo ao domínio amostral, e isso não está declarado em lugar nenhum.

## 2. Por que importa cientificamente

`Risk_Hazard` é publicado numa escala 0–1 com legenda de oito classes de
intervalo igual. Essa apresentação convida à leitura como medida absoluta —
"risco 0,9 é quase o máximo possível". Não é: é a posição relativa dentro de um
conjunto de 280 municípios brasileiros, ancorada em dois municípios específicos.

Consequências práticas:

- o valor de um município **muda** se outro for adicionado ou removido do estudo,
  o que impede comparação com qualquer outro trabalho ou com uma futura
  atualização do próprio OSR11;
- a âncora inferior é **Balneário Camboriú**, cujo `Risk_Hazard = 0,000` existe
  apenas porque seu `SVI = 0,000` é o mínimo do Min–Max do SVI (AUD-09) — um
  artefato de escala propagado até o produto final;
- as classes de intervalo igual são arbitrárias e não correspondem a nenhuma
  quebra na distribuição (ver AUD-16).

## 3. Evidência original

### 3.1 A cadeia de normalizações

| Etapa | Código | Amplitude de entrada | Fator de amplificação |
|---|---|---|---|
| Componentes → `Hazard_Index_raw` | `hazard_index.py` L115 | — | Min–Max por componente |
| `Hazard_Index_raw` → `Hazard_Index` | `hazard_index.py` L120 | [0,1468; 0,7278] | **1,72×** |
| `Hazard_Index` → `Hazard_Index_mun` | `export_risk_index_data.py` L556 | [0,0034; 0,8291] | 1,21× |
| `Risk_Hazard_raw` → `Risk_Hazard` | `export_risk_index_data.py` L580 | [0,0924; 0,7185] | **1,60×** |

`Risk_Hazard_raw` tem razão máx/mín de apenas 7,8, e é apresentado como um mapa
que vai de 0,000 a 1,000.

### 3.2 Análise de influência — remoção de um município

Recalculando o Min–Max final sem cada município e comparando com o valor
publicado dos demais:

| Município removido | deslocamento médio | deslocamento máximo |
|---|---|---|
| **Balneário Camboriú** (âncora inferior) | **0,0428** | **0,0945** |
| **Icatu** (âncora superior) | 0,0257 | 0,0420 |
| Santa Rita (não é âncora) | 0,0000 | 0,0000 |

### 3.3 Origem da âncora inferior

Balneário Camboriú: `Hazard_Index_mun` = 0,089; `Exposure_Index` = 0,885;
`SVI/100` = **0,000** → recortado ao piso 0,01.

`Risk_Hazard_raw` = (0,089 × 0,885 × 0,01)^(1/3) = **0,0924** = mínimo exato do
domínio → `Risk_Hazard` = 0,000.

### 3.4 O piso de recorte não altera o ranking

Testado: com piso 1e-6 em vez de 0,01, ρ de Spearman com o publicado = **1,000**,
top-20 = 20/20. O piso protege contra zero absoluto, mas **não** impede que
Balneário Camboriú seja a âncora inferior.

### 3.5 A renormalização municipal é monotônica

`Hazard_Index_mun` = Min–Max de `Hazard_Index` sobre os municípios. Testado: usar
`Hazard_Index` diretamente no produto dá ρ = **1,000** e top-20 = 20/20 — o
Min–Max é monotônico e não altera a ordenação. Ele altera apenas a **amplitude
relativa** entre as três componentes dentro da média geométrica, que é o efeito
declarado na justificativa do código (L546–555).

### 3.6 Distribuição nas classes publicadas

`FIXED_BOUNDARIES["Risk_Hazard"]` = 8 classes de intervalo igual:

| classe | n |
|---|---|
| (0,000; 0,125] | 3 |
| (0,125; 0,250] | 10 |
| (0,250; 0,375] | 26 |
| (0,375; 0,500] | 47 |
| (0,500; 0,625] | 65 |
| (0,625; 0,750] | 80 |
| (0,750; 0,875] | 39 |
| (0,875; 1,000] | 10 |

### 3.7 Normalização alternativa por posto

Componentes do perigo normalizadas por posto percentílico em vez de Min–Max:
ρ com o publicado = **0,967**, top-20 = 17/20. A alternativa é próxima, mas não
idêntica, e elimina a ancoragem.

## 4. Localização exata

### Código

| Caminho | Elemento | Papel |
|---|---|---|
| `src/04_risk_integration/hazard_index.py` | `_minmax()` L39–51 | Min–Max das componentes e do índice de perigo |
| `src/04_risk_integration/hazard_index.py` | L120 | Segunda normalização |
| `src/04_risk_integration/exposure_index.py` | `minmax()` L73–80 | Usada por `E_log10` e `E_linear` (não pelo índice publicado) |
| `src/04_risk_integration/exposure_index.py` | `GOALPOST_MIN/MAX` L61–62 | **Contraexemplo positivo**: a exposição já usa balizas fixas, imune ao problema |
| `src/04_risk_integration/exposure_index.py` | `CLIP_FLOOR` L66 | Piso 0,01 |
| `src/site/export_risk_index_data.py` | `_minmax()` L220–229 | Min–Max municipal |
| `src/site/export_risk_index_data.py` | L556 | `Hazard_Index_mun` |
| `src/site/export_risk_index_data.py` | L580 | `Risk_Hazard` |
| `src/site/export_risk_index_data.py` | `FIXED_BOUNDARIES` L461–468 | Classes de intervalo igual |

### Metadados publicados

`site/public/data/risk_index_metadata.json`:
`hazard_index_normalization`, `municipal_hazard_renormalization`,
`integrated_risk_normalization`, `integrated_risk_formula`. Todos documentam a
mecânica; **nenhum** documenta a consequência interpretativa.

### Figuras afetadas

Todas as que mostram `Risk_Hazard` ou `Hazard_Index` em escala 0–1:
`hazard_vulnerability_risk_multiplot.png`,
`supplementary_integrated_risk_zooms.png`,
`coastal_hazard_index_components.png` (painel do Hazard Index).

## 5. Comportamento atual vs. comportamento pretendido

| | Descrição |
|---|---|
| **Implementado** | Min–Max sobre os extremos observados, em cadeia, com classes de intervalo igual |
| **Pretendido** | Uma escala cujo significado não dependa de qual conjunto de municípios está presente — como a própria exposição já faz com balizas fixas |

O repositório já contém a solução aplicada a uma das componentes. A justificativa
está escrita em `exposure_index.py` L28–34, citando INFORM §6.3: balizas fixas
"preserve the rescaling factor" e "exclude the distortion effect of outliers". O
mesmo argumento se aplica ao perigo e ao risco, e não foi aplicado.

## 6. Divergência documentação ↔ implementação ↔ saídas

- Documentação e código concordam sobre a **mecânica**.
- Nenhum documento declara que `Risk_Hazard` é **relativo ao domínio amostral**
  e não comparável entre estudos. Nem o `README.md` §4.4, nem os metadados
  publicados, nem as legendas das figuras.
- **Divergência confirmada nos metadados publicados:** `export_risk_index_data.py`
  L818–822 afirma que `Hazard_Index_mun` *"is not used by any published field"* e
  L898–903 repete *"no published field uses it"*, enquanto `integrated_risk_formula`
  no mesmo JSON o usa como fator. Ver AUD-17, inconsistência #3.

## 7. Explicações alternativas plausíveis

1. **Min–Max é a prática padrão em índices compostos** e a ancoragem é conhecida
   e aceita na literatura de indicadores. Publicar a análise de influência pode
   bastar.
2. **O deslocamento de 0,043 é pequeno** em relação à incerteza do índice como um
   todo. Se o bootstrap de AUD-07 mostrar intervalos de confiança de largura
   0,2, a ancoragem é ruído de segunda ordem.
3. **O problema real pode ser o SVI = 0**, não o Min–Max do risco. Corrigir a
   normalização do SVI (AUD-09) removeria a âncora sem tocar no risco.
4. **A amplificação de contraste pode ser desejável** para comunicação: um mapa
   que usa toda a paleta é mais legível. O problema é apenas se o leitor
   interpretar os valores como absolutos.
5. **Balizas fixas exigem escolher os valores**, o que é sua própria decisão
   arbitrária. A INFORM as ancora em números redondos na escala log; para um
   índice adimensional 0–1 não há equivalente óbvio.

## 8. Diagnósticos propostos

1. **Análise de influência completa**: remover cada um dos 280 municípios, um a
   um, e mapear o deslocamento máximo induzido. Identificar todos os municípios
   com influência acima de um limiar.
2. **Comparar quatro esquemas de normalização** ponta a ponta — Min–Max
   (atual), posto percentílico, balizas fixas, e z-score truncado — quanto a:
   ρ de Spearman, sobreposição de top-20, distribuição nas classes, e influência
   de município individual.
3. **Testar a remoção da ancoragem via SVI**: recalcular `Risk_Hazard` com o SVI
   normalizado por posto e verificar se a influência de Balneário Camboriú
   desaparece. *Se sim, esta questão pode fechar por meio de AUD-09.*
4. **Quantificar a amplificação percebida**: mostrar lado a lado o mapa de
   `Risk_Hazard_raw` (escala nativa, 0,092–0,719) e de `Risk_Hazard` (0–1). Os
   dois já são exportados como camadas; falta a figura comparativa.
5. **Testar a estabilidade a mudanças de domínio**: recalcular tudo excluindo os
   estados do Norte (AP, PA, MA) e verificar quanto muda o valor dos municípios
   do Sul. Isso simula o cenário de AUD-01 e mede diretamente a dependência de
   domínio.

## 9. Critérios objetivos de resolução

> **Nota.** Dois destes critérios pareciam ter perdido o objeto com a adoção das
> âncoras fixas. **Não perderam** — ver §14. Foram executados, e é deles que sai
> o achado principal do fechamento.

- [x] A análise de influência município-a-município está executada, versionada e
      publicada; os municípios com influência acima do limiar estão listados.
      *`outputs/audit/AUD-11_scale_anchoring/leave_one_out_influence.csv`, os 282,
      **recalculando `sd(PC1)` dentro de cada reamostra** — sem isso o teste é
      vazio. Pior caso **Chaves/PA**: desloca qualquer outro município em no
      máximo **0,0036** e nenhum posto em mais de **3** posições. Contra
      **0,0945** sob a cadeia de Min–Max: redução de **26×**.*
- [x] Os quatro esquemas de normalização estão comparados quantitativamente.
      *`normalization_scheme_comparison.csv`: âncoras fixas (publicado) · Min–Max
      por componente seguido de Min–Max (ρ = 0,998, mas produz **1 município em
      exatamente 1,000** e continua ancorado em indivíduos) · posto percentílico
      (ρ = 0,638) · z-score truncado (ρ = 0,592). A escolha adotada preserva
      quase integralmente a ordenação do Min–Max **sem** as âncoras exatas, e as
      duas alternativas livres de ancoragem destroem a informação de magnitude.*
- [x] A decisão está tomada: manter Min–Max com a limitação declarada, ou migrar
      para posto/balizas fixas. Se migrar, a escolha das balizas está justificada.
      *Migrou para âncoras fixas, implementado em 2026-07-31. Balizas
      justificadas: 99 eventos = 3/ano (nenhum ponto satura; máximo 98) e
      severidade 1,0 = um dia de critério pleno no excesso diário máximo do
      domínio (máximo observado 0,948).*
- [x] **Nenhum município recebe `Risk_Hazard` exatamente 0,000 nem 1,000 como
      artefato de escala**, ou está demonstrado que o valor é substantivo.
      ***Demonstrado.*** *Zero em exatamente 1,000: **nenhum** — o máximo é
      0,566. Em 0,000: **84**, e são substantivos, não artefato —
      `risk_zero_cause` os separa em perigo nulo (82), perigo e exposição nulos
      (1) e exposição nula (1). "Zero" significa nenhum evento composto aceito em
      1993–2025. O contraste é direto: o esquema de Min–Max produz 1 município em
      1,000 **por construção**.*
- [x] O `README.md` §4.4, os metadados publicados e as legendas das figuras
      declaram que `Risk_Hazard` é um **índice de priorização relativa** dentro do
      conjunto de municípios costeiros brasileiros analisados, e **não** risco
      absoluto, probabilidade ou quantidade comparável entre estudos.
      *Acrescentado em 2026-07-31: bloco em `README.md` §4.4 e campo
      `integrated_risk_formula.interpretation` nos metadados publicados
      (`risk_index_metadata.json`, regenerado — o GeoJSON não mudou). As legendas
      das figuras já traziam "comparative among coastal municipalities and do not
      represent absolute expected damage". **Os três declaram também a dependência
      residual de `sd(PC1)`**, que é a parte que faltava.*
- [x] O teste de mudança de domínio (§8.5) está executado e reportado.
      ***E não era um teste vazio.*** *`domain_change_tests.csv`: excluir AP+PA+MA
      muda `sd(PC1)` em **−16,6 %** (ρ = 0,991, desloc. máx. 27); excluir todo o
      **N/NE** muda em **−57,5 %** e reordena os 104 restantes a **ρ = 0,696**,
      com deslocamento de até 0,292 no índice. Reportado no `README.md` e nos
      metadados.*
- [x] A inconsistência dos metadados sobre `Hazard_Index_mun` está corrigida
      (AUD-17). *Corrigida em 2026-07-29, commit `e2680ed`; ver AUD-17 §9 item #3.*

## 10. Riscos de alteração prematura

- **Migrar para posto** destrói a informação de magnitude: dois municípios com
  risco muito diferente ficam separados por uma posição, o que é pior para
  priorização de investimento do que o problema que resolve.
- **Balizas fixas para um índice adimensional** exigem escolher valores sem
  referência externa — trocaria uma arbitrariedade por outra, mas com a vantagem
  de ser estável no tempo.
- **Remover a renormalização `Hazard_Index_mun`** parece atraente (ρ = 1,000), mas
  ela existe por uma razão documentada: sem ela o perigo entra no produto
  geométrico com amplitude menor que as outras duas componentes e é silenciosamente
  subponderado. Ver `export_risk_index_data.py` L546–555.
- Alterar a normalização **muda todos os valores publicados** e invalida
  simultaneamente site, figuras e tabelas.

## 11. Condições sob as quais o resultado atual pode ser mantido

Provável e razoável manter Min–Max, desde que:

1. A análise de influência seja publicada;
2. O caráter relativo do índice seja declarado em README, metadados e legendas;
3. AUD-09 elimine o SVI = 0 exato, removendo a âncora patológica;
4. AUD-16 substitua as classes de intervalo igual por classes justificadas;
5. O teste de mudança de domínio seja reportado.

## 12. Produtos a jusante que exigiriam regeneração

```bash
python -m src.site.export_risk_index_data
python -m src.site.export_coastal_hazard_data
python -m src.figures_article.make_article_coastal_hazard_components_map
python -m src.figures_article.make_article_hazard_vulnerability_risk_multiplot
python -m src.figures_article.make_article_supplementary_integrated_risk_zooms
python -m src.figures_article.make_article_top10_municipality_tables
```

Se apenas houver declaração interpretativa: nenhum produto muda; apenas README,
metadados e legendas.

## 13. Rastreabilidade de versionamento

| Data | Commit | Ramo | Arquivos alterados | Natureza |
|------|--------|------|--------------------|----------|
| 2026-07-31 | *(a commitar)* | `main` | **Novos:** `src/exploratory/audit_AUD_11_scale_anchoring.py`, `outputs/audit/AUD-11_scale_anchoring/`. **Alterados:** este registro (§9, §13, §14 e nota de leitura), `README.md` (§4.4), `src/site/export_risk_index_data.py` (`integrated_risk_formula.interpretation`), `site/public/data/risk_index_metadata.json` (regenerado; **GeoJSON inalterado**), `docs/scientific_audit/issues/AUD-07_*.md` (correção da §3-bis.1), `docs/scientific_audit/ISSUE_TRACKER.md` | Verificação dos critérios + declaração. **Nenhum valor numérico publicado alterado** |

## 14. Histórico de investigação

*Nenhuma investigação registrada além do diagnóstico de linha de base de
2026-07-29.*


### 2026-07-31 — DECISÃO: remover a cadeia de Min–Max e o piso de 0,01

> Esta é a entrada canônica da decisão. AUD-09 (escala do SVI), AUD-15 (piso) e
> AUD-08 (banda de exposição) a referenciam em vez de duplicá-la.

| Campo | Conteúdo |
|-------|----------|
| **Quem decidiu** | Danilo Couto de Souza (PI), 2026-07-31, sobre a simulação registrada abaixo |
| **Decisão** | **Substituir toda normalização ancorada na amostra por escalas de âncora fixa, e remover o piso de 0,01.** O objeto de AUD-11 deixa de existir: nenhum valor publicado passará a depender de qual município ou qual ponto está no conjunto |
| **Pergunta que orientou** | Não era "remover a normalização" — uma média geométrica exige fatores não negativos e comparáveis, então alguma escala é obrigatória. Era **remover a ancoragem amostral**: o fato de o valor de um município depender do mínimo e do máximo observados em outros |

#### O que muda, camada por camada

| Camada | Hoje | Passa a ser | Por quê |
|---|---|---|---|
| **Exposição** | `Exposure_absolute` com balizas fixas 10²–10⁶ hab sobre `pop_10km`; `Exposure_relative` = `pop_10km`/`pop_municipality` | **fórmula mantida**, mas aplicada à **população efetiva** `pop_ef = w₁·pop_1km + w₅·pop_5km + w₁₀·pop_10km` | Já estava livre de ancoragem amostral; o que mudou foi o **suporte espacial**, decidido em AUD-08 §14 em 2026-07-31: média ponderada das bandas com decaimento por distância. Nenhum município fica com exposição zero |
| **Perigo — frequência** | Min–Max sobre os 808 pontos | `min(compound_count_total / 99, 1)` | 99 eventos em 33 anos = **3 eventos/ano**, baliza fixa e fisicamente legível. Zero natural preservado (208 pontos sem evento). **Nenhum ponto satura**: o máximo observado é 98 |
| **Perigo — severidade** | Min–Max sobre os 808 pontos | `min(mean_integrated_severity / 1.0, 1)` | Já é adimensional e não negativa. A baliza 1,0 equivale a **um dia de critério pleno no excesso diário máximo do domínio** — unidade interpretável. Máximo observado 0,948, **ninguém satura**. Na prática a componente passa a ser usada como está |
| **Perigo — composição** | Min–Max da média | **média simples, sem segundo Min–Max** | O segundo Min–Max era pura reancoragem |
| **Vulnerabilidade (SVI)** | Min–Max 0–100 do PC1 | **Φ(PC1 / sd(PC1))**, CDF normal | PC1 **não** tem escala natural: média 0, sd 2,247, faixa −5,06 a +5,75, **48 % negativo**. Não pode entrar cru numa média geométrica. A CDF normal é limitada em (0,1), **não produz âncora exata** (faixa observada 0,0122–0,9948) e é ancorada em média/desvio, não em dois municípios individuais. É **monótona**, logo ρ = **1,0000** com o SVI atual: a ordenação não muda, só a escala deixa de depender de Balneário Camboriú e Chaves |
| **Piso `CLIP_FLOOR = 0,01`** | aplicado aos três fatores | **removido** | Com zero natural no perigo, a média geométrica passa a ser genuinamente conjuntiva: perigo nulo ⇒ risco nulo |
| **Min–Max final do risco** | `norm_municipal(Risk_Hazard_raw)` | **removido** | Reancoraria tudo de novo. O risco passa a ocupar **0 – 0,59** em vez de 0 – 1 |

#### Consequências medidas

Simulação com exposição mantida em 10 km, para isolar o efeito da normalização:

| | valor |
|---|---|
| ρ de Spearman com o ranking publicado | **0,954** |
| Deslocamento mediano de posto | 21 posições (máximo 82) |
| Top-10 preservado | 8 de 10 |
| Municípios com risco **exatamente zero** | **84** (83 por perigo nulo + Santa Rita/MA por exposição) |
| Faixa do risco | 0,000 – 0,586 |

**Não é mudança cosmética.** Exige regenerar todos os produtos municipais e as figuras do artigo.

#### O que a decisão resolve e o que não resolve

Resolve: nenhum município recebe 0 ou 100 exatos por artefato de escala; remover
um município do conjunto deixa de mover os valores dos demais; a média
geométrica passa a ser de fato conjuntiva.

**Não resolve**, e precisa ficar declarado no manuscrito: o índice continua
**relativo a balizas escolhidas**, não uma medida absoluta de dano esperado. A
baliza de 3 eventos/ano é uma escolha justificada por não saturar nenhum ponto
deste domínio — não é uma constante física. Trocou-se uma âncora amostral por
uma âncora **explícita e estável**, o que é o ganho; não se obteve uma escala
absoluta.

| Campo | Conteúdo |
|-------|----------|
| **Scripts executados** | Simulação em sessão, não versionada. Deve ser convertida em implementação — ver o prompt de implementação entregue ao pesquisador em 2026-07-31 |
| **Alterações implementadas** | **Nenhuma no código.** Por instrução do pesquisador, esta sessão apenas documenta; a implementação será feita em sessão própria |
| **Incerteza remanescente** | (1) A baliza de frequência (99 eventos / 33 anos) não foi comparada com nenhuma referência externa da literatura — foi escolhida por não saturar. (2) O efeito sobre a definição de hotspot (AUD-16) não foi avaliado: com 84 municípios em zero exato, qualquer corte por percentil muda de significado. (3) Os 83 municípios de perigo nulo passam a **empatar** em zero, e a ordenação interna deles desaparece |
| **Próxima decisão necessária** | Nenhuma de estrutura. A banda de distância foi decidida em AUD-08 §14 (2026-07-31): média ponderada de 1/5/10 km com pesos decrescentes. Falta apenas **confirmar os pesos exatos** — recomendação: pesos de anel 1,00 / 0,50 / 0,20, equivalentes a w = 0,50 / 0,30 / 0,20 |

### 2026-07-31 — Verificação dos critérios: dois que pareciam vazios não eram

| Campo | Conteúdo |
|-------|----------|
| **Pergunta testada** | Os sete critérios da §9 podem ser confrontados depois da implementação? Em particular: a análise de influência (§8.1) e o teste de mudança de domínio (§8.5) ainda têm objeto, agora que a ancoragem amostral foi substituída por âncoras fixas? |
| **Dados e métodos** | `site/public/data/risk_index_municipalities.geojson` (282 entregues, 280 com risco). Caminho de **recálculo**: `V = Φ(PC1/sd)` com `sd` reestimado dentro de cada subamostra, e `Risk = (H·E·V)^(1/3)`. Leave-one-out sobre os 282; quatro testes de exclusão de domínio; e comparação ponta a ponta de quatro esquemas de normalização. O script **levanta erro** se o recálculo com a amostra completa não reproduzir o risco publicado |
| **Scripts executados** | `python -m src.exploratory.audit_AUD_11_scale_anchoring` |
| **Novas saídas geradas** | `outputs/audit/AUD-11_scale_anchoring/{leave_one_out_influence.csv, domain_change_tests.csv, normalization_scheme_comparison.csv, summary.json}` |
| **Achados** | (a) **A promessa da decisão não se cumpriu inteiramente.** Perigo e exposição usam âncoras fixas e são de fato independentes do conjunto, mas `sd(PC1)` é estimado da amostra, logo a vulnerabilidade — e portanto o risco — depende de quem está no conjunto. (b) **No nível do município a melhoria é grande e real**: pior caso Chaves/PA, deslocamento máximo de **0,0036** e de **3** postos, contra **0,0945** sob Min–Max — **redução de 26×**. (c) **No nível de domínio a dependência é material**: excluir AP+PA+MA muda `sd(PC1)` em −16,6 % (ρ = 0,991, desloc. máx. 27 postos, 0,066 no índice); excluir **todo o N/NE** muda em **−57,5 %** e reordena os 104 restantes a **ρ = 0,696**, com deslocamento de até **0,292**. (d) **Nenhum município em 1,000** — máximo 0,566 — e os **84 em 0,000 são substantivos**, separados por `risk_zero_cause`; o esquema de Min–Max, por contraste, produz um município em 1,000 **por construção**. (e) Entre os quatro esquemas, Min–Max preserva a ordenação (ρ = 0,998) mas mantém as âncoras exatas, enquanto posto percentílico (ρ = 0,638) e z-score truncado (ρ = 0,592) removem a ancoragem ao custo da magnitude. As âncoras fixas são o único esquema testado que consegue as duas coisas |
| **Interpretação** | O desfecho não é `metodologia-alterada` nem `resultado-validado-mantido`: é `mitigado-parcialmente`, e a distinção importa. A questão foi criada porque o valor de um município dependia de dois municípios específicos; isso acabou. O que **não** acabou é a dependência do **domínio**, que migrou de "quais são os extremos" para "qual é a dispersão de PC1". É uma dependência mais fraca, mais estável e mais defensável — mas continua existindo, e num trabalho cujo próprio artigo discute recortes regionais ela precisa estar declarada. A regra prática que sai daqui: **os valores publicados são condicionais ao domínio de 282 municípios; qualquer análise de subconjunto tem de recalcular a escala, não fatiar estes valores** |
| **Alterações implementadas** | Script novo. `README.md` §4.4 e `integrated_risk_formula.interpretation` nos metadados publicados passaram a declarar o caráter relativo do índice **e** a dependência residual. Metadados regenerados pelo exportador; **o GeoJSON não mudou**. Nenhum valor numérico publicado alterado |
| **Validação realizada** | O recálculo com a amostra completa reproduz o risco publicado a 1e-5, verificado por asserção no script; `V` reproduz o campo publicado a 5e-07. Reexecução do script devolve saídas idênticas |
| **Incerteza remanescente** | (1) **A dependência de `sd(PC1)` não foi removida**, apenas medida e declarada. Removê-la exigiria uma escala de vulnerabilidade com âncora externa — por exemplo `sd` fixado de uma referência nacional —, o que não foi avaliado. (2) Os testes de domínio usam recortes por unidade federativa, que são escolhas grosseiras; não há varredura sistemática de subconjuntos. (3) A comparação de esquemas usa as componentes atuais como entrada, portanto mede o efeito da **normalização**, não o de um pipeline inteiramente alternativo |
| **Correção de um registro anterior** | A entrada de AUD-07 de 2026-07-31 afirma que "com âncoras fixas, o valor de um município não depende da amostra", apoiada num bootstrap que devolveu deslocamento **0,0**. Aquele bootstrap reamostrava os **valores publicados sem recalcular `sd(PC1)`**, de modo que demonstrava uma tautologia, não a propriedade. A afirmação é **forte demais** e foi corrigida em AUD-07 §3-bis.1. A conclusão de AUD-07 sobre o **desenho do bootstrap** — reamostrar municípios não é o teste certo, reamostrar anos é — permanece válida |

### 2026-07-31 — DECISÃO: fechar como `mitigado-parcialmente`

| Campo | Conteúdo |
|-------|----------|
| **Quem decidiu** | Danilo Couto de Souza (PI), 2026-07-31 |
| **Decisão** | Fechar sem alterar o método. A dependência residual de `sd(PC1)` fica **medida e declarada** no `README.md` §4.4, nos metadados publicados e neste registro, em vez de removida |
| **Por que não `metodologia-alterada`** | Esse desfecho descreveria uma mudança que resolvesse a questão. A mudança foi feita e resolveu **parte** dela: a ancoragem em municípios individuais acabou, a ancoragem no domínio não |
| **Trabalho futuro nomeado** | Uma escala de vulnerabilidade com `sd` de âncora externa — nacional, não amostral — eliminaria o resíduo. Não avaliada |
| **O que o desfecho NÃO cobre** | (1) A remoção do resíduo. (2) A suíte de casos conhecidos — **AUD-05**, última questão aberta |
