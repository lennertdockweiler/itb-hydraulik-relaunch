/*
 * ITB – gemeinsame Interaktionen aller Varianten
 * 1. Mobile Navigation  2. Scrollspy  3. Anfrageformular  4. Baukasten-Konfigurator
 */
(() => {
  const d = document;

  /* 1. Mobile Navigation ------------------------------------------------ */
  const toggle = d.querySelector("[data-nav-toggle]");
  const nav = toggle && d.getElementById(toggle.getAttribute("aria-controls"));
  if (toggle && nav) {
    const setOpen = (open) => {
      toggle.setAttribute("aria-expanded", String(open));
      nav.dataset.open = String(open);
    };
    toggle.addEventListener("click", () => setOpen(toggle.getAttribute("aria-expanded") !== "true"));
    nav.addEventListener("click", (e) => { if (e.target.closest("a")) setOpen(false); });
    d.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && toggle.getAttribute("aria-expanded") === "true") {
        setOpen(false);
        toggle.focus();
      }
    });
  }

  /* 2. Scrollspy: markiert den Menüpunkt der sichtbaren Sektion ---------- */
  const spyLinks = [...d.querySelectorAll("[data-spy] a[href*='#']")];
  const sections = new Map();
  spyLinks.forEach((a) => {
    const target = d.getElementById(a.hash.slice(1));
    if (target) sections.set(target, a);
  });
  if (sections.size && "IntersectionObserver" in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        spyLinks.forEach((l) => l.removeAttribute("aria-current"));
        sections.get(entry.target).setAttribute("aria-current", "true");
      });
    }, { rootMargin: "-40% 0px -55% 0px" });
    sections.forEach((_, section) => io.observe(section));
  }

  /* Mobile Aktionsleiste ausblenden, sobald der Kontaktbereich im Bild ist */
  const actionbar = d.querySelector("[data-actionbar]");
  const contact = d.getElementById("kontakt");
  if (actionbar && contact && "IntersectionObserver" in window) {
    new IntersectionObserver(([entry]) => actionbar.classList.toggle("is-hidden", entry.isIntersecting), { threshold: 0.05 }).observe(contact);
  }

  d.querySelectorAll("[data-year]").forEach((el) => { el.textContent = new Date().getFullYear(); });

  /* 3. Anfrageformular -------------------------------------------------- */
  const form = d.querySelector("[data-inquiry]");
  if (!form) return;

  const status = form.querySelector("[data-status]");
  const button = form.querySelector("button[type='submit']");
  const fields = [...form.querySelectorAll("input:not([name='_gotcha']), select, textarea")];
  const MESSAGES = {
    valueMissing: "Bitte füllen Sie dieses Feld aus.",
    typeMismatch: "Bitte geben Sie eine gültige E-Mail-Adresse ein, z. B. name@firma.de.",
  };

  const validate = (field) => {
    const error = d.getElementById(`${field.id}-error`);
    let text = "";
    if (!field.validity.valid) {
      text = field.validity.valueMissing ? (field.dataset.missing || MESSAGES.valueMissing)
        : field.validity.typeMismatch ? MESSAGES.typeMismatch
        : field.validationMessage;
    }
    if (error) error.textContent = text;
    field.setAttribute("aria-invalid", text ? "true" : "false");
    return !text;
  };

  const setStatus = (state, html) => {
    status.dataset.state = state;
    status.innerHTML = html;
  };

  form.noValidate = true;
  fields.forEach((field) => {
    field.addEventListener("blur", () => { if (field.value || field.hasAttribute("aria-invalid")) validate(field); });
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const invalid = fields.filter((f) => !validate(f));
    if (invalid.length) {
      setStatus("error", invalid.length === 1 ? "Bitte prüfen Sie das markierte Feld." : `Bitte prüfen Sie die ${invalid.length} markierten Felder.`);
      invalid[0].focus();
      return;
    }
    if (form.elements._gotcha.value) return; // Honeypot ausgefüllt -> Bot, still verwerfen

    // Solange keine Formspree-ID eingetragen ist, läuft das Formular im Vorschau-Modus
    const demo = form.action.includes("ERSETZEN");
    button.disabled = true;
    button.setAttribute("aria-busy", "true");
    setStatus("loading", "Anfrage wird gesendet …");
    try {
      if (demo) {
        await new Promise((r) => setTimeout(r, 900));
      } else {
        const res = await fetch(form.action, { method: "POST", body: new FormData(form), headers: { Accept: "application/json" } });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
      }
      form.reset();
      fields.forEach((f) => f.removeAttribute("aria-invalid"));
      setStatus("success", demo
        ? "<strong>Vorschau-Modus:</strong> Formular und Prüfung funktionieren. Versendet wird erst, wenn die Formspree-ID eingetragen ist."
        : "<strong>Danke, Ihre Anfrage ist angekommen.</strong> Wir prüfen Ihre Angaben und melden uns mit Rückfragen oder einem Angebot.");
    } catch {
      setStatus("error", 'Das Senden hat nicht geklappt. Schreiben Sie uns bitte direkt an <a href="mailto:mail@itb-hydraulik.com">mail@itb-hydraulik.com</a> oder rufen Sie an: <a href="tel:+4977329592105">07732 95921-05</a>.');
    } finally {
      button.disabled = false;
      button.removeAttribute("aria-busy");
    }
  });

  /* Formular vorbefüllen – vorhandener Text bleibt erhalten, Neues wird angehängt */
  const prefill = (topic, text) => {
    if (topic) form.elements.anliegen.value = topic;
    if (!text) return;
    const message = form.elements.nachricht;
    const current = message.value.trim();
    if (!current.includes(text)) message.value = current ? `${current}\n\n${text}` : text;
  };
  d.addEventListener("click", (e) => {
    const trigger = e.target.closest("[data-topic], [data-prefill]");
    if (trigger) prefill(trigger.dataset.topic, trigger.dataset.prefill);
  });

  /* Vorbefüllen per URL – z. B. von Produktseiten: ./?anliegen=datenblatt&nachricht=…#kontakt */
  const params = new URLSearchParams(location.search);
  if (params.has("anliegen") || params.has("nachricht")) {
    const topic = params.get("anliegen");
    const known = [...form.elements.anliegen.options].some((o) => o.value === topic);
    prefill(known ? topic : null, params.get("nachricht"));
    history.replaceState(null, "", location.pathname + location.hash);
  }

  /* 4. Baukasten-Konfigurator ------------------------------------------- */
  const kit = d.querySelector("[data-kit]");
  if (kit) {
    const bom = d.querySelector("[data-bom]");
    const kitStatus = d.querySelector("[data-kit-status]");
    const modules = d.querySelectorAll(".kit__mod");
    const ROWS = [["aufgabe", "Aufgabe"], ["medium", "Medium"], ["pumpe", "Pumpe"], ["antrieb", "Strom"], ["tank", "Tank"], ["zubehoer", "Zubehör"]];

    const selection = () => Object.fromEntries(ROWS.map(([name]) => [
      name, [...kit.querySelectorAll(`[name="${name}"]:checked`)].map((i) => i.value),
    ]));

    const render = () => {
      const sel = selection();
      bom.replaceChildren(...ROWS.flatMap(([name, label]) => {
        const dt = d.createElement("dt");
        const dd = d.createElement("dd");
        dt.textContent = label;
        dd.textContent = sel[name].length ? sel[name].join(", ") : "–";
        return [dt, dd];
      }));
      // Pumpe + Motor gehören immer dazu, alle anderen Module je nach Auswahl
      const active = new Set(["pumpe"]);
      kit.querySelectorAll("[data-module]:checked").forEach((i) => active.add(i.dataset.module));
      modules.forEach((m) => m.classList.toggle("is-on", [...active].some((a) => m.classList.contains(`kit__mod--${a}`))));
      kitStatus.textContent = "";
      return sel;
    };

    const topicFor = (sel) => {
      if (sel.tank[0]?.startsWith("ohne")) return "motor-pumpe";
      if (sel.aufgabe.length && !sel.aufgabe.includes("Druckölversorgung")) return "kuehlmodul";
      return "aggregat";
    };

    kit.addEventListener("change", render);
    render();

    d.querySelector("[data-kit-apply]").addEventListener("click", () => {
      const sel = render();
      const text = [
        "Meine Auswahl aus dem ITB-Baukasten:",
        ...ROWS.map(([name, label]) => `- ${label}: ${sel[name].length ? sel[name].join(", ") : "offen"}`),
        "",
        "Falls bekannt: Menge ___ l/min, Druck ___ bar, Temperatur ___ °C, Stückzahl ___",
      ].join("\n");
      form.elements.nachricht.value = form.elements.nachricht.value.replace(/Meine Auswahl aus dem ITB-Baukasten:[\s\S]*?Stückzahl ___/, "").trim();
      prefill(topicFor(sel), text);
      kitStatus.textContent = "Übernommen – weiter geht es im Anfrageformular.";
      const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
      d.getElementById("kontakt").scrollIntoView({ behavior: reduce ? "auto" : "smooth" });
      form.elements.name.focus({ preventScroll: true });
    });
  }

  window.ITB = { prefill };
})();

// Beim Drucken alle FAQ-Antworten aufklappen
window.addEventListener('beforeprint', function () {
  document.querySelectorAll('.pp-faq details').forEach(function (d) { d.open = true; });
});
