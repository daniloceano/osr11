# AUD-11 — Min–Max em cadeia, ancoragem da escala em municípios individuais e limites de interpretação do índice

| Campo | Valor |
|-------|-------|
| **ID** | AUD-11 |
| **Tipo** | `risco-interpretacao` |
| **Componente** | integração (transversal) |
| **Etapa do fluxo** | Step 4.4 |
| **Afeta** | código, interpretação, saídas, documentação |
| **Prioridade** | P1 |
| **Bloqueia publicação?** | Sim, salvo qualificação explícita — o índice não pode ser lido como risco absoluto e isso não está declarado |
| **Status** | `aberto` |
| **Desfecho** | — |
| **Depende de** | — |
| **Bloqueia** | AUD-05, AUD-16 |
| **Relacionado a** | AUD-06, AUD-07, AUD-09, AUD-13, AUD-15 |
| **Origem** | `baseline/2026-07-29_initial_review.md` §4.3, §4.4, §8 item 9, §9.2 item 8 |
| **Criado em** | 2026-07-29 |
| **Última atualização** | 2026-07-29 |

---

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

- [ ] A análise de influência município-a-município está executada, versionada e
      publicada; os municípios com influência acima do limiar estão listados.
- [ ] Os quatro esquemas de normalização estão comparados quantitativamente.
- [ ] A decisão está tomada: manter Min–Max com a limitação declarada, ou migrar
      para posto/balizas fixas. Se migrar, a escolha das balizas está justificada.
- [ ] **Nenhum município recebe `Risk_Hazard` exatamente 0,000 nem 1,000 como
      artefato de escala**, ou está demonstrado que o valor é substantivo.
- [ ] O `README.md` §4.4, os metadados publicados e as legendas das figuras
      declaram que `Risk_Hazard` é um **índice de priorização relativa** dentro do
      conjunto de municípios costeiros brasileiros analisados, e **não** risco
      absoluto, probabilidade ou quantidade comparável entre estudos.
- [ ] O teste de mudança de domínio (§8.5) está executado e reportado.
- [ ] A inconsistência dos metadados sobre `Hazard_Index_mun` está corrigida
      (AUD-17).

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
| — | — | — | — | *nenhuma alteração até o momento* |

## 14. Histórico de investigação

*Nenhuma investigação registrada além do diagnóstico de linha de base de
2026-07-29.*
