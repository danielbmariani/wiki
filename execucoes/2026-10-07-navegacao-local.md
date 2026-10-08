---
id: BR
autor: agente:gpt-6
data: 2026-10-07
fontes: [tse-eleitorado-local-votacao-2026]
status: rascunho
---

# Navegação local e envio do projeto

## Objetivo

Atender à revisão do usuário: remover canais nacionais, tornar o zoom reconhecível
e enviar a pasta ao repositório por branch e Pull Request.

## Entradas

SPEC.md, AGENTS.md, memória, aplicação Jekyll, índices TSE e grupos existentes.
Documentação oficial do Leaflet, Photon e política de tiles do OpenStreetMap.
Alterações locais e importação de grupos concomitante foram preservadas.

## Modelo

Agente GPT-6, via Codex.

## Saídas

- Mapa de ruas com escala, zoom, nomes e caminho estado → cidade → bairro.
- Busca progressiva por cidade, bairro e escola; opção de localizar a cidade da área.
- Consulta geográfica com fila, cache em memória, timeout e alternativa local.
- Remoção de grupos nacionais e de herança estadual/nacional nos quadros de zona.
- Guia local Como participar substitui o catálogo amplo de recursos.
- Especificação e memória alinhadas à revisão; caches excluídos do versionamento.
- Envio solicitado inclui a aplicação e infraestrutura que estavam sem versionamento.

## Verificação

Revisão posterior do usuário simplificou a célula para grupos e envio de convite.
Removidas todas as seções de conteúdo e herança da interface; formulário valida
o link e abre issue preenchida para admins. Avisos reduzidos a uma linha curta.

Build Jekyll, sintaxe JavaScript, checagem do projeto e 32 testes do pipeline.
Corrigida a checagem para ignorar assets binários fora do seu escopo de conteúdo.
Chromium local em 1440, 768, 390 e 320 pixels, sem overflow horizontal. Fluxo real,
sem simulação externa: São Paulo → Pinheiros → escola → quadro local. CDN, tiles
e Photon carregaram; canais nacionais não apareceram. Capturas inspecionadas e
corrigida interferência de CSS antigo no ícone de atribuição do mapa.

## Em aberto

Revisão humana e mescla do Pull Request. Não publicar diretamente na principal.
Serviços públicos de mapas e geocodificação não oferecem garantia de disponibilidade;
podem exigir provedor dedicado conforme o tráfego crescer. Sem inferência de zona
por endereço e sem persistência de localização pessoal.
