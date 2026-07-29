# AUD-09 — SVI_Coast_2022: dois indicadores com direcionalidade invertida; o índice é um eixo de pobreza, não de suscetibilidade costeira

| Campo | Valor |
|-------|-------|
| **ID** | AUD-09 |
| **Tipo** | `fragilidade-metodologica` |
| **Componente** | vulnerabilidade |
| **Etapa do fluxo** | Step 4.3 |
| **Afeta** | dados, interpretação, saídas, documentação |
| **Prioridade** | P1 |
| **Bloqueia publicação?** | Sim, salvo qualificação explícita — as cargas do PC1 precisam ser publicadas e a inversão discutida |
| **Status** | `aberto` |
| **Desfecho** | — |
| **Depende de** | — |
| **Bloqueia** | AUD-05, AUD-11 |
| **Relacionado a** | AUD-10, AUD-13 |
| **Origem** | `baseline/2026-07-29_initial_review.md` §3.3, §8 item 7, §9.2 item 11 |
| **Criado em** | 2026-07-29 |
| **Última atualização** | 2026-07-29 |

---

## 1. Problema

O `SVI_Coast_2022` é construído por PCA sobre dez indicadores padronizados, com o
sinal do PC1 ajustado **globalmente**. Dois dos dez indicadores entram no índice
com carga **oposta à sua direção conceitual**:

- `pop_rent` (proporção em domicílio não próprio): r = **−0,765** com o SVI —
  mais locatários resulta em **menor** vulnerabilidade;
- `pop_agevul` (proporção em faixas etárias vulneráveis, < 9 e 60+): r = **−0,323**.

Além disso, o índice correlaciona r = **+0,944** com `pop_poverty`: funcionalmente
ele é um eixo de pobreza, saneamento e ruralidade, não uma medida de
suscetibilidade a inundação costeira.

Há ainda um artefato de escala: **Balneário Camboriú recebe SVI = 0,000
exatamente**, por ser o mínimo do Min–Max.

## 2. Por que importa cientificamente

1. **A interpretação declarada não corresponde ao conteúdo.** O `README.md`
   §"Conceptual Framework" define vulnerabilidade como suscetibilidade física e
   social. O índice implementado mede o gradiente de desenvolvimento Norte–Sul do
   Brasil — real e importante, mas não específico do perigo costeiro. Isso explica
   por que o top-10 de risco migra do Sudeste (perigo) para o Maranhão (SVI).
2. **A inversão de sinal será questionada.** Um revisor de vulnerabilidade social
   perguntará por que insegurança de posse (locação) e população idosa reduzem a
   vulnerabilidade. A resposta — que na estrutura urbana brasileira essas
   variáveis se concentram em municípios mais ricos, e a PCA captura o eixo
   dominante — é defensável, mas precisa estar escrita.
3. **O SVI = 0,000 exato** propaga-se ao produto final: é a âncora inferior da
   escala de `Risk_Hazard` (ver AUD-11) e o mecanismo terminal da reprovação de
   Balneário Camboriú (ver AUD-05).

## 3. Evidência original

De `site/public/data/risk_index_municipalities.geojson` (282 municípios):

### 3.1 Direcionalidade dos dez indicadores

| Indicador | r com SVI | ρ com SVI | Direção conceitual | Coerente? |
|---|---|---|---|---|
| `pop_poverty` | **+0,944** | +0,944 | ↑ vulnerabilidade | ✓ |
| `pop_illiterate` | +0,832 | +0,853 | ↑ | ✓ |
| `pop_house` | +0,825 | +0,830 | ↑ | ✓ |
| `pop_nogarbage` | +0,783 | +0,805 | ↑ | ✓ |
| `pop_nonwhite` | +0,779 | +0,820 | ↑ | ✓ |
| `pop_nosewage` | +0,720 | +0,741 | ↑ | ✓ |
| `pop_nowater` | +0,569 | +0,586 | ↑ | ✓ |
| `pop_nopaving` | +0,342 | +0,363 | ↑ | ✓ (fraco) |
| `pop_agevul` | **−0,323** | −0,252 | ↑ | ✗ **invertido** |
| `pop_rent` | **−0,765** | −0,756 | ↑ | ✗ **invertido** |

### 3.2 Redundância

- |r| médio fora da diagonal entre os dez indicadores: **0,433**.
- Bloco de saneamento (`nowater`, `nosewage`, `nogarbage`, `nopaving`):
  r interno 0,215 a 0,459 — quatro dos dez indicadores medem a mesma dimensão
  latente de infraestrutura, o que constitui **contagem múltipla parcial**.
- Menores |r| médios: `pop_agevul` 0,230 e `pop_nopaving` 0,241 — os dois
  indicadores menos integrados ao eixo dominante.

### 3.3 Efeitos de escala

| relação | ρ (Spearman) |
|---|---|
| SVI × log₁₀(`pop_municipality`) | **−0,494** |
| SVI × `Exposure_Index` | **−0,588** |
| SVI × `Risk_Hazard` | +0,297 |
| SVI × `Risk_Hazard` (parcial, controlando H e E) | **+0,795** |

### 3.4 Extremos

| Maiores SVI | valor | pop. municipal |
|---|---|---|
| Chaves/PA | **100,000** | 19 848 |
| Santo Amaro do Maranhão/MA | 93,237 | 13 561 |
| Icatu/MA | 91,702 | 24 618 |
| Primeira Cruz/MA | 91,288 | 13 521 |
| Paulino Neves/MA | 91,100 | 17 355 |

| Menores SVI | valor | pop. municipal |
|---|---|---|
| **Balneário Camboriú/SC** | **0,000** | 136 326 |
| Santos/SP | 8,687 | 418 360 |
| Florianópolis/SC | 10,154 | 536 876 |
| Niterói/RJ | 11,667 | 480 647 |
| São José/SC | 11,762 | 271 013 |

### 3.5 Reprodutibilidade — o que **está** correto

Auditoria registrada em `src/04_risk_integration/external_svi/README.md`
(2026-07-28): recomputar PC1 e o SVI a partir das dez variáveis entregues
reproduz os valores publicados **exatamente** (r = +1,000000, max|Δ| = 0,0000).
PC1 explica **50,5 %** da variância dos dez indicadores padronizados. Esta
questão **não** é sobre erro de cálculo.

## 4. Localização exata

### Código

| Caminho | Elemento | Papel |
|---|---|---|
| `src/04_risk_integration/external_svi/build_svi_coast_2022.py` | script completo | Produziu o SVI. **Externo, não executável a partir do repositório** — monta Google Drive, usa `!pip`, lê planilhas de `/content/drive/MyDrive/OSR11/` |
| `src/04_risk_integration/external_svi/README.md` | auditoria de 2026-07-28 | Registro de reprodutibilidade e da anomalia de `pop_house` |
| `src/site/export_risk_index_data.py` | `SOURCE_LAYER_SPECS` L91–99 | Única quantidade lida do shapefile entregue |
| `src/site/export_risk_index_data.py` | L517 | `svi_fraction = SVI_Coast_2022 / 100` |
| `src/site/export_risk_index_data.py` | L576–579 | Aplicação do piso `CLIP_FLOOR` = 0,01 antes do produto |

### Dados e saídas

- `outputs/risk_index/risk_index.shp` — fonte externa; carrega `SVI_Coast_2022`
  (truncado no DBF para `SVI_Coast_`), `PC1` e os dez indicadores.
- `site/public/data/risk_index_municipalities.geojson` — dez indicadores
  disponíveis nas propriedades, permitindo toda a análise sem o shapefile.

### Figuras e tabelas afetadas

- `outputs/article_figures/hazard_vulnerability_risk_multiplot.png` (painel SVI)
- `outputs/article_figures/tables/top10_municipalities_by_svi.*`

### Anomalia já documentada (não é esta questão)

`pop_house` é publicado **pré-normalizado** (Min–Max 0–1), enquanto o manuscrito
o define como residentes por domicílio (2,40–4,45). A auditoria de 2026-07-28
demonstrou que isso é **inócuo para o índice** (Min–Max e z-score são ambos
afins; matrizes padronizadas idênticas a 5,7e-15) mas **real para a tabela
publicada**. Rastreado em AUD-17.

## 5. Comportamento atual vs. comportamento pretendido

| | Descrição |
|---|---|
| **Implementado** | z-score dos dez indicadores → PCA → PC1 → inversão global de sinal se a correlação média com as entradas for negativa → Min–Max 0–100 |
| **Pretendido/conceitual** | Índice em que valores altos representem consistentemente maior suscetibilidade a impactos costeiros |

A PCA não impõe direção aos indicadores individuais: extrai o eixo de maior
variância. A inversão global garante que o **eixo** aponte na direção certa, não
que cada indicador contribua na direção certa.

## 6. Divergência documentação ↔ implementação ↔ saídas

- `README.md` §4.3 lista os dez indicadores com descrições que implicam direção
  positiva de vulnerabilidade para todos (ex.: "Proportion in non-owned housing",
  "Proportion in vulnerable age groups"). O índice trata dois deles em direção
  oposta. A tabela do README não é falsa, mas é enganosa sem a nota de cargas.
- `README.md` §4.3 não reporta as cargas do PC1 nem a variância explicada
  (50,5 %), ambas disponíveis.
- Implementação e saídas concordam.

## 7. Explicações alternativas plausíveis

1. **A inversão é um resultado empírico legítimo do Brasil costeiro.** Locação e
   envelhecimento se concentram nos balneários ricos do Sul/Sudeste; a PCA
   corretamente identifica que, neste conjunto, essas variáveis marcam o polo de
   **baixa** vulnerabilidade. Forçar a direção conceitual seria impor uma teoria
   contra o dado.
2. **A metodologia segue a referência declarada.** O SVI-Coast de Lima et al.
   (2024, *Nat. Hazards*, DOI 10.1007/s11069-023-06246-w) usa a mesma abordagem
   PCA para 281 municípios costeiros brasileiros. Reproduzir a metodologia de
   referência é defensável; divergir dela exige justificativa.
3. **Um índice de pobreza pode ser exatamente o que se quer.** Se a hipótese é
   que a capacidade de resposta a desastres costeiros é limitada primariamente
   por privação material, um eixo de pobreza é o indicador correto. O problema
   seria apenas de nomenclatura.
4. **A correlação negativa com o tamanho da população pode ser real.** Municípios
   maiores têm melhor infraestrutura per capita no Brasil; ρ = −0,494 é um fato,
   não um artefato.
5. **O SVI = 0 de Balneário Camboriú pode ser inofensivo** se o piso de 0,01
   estiver funcionando. Contra-argumento: ele ainda é a âncora da escala final
   (AUD-11).

## 8. Diagnósticos propostos

1. **Publicar as cargas do PC1** por indicador, com sinal e magnitude, e a
   variância explicada por PC1 e PC2. Extraível dos dez indicadores presentes no
   GeoJSON — não requer o script externo.
2. **Construir um índice aditivo com direcionalidade imposta** (z-score de cada
   indicador, sinal fixado conceitualmente, média simples) e comparar com o PC1:
   ρ de Spearman, mudança de posição por município, efeito no ranking de risco.
   *Saída esperada:* saber quanto da estrutura do SVI depende da inversão.
3. **Testar a remoção de `pop_rent` e `pop_agevul`**: recomputar PCA com oito
   indicadores; medir ρ com o SVI atual e a variância explicada.
4. **Testar o tratamento da redundância do bloco de saneamento**: agregar os
   quatro indicadores em um único fator antes da PCA, ou aplicar ponderação
   inversa à redundância; comparar.
5. **Substituir o Min–Max final por posto percentílico ou balizas fixas**, de modo
   que nenhum município receba 0 ou 100 exatos. Medir o efeito sobre
   `Risk_Hazard` (interage com AUD-11).
6. **Comparar com o SVI-Coast publicado** de Lima et al. (2024), baseado no censo
   de 2010, para os municípios em comum: ρ de Spearman entre os dois índices.
   Serve como validação externa da camada.

## 9. Critérios objetivos de resolução

- [ ] As cargas do PC1 por indicador, os sinais e a variância explicada estão
      publicados no manuscrito ou no material suplementar.
- [ ] O manuscrito discute explicitamente que `pop_rent` e `pop_agevul` entram
      com sinal oposto à sua interpretação conceitual, e por quê.
- [ ] O manuscrito declara que o `SVI_Coast_2022` é dominado por privação
      material (r = 0,944 com pobreza) e **não** contém suscetibilidade física
      (ver AUD-10).
- [ ] Existe comparação quantificada entre o PC1 e ao menos um índice
      alternativo com direcionalidade imposta, com o efeito no ranking de risco
      medido.
- [ ] A redundância entre indicadores está quantificada e discutida.
- [ ] Nenhum município recebe SVI exatamente 0 ou 100 por artefato de Min–Max,
      **ou** está demonstrado que o piso de 0,01 neutraliza completamente o efeito
      no produto final (requer AUD-11).
- [ ] Existe comparação com o SVI-Coast de referência (Lima et al. 2024), ou está
      registrado por que não foi possível.

## 10. Riscos de alteração prematura

- **Recompor o SVI dentro deste repositório** rompe a autoria e a proveniência da
  camada, produzida por Karine Bastos Leal (INPE). Qualquer alteração deve ser
  acordada com a autora; a auditoria existente foi deliberadamente conduzida sem
  modificar o produto entregue.
- **Impor direcionalidade** afasta o índice da metodologia de referência
  (Lima et al. 2024) e exige justificar a divergência.
- **Remover indicadores** reduz a comparabilidade com o índice publicado de
  referência, que usa dez variáveis.
- O SVI é a camada **mais** reprodutível do trabalho. Alterá-la sem necessidade
  troca uma força por uma incerteza.

## 11. Condições sob as quais o resultado atual pode ser mantido

Muito provável que o SVI seja mantido como está. Basta que:

1. As cargas do PC1 sejam publicadas;
2. A inversão de `pop_rent` e `pop_agevul` seja discutida;
3. O índice seja nomeado e interpretado pelo que é — vulnerabilidade **social**
   dominada por privação material — e não como suscetibilidade costeira;
4. AUD-10 declare explicitamente a ausência da camada física;
5. AUD-11 resolva o problema da âncora de escala.

## 12. Produtos a jusante que exigiriam regeneração

Somente se o SVI mudar:

```bash
# o SVI vem do shapefile externo; alterá-lo exige nova entrega ou
# reimplementação dentro do repositório, e então:
python -m src.site.export_risk_index_data
python -m src.figures_article.make_article_hazard_vulnerability_risk_multiplot
python -m src.figures_article.make_article_top10_municipality_tables
python -m src.figures_article.make_article_supplementary_integrated_risk_zooms
```

Se apenas as cargas forem publicadas: nenhum produto muda.

## 13. Rastreabilidade de versionamento

| Data | Commit | Ramo | Arquivos alterados | Natureza |
|------|--------|------|--------------------|----------|
| — | — | — | — | *nenhuma alteração até o momento* |

## 14. Histórico de investigação

*A auditoria de reprodutibilidade do SVI de 2026-07-28 está registrada em
`src/04_risk_integration/external_svi/README.md` e não é repetida aqui. Os
diagnósticos de direcionalidade da §3 vêm da revisão de linha de base de
2026-07-29.*
