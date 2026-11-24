"""Relógio do app.

Tudo no BayViva usa o horário de America/Sao_Paulo, sem fuso nos valores
(`datetime` ingênuo), que é como `visitas.data_hora` é gravado.

Para demonstrações e testes, a variável BAYVIVA_AGORA (ISO, ex.: 2026-11-04T08:00)
fixa o "agora". Valor inválido é ignorado e vale o relógio real.
"""

from __future__ import annotations

import os
from datetime import date, datetime
from zoneinfo import ZoneInfo

FUSO = ZoneInfo("America/Sao_Paulo")


def agora() -> datetime:
    valor = os.environ.get("BAYVIVA_AGORA", "").strip()
    if valor:
        try:
            return datetime.fromisoformat(valor).replace(tzinfo=None, microsecond=0)
        except ValueError:
            pass
    return datetime.now(FUSO).replace(tzinfo=None, microsecond=0)


def hoje() -> date:
    return agora().date()
