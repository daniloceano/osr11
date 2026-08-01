# Auditoria científica do OSR11 — relatório final

**Data:** 2026-08-01
**Objeto:** as dezoito questões abertas pela revisão científica independente de
2026-07-29, e o produto que resultou delas
**Destinatários:** coautores do manuscrito de risco costeiro composto
**Situação:** auditoria encerrada — dezoito questões, dezoito com desfecho registrado

Substitui, sem invalidar, o relatório de 2026-07-30
(`2026-07-30_relatorio_auditoria_perigo.md`), que trata apenas da redefinição do
evento composto e do índice de perigo. Aquele documento continua sendo a
referência detalhada para os testes de fase e a escolha do datum.

---

## Sumário executivo

Uma revisão independente examinou o produto em 2026-07-29 e concluiu, sobre o
litoral central de Santa Catarina, que o resultado *"por si só invalida o mapa
como instrumento de priorização de adaptação"*. Balneário Camboriú — a cidade com
o caso de engorda de praia mais visível do país — aparecia em **280º lugar de
280**, com risco exatamente 0,000.

**Esse caso foi corrigido.** Balneário Camboriú, Itajaí e Navegantes estão hoje em
**81º de 280 no perigo**, terço superior. Nenhum município com evidência
documentada de disrupção portuária, erosão severa ou inundação recorrente
permanece no decil inferior.

A correção não veio de ajustar o índice até os casos conhecidos subirem. Veio de
duas mudanças de método com justificativa própria, decididas antes de se olhar o
efeito no ranking:

1. **O detector deixou de segmentar sobre uma variável que contém a maré
   astronômica.** Sobre `SSH_total = zos + maré`, o percentil local selecionava,
   no Norte macromareal, os dias de sizígia — um ciclo determinístico, não um
   evento meteorológico. A estatística de Rayleigh contra o ciclo
   sizígia–quadratura dava **R = 0,82 (p < 0,01)** no Maranhão contra **R = 0,085**
   no Rio Grande do Sul. A segmentação passou a rodar sobre `zos` livre de maré, e
   a maré voltou como **variável condicionante**, pelo portão `max(SWL) > HAT`.
2. **Toda normalização ancorada na amostra foi substituída por âncoras fixas**, e
   o piso de 0,01 foi removido.

O resultado é um campo de perigo regionalmente coerente (ρ com |latitude| = +0,58)
cujas duas componentes se reforçam (ρ = +0,60, contra −0,55 na versão de três
componentes).

**O que a auditoria não fez:** não forçou concordância com a literatura. Cinco
questões fecharam com o resultado suspeito **mantido** após exame, e sete
permanecem como **limitações declaradas**. Duas delas o leitor precisa encontrar
cedo, e estão na §5.

---

## 1. Como a auditoria foi conduzida

Cada fragilidade recebeu um registro autocontido, com problema, evidência,
localização exata no código, explicações alternativas plausíveis, diagnósticos
propostos e **critérios objetivos de resolução fixados antes da investigação**. A
regra de fechamento foi explícita:

> Uma alteração de código, por si só, não é evidência de que a questão foi
> resolvida. O fechamento exige demonstração — diagnóstico reproduzido, comparação
> antes/depois, produtos a jusante regenerados sem nova inconsistência.

Trinta e dois scripts diagnósticos foram versionados em `src/exploratory/audit_AUD_*.py`,
com saídas em `outputs/audit/`. Todos são read-only sobre os produtos publicados e
determinísticos.

**Um princípio que orientou várias decisões:** um resultado inesperado não é, por
si só, um erro. O objetivo era decidir se os resultados são **defensáveis**, não
forçá-los a concordar com a expectativa prévia.

### Distribuição dos desfechos

| Desfecho | N | Questões |
|---|---|---|
| `metodologia-alterada` | 2 | AUD-01, AUD-06 |
| `mitigado-parcialmente` | 3 | AUD-05, AUD-08, AUD-11 |
| `resultado-validado-mantido` | 5 | AUD-07, AUD-09, AUD-12, AUD-13, AUD-16 |
| `limitacao-reconhecida` | 7 | AUD-02, AUD-03, AUD-04, AUD-10, AUD-14, AUD-15, AUD-18 |
| `erro-confirmado-corrigido` | 1 | AUD-17 |

---

## 2. O que mudou no método

### 2.1 O detector (AUD-01, AUD-06)

Duas questões resolvidas em conjunto, por serem indissociáveis. A duração média de
sobreposição foi **removida** do índice de perigo: era dominada pelo mínimo do
domínio e deprimia exatamente o setor com os impactos mais documentados. O perigo
passou de três para **duas** componentes.

Situação atual: **16 768 eventos aceitos, 15 857 candidatos rejeitados pelo
portão, 208 dos 808 pontos sem nenhum evento aceito** em 33 anos.

### 2.2 As escalas (AUD-11, AUD-09, AUD-08)

| Camada | Antes | Agora |
|---|---|---|
| Frequência | Min–Max sobre os 808 pontos | `min(contagem / 99, 1)` — 3 eventos/ano |
| Severidade | Min–Max sobre os 808 pontos | `min(severidade / 1, 1)` |
| Vulnerabilidade | Min–Max 0–100 do PC1 | **Φ(PC1/sd(PC1))** |
| Exposição | banda única de 10 km | **população efetiva** de quatro bandas |
| Piso e Min–Max final | aplicados | **removidos** |

O PC1 não tem escala natural — média 0, sd 2,247, faixa −5,06 a +5,75, 48 %
negativo — e não pode entrar cru numa média geométrica. A CDF normal é limitada,
não produz âncora exata e é **monótona**, de modo que a ordenação do SVI entregue
é preservada exatamente (ρ = 1,0000). **O SVI não foi recalculado em momento
algum.**

### 2.3 O que a mudança custou, medido

| | valor |
|---|---|
| ρ de Spearman com o ranking anterior | 0,947 |
| Deslocamento mediano de posto | 20 posições |
| Top-10 preservado | 5 de 10 |
| Faixa do risco | 0 – 0,566 |
| Municípios em risco exatamente zero | **84** |

---

## 3. O que foi examinado e **mantido**

Cinco questões fecharam com o resultado suspeito confirmado. Vale destacar duas,
porque contrariam a expectativa da revisão.

### 3.1 Não há indicador de vulnerabilidade invertido (AUD-09)

A revisão suspeitava que `pop_rent` e `pop_agevul` estivessem codificados ao
contrário. Os dez indicadores foram rastreados até suas consultas ao SIDRA e
submetidos a um **teste de reversão** contra municípios de posição indisputada.
**Todos passaram.** A inversão global do sinal do PC1 **nunca disparou**
(correlação média +0,468), e impor direção antes do PCA é um **no-op matemático**.

As duas cargas negativas são resultado empírico: não-propriedade é traço de
afluência urbana no Brasil, e a soma de duas caudas etárias que se movem em
sentidos opostos com a renda é quase plana.

### 3.2 Não existem hotspots discretos (AUD-16)

O teste de unimodalidade de Silverman **rejeita** sobre os 280 municípios
(*p* = 0,002) e **não rejeita** sobre os 196 com risco positivo (*p* = 0,556). A
bimodalidade é a massa em zero, não um agrupamento de alto risco. O Fisher–Jenks
concorda: GVF sobe suavemente de 0,678 a 0,974 **sem cotovelo**.

**O risco costeiro brasileiro varia continuamente.** É uma conclusão científica
legítima, e mais informativa que um corte imposto. "Hotspot" passou a ter
definição operacional por **intervalo de confiança**: 7 municípios mantêm o IC de
90 % dentro do top-10, 14 dentro do top-20.

---

## 4. Como o índice se comporta (AUD-13, AUD-07)

### 4.1 O índice é conduzido pelo perigo

Sobre os 196 municípios com risco positivo, o perigo responde por **84,7 %** da
variância de log(risco), a exposição por 35,0 % e a vulnerabilidade por
**−19,7 %** — participação negativa significa que a vulnerabilidade **comprime** a
dispersão. Removendo o perigo da fórmula, ρ = **+0,092** contra o ranking
publicado: **o índice integrado é, operacionalmente, o índice de perigo.**

### 4.2 Uma leitura que precisa ser evitada

A correlação **marginal** entre vulnerabilidade e risco é **−0,372**. Isso **não**
significa que a vulnerabilidade reduza o risco: a correlação **parcial**,
controlando perigo e exposição, é **+0,790**. É supressão, causada pela forte
anticorrelação perigo–vulnerabilidade (ρ = −0,601).

**Interpretação:** o perigo composto no Brasil concentra-se onde a privação
material é menor, porque o forçante é extratropical. É um achado real. Mas parte
da *magnitude* dessa anticorrelação é produzida pela geografia do próprio portão —
o HAT médio vai de **0,49 m** a **2,61 m** de sul a norte, enquanto o forçante
enfraquece na mesma direção.

### 4.3 Estabilidade do ranking

Reamostrando os 33 anos de registro: as posições 1–3 são degeneradas, e a largura
mediana do IC de 90 % é **4,5 posições no top-10** contra **45 na faixa 101–196**.
Oito municípios têm intervalo cobrindo a posição 10 — "top-10" é corte de
apresentação, não classe estatística.

Agregação e ponderação são robustas: ρ ≥ 0,94 em toda a varredura de peso entre
frequência e severidade.

**Uma propriedade a declarar:** 94 dos 196 municípios com risco positivo repousam
sobre **menos de dez eventos** aceitos, e 90 sobre menos de cinco. O mais bem
colocado deles é o **21º do país, com um único evento em 33 anos**.

---

## 5. As duas ressalvas que o leitor precisa encontrar cedo

### 5.1 O critério de onda mede raridade local, não severidade (AUD-02)

O limiar de onda é o **q70 local**, de modo que seu valor absoluto varia por uma
ordem de grandeza: mínimo **0,14 m**, mediana **0,90 m no Maranhão** contra
**1,71 m no Rio Grande do Sul**. **161 dos 280** municípios publicados extraem
perigo de pontos com limiar abaixo de 1,5 m — **incluindo o primeiro colocado**,
São José do Norte, com 1,20 m.

Nenhum piso foi imposto, por duas indisponibilidades demonstradas: a calibração PU
**não determina** o eixo da onda (seis melhores pares dentro de 1 % do score,
cobrindo q50–q80), e a âncora externa exigiria uma formulação de setup/runup com
declividade de face de praia, camada que o projeto reconhecidamente não tem.

**Consequência para o texto:** a quantidade deve ser chamada de *excedência local
de Hₛ*, nunca de "onda extrema".

### 5.2 Dois dos cinco primeiros carregam perigo importado (AUD-05, AUD-04)

**Magé em 3º e Paraty em 5º.** Ambos ficam dentro de baías abrigadas e extraem
perigo de pontos de plataforma **aberta**, a **34,7 km** e **14,8 km**, fora das
baías que os protegem. Duque de Caxias e Guapimirim usam o mesmo ponto de Magé. A
inundação documentada nos quatro é **fluvial e pluvial**, não por onda.

Foi **declarado e não corrigido**: a associação município↔ponto é julgamento de
especialista, versionada como dado de entrada, e redesenhá-la para uma baía
depois de ver o ranking seria seleção sobre o resultado. A legenda da tabela de
top-10 do artigo registra a ressalva.

---

## 6. A validação contra casos conhecidos (AUD-05)

Trinta e dois municípios com evidência independente foram fixados como lista de
referência **antes** da comparação, a partir apenas de fontes anteriores a toda
mudança de método, e commitados antes de a suíte rodar. Perigo e risco receberam
expectativas **separadas**.

**Acertos.** 13 de 14 controles positivos cumprem a expectativa de perigo: São
José do Norte 3º, Laguna 4º, Bertioga 6º, São Sebastião 7º, Rio Grande 17º. Os
controles negativos do Norte **saíram do topo do perigo** — Macapá 188º, Turiaçu
167º, Chaves 138º, Icatu 121º, meio da distribuição.

**Divergências, com três mecanismos distintos:**

| Mecanismo | Casos | Registro |
|---|---|---|
| Importação de perigo por associação | Magé 3º, Paraty 5º, Duque de Caxias, Guapimirim | AUD-04 |
| Supressão perigo–vulnerabilidade | Santa Vitória do Palmar **1º em perigo, 131º em risco**; Osório 40º/156º | AUD-13 |
| MAUP do denominador | Campos dos Goytacazes 159º, Linhares 188º | AUD-08 |

Nenhuma foi explicada por "é risco relativo".

---

## 7. As limitações declaradas

Doze parágrafos transferíveis estão em `README.md` → *Declared limitations for the
manuscript*, com números e scripts. Em resumo:

1. **Calibração 100 % catarinense**, aplicada a 27° de latitude. A busca por base
   de impactos no N/NE deu **negativo qualificado**: recalibrar é impossível, mas
   duas rotas parciais foram nomeadas e não usadas — verificação qualitativa
   contra Muehe (2018) e comparação com marégrafos GLOSS-Brasil/RMPG.
2. **Vulnerabilidade é social apenas** — sem camada de suscetibilidade física.
3. **Exposição é *de jure* e instantânea** — a população flutuante dos balneários
   é invisível, e o viés subestima exatamente o setor de maior perigo.
4. **MAUP do denominador municipal.** Remover o termo relativo levaria Itaboraí de
   118º a 9º e Campos de 159º a 72º — mas também o Rio de Janeiro em 49 posições,
   que é a distorção oposta. O ranking de municípios grandes e parcialmente
   interiores é **piso**.
5. **Erro de fase diário** de 1,2 cm mediano, mas 5–10 cm no Sul micromareal.
6. **"Zero" significa nenhum evento aceito em 1993–2025**, nunca impossibilidade —
   e a fronteira é amostralmente instável: além dos 84 sempre nulos, **94 caem a
   zero em alguns sorteios**, restando **102 dos 280** robustamente não nulos.
7. **O índice é de priorização relativa**, condicional ao domínio de 282
   municípios. `sd(PC1)` é estimado da amostra: excluir o N/NE muda a escala em
   **−57 %** e reordena o restante a ρ = 0,70. **Qualquer análise de subconjunto
   precisa recalcular a escala, não fatiar estes valores.**

---

## 8. Próximos passos, em ordem de tratabilidade

1. **Validação da componente de nível contra marégrafos** GLOSS-Brasil (CHM) e
   RMPG (IBGE) no N/NE. Dado público, e fecha duas limitações de uma vez.
2. **Wave setup calculado diretamente de Hₛ**, substituindo o limiar percentílico
   por um de significado físico local — resolveria piso e abrigo simultaneamente.
3. **Camada de vulnerabilidade física** — cota de terreno, declividade de face de
   praia, barreiras naturais e defesas.
4. **Termo de severidade que escale com raridade**, para que um perigo sustentado
   por um evento em 33 anos não pontue como um sustentado por noventa.
5. **Comparação com o SVI-Coast de Lima et al. (2024)**, não realizada.

---

## 9. Onde está cada coisa

| | |
|---|---|
| Rastreador central | `docs/scientific_audit/ISSUE_TRACKER.md` |
| Registros por questão | `docs/scientific_audit/issues/AUD-NN_*.md` |
| Revisão original, imutável | `docs/scientific_audit/baseline/2026-07-29_initial_review.md` |
| Lista de casos de referência | `docs/scientific_audit/reference_cases.csv` |
| Scripts diagnósticos | `src/exploratory/audit_AUD_*.py` |
| Saídas auditáveis | `outputs/audit/AUD-*/` |
| Notas científicas | `SCIENTIFIC_NOTES.md` |
| Limitações para o manuscrito | `README.md` → *Declared limitations* |

---

## 10. Nota sobre o que este relatório não afirma

O produto **não** foi validado contra observações independentes fora de Santa
Catarina. Nenhuma comparação com marégrafo foi feita. A suíte de casos de
referência é um **teste de sanidade qualitativo**, não validação estatística — a
base catarinense é reconhecidamente sub-reportada e foi usada apenas na
calibração.

O que a auditoria estabelece é mais modesto e mais verificável: que o produto
publicado é **reprodutível a partir da documentação** — as nove fórmulas do README
reconstroem os campos publicados com desvio máximo de 1,3e-06 —, que suas
fragilidades estão **medidas e nomeadas**, e que cada divergência contra a
evidência conhecida tem **mecanismo identificado**.
