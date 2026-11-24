# Desafio do Lab 2: Registrar insight

As telas de **registrar visita**, **painel de médicos** e **agenda de visitas** já estão prontas, com specs completas em `docs/specs/lab2-specs/`. O ícone "Registrar insight" da home ainda leva a "em construção". É daí que vocês partem.

> **O desafio é propositalmente incompleto.** Ele diz o que construir, não como. Descobrir o que falta é parte do exercício. Não existe spec pronta: vocês a escrevem.

## Trilha A: Registrar insight (obrigatória)

Um representante visita médicos e percebe coisas que não cabem no registro de visita: uma objeção, uma oportunidade, uma dúvida recorrente. Construam a funcionalidade que permite anotar essa percepção sobre um médico e voltar a ela depois.

Depois que houver insights gravados, usem o servidor MCP `bayviva` para o Claude ler os insights e sintetizar os temas que aparecem.

## Trilha B: Metas e alertas de cobertura (se sobrar tempo)

O gerente quer saber quem está abaixo do esperado e quais médicos estão sem atenção. Construam a visão que responde isso.

## Como trabalhar

1. Abram o **plan mode** e conversem com o Claude sobre o que a tela precisa. Perguntem a ele o que teria de decidir sozinho.
2. Escrevam a spec em `docs/specs/` no formato do `TEMPLATE.md`. Rodem `/checar-spec` até ela passar.
3. Gerem os testes com `/spec-para-testes` e implementem em passos pequenos, rodando `pytest` a cada passo.
4. Usem o servidor MCP `bayviva` para inspecionar o banco e para o Claude ler os dados reais que a funcionalidade gerou. Confira com `/mcp` que ele está conectado.
5. Criem **uma skill** que automatize algo útil para o seu fluxo e **um hook** que proteja uma regra do projeto.

## Entregáveis

- a spec da tela, aprovada pelo `/checar-spec`;
- a tela funcionando, com testes para cada critério de aceite;
- uma skill criada por vocês;
- um hook criado por vocês.

## Pronto quando

- a spec está completa e nada foi implementado fora do escopo dela;
- os critérios de aceite têm teste e `pytest` passa;
- o que a spec manda gravar foi **comprovado no banco** (mensagem de sucesso na tela não é prova);
- a skill e o hook funcionam.

## Lembretes

- Os dados são sempre sintéticos: e-mails em `@example.com`, telefones com DDD 00.
- Não commitem na `main`: usem uma branch de feature e um PR.
- O MCP é somente leitura de propósito: quem grava no banco é o app.
- Se registrarem um hook, usem `.claude/settings.local.json`, para não alterar o `.claude/settings.json` do repositório.
- Não alterem `db/seed.py` sem manter a semente fixa: todos precisam ver os mesmos números.
