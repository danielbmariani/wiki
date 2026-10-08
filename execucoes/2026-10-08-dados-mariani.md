---
id: BR
autor: agente:claude-fable-5
data: 2026-10-08
fontes: [mariani-voto-renda-2026]
status: rascunho
---

# Incorporação dos dados (voto × renda × área de ponderação)

- **Objetivo:** disponibilizar na Colmeia os dados combinados no grupo
  (Daniel Mariani + Adriano, 08/10): votações pelo método da Folha estendido por
  setor e as áreas de ponderação com religião, evitando duplicar o que o
  pipeline local já gera.
- **Entradas:** pacote v1.0.0 de dados-eleicoes.danielmariani.com.br (manifest com
  SHA-256; gerado por pipeline com gates de auditoria — spot-checks
  contra a fonte, universo = malha 2022, checksums).
- **Modelo:** agente:claude-fable-5, operado pelo autor do pipeline (@danielbmariani).
- **Saídas:** `dados/mariani/` na Colmeia (parquet por setor, área de
  ponderação completa, correspondência setor→área, dicionário, README com
  limitações); ficha `fontes/mariani-voto-renda-2026.md`; memória
  `memoria/2026-10-08-dados-mariani.md`.
- **Em aberto:** 2º turno de 2026 entra após 25/10 (mesmo processo de
  auditoria); eleições 2010–2018 em preparação;
  avaliar juntar os `dados/setores/` da Colmeia com as áreas de
  ponderação via `setor_apond.csv.gz` (abstenção por área de ponderação ×
  religião seria análise nova, impossível só com dados por município).
