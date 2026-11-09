---
name: verificar-gravacao
description: Confere, usando o servidor MCP bayviva (somente leitura), se uma visita registrada pelo app realmente chegou ao banco DuckDB com os valores certos e se não grava nada quando há erro. Use depois de implementar ou alterar o registro de visitas, quando o usuário pedir para verificar a gravação, ou quando um botão de salvar "parece funcionar" sem prova.
---

# Verificar gravação

Objetivo: provar, olhando o banco, que a tela grava de verdade. Um teste verde ou uma mensagem de sucesso na tela não bastam: o que vale é a linha na tabela `visitas`. O servidor MCP `bayviva` é **somente leitura**, então as gravações são feitas pelo app, e o MCP só observa.

## Pré-requisitos
- As ferramentas `consultar`, `listar_tabelas` e `descrever_tabela` do servidor `bayviva` estão disponíveis. Se não estiverem, peça ao usuário para rodar `/mcp` e conferir se `bayviva` aparece conectado. Sem MCP, avise e pare, não troque por outro método sem dizer.
- O app está no ar (`uvicorn app.main:app`, normalmente em http://127.0.0.1:8000) **e usa o mesmo banco** que o MCP (`db/bayviva.duckdb`, ou o caminho em `BAYVIVA_DB`). Se o app não estiver rodando, peça ao usuário para subi-lo.
- A spec de registrar visita define a rota e os campos (`docs/specs/lab2-specs/registrar-visita.md`). Leia-a: use as rotas, os nomes de campo e as mensagens que ela define.

## Passos
1. **Estado inicial.** Com `consultar`: `SELECT count(*) AS total, max(id) AS ultimo_id FROM visitas`. Guarde os dois valores.
2. **Visita válida.** Registre uma visita pelo app, seguindo a spec: peça ao usuário para preencher o formulário na tela, ou, se ele autorizar, envie o POST com `curl` usando os nomes de campo da spec e notas começando com `[verificacao]` para identificar o registro de teste.
3. **Prova no banco.** Com `consultar`: `SELECT * FROM visitas ORDER BY id DESC LIMIT 3`. Confirme:
   - o total aumentou em exatamente 1;
   - a linha nova tem `medico_id`, `data_hora` e `notas` iguais ao que foi enviado;
   - `representante_id` e `status` seguem o que a spec manda gravar;
   - o `id` é novo e não repete nenhum existente.
4. **Clique duplo.** Se a spec exige proteção contra duplicidade, envie o mesmo POST duas vezes em seguida e confirme pelo banco quantas linhas surgiram.
5. **Visita inválida.** Envie um POST que a spec manda recusar (por exemplo notas curtas demais ou médico vazio). Confirme que o total **não mudou** e que a resposta trouxe a mensagem de erro da spec.
6. **Efeito nas outras telas.** Se a spec diz que a visita aparece no painel ou na agenda, abra essa tela e confirme (por exemplo, a "última visita" do médico mudou).

## Saída
Em português, uma tabela de verificações, cada uma com **OK** ou **FALHA**, o valor esperado, o valor encontrado no banco e a consulta usada:

```
| Verificação | Esperado | Encontrado | Resultado |
```

Termine com o veredito: "A gravação está comprovada no banco" ou "A gravação NÃO está comprovada", com a causa provável das falhas (por exemplo: o handler não chama o banco, o commit não acontece, a rota grava em outra tabela).

## Observações
- Os dados são sintéticos. Os registros de teste ficam no banco local; para voltar ao estado original, o usuário roda `python db/seed.py`. Lembre-o disso ao final.
- Nunca tente gravar pelo MCP: ele recusa e o objetivo é testar o app.
- Se o MCP responder que o banco está ocupado, aguarde alguns segundos e repita.
