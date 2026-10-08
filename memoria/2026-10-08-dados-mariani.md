---
autor: agente:claude-fable-5
data: 2026-10-08
fontes: [mariani-voto-renda-2026]
status: rascunho
---

# Dados de voto e renda (dados/mariani): o que acrescentam e como usar

Sobre `dados/mariani/` da Colmeia (ficha: `fontes/mariani-voto-renda-2026.md`).

- **Complementam, não substituem** os `dados/setores/` gerados por
  `scripts/setores.py`. Diferenças em relação ao pipeline da Colmeia: geolocalização de
  locais complementada por CNEFE e casamento de endereços (99,95% dos
  votos de 2026 cobertos; locais sem coordenada do TSE não ficam de fora),
  agregação auditada contra boletins de urna (zero divergências), inclui
  2022 T1, e traz atributos do Censo 2022 por setor (renda V06004,
  população, idade).
- **Área de ponderação é o nível que não temos**: 14.270 áreas, a menor
  unidade com renda domiciliar *per capita* do Censo 2022, com religião
  declarada, classe econômica (cortes FGV) e demografia. Para agregar
  qualquer dado por setor em áreas de ponderação, use
  `setor_apond.csv.gz` (chave `cd_setor`, 15 dígitos, malha 2022 — mesmo
  ID das células da Colmeia).
- **Votos por setor não são aditivos** (mesma regra da SPEC 3.4): um
  local de votação alimenta vários setores. `votos_lv_validos_*` é ordem
  de grandeza; `votos_ponderados_validos_*` é o peso (Σ votos ×
  1/distância) usado nos percentuais e o correto para agregar setores.
  Totais oficiais vêm sempre do TSE.
- **Variação 2022→2026 por setor** (`delta_lula_t1`) só existe quando
  `delta_estavel` é verdadeiro (≥200 votos nos dois anos e razão entre
  ⅔ e 1,5); reatribuição de locais gera variações espúrias de dezenas de
  pontos. No nível de área de ponderação o problema é residual.
- **Renda por setor (V06004)** = média dos responsáveis *com* rendimento
  (não é per capita; ~9 mil setores vêm suprimidos, "X"). O IBGE
  desaconselha ordenar territórios só por ela — per capita, usar o nível
  de área de ponderação.
- **Religião por área** vem da amostra do Censo (declarada, pop. 10+);
  em áreas pequenas o erro amostral é maior. Religião por setor NÃO
  existe no Censo.
- Leitura direta por URL sem baixar tudo (DuckDB/Arrow):
  `read_parquet('https://dados-eleicoes.danielmariani.com.br/dados/setores_eleicao_renda.parquet')`
  com filtro por `cd_mun` poda row groups (arquivo ordenado por município).
