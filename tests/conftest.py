import shutil
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "db"))

import seed  # noqa: E402


@pytest.fixture(scope="session")
def banco_modelo(tmp_path_factory):
    """Banco com a semente fixa, criado uma vez por sessão (criar o seed leva segundos)."""
    modelo = tmp_path_factory.mktemp("modelo") / "modelo.duckdb"
    seed.criar(modelo)
    return modelo


@pytest.fixture()
def client(tmp_path, monkeypatch, banco_modelo):
    """Cliente de teste com uma cópia do banco sintético (semente fixa) só para este teste."""
    banco = tmp_path / "teste.duckdb"
    shutil.copyfile(banco_modelo, banco)
    monkeypatch.setenv("BAYVIVA_DB", str(banco))
    # Relógio fixo: quarta-feira 04/11/2026 08:00, o mesmo dia de referência do seed.
    monkeypatch.setenv("BAYVIVA_AGORA", "2026-11-04T08:00")
    from app.main import app

    return TestClient(app)


@pytest.fixture()
def banco(client):
    """Função que consulta o banco temporário do teste: banco("SELECT ... WHERE x = ?", [1])."""
    from app.db import conexao

    def consultar(sql, params=()):
        with conexao(somente_leitura=True) as con:
            return con.execute(sql, list(params)).fetchall()

    return consultar
