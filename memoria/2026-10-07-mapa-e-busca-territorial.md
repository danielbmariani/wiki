---
autor: agente:gpt-6
data: 2026-10-07
fontes: [tse-eleitorado-local-votacao-2026]
status: rascunho
---

# Entrada geográfica e busca de território

A entrada usa Leaflet e tiles do OpenStreetMap para mostrar cidades, bairros e ruas
reconhecíveis. Isso substitui a navegação por contornos estaduais e hexágonos, rejeitada
pelo usuário. O caminho estado → cidade → bairro preserva a orientação após o zoom.
A referência no mapa não é um limite de zona nem permite inferir a zona de uma residência.
Revisão mais recente: cada célula mostra somente seus próprios grupos e o campo
para enviar um link. Sem quadros herdados, ações, notas, materiais ou lugares de
conversa. Sugestão vira issue; admins publicam por PR. Evitar blocos de avisos.

`assets/js/busca.js` compartilha a busca entre a página inicial e Células. Cidades,
estados e combinações de nome com sigla são resolvidos localmente. Escolher uma cidade
carrega somente o índice da UF, preservando a relação muitos-para-muitos entre municípios
e zonas. Bairros e locais públicos oferecem os links para os quadros das zonas.

## Consulta geográfica externa

Justificativa da exceção à preferência por serviços do GitHub: os índices atuais não
contêm ruas; uma consulta opcional ao Photon/OpenStreetMap permite localizar a cidade
por uma rua ou localização aproximada sem introduzir servidor próprio ou chave de API.
O provedor é substituível pelo campo `geocodificador` em `_config.yml`.

- A busca textual de cidades e estados é local. Centralizar um território escolhido
  no mapa consulta uma referência pública no Photon; bairros também podem usá-la.
- A consulta externa acontece apenas ao enviar uma busca sem resultados locais, clicar
  em “Buscar rua ou lugar” ou autorizar “Usar minha localização”.
- Não persistir texto de endereço ou coordenadas no repositório, URL ou armazenamento
  local. Números são removidos da consulta textual; a localização é arredondada e pede
  resultados de cidade. A interface informa o provedor e atribui o OpenStreetMap.
- Um endereço localiza a cidade; a zona precisa ser confirmada pelo local de votação.
- O servidor público tem limites de uso e não garante disponibilidade. Há intervalo
  entre consultas, cache em memória, timeout e alternativa pelos dados locais.
- Tiles são outra exceção à hospedagem GitHub: `mapa_tiles` configura o provedor,
  com atribuição visível, cache normal do navegador e sem download em massa. Leaflet
  vem de CDN com versão fixa e SRI; se falhar, a busca local segue disponível.

Referências: [Photon](https://github.com/komoot/photon),
[API](https://github.com/komoot/photon/blob/master/docs/api-v1.md),
[atribuição do OpenStreetMap](https://www.openstreetmap.org/copyright).
