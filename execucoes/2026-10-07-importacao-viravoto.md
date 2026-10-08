---
id: BR
autor: agente:gpt-6
data: 2026-10-07
fontes: [flow-page-viravoto]
status: rascunho
---

# Importação dos grupos Vira Voto

## Objetivo

Adicionar à base da Colmeia os links coletivos públicos do diretório Vira Voto, conforme solicitado.

## Entradas

Página https://flow.page/viravoto, IDs de `dados/celulas.json` e arquivos existentes de `_data/grupos/`.

## Modelo

agente:gpt-6.

## Saídas

33 links do Telegram: um grupo em cada uma das 27 UFs brasileiras, um grupo em ZZ (Exterior) e cinco links em BR (canal, grupo nacional, debates, designers e produção audiovisual). Os links nacionais existentes foram preservados. A interface existente carrega os YAMLs por `site.data.grupos` em `dados/quadros.json`, sem necessidade de alterar JavaScript ou quadros.

Ficha da fonte: `inteligencia/fontes/2026-10-07-viravoto.md`.

## Validação

`python pipeline/checar.py <arquivos alterados>` passou sem erros. Conferência com a fonte confirmou os 33 links importados sem duplicatas e a preservação dos dois canais nacionais existentes.

## Em aberto

Validade e atividade atual dos grupos não verificadas. Publicação e aprovação dos links continuam sujeitas à revisão dos admins pelo fluxo do projeto. Não foram coletados dados de participantes.
