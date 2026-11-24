# Contrato de tokens e boas práticas

A ideia central: **as telas nunca decidem aparência, só consomem tokens.** Quem decide é o `:root`. Assim, qualquer visual (iOS, terminal, marca) é só outro conjunto de valores.

## 1. Camadas de token
1. **Primitivos** (opcional, para paletas grandes): `--cinza-50 … --cinza-900`, `--marca-500`. Nunca usados direto nas telas.
2. **Semânticos** (o que as telas usam): `--surface`, `--text`, `--brand`... Descrevem o papel, não a cor. `--brand` e não `--laranja`; `--danger` e não `--vermelho`. Um tema que troca laranja por verde não pode deixar o nome mentindo.
3. **De componente** (só quando precisa): `--btn-radius`, `--card-shadow`, que por padrão apontam para os semânticos.

## 2. Contrato mínimo (o que o `:root` deve ter)
Os nomes atuais do BayViva (`--brand`, `--bg`, `--card`, `--border`, `--text`...) são mantidos para não quebrar nada. Acrescente os que faltarem.

| Grupo | Tokens |
|---|---|
| Fundos | `--bg` (página), `--card` (superfície elevada), `--surface-alt` (cabeçalho de tabela/dia), `--surface-input`, `--overlay` (fundo de pop-up) |
| Texto | `--text`, `--text-weak`, `--text-muted`, `--text-on-brand`, `--text-link` |
| Bordas | `--border`, `--border-strong` |
| Marca | `--brand`, `--brand-hover`, `--brand-dark`, `--brand-tint`, `--brand-tint-border` |
| Estados | `--success`, `--success-tint`, `--success-text`, `--danger`, `--danger-tint`, `--danger-text`, `--warn`, `--warn-tint`, `--warn-text`, `--info` |
| Foco | `--focus`, `--focus-ring` (a sombra/anel completo) |
| Categorias (ícones de objeto, agenda) | `--cat-conta`, `--cat-visita`, `--cat-insight`, `--cat-painel`, `--cat-agenda`, cada uma com par de texto se o fundo for claro |
| Tipografia | `--font-body`, `--font-heading`, `--font-mono`, `--fs-xs`, `--fs-sm`, `--fs-base`, `--fs-md`, `--fs-lg`, `--fs-xl`, `--fs-2xl`, `--fw-regular`, `--fw-medium`, `--fw-bold`, `--lh-base`, `--tracking-caps` |
| Forma | `--radius-sm`, `--radius`, `--radius-lg`, `--radius-pill` |
| Profundidade | `--shadow-1` (cartão), `--shadow-2` (menu/popover), `--shadow-3` (modal/toast), `--blur` (vidro; `0` se não usar) |
| Densidade | `--control-h` (altura de botão/campo), `--control-h-sm`, `--control-h-lg`, `--pad` (espaçamento base), `--gap` |
| Movimento | `--dur-fast`, `--dur`, `--ease` (zere as durações em `prefers-reduced-motion`) |
| Casca | `--header-bg`, `--nav-bg`, `--nav-accent-w` (espessura da linha ativa), `--logo-color` |
| Nativo | `color-scheme: light` (ou `dark`) no `:root` |

Escala de espaçamento: use múltiplos de uma base (`--pad`) em vez de px soltos; densidade vira trocar um número.

## 3. Boas práticas que dão liberdade ao usuário
- **Cor nunca fica literal.** Nem `#fff` (vira `--card`/`--surface-input`/`--text-on-brand` conforme o papel), nem sombra com cor embutida (use `color-mix(in srgb, var(--text) 12%, transparent)` ou um token `--shadow-color`).
- **Estados derivam da marca, não são fixos.** Hover = `--brand-hover`; fundo suave = `--brand-tint`. Se o usuário trocar a marca, tudo acompanha. Para gerar tints e hovers a partir de um único hex, use `color-mix(in srgb, var(--brand) 12%, var(--card))` e `color-mix(in srgb, var(--brand) 85%, black)`.
- **Estado nunca depende só de cor.** Sucesso/erro/aviso têm ícone ou texto (já existem ✓ e ⚠). Em temas monocromáticos (terminal verde), é isso que mantém os estados distinguíveis: use prefixos de texto (`[OK]`, `[ERRO]`) via `::before`.
- **Contraste mínimo WCAG AA:** 4.5:1 texto normal, 3:1 texto grande (≥18px ou 14px negrito), 3:1 bordas de campo, ícones e anel de foco contra o fundo. Teste cada par, em cada tema.
- **Foco sempre visível** e com contraste, em todos os temas. Não remova `outline` sem substituto.
- **Tipografia:** pilha de fontes do sistema (`system-ui, -apple-system, "Segoe UI", Roboto, sans-serif`); arquivo local em `app/static/fonts/` se o usuário fornecer, com `font-display: swap` e fallback. Tamanho base ≥ 14px no celular (evita zoom automático do iOS em campos: `font-size: 16px` nos `input`).
- **Alvos de toque ≥ 44px** em telas estreitas (já existe regra para botões; mantenha ao mudar `--control-h`).
- **Tema escuro de verdade:** não é inverter. Fundos em cinza muito escuro (não `#000` puro, exceto em tema "terminal" por escolha), superfícies elevadas mais claras que o fundo, cores de marca e de estado **dessaturadas/clareadas**, sombras trocadas por borda ou brilho sutil. Declare `color-scheme: dark`.
- **Dois mecanismos de tema:** automático por `@media (prefers-color-scheme: dark)` e manual por `:root[data-tema="..."]`. O CSS dos componentes é o mesmo; só os tokens mudam.
- **Forma e densidade são tokens, não regras.** Trocar de canto reto para pílula é mudar `--radius*`; de compacto para arejado, `--control-h` e `--pad`.
- **Logo como `currentColor`** e dimensionado por token; versões claro/escuro do arquivo do usuário só se ele fornecer as duas.
- **Impressão:** `@media print` com fundo branco e texto preto, independentemente do tema.
- **Movimento opcional:** respeite `prefers-reduced-motion` (já existe).
- **Sem `!important`** para vencer tema; se precisar, a especificidade está errada.
- **Documente o que cada token significa** em `docs/specs/design-system.md`; é o que permite a próxima pessoa (ou a próxima execução da skill) trocar o visual sem reler o CSS inteiro.

## 4. Checagem de contraste (rodar na verificação)
Salve no scratchpad e rode com `python -I`, ajustando a lista `PARES` (nome, texto, fundo) com os valores finais dos tokens, para cada tema:

```python
def lum(h):
    h = h.lstrip("#"); r, g, b = (int(h[i:i+2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)

def razao(a, b):
    x, y = sorted((lum(a), lum(b)), reverse=True)
    return (x + 0.05) / (y + 0.05)

PARES = [  # (nome, texto, fundo, mínimo)
    ("texto/página", "#1f1e1d", "#f5f4ee", 4.5),
    ("texto/cartão", "#1f1e1d", "#ffffff", 4.5),
    ("texto fraco/cartão", "#4a4843", "#ffffff", 4.5),
    ("texto suave/cartão", "#7a776d", "#ffffff", 4.5),
    ("botão marca", "#ffffff", "#d97757", 4.5),
    ("link/cartão", "#d97757", "#ffffff", 4.5),
    ("foco/cartão", "#1b6ec2", "#ffffff", 3.0),
    ("borda campo/cartão", "#cfcdc0", "#ffffff", 3.0),
]
for nome, t, f, minimo in PARES:
    r = razao(t, f)
    print(f"{'OK ' if r >= minimo else 'FALHA'} {r:5.2f}:1 (mín {minimo})  {nome}")
```

Atenção: tokens com `color-mix()`/transparência precisam ser resolvidos para o hex efetivo antes de entrar na lista. Os valores acima são os do tema atual, só como exemplo do formato; substitua pelos finais. (Nota: no visual atual, `--text-muted` sobre branco e `--brand` como texto/botão com `#fff` ficam abaixo de 4.5:1; é exatamente o tipo de achado que a verificação deve apontar.)
