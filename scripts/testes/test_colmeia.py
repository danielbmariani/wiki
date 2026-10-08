import json

from colmeia import anel, layout_hexagonal
from comum import DADOS


def test_anel_tem_6k_hexagonos():
    assert len(anel(0, 0, 3)) == 18
    assert len(set(anel(0, 0, 3))) == 18


def quadrado(codarea, lon0, lat0, lado):
    anel = [[lon0, lat0], [lon0 + lado, lat0], [lon0 + lado, lat0 + lado], [lon0, lat0 + lado], [lon0, lat0]]
    return {"properties": {"codarea": codarea}, "geometry": {"type": "Polygon", "coordinates": [anel]}}


def test_layout_sem_sobreposicao_e_dentro_do_territorio():
    malha = {"features": [quadrado("35", -48, -25, 3), quadrado("13", -62, -5, 4)]}
    centroides = {f"SP-{i:03d}": (-23.5, -46.6) for i in range(1, 40)}
    centroides["AM-001"] = (-3.1, -60.0)
    r = layout_hexagonal(centroides, malha, tamanho=0.2)
    pos = r["zonas"]
    assert len({tuple(p) for p in pos.values()}) == len(centroides)
    assert set(r["ufs"]) == {"SP", "AM"}


def test_colmeia_gerada_cobre_todas_as_zonas_do_brasil():
    zonas = json.loads((DADOS / "celulas.json").read_text())["zonas"]
    pos = json.loads((DADOS / "colmeia.json").read_text())["zonas"]
    assert set(pos) == {z for z in zonas if not z.startswith("ZZ")}
    assert len({tuple(p) for p in pos.values()}) == len(pos)
