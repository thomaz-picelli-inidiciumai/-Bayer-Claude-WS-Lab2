# Spec: Registrar visita

## Objetivo e usuário
Permitir que o representante registre uma visita realizada a um médico, para que ela apareça no histórico e no painel. Na base, a carteira do representante são todos os médicos da tabela `medicos`.

## Critérios de aceite
1. **Dado** o formulário preenchido com médico, data/hora passada e notas válidas, **quando** clico em Salvar, **então** uma linha é gravada em `visitas` (status `realizada`, `representante_id` = 1) e vejo a mensagem "Visita registrada com sucesso".
2. **Dado** o formulário com campo obrigatório vazio, **quando** clico em Salvar, **então** nada é gravado e vejo o erro ao lado do campo.
3. **Dado** uma visita salva e a tela do painel já construída (spec `painel-de-medicos.md`), **quando** abro o painel, **então** a "última visita" do médico mostra essa data. Sem o painel, este critério fica para depois e não bloqueia a entrega.
4. **Dado** que cliquei em Salvar, **quando** a gravação está em andamento, **então** o botão fica desabilitado (evita visita duplicada). *Verificação manual: depende do navegador, não dá para provar por HTTP.*

## Campos e validações
| Campo | Tipo | Obrigatório | Regra | Placeholder / mensagem de erro |
| --- | --- | --- | --- | --- |
| Médico | lista suspensa (nome, ordem alfabética) | sim | deve existir em `medicos` | "Selecione um médico" / "Selecione um médico" |
| Data e hora | data-hora | sim | não pode ser futura (maior que o momento atual é futura; igual ou menor é aceita) | — / vazia: "Informe a data e a hora da visita"; futura: "A data da visita não pode estar no futuro" |
| Notas | texto longo | sim | 10 a 1000 caracteres | "Resuma o que foi discutido (mín. 10 caracteres)" / "Informe de 10 a 1000 caracteres" |

## Interface (rotas e nomes de campo)
- `GET /visitas/nova`: exibe o formulário (200).
- `POST /visitas/nova`: campos de formulário `medico_id`, `data_hora` (formato `AAAA-MM-DDTHH:MM`, como o input `datetime-local`) e `notas`.
  - Sucesso: 200, página com a mensagem "Visita registrada com sucesso".
  - Erro de validação: 422, nada é gravado e cada mensagem aparece junto do campo.

## Estados da tela
- **Vazio:** formulário em branco, botão Salvar habilitado.
- **Carregando:** botão desabilitado com texto "Salvando…".
- **Erro:** mensagens por campo; dados digitados são mantidos.
- **Sucesso:** mensagem verde, formulário limpo, link "Ver painel".

## Dados e regras de negócio
- Gravar em `visitas(id, medico_id, representante_id, data_hora, status, notas)` no DuckDB; `id` = máximo + 1.
- Status gravado: sempre `realizada`. Representante: o usuário logado (fixo em 1 na base).
- Notas não podem conter e-mail ou telefone (dado pessoal): rejeitar com "Remova dados pessoais das notas". Considere e-mail qualquer texto com `@`, e telefone qualquer sequência de 8 ou mais dígitos (com ou sem espaços, hífens ou parênteses).

## Fora de escopo
Edição ou exclusão de visitas, anexos, múltiplos representantes, visitas planejadas (são da agenda).
