import pytest

import comum
from checar import checar, checar_grupos, checar_quadro, dados_pessoais
from comum import carregar_celulas, ids_validos, modelo_quadro

CELULAS = carregar_celulas()
VALIDOS = ids_validos(CELULAS)


def quadro(id_="SP-001", acoes=""):
    texto = modelo_quadro(id_, CELULAS)
    return texto.replace("## Próximas ações\n", f"## Próximas ações\n\n{acoes}\n")


def erros_quadro(texto, caminho="celulas/SP/zonas/001.md"):
    return checar_quadro(caminho, texto, VALIDOS, CELULAS)


def test_modelo_passa():
    assert erros_quadro(quadro()) == []


def test_acao_com_data_e_hora_passa():
    assert erros_quadro(quadro(acoes="- **Sáb 18/10, 9h** — panfletagem na Feira da Praça X")) == []


@pytest.mark.parametrize("texto", [
    "Liga pra mim: (11) 98765-4321",
    "zap 11987654321",
    "escreve pra fulano@gmail.com",
    "CPF 123.456.789-09",
    "Rua X, CEP 01310-100",
    "fala comigo https://wa.me/5511987654321",
])
def test_dados_pessoais_bloqueados(texto):
    assert dados_pessoais(texto)


@pytest.mark.parametrize("texto", [
    "Ato no dia 25/10/2026 às 10h",
    "Material em https://www.diretorio13.com/123456789",
    "Zona 001, 2026-10-20",
    "SHA-256 `86777db621ca40d23d19a0cb9fffa561246e3ab59dbc8cc3264da2f9cb4f0215`",
])
def test_textos_comuns_passam(texto):
    assert dados_pessoais(texto) == []


def test_id_diferente_do_caminho():
    assert any("não corresponde" in e for e in erros_quadro(quadro("SP-002")))


def test_id_inexistente():
    texto = quadro().replace("id: SP-001", "id: SP-999")
    assert erros_quadro(texto, "celulas/SP/zonas/999.md")


def test_secao_faltando():
    assert erros_quadro(quadro().replace("## Notas\n", ""))


def test_html_bloqueado():
    assert any("HTML" in e for e in erros_quadro(quadro(acoes="<script>alert(1)</script>")))


def test_link_de_grupo_no_quadro_bloqueado():
    assert any("grupos" in e for e in erros_quadro(quadro(acoes="https://chat.whatsapp.com/abc")))


@pytest.mark.parametrize("link,ok", [
    ("https://chat.whatsapp.com/AbCdEf", True),
    ("https://whatsapp.com/channel/0029Va9GZPM8vd1ThwjXO91d", True),
    ("https://t.me/grupo", True),
    ("http://t.me/grupo", False),
    ("https://chat.whatsapp.com.golpe.com/x", False),
    ("https://bit.ly/abc", False),
    ("javascript:alert(1)", False),
])
def test_dominios_de_grupos(link, ok):
    texto = f"grupos:\n  - nome: Zona 1\n    link: {link}\n"
    assert (checar_grupos("_data/grupos/SP/zonas/001.yml", texto, VALIDOS) == []) is ok


def test_rotulos_e_somente_texto(tmp_path):
    destino = tmp_path / "celulas/SP/zonas/001.md"
    destino.parent.mkdir(parents=True)
    destino.write_text(quadro(), encoding="utf-8")
    r = checar(tmp_path, ["celulas/SP/zonas/001.md"], CELULAS)
    assert r["erros"] == {}
    assert r["somente_texto"] is True
    assert "zona:SP-001" in r["rotulos"] and "nivel:zona" in r["rotulos"]

    r = checar(tmp_path, ["celulas/SP/zonas/001.md", "_data/grupos/SP/zonas/001.yml"], CELULAS)
    assert r["somente_texto"] is False


def test_caminhos_ida_e_volta():
    for id_ in ["BR", "SP", "SP-71072", "SP-001"]:
        assert comum.id_do_caminho(f"celulas/{comum.caminho_relativo(id_)}.md") == id_
        assert comum.id_do_caminho(f"_data/grupos/{comum.caminho_relativo(id_)}.yml") == id_


def test_ignora_assets_binarios(tmp_path):
    (tmp_path / "avatar.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    r = checar(tmp_path, ["avatar.png"], CELULAS)
    assert r["erros"] == {}
    assert r["somente_texto"] is False


def test_quadros_do_repositorio_passam():
    if not comum.CELULAS.is_dir():
        pytest.skip("sem checkout da colmeia")
    for arq in comum.CELULAS.rglob("*.md"):
        rel = arq.relative_to(comum.COLMEIA).as_posix()
        assert erros_quadro(arq.read_text(encoding="utf-8"), rel) == [], rel


def test_grupos_do_repositorio_passam():
    if not comum.GRUPOS.is_dir():
        pytest.skip("sem checkout da colmeia")
    for arq in comum.GRUPOS.rglob("*.yml"):
        rel = arq.relative_to(comum.COLMEIA).as_posix()
        assert checar_grupos(rel, arq.read_text(encoding="utf-8"), VALIDOS) == [], rel


SETOR = "355030805000001"


def test_grupo_de_setor_passa():
    texto = "grupos:\n  - nome: Vila Setor\n    link: https://chat.whatsapp.com/AbCdEf\n"
    validos = ids_validos(CELULAS, {SETOR})
    assert checar_grupos(f"_data/grupos/SP/setores/{SETOR}.yml", texto, validos) == []


def test_setor_inexistente_ou_na_uf_errada():
    texto = "grupos: []\n"
    validos = ids_validos(CELULAS, {SETOR})
    assert checar_grupos("_data/grupos/SP/setores/355030805999999.yml", texto, validos)
    assert checar_grupos(f"_data/grupos/RJ/setores/{SETOR}.yml", texto, validos)


def test_caminho_de_setor_ida_e_volta():
    assert comum.nivel(SETOR) == "setor"
    assert comum.caminho_relativo(SETOR) == f"SP/setores/{SETOR}"
    assert comum.id_do_caminho(f"_data/grupos/SP/setores/{SETOR}.yml") == SETOR
    assert comum.nivel("995030805000001") is None
