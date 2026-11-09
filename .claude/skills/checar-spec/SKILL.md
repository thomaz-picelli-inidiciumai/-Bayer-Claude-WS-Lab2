---
name: checar-spec
description: Confere se uma spec do BayViva está completa antes de qualquer código, comparando com docs/specs/TEMPLATE.md, e lista o que falta. Use quando o usuário pedir para revisar, validar ou checar uma spec, ou antes de implementar uma tela a partir de uma spec em docs/specs/.
---

# Checar spec

Objetivo: dizer, antes de codar, se a spec responde as perguntas que o agente teria de responder sozinho. **Não implemente nada e não edite a spec** a menos que o usuário peça depois.

## Entrada
O caminho da spec (por exemplo `docs/specs/lab2-specs/registrar-visita.md`). Se não foi dado, liste os `.md` em `docs/specs/` e pergunte qual.

## Passos
1. Leia `docs/specs/TEMPLATE.md` e a spec indicada.
2. Para cada seção do template, classifique a spec como **OK**, **Incompleta** ou **Ausente**, citando o trecho que serviu de evidência (ou dizendo que não há):
   - Objetivo e usuário
   - Critérios de aceite
   - Campos e validações
   - Interface (rotas e nomes de campo)
   - Estados da tela
   - Dados e regras de negócio
   - Fora de escopo
3. Aplique estas verificações mais finas e anote cada falha:
   - **Critérios:** estão no formato dado/quando/então? O "então" é algo observável (mensagem, linha no banco, posição na lista), e não uma intenção vaga como "funciona bem"?
   - **Campos:** cada campo tem tipo, obrigatoriedade, regra, placeholder e mensagem de erro? Há limites (tamanho mínimo e máximo, formatos)?
   - **Estados:** vazio, carregando, erro e sucesso estão descritos?
   - **Dados:** a spec diz em qual tabela e em quais colunas gravar e ler? Diz o que fazer com status, ids e valores padrão?
   - **Regras:** conflitos, ordenação, paginação, filtros, fuso e itens cancelados estão definidos quando a tela envolve isso?
   - **Botões e ações:** todo botão tem comportamento descrito (o que acontece ao clicar, o que o usuário vê)?
4. Confira o que a spec afirma contra o repositório quando for barato: a tabela e as colunas citadas existem em `db/schema.sql`? A rota citada já existe em `app/main.py`?

## Saída
Responda neste formato, em português:

```
Spec: <caminho>
Veredito: PRONTA PARA IMPLEMENTAR | FALTAM ITENS

| Seção | Situação | Evidência ou lacuna |
| ... |

Lacunas (da mais grave para a menos grave):
1. <o que falta> → pergunta a responder: "<pergunta objetiva>"
```

- O veredito só é PRONTA quando nenhuma seção está Ausente e não há lacuna que mude o comportamento visível (onde gravar, validação, estados).
- Cada lacuna vira uma **pergunta concreta**, para o usuário responder ou para ser escrita na spec. Não invente a resposta.
- Se a spec estiver pronta, termine sugerindo o próximo passo: pedir um plano (plan mode) e gerar os testes com `/spec-para-testes`.
