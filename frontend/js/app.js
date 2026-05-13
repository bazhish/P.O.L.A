/**
 * POLAR — comportamento compartilhado entre telas
 */
(function () {
  "use strict";

  function qs(sel, root) {
    return (root || document).querySelector(sel);
  }
  function qsa(sel, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(sel));
  }

  function initNavGroups() {
    qsa(".nav__group-toggle").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var group = btn.closest(".nav__group");
        if (!group) return;
        var open = group.classList.toggle("is-open");
        qsa(".nav__group").forEach(function (g) {
          if (g !== group) g.classList.remove("is-open");
        });
        btn.setAttribute("aria-expanded", open ? "true" : "false");
      });
    });
  }

  function initLoginPage() {
    var form = qs("#login-form");
    if (!form) return;

    var passInput = qs("#password", form);
    var toggle = qs("#toggle-password", form);
    var err = qs("#login-error", form);

    if (toggle && passInput) {
      toggle.addEventListener("click", function () {
        var show = passInput.type === "password";
        passInput.type = show ? "text" : "password";
        toggle.setAttribute("aria-label", show ? "Ocultar senha" : "Mostrar senha");
      });
    }

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var email = (qs("#email", form).value || "").trim();
      var pass = (passInput.value || "").trim();

      if (!email || !pass) {
        if (err) {
          err.textContent = "Preencha e-mail e senha.";
          err.classList.add("is-visible");
        }
        return;
      }

      // Demo: qualquer combinação válida não vazia "entra"; senão mostra erro de exemplo
      if (email === "demo" && pass === "demo") {
        if (err) err.classList.remove("is-visible");
        window.location.href = "dashboard.html";
        return;
      }

      // Aceita qualquer e-mail com @ e senha com 3+ caracteres como sucesso de demonstração
      if (email.indexOf("@") !== -1 && pass.length >= 3) {
        try {
          sessionStorage.setItem("polar_user", JSON.stringify({ email: email, name: "Professor" }));
        } catch (x) {}
        if (err) err.classList.remove("is-visible");
        window.location.href = "dashboard.html";
        return;
      }

      if (err) {
        err.textContent = "E-mail ou senha inválidos.";
        err.classList.add("is-visible");
      }
    });
  }

  function initCharCounters() {
    qsa("[data-max-length]").forEach(function (ta) {
      var max = parseInt(ta.getAttribute("data-max-length"), 10);
      var out = qs("[data-char-for='" + ta.id + "']");
      if (!out || !ta.id) return;

      function sync() {
        var len = ta.value.length;
        if (len > max) {
          ta.value = ta.value.slice(0, max);
          len = max;
        }
        out.textContent = len + " / " + max + " caracteres";
      }
      ta.addEventListener("input", sync);
      sync();
    });
  }

  function initRichEditor() {
    var editor = qs("[data-rte-body]");
    if (!editor) return;

    var max = parseInt(editor.getAttribute("data-max-length") || "2000", 10);
    var counter = qs("[data-rte-count]");

    function textLen() {
      var t = editor.innerText || "";
      return t.replace(/\n/g, "").length;
    }

    function syncCount() {
      if (!counter) return;
      var len = textLen();
      counter.textContent = len + " / " + max + " caracteres";
    }

    editor.addEventListener("input", function () {
      while (textLen() > max) {
        // remove último caractere de forma simples
        editor.innerText = (editor.innerText || "").slice(0, -1);
      }
      syncCount();
    });

    qsa("[data-rte-cmd]").forEach(function (btn) {
      btn.addEventListener("mousedown", function (e) {
        e.preventDefault();
      });
      btn.addEventListener("click", function () {
        var cmd = btn.getAttribute("data-rte-cmd");
        var val = btn.getAttribute("data-rte-value") || null;
        document.execCommand(cmd, false, val);
        editor.focus();
        syncCount();
      });
    });

    var styleSel = qs("[data-rte-style]");
    if (styleSel) {
      styleSel.addEventListener("change", function () {
        document.execCommand("formatBlock", false, styleSel.value || "p");
        editor.focus();
      });
    }

    syncCount();
  }

  function initFiltersClear() {
    var btn = qs("[data-clear-filters]");
    if (!btn) return;
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      var form = btn.closest("form") || document;
      qsa("input[type='search'], input[type='text']", form).forEach(function (i) {
        if (!i.closest(".input-wrap")) i.value = "";
      });
      qsa("select", form).forEach(function (s) {
        s.selectedIndex = 0;
      });
    });
  }

  function initPaginationDemo() {
    qsa("[data-pagination]").forEach(function (wrap) {
      qsa("button[data-page]", wrap).forEach(function (b) {
        b.addEventListener("click", function () {
          if (b.disabled) return;
          qsa("button[data-page]", wrap).forEach(function (x) {
            x.classList.remove("is-active");
          });
          b.classList.add("is-active");
        });
      });
    });
  }

  function initOccurrenceActions() {
    var assume = qs("[data-action-assume]");
    var resolve = qs("[data-action-resolve]");
    if (assume) {
      assume.addEventListener("click", function () {
        alert("Demonstração: análise assumida pelo coordenador.");
      });
    }
    if (resolve) {
      resolve.addEventListener("click", function () {
        alert("Demonstração: ocorrência marcada como resolvida.");
      });
    }
  }

  function initFormDemoSubmit(formSel, msg) {
    var f = qs(formSel);
    if (!f) return;
    f.addEventListener("submit", function (e) {
      e.preventDefault();
      var invalid = f.querySelector(":invalid");
      if (invalid) {
        invalid.focus();
        return;
      }
      alert(msg || "Formulário validado (demonstração).");
    });
  }

  function initTabs() {
    var tabs = qs(".tabs");
    if (!tabs) return;
    qsa(".tabs button").forEach(function (btn, idx) {
      btn.addEventListener("click", function () {
        qsa(".tabs button").forEach(function (b) {
          b.classList.remove("is-active");
        });
        btn.classList.add("is-active");
        var panels = qsa("[data-tab-panel]");
        panels.forEach(function (p, i) {
          p.hidden = i !== idx;
        });
      });
    });
  }

  function initCancelLinks() {
    qsa("[data-cancel-href]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var href = btn.getAttribute("data-cancel-href");
        if (href) window.location.href = href;
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initNavGroups();
    initLoginPage();
    initCharCounters();
    initRichEditor();
    initFiltersClear();
    initPaginationDemo();
    initOccurrenceActions();
    initFormDemoSubmit("#form-nova-turma", "Turma salva (demonstração).");

    var fNovaOc = qs("#form-nova-ocorrencia");
    if (fNovaOc) {
      fNovaOc.addEventListener("submit", function (e) {
        e.preventDefault();
        var invalid = fNovaOc.querySelector(":invalid");
        if (invalid) {
          invalid.focus();
          return;
        }
        var rte = qs("[data-rte-body]", fNovaOc);
        var txt = rte ? (rte.innerText || "").replace(/\s+/g, " ").trim() : "";
        if (txt.length < 10) {
          alert("Preencha a descrição detalhada (mínimo 10 caracteres).");
          if (rte) rte.focus();
          return;
        }
        alert("Ocorrência registrada (demonstração).");
      });
    }
    initTabs();
    initCancelLinks();
  });
})();
