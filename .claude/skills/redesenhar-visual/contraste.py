"""Checagem de contraste WCAG AA lendo os tokens direto do :root de um CSS.

Uso (um comando só):  python -I .claude/skills/redesenhar-visual/contraste.py app/static/style.css
Sai com código 1 se algum par falhar. Pares cujos tokens não existem no CSS são ignorados (e listados no fim).
Tokens com transparência (#rrggbbaa), color-mix() ou var() encadeado: resolva para hex antes, ou eles são ignorados.
Ajuste PARES ao contrato do tema: (nome, token do texto, token do fundo, razão mínima).
"""
import re
import sys
from pathlib import Path

PARES = [
    ("text sobre bg", "--text", "--bg", 4.5),
    ("text sobre card", "--text", "--card", 4.5),
    ("text sobre surface-alt", "--text", "--surface-alt", 4.5),
    ("text sobre surface-input", "--text", "--surface-input", 4.5),
    ("text sobre brand-tint", "--text", "--brand-tint", 4.5),
    ("text-weak sobre bg", "--text-weak", "--bg", 4.5),
    ("text-weak sobre card", "--text-weak", "--card", 4.5),
    ("text-muted sobre bg", "--text-muted", "--bg", 4.5),
    ("text-muted sobre card", "--text-muted", "--card", 4.5),
    ("text-muted sobre surface-alt", "--text-muted", "--surface-alt", 4.5),
    ("text-link sobre bg", "--text-link", "--bg", 4.5),
    ("text-link sobre card", "--text-link", "--card", 4.5),
    ("brand sobre bg", "--brand", "--bg", 4.5),
    ("brand sobre card", "--brand", "--card", 4.5),
    ("brand sobre surface-alt", "--brand", "--surface-alt", 4.5),
    ("success-text sobre success-tint", "--success-text", "--success-tint", 4.5),
    ("danger-text sobre danger-tint", "--danger-text", "--danger-tint", 4.5),
    ("danger sobre card", "--danger", "--card", 4.5),
    ("warn-text sobre warn-tint", "--warn-text", "--warn-tint", 4.5),
    ("hero-text sobre hero-bg", "--hero-text", "--hero-bg", 4.5),
    ("on-brand sobre brand", "--text-on-brand", "--brand", 4.5),
    ("on-brand sobre brand-hover", "--text-on-brand", "--brand-hover", 4.5),
    ("on-brand sobre success", "--text-on-brand", "--success", 4.5),
    ("on-brand sobre danger", "--text-on-brand", "--danger", 4.5),
    ("brand-dark sobre brand-tint (tag)", "--brand-dark", "--brand-tint", 4.5),
    ("on-cat sobre cat-conta", "--text-on-cat", "--cat-conta", 4.5),
    ("on-cat sobre cat-visita", "--text-on-cat", "--cat-visita", 4.5),
    ("on-cat sobre cat-insight", "--text-on-cat", "--cat-insight", 4.5),
    ("on-cat sobre cat-painel", "--text-on-cat", "--cat-painel", 4.5),
    ("on-cat sobre cat-agenda", "--text-on-cat", "--cat-agenda", 4.5),
    # componentes (bordas de campo, anel de foco): mínimo 3:1
    ("foco sobre bg", "--focus", "--bg", 3.0),
    ("foco sobre card", "--focus", "--card", 3.0),
    ("border-strong sobre surface-input (campo)", "--border-strong", "--surface-input", 3.0),
    ("border-strong sobre card", "--border-strong", "--card", 3.0),
]


def luminancia(hexa: str) -> float:
    h = hexa.lstrip("#")[:6]
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def razao(a: str, b: str) -> float:
    x, y = sorted((luminancia(a), luminancia(b)), reverse=True)
    return (x + 0.05) / (y + 0.05)


def tokens_da_raiz(css: str) -> dict[str, str]:
    """Tokens do primeiro `:root {}` (o do tema; o de @media print vem depois)."""
    m = re.search(r":root\s*\{", css)
    profundidade, i = 1, m.end()
    while profundidade:
        profundidade += {"{": 1, "}": -1}.get(css[i], 0)
        i += 1
    bloco = css[m.end():i - 1]
    return {k: v.strip() for k, v in re.findall(r"(--[\w-]+):\s*([^;]+);", bloco)}


def main() -> int:
    css = Path(sys.argv[1]).read_text(encoding="utf-8")
    t = tokens_da_raiz(css)
    hexa = lambda token: t.get(token) if re.fullmatch(r"#[0-9a-fA-F]{6}([0-9a-fA-F]{2})?", t.get(token, "")) else None
    falhas, ignorados, total = 0, [], 0
    for nome, tx, fd, minimo in PARES:
        a, b = hexa(tx), hexa(fd)
        if not a or not b:
            ignorados.append(nome)
            continue
        total += 1
        r = razao(a, b)
        ok = r >= minimo
        falhas += not ok
        print(f"{'OK   ' if ok else 'FALHA'} {r:5.2f}:1 (min {minimo})  {nome}")
    print(f"\n{total} pares, {falhas} falha(s)")
    if ignorados:
        print(f"ignorados (token ausente ou nao-hex): {', '.join(ignorados)}")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
