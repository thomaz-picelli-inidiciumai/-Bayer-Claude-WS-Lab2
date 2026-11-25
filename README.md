# crm-pharma-base (BayViva)

Repositório inicial do workshop Claude Code. CRM fictício, dados 100% sintéticos.

## Começar (um comando só)
```bash
bash iniciar.sh
```
Cria o ambiente Python, instala as dependências, cria o banco se faltar, escolhe prefixo e porta que combinam entre si, sobe o app e **confere** se o login, o redirecionamento e o CSS respondem no endereço certo. Por padrão roda no ambiente do workshop (atrás do proxy da VM): abra `https://<seu-host>/proxy/8000/login`.

| Comando | Para que serve |
|---|---|
| `bash iniciar.sh` | ambiente do workshop (proxy da VM, `/proxy/8000`) |
| `bash iniciar.sh local` | no seu computador, sem proxy (`http://127.0.0.1:8000/login`) |
| `PORTA=8001 bash iniciar.sh` | outra porta, com banco próprio e prefixo `/proxy/8001` |
| `bash iniciar.sh --so-verificar` | sobe, confere e encerra (útil para testar o ambiente) |

Se a porta estiver em uso, o script avisa e sugere outra. Se a conferência falhar, ele mostra o final do log (`/tmp/bayviva-<porta>.log`). O script não mexe no `.mcp.json` nem em `mcp_server/`.

## Começar (passo a passo, sem o script)
```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt   # Windows; Linux/Mac: .venv/bin/pip
python db/seed.py
uvicorn app.main:app --reload
```
Abra http://127.0.0.1:8000 e clique em **Entrar**.

Atrás do proxy da VM (`https://<seu-host>/proxy/8000/login`):
```bash
BAYVIVA_ROOT_PATH=/proxy/8000 uvicorn app.main:app --port 8000 --proxy-headers --forwarded-allow-ips='*'
```

## O que já funciona
Login, barra superior, home, contas (50 médicos de Cardiologia) com ficha.

## O que será construído nos labs
Registrar visita, painel de médicos a visitar e agenda. Specs em `docs/specs/`.

## Ferramentas para trabalhar com o Claude Code
- **MCP `bayviva`:** consulta somente leitura ao banco (`.mcp.json`). Dentro do Claude Code, `/mcp` mostra se está conectado.
- **Skills:** `/checar-spec`, `/spec-para-testes` e `/verificar-gravacao`.
- O fluxo recomendado está no `CLAUDE.md`.

## Testes
`pytest`

## Tags de retomada
`lab0-inicio`, `lab1-pronto`, `lab2-inicio`, `lab2-solucao`, `lab3-inicio`.
