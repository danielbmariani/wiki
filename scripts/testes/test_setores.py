import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point, box

from setores import estimar, indicadores, ligar


def cenario():
    setores = gpd.GeoDataFrame(geometry=[box(0, 0, 100, 100), box(1000, 0, 1100, 100)])
    pontos = gpd.GeoDataFrame({
        "lula": [60, 40, 10], "adv": [40, 60, 90], "validos": [100, 100, 100],
        "aptos": [130, 130, 130], "abst": [20, 20, 20], "brancos": [5, 5, 5], "nulos": [5, 5, 5],
    }, geometry=[Point(50, 50), Point(150, 50), Point(1600, 50)])
    return setores, pontos


def test_faixa_mais_proxima():
    setores, pontos = cenario()
    pares, perto = ligar(setores, pontos)
    ligados = pares.groupby("s").p.apply(sorted).to_dict()
    assert ligados[0] == [0, 1]          # dentro e a 50 m: mesma faixa de 0–100 m
    assert ligados[1] == [2]             # 850 m e 500 m: só a faixa de 500–600 m
    assert perto[0] == 0


def test_estimativa_ponderada():
    setores, pontos = cenario()
    pares, _ = ligar(setores, pontos)
    t = estimar(pares, pontos, 2)
    i = indicadores(t)
    assert 50 < i.lula[0] < 60           # o local de dentro pesa mais
    assert np.isclose(i.abst[0], 100 * 20 / 130)
    fora = t.abst[0] + t.brancos[0] + t.nulos[0]
    assert np.isclose(i.espaco[0], fora / abs(t.lula[0] - t.adv[0]))


def test_sem_margem_nao_divide_por_zero():
    t = pd.DataFrame({"lula": [50.0], "adv": [50.0], "validos": [100.0], "aptos": [130.0],
                      "abst": [20.0], "brancos": [5.0], "nulos": [5.0]})
    assert np.isnan(indicadores(t).espaco[0])
