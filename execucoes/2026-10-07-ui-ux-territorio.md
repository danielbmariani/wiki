---
id: BR
autor: agente:gpt-6
data: 2026-10-07
fontes: [tse-eleitorado-local-votacao-2026]
status: rascunho
---

# Interface e navegação territorial

## Objetivo

Melhorar a interface e a experiência de localização. Incorporar a orientação de usar
geografia reconhecível, uma apresentação mais marcante e busca por cidades, estados,
bairros, lugares públicos e ruas.

## Entradas

SPEC.md, AGENTS.md, arquivos de memória, layouts Jekyll, estilos e scripts existentes,
índices de células e locais públicos, contornos das UFs já presentes nos dados,
documentação pública do Photon/OpenStreetMap. O checkout já tinha alterações locais;
foram preservadas, inclusive alterações concomitantes de conteúdo e contribuição.

## Modelo

Agente GPT-6, via Codex.

## Saídas

- Entrada com mapa real do Brasil, siglas, seleção de UF por clique ou teclado,
  aproximação do território, retorno à visão nacional e acesso aos quadros.
- Tipografia maior, cores de papel e vegetação, linhas editoriais e menos cartões
  arredondados. Navegação, busca, quadros e recursos compartilham a linguagem visual.
- Componente único de busca com cidades e estados locais, consultas como “Campinas SP”,
  seleção de cidade e busca de bairros ou locais de votação no índice estadual.
- Ruas e localização aproximada via consulta opcional ao Photon, sem persistir endereço
  ou coordenadas, com confirmação da cidade antes de escolher o local de votação.
- Carregamento, sugestões, falhas recuperáveis e explicação de como contribuir.
- Proposta de memória sobre geografia e limites da consulta externa.

## Verificação

Build do Jekyll, sintaxe dos scripts e checagem do projeto. Os 31 testes existentes do
pipeline passaram. Verificação em Chromium local nas larguras de 1440, 768, 390 e 320
pixels para início, busca, quadro de zona e recursos, com capturas inspecionadas.
Os fluxos incluem teclado no mapa, recorte estadual, seleção de célula, retorno ao
Brasil, nomes de cidades/estados/siglas, bairro com cidade e localização autorizada
ou negada. Respostas externas foram simuladas nos testes de navegador; uma consulta
real de uma avenida pública confirmou o formato de retorno do Photon. O fluxo real
no Chromium também retornou a cidade correta, incluindo a validação de CORS.

O navegador compartilhado estava indisponível; a inspeção usou Chromium local. Os
artefatos temporários de QA ficam em `/tmp/colmeia-ui-qa-v2`. A prévia Jekyll está em
`http://127.0.0.1:4100/colmeia/`.

## Em aberto

Publicação e revisão humana pelo fluxo de Pull Request. Nenhum push ou deploy foi
feito. A consulta externa depende da disponibilidade e dos limites do provedor público;
o mapa e a busca local continuam sendo alternativas. A zona não é deduzida do endereço.
