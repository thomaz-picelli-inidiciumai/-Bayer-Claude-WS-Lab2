# crm-pharma-base (BayViva)

Repositório inicial do workshop Claude Code. CRM fictício, dados 100% sintéticos.

## Começar
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

## Testes
`pytest`

## Tags de retomada
`lab0-inicio`, `lab1-pronto`, `lab2-inicio`, `lab2-solucao`, `lab3-inicio`.
