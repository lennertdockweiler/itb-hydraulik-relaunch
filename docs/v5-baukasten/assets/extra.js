/* ITB Variante 5 – Baukasten-Konfigurator
 * Zeigt die Auswahl als Stückliste, hebt die Module im Stapel hervor
 * und übernimmt alles ins Anfrageformular. */
(() => {
  const kit = document.querySelector("[data-kit]");
  if (!kit) return;
  const bom = document.querySelector("[data-bom]");
  const modules = document.querySelectorAll(".mod");
  const ROWS = [
    ["aufgabe", "Aufgabe"],
    ["medium", "Medium"],
    ["pumpe", "Pumpe"],
    ["antrieb", "Antrieb"],
    ["tank", "Tank"],
    ["zubehoer", "Zubehör"],
  ];

  const selection = () => Object.fromEntries(ROWS.map(([name]) => [
    name,
    [...kit.querySelectorAll(`[name="${name}"]:checked`)].map((i) => i.value),
  ]));

  const render = () => {
    const sel = selection();
    bom.replaceChildren(...ROWS.flatMap(([name, label]) => {
      const dt = document.createElement("dt");
      const dd = document.createElement("dd");
      dt.textContent = label;
      dd.textContent = sel[name].length ? sel[name].join(", ") : "–";
      return [dt, dd];
    }));
    // Pumpe + Motor gehören immer dazu, alle anderen Module je nach Auswahl
    const active = new Set(["pumpe"]);
    kit.querySelectorAll("[data-module]:checked").forEach((i) => active.add(i.dataset.module));
    modules.forEach((m) => m.classList.toggle("is-on", [...active].some((a) => m.classList.contains(`mod--${a}`))));
    return sel;
  };

  const topicFor = (sel) => {
    if (sel.tank[0]?.startsWith("ohne")) return "motor-pumpe";
    const tasks = sel.aufgabe;
    if (tasks.length && !tasks.includes("Druckölversorgung")) return "kuehlmodul";
    return "aggregat";
  };

  kit.addEventListener("change", render);
  render();

  document.querySelector("[data-kit-apply]").addEventListener("click", () => {
    const sel = render();
    const lines = ROWS.map(([name, label]) => `- ${label}: ${sel[name].length ? sel[name].join(", ") : "offen"}`);
    const text = [
      "Konfiguration aus dem ITB-Baukasten:",
      ...lines,
      "",
      "Betriebsdaten: Volumenstrom ___ l/min, Betriebsdruck ___ bar, Temperaturen ___ °C, Stückzahl ___",
    ].join("\n");
    const form = document.querySelector("[data-inquiry]");
    const message = form.elements.nachricht;
    form.elements.anliegen.value = topicFor(sel);
    message.value = message.value.trim() ? `${message.value.trim()}\n\n${text}` : text;
    document.getElementById("kontakt").scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
    message.focus({ preventScroll: true });
  });
})();
