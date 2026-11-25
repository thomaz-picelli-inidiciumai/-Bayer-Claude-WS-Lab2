---
name: redesenhar-visual
description: Entrevista o usuário e troca o design system inteiro do BayViva (cores, tipografia, formas, densidade, tema claro/escuro, logo e tom visual), varrendo todas as telas e aplicando por um plano. Use quando o usuário pedir para mudar o visual, tema, identidade visual, "skin" ou marca do app (ex.: estilo iPhone/Apple, terminal preto com letras verdes, identidade de uma marca como a Bayer, modo escuro).
---

# Redesenhar visual (troca de design system)

Objetivo: o usuário descreve a aparência que quer, em qualquer direção, e o app inteiro passa a ter essa aparência, **sem mudar comportamento**. Rotas, nomes de campo, `id`, atributos `data-*`, mensagens e regras ficam como estão. Muda só a camada visual.

Arquivos de apoio (leia sob demanda, não de uma vez):
- [tokens.md](tokens.md): o contrato de tokens, as boas práticas e a checagem de contraste.
- [estilos.md](estilos.md): receitas de direções visuais (Apple/iOS, terminal, marca corporativa, escuro, etc.) para propor opções na entrevista.
- [verificacao.md](verificacao.md): contraste, guarda de testes, auditoria de UX, conferência visual sem imagens e dicas de ambiente.
- [contraste.py](contraste.py): script que lê o `:root` do CSS e checa os pares texto/fundo em AA.

## Regras de ouro
1. **Tokens primeiro, telas depois.** Toda decisão visual vive em variáveis CSS no `:root` de `app/static/style.css`. Trocar de visual = trocar tokens, mais poucos ajustes estruturais. Se uma tela exige valor fixo para ficar bonita, o token está faltando: crie-o.
2. **Nada de comportamento muda.** Não renomeie classes, `id`, `data-*`, rotas, `name` de campos nem textos que testes ou `app.js` usam. Se um ajuste estrutural exigir isso, pare e pergunte.
3. **Segue o fluxo do repositório.** Redesenho não é tela nova, mas continua sendo "spec primeiro": a entrevista termina numa spec de design em `docs/specs/design-system.md`, o usuário aprova, e só então se implementa.
4. **Plano antes do código** (plan mode ou plano escrito e aprovado), **passos pequenos**, `pytest` a cada passo, commits pequenos.
5. **Sem inventar marca.** Para identidade de uma marca real, peça ao usuário as cores (hex), a fonte e o arquivo do logo. Não reproduza logotipo de memória nem copie ativos protegidos; sem logo fornecido, use um símbolo genérico ou só o nome em texto. Sem dados reais: o repositório continua fictício.
6. **Sem dependência externa em runtime.** Nada de CDN, Google Fonts ou bibliotecas de CSS (a VM pode estar sem internet e atrás de proxy). Use pilha de fontes do sistema ou arquivos locais em `app/static/fonts/`, referenciados com `{{ rota('static', path='...') }}` / caminho relativo ao CSS.
7. **Skills e plugins de design externos são consulta, nunca decisão.** Se existir uma (ex.: de UX ou de design), use-a para propor opções ou auditar, e deixe a spec aprovada decidir; as sugestões dela costumam ignorar estas regras (CDN, dados fictícios, não mudar markup). **Não instale** plugin ou skill de terceiros sem o aval do usuário: roda código na máquina dele.
8. **Sempre reversível.** Um commit por camada. Toda decoração da casca (prefixos, glifos, rótulos de estado, animação) fica atrás de token (`content: var(--x)`), de modo que um preset só de tokens reproduza o tema por inteiro; token ausente = regra sem efeito.

## Fase 0: Diagnóstico (sempre, antes de perguntar)
Mapeie o que existe hoje, de verdade, sem confiar em lista antiga:
1. Liste `app/templates/*.html`, `app/static/*` e as rotas/`ATALHOS` em `app/main.py`. **Toda tela encontrada entra no plano**, inclusive as que forem criadas depois desta skill existir.
2. Rode e anote o que está fixo fora do `:root`:
   - cores literais: `Grep` por `#[0-9a-fA-F]{3,8}\b`, `rgb(`, `rgba(` em `app/static/style.css` fora do bloco `:root`, e em `app/templates/` e `app/static/app.js`;
   - `style=` inline e blocos `<style>` nos templates;
   - `font-family`, `font-size` em px soltos, `border-radius`, `box-shadow`, `transition`/`animation` literais;
   - SVGs com cor embutida (ex.: ícone da busca em data-URI, `_simbolo.html`).
3. Confira o ambiente (detalhes em [verificacao.md](verificacao.md), seção 5): Python do `.venv`, porta livre, e que o `pytest` passa **antes** de mexer (a linha de base).
4. Resuma ao usuário em poucas linhas: quantas telas, qual a identidade atual (cor de marca, fonte, raio, densidade) e quanto está "preso" a valores fixos.

## Fase 1: Tokenizar (só se o diagnóstico achar valores fixos)
Antes de qualquer troca de visual, deixe o CSS 100% dirigido por tokens, **sem mudar a aparência atual** (a tela deve ficar idêntica):
- Complete o contrato de [tokens.md](tokens.md) no `:root` (superfícies, texto, marca, estados, categorias, tipografia, forma, sombras, movimento, densidade).
- Substitua cada literal fora do `:root` pelo token correspondente. Mova os `style=` inline para classes.
- Cores dentro de data-URI de SVG (ícone de busca): troque por máscara CSS (`mask` + `background: currentColor`) ou por SVG inline com `currentColor`, para o ícone seguir o tema.
- Rode `pytest` e confira uma tela. Commit: "Tokenizar o CSS sem mudar o visual".
Se o `:root` já estiver completo e sem literais, pule esta fase e diga isso.

## Fase 2: Entrevista
Use `AskUserQuestion`, em rodadas de até 4 perguntas, com opções concretas e `(Recomendado)` quando houver bom padrão. Deixe a descrição livre sempre possível ("Outro"). Não pergunte o que o usuário já disse no pedido. Cubra, nesta ordem:

**Rodada 1: direção**
- *Ponto de partida:* uma referência (Apple/iOS, terminal, marca X, minimalista, corporativo clássico...) ou construir do zero a partir de adjetivos? Se o usuário já deu a referência, confirme a interpretação em uma frase em vez de perguntar.
- *Tema:* claro, escuro, ou os dois com alternância automática (`prefers-color-scheme`)?
- *Cor de marca:* hex, nome da marca ou "escolha você". Se for marca real, peça os hex oficiais e se há logo (arquivo).
- *Personalidade:* sóbria, amigável, técnica, luxuosa, lúdica, retrô.

**Rodada 2: forma e leitura**
- *Cantos:* retos (0), suaves (4-8px), arredondados (12-16px), pílula.
- *Profundidade:* plano com bordas, sombras suaves, vidro/translúcido (blur), brutalista.
- *Densidade:* compacta (muita informação), confortável, arejada. Isso muda a altura de campos e botões, e vale para o toque no celular.
- *Tipografia:* sistema (sans), serifada, monoespaçada em tudo, ou arquivo de fonte local do usuário. Tamanho base.

**Rodada 3: detalhes**
- *Logo e nome:* manter símbolo atual, trocar por arquivo do usuário, só texto, ou ícone novo gerado em SVG simples.
- *Cabeçalho e navegação:* barra superior, abas, barra lateral, barra inferior no celular (estilo iOS)?
- *Movimento:* nenhum, sutil, expressivo (respeita `prefers-reduced-motion` sempre).
- *Restrições:* acessibilidade mínima (padrão: WCAG AA), contraste alto, daltonismo, impressão, idioma dos textos de interface.

Termine a entrevista **devolvendo um resumo de decisões** (tabela curta) e pedindo confirmação. Se a escolha do usuário colidir com boa prática (ex.: verde puro sobre preto em fonte fina de 11px, contraste ok mas cansativo; ou cinza claro sobre branco), diga o risco e proponha o ajuste mais próximo da intenção, mas **a decisão é do usuário**.

## Fase 3: Spec de design
Escreva `docs/specs/design-system.md` (crie ou atualize) com: decisões da entrevista, tabela completa de tokens (claro e, se houver, escuro) com os valores finais, regras de uso (quando usar cor de marca, estados, categorias), e **critérios de aceite verificáveis**, por exemplo:
- nenhum literal de cor fora do `:root` em `style.css`, templates e `app.js`;
- todos os pares texto/fundo do contrato passam em contraste AA (o relatório da checagem anexo);
- as N telas listadas abrem sem erro e usam só tokens;
- `pytest` passa sem alterar nenhum teste.
Peça aprovação da spec antes de seguir.

## Fase 4: Plano e execução
1. **Plano** (plan mode se disponível): liste, uma linha por item, cada arquivo a tocar e o que muda. Estrutura fixa:
   1. Tokens (`:root`, e o bloco do tema alternativo se houver)
   2. Base: tipografia, `body`, links, foco, seleção, barras de rolagem
   3. Casca: cabeçalho global, navegação, `main`, logo/símbolo, favicon se existir
   4. Componentes: botões, campos, selos, avisos, toasts, pop-ups, tabelas, cartões
   5. **Uma linha por tela** encontrada na Fase 0 (home, login, contas, ficha, visita_nova, painel, agenda, em_construcao e as demais), indicando ajustes estruturais específicos
   6. Estados e responsivo: vazio, erro, desabilitado, foco, cartões em tela estreita
   7. Verificação
2. **Execute em passos pequenos**, na ordem acima, com `pytest` ao fim de cada passo. Prefira mudar token a mudar regra. Quando for preciso mexer na estrutura de um template (ex.: mover a navegação para barra lateral), altere só markup/classes, preservando `rota(...)`, `id` e `data-*`.
3. **Tema escuro:** declare os tokens em `:root` (claro) e redefina em `@media (prefers-color-scheme: dark)` e em `:root[data-tema="escuro"]`, se o usuário quiser alternância manual. Defina `color-scheme` para os controles nativos e `<meta name="theme-color">` no `base.html`.
4. **Logo/símbolo:** `_simbolo.html` deve usar `currentColor`. Se o usuário forneceu arquivo, salve em `app/static/` e referencie com `rota('static', ...)`.
5. Commits pequenos e no imperativo, um por camada (tokens, componentes, cada grupo de telas).
6. **Guarda de testes antes do CSS:** crie `tests/test_design_system.py` ([verificacao.md](verificacao.md), seção 2), veja-o falhar e só então aplique os tokens.
7. **Auditoria de UX** ao fim dos componentes ([verificacao.md](verificacao.md), seção 3): 16px nos campos no celular, texto ≥ 12px, quebra de texto longo, `touch-action`, estado `:active`. O que exigir mudar markup vira sugestão, não entra.

## Fase 5: Verificação (não encerre sem isto)
1. `pytest` passa, sem editar testes para "ficar verde". Se um teste dependia de texto/estrutura visual, explique e pergunte.
2. Re-rode o diagnóstico da Fase 0: **zero** literais de cor fora do `:root`, zero `style=` inline.
3. Contraste: rode `python -I .claude/skills/redesenhar-visual/contraste.py app/static/style.css` ([verificacao.md](verificacao.md), seção 1), para cada tema, e anexe o resultado à spec. Corrija o que ficar abaixo de AA (4.5:1 texto, 3:1 ícones/bordas de campo/foco).
4. Veja as telas: suba o app (porta livre, banco de teste, `BAYVIVA_AGORA=2026-11-04T08:00`; nunca encerre processo alheio) e siga a ordem de [verificacao.md](verificacao.md), seção 4: captura se houver navegador (perguntando antes de instalar um), senão o plano B sem imagens, listando para o usuário o que só o olho confere. Cada tela do plano deve responder 200 e usar só tokens. Diga qual caminho foi usado.
5. Entregue um relatório curto: o que mudou (tokens e arquivos), o que foi verificado e como, o que ficou pendente. Atualize o `CLAUDE.md` (seção Estrutura) só se surgirem arquivos novos, como `docs/specs/design-system.md` ou `app/static/fonts/`.

## Reverter e alternar
Mantenha o visual anterior recuperável: a troca fica em commits próprios na branch (por exemplo `feat/redesenho-visual`). Para desfazer tudo, o caminho é o git, sem mexer à mão: `git checkout <commit-anterior> -- app/static/style.css app/templates/<arquivos tocados>` e remover os arquivos criados pelo redesenho (spec, guarda de testes, presets). Prefira um commit de reversão a reescrever o histórico.
Para alternar entre temas sem git, o usuário pode pedir "salve este visual como preset": copie o bloco de tokens para `app/static/temas/<nome>.css` (somente `:root{...}`). Como a decoração da casca está atrás de tokens (regra de ouro 8), trocar o bloco troca o tema inteiro; regras estruturais que não dependam de token (ex.: toast com barra lateral) não viajam no preset, avise o usuário.

## O que não fazer
- Não trocar o visual sem entrevista e sem spec aprovada, nem "melhorar" além do pedido (nada de novos componentes ou funcionalidades).
- Não alterar banco, `db/seed.py`, regras, rotas ou textos de validação.
- Não usar CDN, fontes externas ou bibliotecas de CSS/JS.
- Não deixar cor, fonte, raio ou sombra literal fora do `:root`.
- Não baixar o contraste abaixo de AA para "ficar fiel" a uma referência sem o usuário assumir o risco por escrito.
- Não copiar logotipos ou ativos protegidos que o usuário não forneceu.
- Não instalar plugin/skill de terceiros nem baixar binários sem aval; não contornar bloqueio de permissão ou de leitura de imagem (use o plano B e diga o que ficou para o usuário).
- Não encerrar processo ou liberar porta que não foi você quem abriu.
