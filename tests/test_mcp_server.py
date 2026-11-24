"""Testes do servidor MCP: leitura funciona, qualquer outra coisa é recusada."""

import duckdb
import pytest

import seed
from mcp.server.mcpserver.exceptions import ToolError
from mcp_server import server


@pytest.fixture(scope="module")
def _banco_semeado(tmp_path_factory):
    # Todos os testes aqui só leem (ou provam que a escrita é recusada): um banco basta.
    caminho = tmp_path_factory.mktemp("mcp") / "mcp.duckdb"
    seed.criar(caminho)
    return caminho


@pytest.fixture()
def banco(_banco_semeado, monkeypatch):
    monkeypatch.setenv("BAYVIVA_DB", str(_banco_semeado))
    return _banco_semeado


def test_listar_tabelas(banco):
    tabelas = {t["tabela"]: t["linhas"] for t in server.listar_tabelas()}
    assert set(tabelas) == {"usuarios", "representantes", "medicos", "visitas"}
    assert tabelas["medicos"] == 50
    assert tabelas["visitas"] > 0


def test_descrever_tabela(banco):
    colunas = {c["coluna"] for c in server.descrever_tabela("visitas")}
    assert {"medico_id", "data_hora", "status", "notas"} <= colunas


def test_descrever_tabela_inexistente(banco):
    with pytest.raises(ToolError, match="não existe"):
        server.descrever_tabela("nao_existe")


def test_consultar_select(banco):
    r = server.consultar("SELECT id_bayviva, nome FROM medicos ORDER BY id LIMIT 3")
    assert r["colunas"] == ["id_bayviva", "nome"]
    assert len(r["linhas"]) == 3
    assert r["linhas"][0][0] == "BV-0001"
    assert r["truncado"] is False


def test_consultar_with_cte_e_datas_serializaveis(banco):
    r = server.consultar("WITH v AS (SELECT data_hora FROM visitas) SELECT max(data_hora) FROM v")
    assert isinstance(r["linhas"][0][0], str)


def test_consultar_respeita_limite_e_marca_truncado(banco):
    r = server.consultar("SELECT * FROM visitas", limite=5)
    assert len(r["linhas"]) == 5
    assert r["truncado"] is True


def test_consultar_limite_maximo(banco):
    r = server.consultar("SELECT * FROM visitas", limite=10**6)
    assert len(r["linhas"]) <= server.LIMITE_MAXIMO


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO visitas VALUES (999999, 1, 1, now(), 'realizada', 'x')",
        "UPDATE medicos SET nome = 'x'",
        "DELETE FROM visitas",
        "DROP TABLE visitas",
        "CREATE TABLE t (a INT)",
        "COPY visitas TO 'saida.csv'",
    ],
)
def test_escrita_e_ddl_sao_recusados(banco, sql):
    with pytest.raises(ToolError):
        server.consultar(sql)


def test_mais_de_um_statement_e_recusado(banco):
    with pytest.raises(ToolError, match="exatamente um"):
        server.consultar("SELECT 1; DROP TABLE visitas")


def test_leitura_de_arquivo_do_disco_e_recusada(banco, tmp_path):
    arquivo = tmp_path / "segredo.csv"
    arquivo.write_text("a\n1\n", encoding="utf-8")
    with pytest.raises(ToolError):
        server.consultar(f"SELECT * FROM read_csv('{arquivo.as_posix()}')")


def test_banco_nao_foi_alterado_pelas_tentativas(banco):
    for sql in ("DELETE FROM visitas", "DROP TABLE medicos"):
        with pytest.raises(ToolError):
            server.consultar(sql)
    con = duckdb.connect(str(banco), read_only=True)
    try:
        assert con.execute("SELECT count(*) FROM medicos").fetchone()[0] == 50
    finally:
        con.close()


def test_banco_ausente_da_mensagem_clara(tmp_path, monkeypatch):
    monkeypatch.setenv("BAYVIVA_DB", str(tmp_path / "nao_existe.duckdb"))
    with pytest.raises(ToolError, match="seed.py"):
        server.listar_tabelas()


def test_servidor_via_protocolo_stdio(banco):
    """Sobe o servidor como o Claude Code faz e confere ferramentas, consulta e mensagem de erro."""
    import asyncio
    import os
    import sys
    from pathlib import Path

    from mcp import Client, StdioServerParameters

    raiz = Path(__file__).resolve().parent.parent
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(raiz / "mcp_server" / "server.py")],
        cwd=str(raiz),
        env={**os.environ, "BAYVIVA_DB": str(banco)},
    )

    async def fluxo():
        async with Client(params) as c:
            ferramentas = {t.name for t in (await c.list_tools()).tools}
            ok = await c.call_tool("consultar", {"sql": "SELECT count(*) AS n FROM medicos"})
            erro = await c.call_tool("consultar", {"sql": "DELETE FROM visitas"})
            return ferramentas, ok, erro

    ferramentas, ok, erro = asyncio.run(fluxo())
    assert ferramentas == {"listar_tabelas", "descrever_tabela", "consultar"}
    assert not ok.is_error and "50" in ok.content[0].text
    assert erro.is_error
    assert "Somente consultas SELECT" in erro.content[0].text  # o modelo vê o motivo
