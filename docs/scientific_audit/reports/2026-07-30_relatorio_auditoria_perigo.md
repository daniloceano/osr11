# Revisão da definição de evento composto e do índice de perigo costeiro

**Relatório técnico-científico — OSR11**
**Data:** 30 de julho de 2026
**Escopo:** questões de auditoria AUD-17, AUD-01, AUD-06 e AUD-04
**Situação:** AUD-01, AUD-04 e AUD-06 encerradas; AUD-17 encerrada em seis de oito itens

---

## Sumário executivo

Uma revisão metodológica independente dos resultados de risco costeiro
identificou que os hotspots dominantes do produto — concentrados no Maranhão,
Pará e Amapá — eram sustentados por eventos classificados como "compostos" que
correspondiam, de fato, à modulação astronômica de sizígia, e não a eventos de
tempestade.

Investigamos a origem do problema, confirmamos o diagnóstico por três vias
independentes, e o resolvemos redefinindo o papel da maré astronômica na
detecção. A maré deixou de ser um **forçante** que decide se houve evento e
passou a ser uma **variável condicionante** que decide se a água efetivamente
superou o nível ao qual a costa está adaptada. No mesmo movimento, a componente
de duração do índice de perigo foi substituída por uma medida de severidade
integrada, após demonstrarmos que as duas correções são inseparáveis.

O campo de perigo resultante apresenta gradiente Sul→Norte coerente com a
climatologia de ciclones extratropicais do Atlântico Sul, e a proporção de
municípios do top-10 de risco situados ao norte de 20°S caiu de 70 % para 50 %.
A cobertura nacional foi integralmente preservada: nenhum município ou ponto de
grade foi excluído.

Três limitações relevantes permanecem e estão declaradas na §6.

---

## 1. O problema identificado

### 1.1 Formulação original

O evento composto era definido como a sobreposição temporal de dois episódios
independentes, ambos detectados por excedência do percentil 90 local ao longo
de 1993–2025:

- um episódio de onda, sobre a altura significativa (WAVERYS);
- um episódio de nível, sobre o nível total `SSH_total = zos + maré`, em que
  `zos` é o nível dinâmico do GLORYS12 e a maré vem do FES2022.

### 1.2 A anomalia observada

Duas observações não se acomodavam à interpretação física declarada:

1. municípios do Golfão Maranhense e do estuário amazônico ocupavam as primeiras
   posições do índice integrado de risco;
2. o litoral central de Santa Catarina — onde há registro documentado de
   interrupção operacional portuária e de obras de engorda de praia de grande
   porte — ocupava as últimas posições.

### 1.3 Hipótese diagnóstica

Formulamos a hipótese de que, em regime macromareal, o percentil 90 local do
nível total não estaria selecionando sobrelevação meteorológica, e sim o
envelope de sizígia. Se verdadeira, as excedências ocorreriam com periodicidade
quinzenal **por construção**, independentemente de qualquer condição atmosférica.

---

## 2. O que foi testado

### 2.1 Teste de fase contra o ciclo sizígia–quadratura

Aplicamos o teste de Rayleigh de uniformidade circular às datas de início dos
eventos compostos de cada um dos 808 pontos costeiros, tomando como referência
o período sinódico-semi de 14,765 dias.

| Setor | Comprimento resultante *R* | Pontos com *p* < 0,01 |
|---|---|---|
| Rio Grande do Sul | 0,085 | 5 % |
| Santa Catarina / Paraná | 0,355 | 70 % |
| São Paulo / Rio de Janeiro | 0,591 | 100 % |
| Nordeste | 0,835 | 100 % |
| Norte equatorial | 0,821 | 100 % |
| Amapá | 0,806 | 100 % |

No conjunto do domínio, 88,5 % dos pontos apresentaram agrupamento de fase
estatisticamente significativo. No Rio Grande do Sul — onde a literatura
documenta ressacas de origem sinótica associadas à passagem de ciclones
extratropicais — a fase é essencialmente aleatória, como se espera de um
forçante meteorológico.

### 2.2 Decomposição da variância do nível total

Para verificar o mecanismo proposto, decompusemos a variância de `SSH_total` em
suas parcelas astronômica e dinâmica:

| Setor | var(maré) / var(nível total) |
|---|---|
| Rio Grande do Sul | 0,22 |
| São Paulo / Rio de Janeiro | 0,73 |
| Norte equatorial | 0,985 |

A correlação de Spearman entre essa razão e o comprimento resultante do teste de
Rayleigh é **0,837**, o que confirma quantitativamente o mecanismo: onde a maré
domina a variância do nível, o percentil local seleciona sizígias.

### 2.3 Magnitudes físicas

Comparamos a sobrelevação meteorológica extrema (anomalia de nível dinâmico no
percentil 99) com a modulação sizígia–quadratura da preamar diária:

| Setor | Sobrelevação q99 | Modulação de sizígia | Razão |
|---|---|---|---|
| Rio Grande do Sul | 48,8 cm | 46,3 cm | **1,05** |
| São Paulo / Rio de Janeiro | 26,5 cm | 65,7 cm | 0,40 |
| Norte equatorial | 11,8 cm | 162,6 cm | **0,07** |

No extremo sul, uma sobrelevação extrema supera toda a oscilação astronômica da
preamar; no setor equatorial ela representa 7 % dessa oscilação.

### 2.4 Discriminação entre artefato e modulação física

Um agrupamento de fase elevado admite duas leituras distintas: a maré **domina**
o nível e os eventos são sizígias, ou a maré **modula** o nível e os eventos são
tempestades cuja coincidência com a preamar as leva a cruzar o limiar. A segunda
situação é fisicamente legítima e desejável num arcabouço de eventos compostos.

Construímos um discriminador: a fração de eventos detectados que apresentam
sinal independente de tempestade, definido como excedência do percentil 90 local
do nível dinâmico — variável que verificamos ser livre de maré (§3.1) — em ao
menos um dia do evento.

| Setor | Fração corroborada por tempestade |
|---|---|
| Rio Grande do Sul | 0,92 |
| Santa Catarina / Paraná | 0,82 |
| São Paulo / Rio de Janeiro | 0,78 |
| Norte equatorial | **0,17** |
| Amapá | 0,33 |

Este resultado tem consequência metodológica além do diagnóstico imediato:
**o teste de fase, isoladamente, não distingue artefato de física** e não deve
ser reportado sem a fração de corroboração ao lado.

---

## 3. O que foi confirmado e o que foi refutado

### 3.1 Confirmado

- **O nível dinâmico do GLORYS12 é livre de maré.** Detecção realizada apenas
  sobre essa variável não apresenta agrupamento de fase em nenhum dos 808 pontos
  (0 %, contra 98,4 % sobre o nível total).
- **A altura de onda também é livre de maré.** Zero pontos com agrupamento
  significativo, o que exclui a possibilidade de reintrodução do sinal
  astronômico pela componente de onda.
- **O agrupamento de fase no setor Sul/Sudeste é modulação física legítima**, não
  artefato, conforme §2.4.
- **A componente de duração media coincidência estatística, não duração física.**
  Ela contabilizava os dias em que dois testes de percentil concordavam. Sua
  amplitude domínio-total era de aproximadamente um dia, imposta pela resolução
  diária do campo de nível, e correlacionava **negativamente** com a frequência
  (Spearman −0,550), de modo que as duas componentes se cancelavam dentro da
  média equiponderada.

### 3.2 Refutado ou não sustentado

- **A hipótese de que o ciclo sazonal explicasse a persistência anômala do nível
  no trópico não se sustentou.** A amplitude sazonal do nível dinâmico é da mesma
  ordem do desvio-padrão sinótico (razão 0,9–1,8), de modo que a remoção da
  sazonalidade seria um ajuste marginal. A proposta de de-sazonalização foi
  descartada, também por ser conceitualmente incoerente com um enquadramento
  baseado em cota física absoluta.
- **A hipótese de contaminação dominante por descarga fluvial nos extremos do
  setor amazônico foi enfraquecida.** A fase do ciclo anual dos extremos de nível
  dinâmico ali não coincide com o máximo de descarga do Amazonas: o Amapá
  apresenta pico em abril e o setor equatorial em setembro, este último o período
  de vazão mínima. A hipótese permanece aberta para o ciclo médio.
- **A correção isolada do detector não resolve o problema.** Aplicada sem a
  revisão da componente de duração, a proporção do top-10 ao norte de 20°S
  aumentava de 70 % para 90 %. Simetricamente, remover apenas a duração do método
  original também elevava essa proporção para 90 %. Apenas a adoção conjunta
  produz o resultado defensável.

---

## 4. A solução adotada

### 4.1 Princípio

A maré astronômica desempenha dois papéis distintos num sistema costeiro. É uma
oscilação previsível e recorrente, à qual a ocupação, a infraestrutura e a
morfologia se adaptam; e é um amplificador do impacto de forçantes
meteorológicos. A formulação original atribuía ambos os papéis a uma única
variável, o que permitia que o primeiro determinasse a existência do evento.

A revisão separa os dois papéis. A maré não decide mais **se** houve evento;
decide **se a água superou o nível rotineiro** e **quão severo** o evento foi.
Esta é a estrutura de forçantes e variável condicionante da tipologia de eventos
compostos de Zscheischler et al. (2020), já adotada no enquadramento conceitual
do trabalho.

### 4.2 Definição de evento

Um evento composto passa a exigir três condições simultâneas:

1. episódio de onda extrema, por excedência do percentil 90 local;
2. episódio de sobrelevação, por excedência do percentil 90 local do nível
   **dinâmico**, isto é, sem a componente astronômica;
3. nível estático superando a **preamar média de sizígia** (MHWS) local em ao
   menos um dia da sobreposição.

O nível estático é a soma da anomalia dinâmica de nível com a maré astronômica.
A anomalia é tomada em relação à média local, porque o nível dinâmico do modelo
é referenciado ao geoide enquanto o datum de maré é referenciado ao nível médio
do mar; a diferença entre os dois é a topografia dinâmica média, que varia ao
longo da costa.

### 4.3 Escolha do datum

Adotamos a **preamar média de sizígia (MHWS)**, calculada a partir das constantes
harmônicas do FES2022 como a soma das amplitudes das componentes M2 e S2 acima do
nível médio do mar. Trata-se de um datum hidrográfico padrão, presente em carta
náutica, e não de um limiar escolhido pelo analista.

A escolha foi submetida a teste de sensibilidade contra três alternativas — os
percentis 90 e 99 da preamar diária e a maior preamar astronômica (HAT). O viés
latitudinal do resultado é praticamente invariante (Spearman contra latitude
absoluta entre +0,925 e +0,932), o que indica que a conclusão não depende do
datum escolhido. Optamos pelo MHWS por ser coerente com o argumento de adaptação:
a ocupação costeira ajusta-se ao nível que observa quinzenalmente, não ao nível
que ocorre uma vez a cada ciclo nodal de 18,6 anos.

Registramos uma estatística de valor próprio, robusta a essa escolha: no
Sul/Sudeste praticamente todo evento composto detectado eleva a água acima da
preamar de sizígia local (99–100 %), ao passo que no setor equatorial apenas
27–66 % dos eventos o fazem, conforme o rigor do datum.

### 4.4 Ausência de termo de empilhamento de onda

Consideramos e descartamos a inclusão de uma parcela de sobrelevação por ondas
no nível. As ondas já atuam como forçante e como metade do termo de severidade;
somá-las também ao nível implicaria contagem parcialmente duplicada. Além disso,
uma parametrização defensável de *setup* depende do parâmetro de similaridade de
surfe, que requer período de onda e declividade de praia — nenhum dos dois
disponível para os 808 pontos.

### 4.5 Revisão do índice de perigo

O índice passou de três para duas componentes equiponderadas:

- **frequência**, o número de eventos compostos no período;
- **severidade integrada**, a severidade composta somada ao longo dos dias em que
  as três condições vigoram, combinando o excesso de onda sobre o limiar local e
  o excesso de nível sobre o MHWS.

Cinco definições candidatas para a terceira componente foram comparadas sobre os
mesmos eventos. O critério de escolha foi estrutural e fixado antes de examinar o
ranking: apenas as formas integradas invertem o sinal da correlação com a
frequência, deixando de cancelá-la.

| Candidata | ρ com frequência | ρ com latitude absoluta |
|---|---|---|
| duração, definição original | −0,77 | −0,79 |
| duração pelos três critérios | −0,49 | −0,54 |
| percentil 95 da duração | −0,44 | −0,63 |
| excesso de nível integrado | **+0,39** | −0,08 |
| **severidade integrada** | **+0,60** | +0,35 |

A severidade integrada resolve simultaneamente as três patologias registradas:
mede grandeza física, é um integral contínuo e portanto não limitado pela
discretização diária, e reforça a frequência em vez de cancelá-la.

Duração e severidade de pico permanecem calculadas e publicadas como
diagnósticos; deixaram apenas de compor o índice.

---

## 5. Resultado: antes e depois

### 5.1 Campo de perigo

| | Método original | Método revisado |
|---|---|---|
| Gradiente latitudinal do índice (ρ com \|latitude\|) | fraco e não monotônico | **+0,584** |
| Interação entre as componentes | ρ = −0,550 (cancelamento) | **ρ = +0,599 (reforço)** |
| Índice médio, Rio Grande do Sul | 0,722 | **0,826** |
| Índice médio, Nordeste | 0,253 | 0,125 |
| Índice médio, Norte equatorial | 0,234 | 0,167 |

O campo revisado apresenta máximo no extremo sul e decaimento monotônico para
norte, coerente com a densidade de ciclogênese e de passagens frontais do
Atlântico Sul.

### 5.2 Ranking municipal de risco

| | Método original | Método revisado |
|---|---|---|
| Top-10 ao norte de 20°S | 70 % | **50 %** |
| Top-20 ao norte de 20°S | 75 % | **45 %** |

Posições de municípios de referência, entre 280 avaliados:

| Município | Antes | Depois |
|---|---|---|
| São José do Norte (RS) | 25º | **4º** |
| São Sebastião (SP) | 17º | **13º** |
| Bertioga (SP) | 24º | **20º** |
| Navegantes (SC) | 273º | **216º** |
| Itajaí (SC) | 275º | **230º** |
| Balneário Camboriú (SC) | 280º | 279º |

Os municípios cuja exposição a ressacas está documentada na literatura e em
registros técnicos subiram consistentemente. A cobertura nacional foi preservada:
nenhum município ou ponto de grade foi excluído do produto.

### 5.3 Concordância global

A correlação de Spearman entre os campos de perigo dos dois métodos é 0,756, e
entre os riscos municipais, 0,854; a sobreposição do top-10, porém, é de apenas
2 municípios. O método altera pouco o ordenamento geral e substancialmente a
composição do topo — que é precisamente o resultado que o manuscrito reporta.

---

## 6. O que **não** foi resolvido

As limitações abaixo estão dentro do escopo desta revisão ou dela decorrem, e
precisam constar do manuscrito.

**Limiar de onda fisicamente vazio em pontos abrigados.** O percentil 90 local da
altura de onda atinge 0,20 m em pontos da Baía do Guajará e 0,51 m em Macapá.
Nenhuma dessas magnitudes corresponde a onda extrema. A condição de nível filtra
parte desses eventos, mas o limiar de onda em si não foi corrigido.

**Calibração de limiares não refeita.** O par de percentis em uso foi otimizado
sobre a definição anterior de nível, empregando 147 pares município–data de
Santa Catarina. Ele segue aplicado à variável nova sem recalibração. Cabe
registrar que o desempenho dessa calibração já era limitado na própria região de
origem, com recuperação de cerca de 10 % dos eventos reportados.

**Ausência de base de impactos fora de Santa Catarina.** Não há registro
sistemático de eventos costeiros para o Norte e o Nordeste comparável ao da
Defesa Civil catarinense. Consequentemente, não é possível distinguir entre
"o sinal não existe na natureza" e "o modelo não resolve o sinal" no setor
amazônico, onde a sobrelevação modelada é da ordem de 4 a 16 cm sobre uma
plataforma larga e rasa em que o empilhamento por vento pode ser eficiente.

**Interação não linear maré–sobrelevação não representada.** O nível dinâmico e a
maré provêm de modelos independentes, e sua soma linear ignora a supressão de
sobrelevação em preamar em água rasa — efeito potencialmente relevante justamente
no setor macromareal.

**Incoerência de fase residual no nível estático.** A anomalia de nível é diária e
a maré entra pelo seu máximo diário; as duas quantidades não são estritamente
simultâneas. A formulação deixou de governar a detecção, mas permanece na
condição de nível e no termo de severidade.

**Casos de Santa Catarina apenas parcialmente corrigidos.** Itajaí e Navegantes
subiram cerca de 45 e 57 posições, mas seguem no terço inferior. Duas causas
independentes desta revisão continuam atuando: o ponto de grade atribuído a esses
municípios encontra-se em setor abrigado, com limiar de onda de 1,82 m contra
2,33 m a 0,2° a leste; e Balneário Camboriú recebe índice de vulnerabilidade
social exatamente nulo, artefato da normalização por mínimo e máximo que fixa sua
posição independentemente do perigo atribuído.

---

## 7. A associação entre pontos de grade e municípios

Cada município recebe o valor de perigo de um ponto da grade oceânica. A revisão
identificou que a regra descrita na documentação — *"o ponto de maior contagem
de eventos compostos"* — não se reproduzia: apenas 15,7 % a 24,6 % das
atribuições correspondiam a ela, contra 59,3 % que correspondiam simplesmente ao
ponto mais próximo.

### 7.1 A origem da regra

A autora da associação esclareceu que o procedimento foi conduzido por
**inspeção visual em ambiente SIG, município a município**, arbitrando
simultaneamente dois critérios: proximidade e atividade de eventos no ponto
candidato. Não existe rotina computacional, e nenhuma pode ser recuperada.

Isso explica exatamente o padrão observado: quem equilibra dois critérios a olho
não coincide sistematicamente com nenhum deles isoladamente.

### 7.2 As escolhas são sistemáticas

Testamos se as decisões manuais eram arbitrárias. Nos 114 municípios em que a
autora não selecionou o ponto mais próximo, **62 %** dos pontos escolhidos
apresentam limiar local de altura de onda **maior** que o do ponto mais próximo
(mediana 1,77 m contra 1,69 m). Esse é o comportamento esperado de quem evita
deliberadamente pontos abrigados no interior de baías.

Vários casos inicialmente classificados como erro — Caraguatatuba, Colares,
Vigia — são municípios de enseada ou baía, nos quais selecionar um ponto
oceânico mais distante é plausivelmente a decisão correta, e uma regra
puramente geométrica erraria. A classificação de erro foi retirada.

### 7.3 O que foi feito

O problema não era a regra, e sim que o artefato **não estava sob controle de
versão**: existia apenas dentro do arquivo entregue, que é excluído do
versionamento. Sua perda implicaria a perda irrecuperável do valor de perigo dos
280 municípios.

A associação passou a ser tratada pelo que é — **um conjunto de dados de entrada
produzido por julgamento de especialista** — e foi arquivada como tal, com
proveniência declarando autoria, método, origem e limitações. O processamento
passou a consumir o artefato arquivado e a verificá-lo contra o arquivo
entregue, interrompendo a execução em caso de divergência. Nenhum valor de
perigo foi alterado.

Julgamento de especialista é entrada legítima em ciência — como uma linha de
costa digitalizada ou uma classificação geomorfológica — desde que arquivado,
descrito e com limitações declaradas. O que não era admissível era a
documentação descrever uma regra determinística que nunca existiu.

### 7.4 Propriedades a reportar

| | |
|---|---|
| Municípios com ponto associado | 280 de 282 |
| Pontos de grade distintos | **178** |
| Máximo de municípios por ponto | **9** |
| Distância município → ponto, mediana | 13,1 km |
| Distância município → ponto, máxima | 89,2 km |
| Atribuições acima de 30 km | 20 |

Duas consequências decorrem e devem acompanhar qualquer resultado derivado. Os
valores de perigo **não são espacialmente independentes** entre municípios
vizinhos, já que 178 pontos servem 280 unidades. E os municípios do fundo da
Baía de Guanabara **não possuem ponto de grade algum num raio de 30 km**: seu
perigo refere-se necessariamente à plataforma aberta e não representa as
condições no interior da baía. Testamos cinco regras alternativas de associação
e todas retornam o mesmo valor nesses casos — trata-se de limitação de
cobertura da grade, não da regra de atribuição.

---

## 8. Correções documentais associadas

Paralelamente, foram corrigidas inconsistências factuais entre a documentação do
projeto e o cálculo efetivamente executado, sem alteração de qualquer valor
numérico publicado. As principais eram a descrição de uma fórmula de risco
superada, de duas componentes, no documento de entrada do repositório; e duas
afirmações, presentes nos metadados publicados, de que um campo utilizado como
fator do índice de risco não seria empregado por nenhum produto. Duas
inconsistências adicionais do mesmo tipo foram localizadas por varredura e
corrigidas.

Dois itens permanecem pendentes: a criação de um documento de notas científicas
referenciado mas inexistente, deliberadamente adiado até a estabilização do
método, e a divergência entre a definição de um indicador socioeconômico no
manuscrito e a coluna correspondente publicada.

---

## 9. Reprodutibilidade

O método anterior foi integralmente preservado, com seus produtos de perigo e de
risco arquivados e documentados, de modo que qualquer resultado publicado antes
desta revisão permanece reproduzível e comparável. A comparação lado a lado entre
os dois métodos foi construída mantendo exposição e vulnerabilidade idênticas nos
dois braços, de forma que as diferenças observadas decorrem exclusivamente da
definição de evento.

A implementação revisada foi verificada contra a anterior nos elementos que não
mudaram: o limiar de onda recalculado reproduz o valor de produção nos 808 pontos
com diferença máxima nula.

---

## Referências

Zscheischler, J., Martius, O., Westra, S., Bevacqua, E., Raymond, C.,
Horton, R. M., van den Hurk, B., AghaKouchak, A., Jézéquel, A., Mahecha, M. D.,
Maraun, D., Ramos, A. M., Ridder, N. N., Thiery, W., & Vignotto, E. (2020).
A typology of compound weather and climate events. *Nature Reviews Earth &
Environment*, 1, 333–347. https://doi.org/10.1038/s43017-020-0060-z

Mardia, K. V., & Jupp, P. E. (2000). *Directional Statistics*. Wiley.

Pugh, D., & Woodworth, P. (2014). *Sea-Level Science: Understanding Tides,
Surges, Tsunamis and Mean Sea-Level Changes*. Cambridge University Press.
https://doi.org/10.1017/CBO9781139235778

Lyard, F. H., Allain, D. J., Cancet, M., Carrère, L., & Picot, N. (2021).
FES2014 global ocean tide atlas: design and performance. *Ocean Science*, 17,
615–649. https://doi.org/10.5194/os-17-615-2021

Stockdon, H. F., Holman, R. A., Howd, P. A., & Sallenger, A. H. (2006).
Empirical parameterization of setup, swash, and runup. *Coastal Engineering*,
53(7), 573–588. https://doi.org/10.1016/j.coastaleng.2005.12.005

Muis, S., Verlaan, M., Winsemius, H. C., Aerts, J. C. J. H., & Ward, P. J.
(2016). A global reanalysis of storm surges and extreme sea levels.
*Nature Communications*, 7, 11969. https://doi.org/10.1038/ncomms11969

---

*Registros detalhados, com diagnósticos, dados intermediários e critérios de
aceitação, encontram-se no sistema de auditoria científica do projeto, questões
AUD-01, AUD-06 e AUD-17.*
