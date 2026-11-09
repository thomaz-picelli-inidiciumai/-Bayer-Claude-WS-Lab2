"""Servidor MCP do BayViva: consultas somente leitura ao DuckDB local.

O Claude Code inicia este processo sozinho (transporte stdio, ver .mcp.json).
Cada participante consulta o próprio banco, na própria máquina.

Segurança:
- conexão read_only: nenhuma gravação é possível;
- enable_external_access desligado: o SQL não lê arquivos do disco (read_csv etc.);
- só um statement SELECT por chamada e no máximo LIMITE_MAXIMO linhas.

Atenção: em stdio, stdout é o canal do protocolo. Nunca use print() aqui.
"""

from __future__ import annotations

import sys
import time
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import duckdb
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError  # falha prevista: a mensagem chega ao modelo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.db import db_path  # noqa: E402  (mesma regra de caminho do app: BAYVIVA_DB)

LIMITE_PADRAO = 100
LIMITE_MAXIMO = 500


def _abrir() -> duckdb.DuckDBPyConnection:
    caminho = db_path()
    if not caminho.exists():
        raise ToolError(
            f"Banco não encontrado em {caminho}. Rode `python db/seed.py` primeiro."
        )
    config = {"enable_external_access": False}
    try:
        return duckdb.connect(str(caminho), read_only=True, config=config)
    except duckdb.IOException:
        # O app pode estar gravando neste instante (DuckDB aceita um escritor). Tenta de novo.
        time.sleep(0.5)
        try:
            return duckdb.connect(str(caminho), read_only=True, config=config)
        except duckdb.IOException as erro:
            raise ToolError(
                "O banco está ocupado (o app está gravando). Tente de novo em instantes."
            ) from erro


def _valor(v):
    if isinstance(v, (datetime, date)):
        return v.isoformat(sep=" ") if isinstance(v, datetime) else v.isoformat()
    if isinstance(v, Decimal):
        return float(v)
    return v


def listar_tabelas() -> list[dict]:
    con = _abrir()
    try:
        nomes = [
            r[0]
            for r in con.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'main' ORDER BY table_name"
            ).fetchall()
        ]
        # Os nomes vêm do próprio catálogo do banco, não do usuário.
        return [
            {"tabela": n, "linhas": con.execute(f'SELECT count(*) FROM "{n}"').fetchone()[0]}
            for n in nomes
        ]
    finally:
        con.close()


def descrever_tabela(nome: str) -> list[dict]:
    con = _abrir()
    try:
        cols = con.execute(
            "SELECT column_name, data_type, is_nullable FROM information_schema.columns "
            "WHERE table_schema = 'main' AND table_name = ? ORDER BY ordinal_position",
            [nome],
        ).fetchall()
    finally:
        con.close()
    if not cols:
        raise ToolError(f"Tabela '{nome}' não existe. Use listar_tabelas para ver as opções.")
    return [{"coluna": c, "tipo": t, "aceita_nulo": n == "YES"} for c, t, n in cols]


def consultar(sql: str, limite: int = LIMITE_PADRAO) -> dict:
    limite = max(1, min(limite, LIMITE_MAXIMO))
    con = _abrir()
    try:
        try:
            statements = con.extract_statements(sql)
        except duckdb.Error as erro:
            raise ToolError(f"SQL inválido: {erro}") from erro
        if len(statements) != 1:
            raise ToolError("Envie exatamente um statement SELECT por chamada.")
        if statements[0].type != duckdb.StatementType.SELECT:
            raise ToolError("Somente consultas SELECT são permitidas (banco somente leitura).")
        try:
            cur = con.execute(sql)
            linhas = cur.fetchmany(limite + 1)
        except duckdb.Error as erro:
            raise ToolError(f"Erro ao executar a consulta: {erro}") from erro
        colunas = [d[0] for d in cur.description]
    finally:
        con.close()
    truncado = len(linhas) > limite
    return {
        "colunas": colunas,
        "linhas": [[_valor(v) for v in linha] for linha in linhas[:limite]],
        "truncado": truncado,
    }


mcp = MCPServer(
    "bayviva",
    instructions=(
        "Consulta somente leitura ao banco DuckDB do BayViva (CRM fictício, dados sintéticos). "
        "Tabelas: usuarios, representantes, medicos, visitas. "
        "visitas.status é 'realizada', 'planejada' ou 'cancelada'. "
        "Comece por listar_tabelas e descrever_tabela; depois use consultar com um SELECT."
    ),
)

mcp.tool(name="listar_tabelas", description="Lista as tabelas do BayViva com a contagem de linhas.")(
    listar_tabelas
)
mcp.tool(name="descrever_tabela", description="Mostra colunas, tipos e nulidade de uma tabela.")(
    descrever_tabela
)
mcp.tool(
    name="consultar",
    description=(
        f"Executa um único SELECT somente leitura. Devolve até {LIMITE_MAXIMO} linhas "
        f"(padrão {LIMITE_PADRAO}); 'truncado' indica se havia mais."
    ),
)(consultar)


if __name__ == "__main__":
    mcp.run(transport="stdio")
