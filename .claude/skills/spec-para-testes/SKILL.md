---
name: spec-para-testes
description: Transforma os critérios de aceite de uma spec do BayViva em testes pytest, um por critério, antes da implementação. Use quando o usuário pedir testes a partir de uma spec, quiser desenvolver por critérios de aceite, ou antes de implementar uma tela descrita em docs/specs/.
---

# Spec para testes

Objetivo: dar ao agente uma forma de verificar o próprio trabalho. Cada critério de aceite da spec vira um teste que **falha antes** da implementação e **passa depois**. **Não implemente a funcionalidade** nesta skill: só os testes.

## Entrada
O caminho da spec. Se não foi dado, liste `docs/specs/` e pergunte.

## Passos
1. Leia a spec e `tests/conftest.py` (fixture `client`: app com banco temporário e semente fixa) e `tests/test_base.py` (exemplo de estilo).
2. Se a spec não tiver rotas e nomes de campo (seção "Interface"), **pare** e sugira rodar `/checar-spec` primeiro. Não invente rotas.
3. Liste os critérios de aceite numerados da spec. Para cada um, escreva um teste em `tests/test_<tela>.py`:
   - nome `test_criterio_<n>_<resumo_curto>`, com uma docstring que copia o critério (dado/quando/então);
   - estrutura: *dado* (preparar dados), *quando* (chamar a rota com `client`), *então* (asserções sobre status, texto da resposta **e** estado do banco);
   - para checar o banco, use `from app.db import conexao` com `conexao(somente_leitura=True)`; a fixture `client` já aponta o app para um banco temporário;
   - não use mocks do banco: o banco temporário é real e rápido;
   - para datas, use valores relativos ao presente (`datetime.now()` menos ou mais dias) ou datas fixas bem afastadas, nunca uma data que vire passado amanhã.
4. Critérios que não dá para provar por HTTP (por exemplo "o botão fica desabilitado enquanto salva") **não viram teste falso**. Liste-os na saída como "verificar manualmente" e, se quiser deixar registro, crie o teste com `@pytest.mark.skip(reason="verificação manual: ...")`.
5. Inclua os casos que a spec define como regra, mesmo sem número de critério: campos obrigatórios, limites de tamanho, mensagens de erro exatas, e o que **não** deve acontecer (nada gravado quando há erro).
6. Rode `pytest tests/test_<tela>.py` e confirme que:
   - os testes **falham pelo motivo certo** (rota inexistente, funcionalidade ausente), e não por erro de importação ou de sintaxe do próprio teste;
   - nenhum teste passa sem a funcionalidade existir. Se passar, o teste está fraco: corrija.

## Saída
Resumo curto, em português:
- arquivo criado e quantos testes (e quantos ficaram como verificação manual);
- tabela critério → teste;
- resultado da execução (quantos falharam, com o motivo típico);
- próximo passo: pedir um plano e implementar até os testes passarem, depois `/verificar-gravacao`.
