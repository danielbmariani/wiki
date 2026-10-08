---
id: BR
autor: agente:claude-opus-5-5
data: 2026-10-08
fontes: [ibge-tse-setores-2026]
status: rascunho
---

# Setor censitário como célula

## Objetivo

Reformular a plataforma para usar o setor censitário (Censo 2022) como célula, em todo o país, com
estimativas eleitorais por setor e uma home no estilo do mapa de resultados por vizinhança.

## Entradas

Pedido do admin em 2026-10-08; método de deltafolha/eleicoes-por-setores-censitarios; malha de setores
do IBGE; locais, votação e detalhe por seção do TSE (2026 T1 e 2022 T2).

## Modelo

Claude Opus 5.5, via Claude Code.

## Saídas

- `SPEC.md` revisada (seções 1, 3, 4, 5, 8, 10).
- `pipeline/setores.py`: ligação setor ↔ locais por faixas de 100 m, estimativas ponderadas, tiles PMTiles.
- Home reescrita com MapLibre (`index.html`, `assets/js/mapa.js`); grupos por setor em `_data/grupos/<UF>/setores/`.
- Workflow `site.yml`: gera os dados e publica o Pages por Actions.

## Em aberto

- Trocar o Pages para "GitHub Actions" nas configurações do repositório.
- Medir tamanho final do PMTiles nacional e tempo do pipeline no runner gratuito.
- Página Células ainda lista zonas e municípios; falta listar setores.
- Geocodificar locais sem coordenada (CNEFE) para aumentar a cobertura de 2022.
