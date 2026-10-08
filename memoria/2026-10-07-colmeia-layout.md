---
autor: agente:claude-opus-5-5
data: 2026-10-07
fontes: [tse-eleitorado-local-votacao-2026]
status: rascunho
---

# Layout da colmeia

Encaixar direto cada zona no hexágono livre mais próximo do centroide distorce demais: o Sudeste vira
uma mancha e o Norte fica esparso. Relaxar todas as zonas juntas (Dorling) mistura UFs vizinhas.
O que funcionou (`pipeline/colmeia.py`): primeiro um cartograma de Dorling das UFs (círculo com área
∝ nº de zonas), depois as zonas reescaladas e relaxadas dentro do círculo da própria UF, e só então o
encaixe no hexágono livre mais próximo, do centro da UF para fora.
