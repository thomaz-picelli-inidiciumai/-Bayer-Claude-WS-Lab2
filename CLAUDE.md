# BayViva (CRM fictício para o workshop de Claude Code)

CRM simplificado para representantes da indústria farmacêutica. Tudo é fictício e sintético: nenhum dado real da Bayer entra neste repositório.

## Stack
- Python 3.11+, FastAPI, templates Jinja2 (sem build de frontend), DuckDB local.

## Comandos
- Instalar: `python -m venv .venv` e `.venv/bin/pip install -r requirements.txt` (Linux) ou `.venv/Scripts/pip ...` (Windows)
- Criar o banco: `python db/seed.py` (gera `db/bayviva.duckdb`, semente fixa; rodar de novo zera os dados)
- Rodar o app: `uvicorn app.main:app --reload` e abrir http://127.0.0.1:8000
- Rodar atrás do proxy da VM (URL `https://<host-do-participante>/proxy/8000/login`): `BAYVIVA_ROOT_PATH=/proxy/8000 uvicorn app.main:app --port 8000 --proxy-headers --forwarded-allow-ips='*'`. Na porta 8001 use `/proxy/8001` e outro banco em `BAYVIVA_DB`.
- Testes: `pytest`

## Estrutura
- `app/main.py` rotas; `app/db.py` conexão DuckDB; `app/templates/` telas; `app/static/` CSS
- `db/schema.sql` e `db/seed.py` schema e dados sintéticos
- `docs/specs/` specs: `00-visao-geral.md`, `TEMPLATE.md`, `lab1-specs/`, `lab2-specs/`
- `tests/` testes pytest (banco temporário por teste, via fixture `client`)
- `mcp_server/` servidor MCP somente leitura do banco (ligado por `.mcp.json`)
- `.claude/skills/` skills do projeto

## Como trabalhar neste repositório
Siga esta ordem para qualquer tela nova:
1. **Spec primeiro.** Toda tela nasce de uma spec em `docs/specs/`. Sem spec, peça-a; não invente comportamento.
2. **Confira a spec** com `/checar-spec <caminho>`. Se faltar algo, responda as perguntas e complete a spec antes de codar.
3. **Plano antes do código.** Use o plan mode, discuta o plano e só então implemente.
4. **Testes a partir dos critérios.** `/spec-para-testes <caminho>` gera um teste por critério de aceite. Eles devem falhar antes e passar depois.
5. **Implemente em passos pequenos**, rodando `pytest` a cada passo.
6. **Comprove a gravação no banco** com `/verificar-gravacao`. Mensagem de sucesso na tela não é prova.

## Ferramentas do projeto
- **Servidor MCP `bayviva`** (somente leitura): `listar_tabelas`, `descrever_tabela`, `consultar` (um SELECT, até 500 linhas). Serve para inspecionar o banco real do app. Ele não grava: as gravações são feitas pelo app. Confira com `/mcp`.
- **Skills:** `/checar-spec`, `/spec-para-testes`, `/verificar-gravacao`.

## Definição de pronto
Uma tela só está pronta quando:
- todos os critérios de aceite da spec têm teste e `pytest` passa;
- os critérios que não dá para testar por HTTP foram verificados à mão e anotados;
- `/verificar-gravacao` comprovou no banco o que a spec manda gravar;
- nada foi implementado fora do escopo da spec.

## Convenções
- Links e CSS nos templates usam `{{ rota('nome_da_rota', ...) }}` (caminho com prefixo do proxy, sem host); nunca `href="/..."` fixo.
- A home gera os ícones a partir de `ATALHOS` em `app/main.py`. Cada ícone aponta sozinho para a rota real quando existe uma função com o nome indicado ali (`visitas_nova`, `painel`, `agenda`); para uma tela nova, acrescente uma linha em `ATALHOS`.
- Textos de interface em português do Brasil.
- Acesso a dados via `app.db.conexao()`; SQL sempre parametrizado (`?`), nunca f-string com entrada do usuário.
- DuckDB aceita um único processo de escrita: abrir conexão curta por requisição e fechá-la ao terminar.
- Nunca abra uma conexão `conexao(...)` dentro de outra no mesmo processo: o DuckDB recusa ("different configuration"). Termine o bloco `with` de escrita antes de renderizar a tela, que abre uma conexão de leitura.
- Toda funcionalidade nova vem com teste. Rode `pytest` antes de commitar.
- Commits pequenos e frequentes, mensagem no imperativo.

## O que não fazer
- Não commitar `db/*.duckdb`, `.env` ou segredos.
- Não usar dados reais; e-mails em `@example.com`, telefones com DDD 00.
- Não alterar `db/seed.py` sem manter a semente fixa (todos precisam ver os mesmos números).
- Não implementar fora do escopo da spec.
- Não tentar gravar no banco pelo MCP: ele é somente leitura de propósito.
