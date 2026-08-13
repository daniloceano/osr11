# `docs/` — Documentação transversal do OSR11

Este diretório reúne documentação que **atravessa mais de uma etapa** do fluxo
de trabalho e que, por isso, não pertence a nenhum diretório numerado de `src/`.

Documentação específica de um módulo continua junto do código, seguindo a
convenção já estabelecida no repositório (`README.md`, `RUN.md`,
`SCIENTIFIC_NOTES.md`, `INTEGRATION_NOTES.md`, `PARAMETER_DECISIONS.md` dentro
de cada `src/0N_*/`).

---

## Conteúdo

| Caminho | O que é |
|---------|---------|
| `scientific_audit/` | Auditoria científica e metodológica dos resultados de risco costeiro: revisão preservada, rastreador central de questões e registros detalhados por questão |
| `DATA_SOURCES.md` (em inglês) | Lista dos dados externos reproduzíveis efetivamente usados nos produtos finais (ID, tipo, acesso, documentação), para a seção de dados do paper |

---

## O que **não** vai aqui

- Scripts de análise (vão para `src/`)
- Dados brutos ou processados (vão para `data/`)
- Saídas regeneráveis — figuras, tabelas, GeoJSON (vão para `outputs/` ou
  `site/public/data/`)
- Documentação de um único módulo (fica junto do módulo em `src/`)
