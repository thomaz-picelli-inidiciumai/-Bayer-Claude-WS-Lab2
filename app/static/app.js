/* BayViva: melhorias de interface. O servidor valida tudo; este arquivo só adianta o aviso.
   Sem JavaScript as telas continuam funcionando (mensagens e pop-ups vêm renderizados). */
(function () {
  "use strict";

  // Mesmas mensagens de app/regras.py (tests/test_regras.py confere a igualdade).
  var MSG = {
    medico: "Selecione um médico",
    dataHoraVazia: "Informe a data e a hora da visita",
    dataHoraFutura: "A data da visita não pode estar no futuro",
    notasTamanho: "Informe de 10 a 1000 caracteres",
    notasPii: "Remova dados pessoais das notas",
    dataVazia: "Informe a data",
    diaUtil: "Escolha um dia útil",
    horaGrade: "Escolha um horário entre 08:00 e 18:00, de 30 em 30 minutos",
    horarioFuturo: "Escolha um horário futuro"
  };
  var ROTULO = {
    medico_id: "Médico", data_hora: "Data e hora", notas: "Notas", data: "Data", hora: "Hora"
  };

  function $(sel, raiz) { return (raiz || document).querySelector(sel); }
  function $$(sel, raiz) { return Array.prototype.slice.call((raiz || document).querySelectorAll(sel)); }

  // ---------- diálogos ----------
  function abrir(dlg) {
    if (!dlg) { return; }
    if (typeof dlg.showModal === "function") {
      if (dlg.open) { dlg.close(); }
      dlg.showModal();
    } else {
      dlg.setAttribute("open", "");
    }
  }

  function fechar(dlg) {
    if (dlg && dlg.open) { dlg.close(); }
  }

  function focarPrimeiroErro(raiz) {
    var alvo = $("[aria-invalid='true']", raiz || document);
    if (alvo) { alvo.focus(); }
  }

  // ---------- erros por campo ----------
  function campoDe(form, nome) { return form.elements[nome]; }

  function mostrarErro(form, nome, msg) {
    var campo = campoDe(form, nome);
    var alvo = $("[data-erro-de='" + nome + "']", form);
    if (campo) {
      campo.setAttribute("aria-invalid", "true");
      if (alvo) { campo.setAttribute("aria-describedby", alvo.id); }
    }
    if (alvo) { alvo.textContent = msg; alvo.hidden = false; }
    var envoltorio = campo && campo.closest(".campo-form");
    if (envoltorio) { envoltorio.classList.add("com-erro"); }
  }

  function limparErro(form, nome) {
    var campo = campoDe(form, nome);
    var alvo = $("[data-erro-de='" + nome + "']", form);
    if (campo) { campo.removeAttribute("aria-invalid"); }
    if (alvo) { alvo.textContent = ""; alvo.hidden = true; }
    var envoltorio = campo && campo.closest(".campo-form");
    if (envoltorio) { envoltorio.classList.remove("com-erro"); }
  }

  function limparErros(form) {
    $$("[data-erro-de]", form).forEach(function (el) {
      limparErro(form, el.getAttribute("data-erro-de"));
    });
  }

  // ---------- regras no navegador ----------
  function temDadoPessoal(texto) {
    return texto.indexOf("@") !== -1 || /\d(?:[\s\-()]*\d){7,}/.test(texto);
  }

  var VALIDADORES = {
    visita: function (form) {
      var erros = {};
      var medico = form.elements.medico_id.value;
      if (!medico) { erros.medico_id = MSG.medico; }

      var dh = form.elements.data_hora.value.trim();
      if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(dh) || isNaN(new Date(dh).getTime())) {
        erros.data_hora = MSG.dataHoraVazia;
      } else if (form.dataset.agora && (dh + ":00") > form.dataset.agora) {
        erros.data_hora = MSG.dataHoraFutura;
      }

      var notas = form.elements.notas.value.trim();
      if (notas.length < 10 || notas.length > 1000) {
        erros.notas = MSG.notasTamanho;
      } else if (temDadoPessoal(notas)) {
        erros.notas = MSG.notasPii;
      }
      return erros;
    },

    agenda: function (form) {
      var erros = {};
      if (!form.elements.medico_id.value) { erros.medico_id = MSG.medico; }

      var data = form.elements.data.value.trim();
      var dia = /^\d{4}-\d{2}-\d{2}$/.test(data) ? new Date(data + "T12:00:00") : null;
      if (!dia || isNaN(dia.getTime())) {
        erros.data = MSG.dataVazia;
      } else if (dia.getDay() === 0 || dia.getDay() === 6) {
        erros.data = MSG.diaUtil;
      }

      var hora = form.elements.hora.value;
      if (!/^(0[89]|1[0-7]):(00|30)$/.test(hora) && hora !== "18:00") {
        erros.hora = MSG.horaGrade;
      }

      if (!erros.data && !erros.hora && form.dataset.agora) {
        if ((data + "T" + hora + ":00") <= form.dataset.agora) { erros.hora = MSG.horarioFuturo; }
      }
      return erros;
    }
  };

  // ---------- pop-up de erros ----------
  function mostrarResumo(form, erros) {
    var dlg = document.getElementById(form.dataset.dialogoErros || "dlg-erros");
    if (!dlg) { return; }
    var lista = $("[data-lista-erros]", dlg);
    lista.innerHTML = "";
    Object.keys(erros).forEach(function (nome) {
      var li = document.createElement("li");
      var b = document.createElement("strong");
      b.textContent = (ROTULO[nome] || nome) + ": ";
      li.appendChild(b);
      li.appendChild(document.createTextNode(erros[nome]));
      lista.appendChild(li);
    });
    abrir(dlg);
  }

  // ---------- formulários ----------
  function travar(form) {
    form.dataset.enviando = "1";
    var botao = $("[data-enviar]", form);
    if (botao) {
      botao.disabled = true;
      botao.dataset.textoOriginal = botao.textContent;
      botao.textContent = "Salvando…";
      botao.setAttribute("aria-busy", "true");
    }
  }

  function destravar(form) {
    delete form.dataset.enviando;
    var botao = $("[data-enviar]", form);
    if (botao) {
      botao.disabled = false;
      botao.removeAttribute("aria-busy");
      if (botao.dataset.textoOriginal) { botao.textContent = botao.dataset.textoOriginal; }
    }
  }

  function prepararFormulario(form) {
    var validar = VALIDADORES[form.dataset.valida];
    if (!validar) { return; }

    form.addEventListener("submit", function (ev) {
      if (form.dataset.enviando) { ev.preventDefault(); return; }  // clique duplo
      limparErros(form);
      var erros = validar(form);
      var nomes = Object.keys(erros);
      if (nomes.length) {
        ev.preventDefault();
        nomes.forEach(function (n) { mostrarErro(form, n, erros[n]); });
        mostrarResumo(form, erros);
        return;
      }
      travar(form);
    });

    // erro some assim que o usuário corrige o campo
    form.addEventListener("input", function (ev) {
      if (ev.target && ev.target.name) { limparErro(form, ev.target.name); }
    });
    form.addEventListener("change", function (ev) {
      if (ev.target && ev.target.name) { limparErro(form, ev.target.name); }
    });
  }

  function prepararContador() {
    $$("[data-contador-de]").forEach(function (saida) {
      var campo = document.getElementById(saida.getAttribute("data-contador-de"));
      if (!campo) { return; }
      var max = parseInt(campo.getAttribute("maxlength") || "1000", 10);
      function atualizar() {
        var n = campo.value.trim().length;
        saida.textContent = n + "/" + max;
        saida.classList.toggle("fora", n > 0 && (n < 10 || n > max));
      }
      campo.addEventListener("input", atualizar);
      atualizar();
    });
  }

  // ---------- inicialização ----------
  document.addEventListener("DOMContentLoaded", function () {
    $$("form[data-valida]").forEach(prepararFormulario);
    prepararContador();

    // pop-ups renderizados pelo servidor: sem JS ficam abertos como aviso simples
    $$("dialog[data-modal][open]").forEach(function (dlg) {
      dlg.removeAttribute("open");
      abrir(dlg);
    });

    $$("dialog").forEach(function (dlg) {
      dlg.addEventListener("click", function (ev) {
        if (ev.target === dlg) { fechar(dlg); }  // clique no fundo escuro
      });
      dlg.addEventListener("close", function () {
        var form = dlg.querySelector("form[data-valida]") || document.querySelector("form[data-valida]");
        if (dlg.hasAttribute("data-foca-erro")) { focarPrimeiroErro(form || document); }
      });
    });

    document.addEventListener("click", function (ev) {
      var alvo = ev.target.closest ? ev.target.closest("[data-fechar],[data-abrir],[data-cancelar-visita]") : null;
      if (!alvo) { return; }

      if (alvo.hasAttribute("data-fechar")) {
        fechar(alvo.closest("dialog"));
      } else if (alvo.hasAttribute("data-abrir")) {
        var dlg = document.getElementById(alvo.getAttribute("data-abrir"));
        var data = alvo.getAttribute("data-data");
        if (dlg && data) {
          var campo = dlg.querySelector("[name='data']");
          if (campo) { campo.value = data; }
        }
        abrir(dlg);
        var primeiro = dlg && dlg.querySelector("select, input, textarea");
        if (primeiro) { primeiro.focus(); }
      } else if (alvo.hasAttribute("data-cancelar-visita")) {
        var confirmacao = document.getElementById("dlg-cancelar");
        if (!confirmacao) { return; }
        $("form", confirmacao).setAttribute("action", alvo.getAttribute("data-acao"));
        $("[data-resumo-visita]", confirmacao).textContent = alvo.getAttribute("data-resumo") || "";
        abrir(confirmacao);
      }
    });

    // avisos temporários (toast)
    $$(".toast[data-auto]").forEach(function (t) {
      setTimeout(function () { t.classList.add("saindo"); }, 6500);
      setTimeout(function () { if (t.parentNode) { t.parentNode.removeChild(t); } }, 7000);
    });
    $$(".toast [data-fechar-toast]").forEach(function (b) {
      b.addEventListener("click", function () { b.closest(".toast").remove(); });
    });
  });

  // voltar pelo histórico não pode deixar o botão preso em "Salvando…"
  window.addEventListener("pageshow", function (ev) {
    if (ev.persisted) { $$("form[data-valida]").forEach(destravar); }
  });
})();
