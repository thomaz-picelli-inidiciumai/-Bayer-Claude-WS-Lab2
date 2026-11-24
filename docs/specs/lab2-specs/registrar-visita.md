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
- `GET /visitas/nova`: exibe o formulário (200). A função da rota se chama `visitas_nova` (é por esse nome que o ícone da home passa a apontar para a tela).
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

## Critérios de aceite adicionais (experiência e robustez)
5. **Dado** o formulário válido e uma falha do banco ao gravar, **quando** clico em Salvar, **então** nada é gravado, a resposta é 500, vejo o pop-up "Não foi possível salvar. Nada foi gravado. Tente novamente." e os dados digitados continuam no formulário.
6. **Dado** que já existe visita `realizada` do mesmo médico no mesmo `data_hora`, **quando** clico em Salvar, **então** nada é gravado, a resposta é 422 e vejo "Esta visita já foi registrada".
7. **Dado** `GET /visitas/nova?medico_id=N` com N existente, **quando** abro a tela, **então** o médico N vem selecionado; N inexistente ou inválido é ignorado (lista em "Selecione um médico").
8. **Dado** um envio com erro de validação, **quando** a resposta chega, **então** além do erro junto de cada campo vejo um pop-up que lista cada problema e o motivo; o pop-up de sucesso só aparece depois que a linha foi gravada e lida de volta do banco.
9. **Dado** um campo inválido, **quando** clico em Salvar no navegador, **então** a validação no cliente impede o envio e mostra o mesmo pop-up e as mesmas mensagens do servidor. *Verificação manual.*

## Decisões de detalhe (resposta ao /checar-spec)
- Notas: espaços nas pontas são removidos antes de validar e de gravar; o limite de 10 a 1000 conta o texto já aparado.
- "Momento atual" é o horário de America/Sao_Paulo (o mesmo da agenda); `data_hora` é gravado sem fuso, nesse horário local.
- Um campo mostra no máximo uma mensagem, na ordem: vazio, tamanho, dado pessoal ("Remova dados pessoais das notas").
- "Esta visita já foi registrada" aparece junto do campo Data e hora. Data e hora em formato inválido é tratada como vazia.
- `medico_id` que não seja número inteiro existente é tratado como não selecionado.

## Experiência
- **Pop-up de sucesso:** título "Visita registrada com sucesso", resumo (médico, data e hora) e ações "Ver painel" e "Registrar outra". Fecha com Esc ou botão.
- **Pop-up de erro:** lista as mensagens por campo; ao fechar, o foco vai para o primeiro campo com erro.
- **Notas:** contador "n/1000" ao vivo; o campo de data e hora recebe `max` igual ao momento atual do servidor.
- **Layout:** formulário ocupa a largura útil da tela, em duas colunas a partir de 900 px e uma coluna abaixo disso; botões com área de toque de pelo menos 40 px.
- **Acessibilidade:** mensagens de erro ligadas ao campo (`aria-describedby`), `aria-live` para avisos, diálogo com foco preso.
- **Sem JavaScript** a tela continua funcionando: o servidor valida e renderiza tudo.

## Fora de escopo
Edição ou exclusão de visitas, anexos, múltiplos representantes, visitas planejadas (são da agenda).
