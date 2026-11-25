# Verificação, guarda de testes e auditoria de UX

Leia na Fase 4 (auditoria) e na Fase 5 (verificação). Tudo aqui roda sem navegador.

## 1. Contraste (obrigatório)
Um comando só, lendo o CSS final:

`python -I .claude/skills/redesenhar-visual/contraste.py app/static/style.css`

Ele lê o primeiro `:root`, checa os pares de [contraste.py](contraste.py) (4.5:1 texto, 3:1 bordas de campo e foco) e sai com código 1 se algum falhar. Corrija o token (clareie a borda, escureça o texto sobre a marca) e rode de novo; anexe o resultado final à spec. Acrescente pares ao `PARES` se o tema criar tokens novos. Valores com `color-mix()` ou transparência precisam virar hex antes.

## 2. Guarda de testes (crie `tests/test_design_system.py`)
Protege o que antes só a pessoa conferia. Lê CSS e templates, não sobe o app, roda em milissegundos. Gere a partir deste esqueleto e **escreva o teste antes do CSS** (ele deve falhar e depois passar):

```python
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CSS = (RAIZ / "app" / "static" / "style.css").read_text(encoding="utf-8")
TEMPLATES = sorted((RAIZ / "app" / "templates").glob("*.html"))
JS = (RAIZ / "app" / "static" / "app.js").read_text(encoding="utf-8")


def _blocos_raiz(css):  # (início, fim) de cada :root { ... }, inclusive o de @media print
    out = []
    for m in re.finditer(r":root\s*\{", css):
        prof, i = 1, m.end()
        while prof and i < len(css):
            prof += {"{": 1, "}": -1}.get(css[i], 0)
            i += 1
        out.append((m.start(), i))
    return out


def _fora_da_raiz(css):
    texto, ultimo = [], 0
    for ini, fim in _blocos_raiz(css):
        texto.append(css[ultimo:ini]); ultimo = fim
    texto.append(css[ultimo:])
    return "".join(texto)


def test_nenhuma_cor_literal_fora_da_raiz():
    achados = re.findall(r"#[0-9a-fA-F]{3,8}\b|rgba?\(", _fora_da_raiz(CSS))
    assert achados == [], achados[:5]


def test_templates_e_js_sem_cor_literal_nem_estilo_inline():
    for caminho in TEMPLATES:
        texto = caminho.read_text(encoding="utf-8")
        assert not re.search(r"\bstyle=|<style", texto), caminho.name
        assert not re.search(r"#[0-9a-fA-F]{6}\b", texto), caminho.name
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b|rgba?\(", JS)


def test_nenhum_texto_menor_que_12px():
    assert [n for n in re.findall(r"font-size:\s*(\d+)px", CSS) if int(n) < 12] == []
```

Some um teste por decisão da spec (marca, raio, `--glow`, rótulos de estado, preset guardado, `prefers-reduced-motion`). Teste de valor de token lê o **primeiro** `:root` (o de `@media print` vem depois).

## 3. Auditoria de UX (só camada visual, sem mudar markup)
Antes de fechar, confira no CSS e corrija o que faltar:
- campos (`input`, `select`, `textarea`) com `font-size: 16px` abaixo de 720px (o iOS dá zoom abaixo disso);
- nenhum `font-size` menor que 12px;
- fonte monoespaçada alarga e-mails, nomes e IDs: `overflow-wrap: anywhere` e `min-width: 0` em células, cartões e filhos flex/grid;
- `touch-action: manipulation` em botões, links e `summary`;
- estado pressionado (`:active`) nos botões, distinto do hover e fora dos desabilitados;
- foco visível e com contraste; alvos de toque ≥ 44px em tela estreita;
- regras de ajuste ficam no **fim** do arquivo para vencer os `:hover` de cima (sem `!important`).
O que exigir mudar markup ou comportamento (link "pular para o conteúdo", `aria-current`, `aria-describedby` nos erros, foco no resumo de erros) **não entra** no redesenho: liste como sugestão para uma spec de acessibilidade.

## 4. Conferência visual quando não dá para ver a tela
Tentar nesta ordem, parando na primeira que funcionar:
1. Navegador/automação já disponível na sessão (captura em ~1280px e ~390px).
2. Se existir uma skill ou MCP de navegador (Playwright), pergunte antes de usar: ela pode baixar binários e mexer em `.mcp.json`.
3. **Plano B, sem imagens** (um bloqueio de leitura de imagem não se contorna): prove o que dá por código (zero literais, `pytest`, contraste, as telas respondendo 200 com a rota real e o banco de teste) e **liste para o usuário** o que só o olho confere: foco por teclado, pop-ups e toast, tabela virando cartões em ~390px, cabeçalho em tela estreita, login, estado pressionado e glifos decorativos que dependem da fonte do sistema.
Diga explicitamente qual caminho foi usado. Nunca escreva "conferido visualmente" sem ter visto.

## 5. Ambiente (evita retrabalho)
- Windows: `.venv/Scripts/python`, não o Python do sistema (que não tem pytest). Linux: `.venv/bin/python`.
- Porta 8000 ocupada (`WinError 10048`): **não encerre o processo alheio.** Suba em outra porta (8001) com uma cópia do banco em `BAYVIVA_DB` e `BAYVIVA_AGORA=2026-11-04T08:00`. Pare só o que você mesmo subiu.
- Um comando por chamada (sem `&&`, `;` ou `for` encadeados): políticas de permissão recusam scripts compostos. Para checar várias rotas, escreva um script `.py` no scratchpad e rode `python -I script.py`.
- Remoção recursiva (`rm -r`) pode ser bloqueada: se for negada, não tente outro caminho para contornar; peça ao usuário para apagar ou autorizar.
