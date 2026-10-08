"""Layout da colmeia: cada zona vira um hexágono do mesmo tamanho, no formato do Brasil.

Hexágonos "pointy-top" em coordenadas axiais (q, r). Centro em unidades de hexágono:
    x = sqrt(3) * (q + r / 2)
    y = 1.5 * r
O contorno das UFs (malha do IBGE) é projetado nas mesmas unidades.
"""

import math

SQRT3 = math.sqrt(3)
VIZINHOS = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]
PENALIDADE_OUTRA_UF = 60.0

IBGE_UF = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
    "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL",
    "28": "SE", "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP", "41": "PR",
    "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF",
}


def projetar(lat, lon, s):
    return lon * math.cos(math.radians(-15)) / s, -lat / s


def para_axial(x, y):
    q = SQRT3 / 3 * x - y / 3
    r = 2 / 3 * y
    cy = -q - r
    rx, ry, rz = round(q), round(cy), round(r)
    dx, dy, dz = abs(rx - q), abs(ry - cy), abs(rz - r)
    if dx > dy and dx > dz:
        rx = -ry - rz
    elif dy <= dz:
        rz = -rx - ry
    return rx, rz


def centro(q, r):
    return SQRT3 * (q + r / 2), 1.5 * r


def anel(q, r, k):
    if k == 0:
        return [(q, r)]
    dq, dr = VIZINHOS[4]
    hq, hr = q + dq * k, r + dr * k
    saida = []
    for i in range(6):
        for _ in range(k):
            saida.append((hq, hr))
            hq, hr = hq + VIZINHOS[i][0], hr + VIZINHOS[i][1]
    return saida


def dentro(x, y, anel_):
    d = False
    n = len(anel_)
    for i in range(n):
        x1, y1 = anel_[i]
        x2, y2 = anel_[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            d = not d
    return d


def poligonos(geojson, s):
    """{UF: [anel projetado, ...]} a partir da malha de UFs do IBGE."""
    saida = {}
    for f in geojson["features"]:
        uf = IBGE_UF[str(f["properties"]["codarea"])]
        g = f["geometry"]
        partes = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        saida[uf] = [[projetar(lat, lon, s) for lon, lat in p[0]] for p in partes]
    return saida


def mapa_de_hexagonos(polis):
    """{(q, r): UF} para todo hexágono cujo centro cai dentro de alguma UF."""
    mapa = {}
    for uf, aneis in polis.items():
        for a in aneis:
            xs, ys = [p[0] for p in a], [p[1] for p in a]
            x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
            for r in range(int(y0 / 1.5) - 1, int(y1 / 1.5) + 2):
                q_ini = int(x0 / SQRT3 - r / 2) - 1
                q_fim = int(x1 / SQRT3 - r / 2) + 2
                for q in range(q_ini, q_fim):
                    x, y = centro(q, r)
                    if x0 <= x <= x1 and y0 <= y <= y1 and dentro(x, y, a):
                        mapa[(q, r)] = uf
    return mapa


def melhor_hexagono(x, y, uf, livres):
    """Hexágono livre de menor custo: distância + penalidade se for de outra UF."""
    q0, r0 = para_axial(x, y)
    melhor, custo_melhor, k = None, math.inf, 0
    while k * 1.5 - 1 < custo_melhor and k < 400:
        for h in anel(q0, r0, k):
            dono = livres.get(h)
            if dono is None:
                continue
            custo = math.dist(centro(*h), (x, y)) + (0 if dono == uf else PENALIDADE_OUTRA_UF)
            if custo < custo_melhor:
                melhor, custo_melhor = h, custo
        k += 1
    return melhor


def caminho_svg(aneis):
    return "".join("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in a) + "Z" for a in aneis)


def layout_hexagonal(centroides, malha_ufs, tamanho=0.14):
    """centroides: {zona_id: (lat, lon)}; malha_ufs: GeoJSON das UFs (IBGE).

    As zonas mais isoladas escolhem primeiro e ficam no lugar certo. As das regiões densas
    ocupam os hexágonos livres mais próximos, de preferência dentro da própria UF e sempre
    dentro do território.
    """
    polis = poligonos(malha_ufs, tamanho)
    livres = mapa_de_hexagonos(polis)
    pontos = {z: projetar(lat, lon, tamanho) for z, (lat, lon) in centroides.items()}

    grade = {}
    for z, (x, y) in pontos.items():
        grade.setdefault((int(x // 8), int(y // 8)), []).append(z)

    def densidade(z):
        gx, gy = int(pontos[z][0] // 8), int(pontos[z][1] // 8)
        return sum(len(grade.get((gx + dx, gy + dy), ())) for dx in (-1, 0, 1) for dy in (-1, 0, 1))

    posicoes = {}
    for z in sorted(pontos, key=lambda z: (densidade(z), z)):
        h = melhor_hexagono(*pontos[z], z[:2], livres)
        del livres[h]
        posicoes[z] = list(h)
    return {
        "zonas": posicoes,
        "ufs": {uf: caminho_svg(aneis) for uf, aneis in sorted(polis.items())},
    }
