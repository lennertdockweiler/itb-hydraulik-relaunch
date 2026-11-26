/* ITB Variante 4 – Thermometer-Skala: kühlt beim Scrollen von 200 °C auf 20 °C ab (rein dekorativ) */
(() => {
  const root = document.documentElement;
  const value = document.querySelector("[data-thermo-value]");
  if (!value) return;
  const MAX = 200, MIN = 20;
  let ticking = false;
  const update = () => {
    const scrollable = root.scrollHeight - innerHeight;
    const progress = scrollable > 0 ? Math.min(1, Math.max(0, scrollY / scrollable)) : 0;
    root.style.setProperty("--heat", (1 - progress).toFixed(3));
    value.textContent = `${Math.round(MAX - progress * (MAX - MIN))} °C`;
    ticking = false;
  };
  addEventListener("scroll", () => { if (!ticking) { ticking = true; requestAnimationFrame(update); } }, { passive: true });
  addEventListener("resize", update);
  update();
})();
