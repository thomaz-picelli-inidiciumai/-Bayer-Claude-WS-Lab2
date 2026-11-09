#!/usr/bin/env bash
# Inicia o servidor MCP do BayViva usando o Python do venv do projeto.
# Chamado pelo .mcp.json; em stdio, stdout é o canal do protocolo: não imprima nada aqui.
cd "$(dirname "$0")/.." || exit 1

if [ -x .venv/bin/python ]; then
  exec .venv/bin/python mcp_server/server.py
elif [ -x .venv/Scripts/python.exe ]; then
  exec .venv/Scripts/python.exe mcp_server/server.py
else
  exec python3 mcp_server/server.py
fi
