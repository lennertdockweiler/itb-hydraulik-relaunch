#!/usr/bin/env python3
"""
ITB-Relaunch – Build-Skript für alle Design-Varianten.

Quelle:  src/<variante>/index.html + style.css (+ optional extra.js)
         src/shared/  (Formular, Rechtstexte, Schriften, Bilder, main.js)
Ausgabe: docs/<variante>/  – jeweils eine eigenständige, direkt hostbare Website
         docs/index.html   – Übersicht aller Varianten (GitHub-Pages-Vorschau)

Platzhalter im Quelltext:
  <!-- include:NAME -->   fügt src/shared/partials/NAME.html ein
  <!-- header:start/end --> und <!-- footer:start/end -->
                          markieren Kopf- und Fußbereich, die 1:1 in Impressum,
                          Datenschutz und 404 übernommen werden.
  <!-- head:start/end -->   gemeinsame <head>-Einträge (Schriften, CSS, Icons)

Aufruf: python3 build.py
"""
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "src"
SHARED = SRC / "shared"
OUT = ROOT / "docs"
DOMAIN = "https://itb-hydraulik.com"

VARIANTS = ["v1-datenblatt", "v2-kreislauf", "v3-editorial", "v4-werkhalle", "v5-baukasten"]

# Alte URLs der bisherigen Website -> neue Sprungziele (Weiterleitungs-Stubs).
# plattenwaermetauscher.html und hydraulikaggregate.html sind wieder echte Produktseiten.
OLD_URLS = {
    "index.htm": "./",
    "kontakt.html": "./#kontakt",
}

# Produktseiten: Datei -> (Titel, Description, Kurzname, Datenblätter)
PRODUCTS = {
    "produkte.html": ("Produkte: Wärmetauscher, Hydraulikaggregate, Komponenten",
        "Plattenwärmetauscher, Rohrbündel- und Luftkühler, Hydraulikaggregate, Kühl- und Filtermodule, Motor-Pumpen-Kombinationen und Komponenten von ITB Radolfzell.",
        "Produkte", []),
    "plattenwaermetauscher.html": ("Gelötete Edelstahl-Plattenwärmetauscher bis 55 bar & 200 °C",
        "Gelötete Plattenwärmetauscher WP, NP, GBS, GBH, GNS: bis 55 bar, 200 °C, Flansch bis DN 100, Bauformen X, Z, U, DW, DUO, Schwimmbad-Typ XCR. Auslegung durch ITB.",
        "Plattenwärmetauscher",
        ["Übersicht gelötete Plattenwärmetauscher (PLWT)", "Maßblätter Baureihe WP", "Maßblätter Baureihe GBS", "Schwimmbad-Ausführung Typ XCR", "Leistungs- und Druckverlustdiagramme"]),
    "waermetauscher-kuehler.html": ("Rohrbündel-Wärmetauscher, Luft-Ölkühler, Ladeluftkühler",
        "Rohrbündel-, Marine- und Stationär-Wärmetauscher, Ladeluft- und Abgas-Wärmetauscher, Luft-Öl- und Luft-Wasserkühler, Kompakt-Durchlauferhitzer von ITB.",
        "Wärmetauscher & Kühler",
        ["Rohrbündel-Wärmetauscher", "Luft-Ölkühler (u. a. LKE6)", "Luft-Wasserkühler", "Ladeluft- und Abgas-Wärmetauscher"]),
    "hydraulikaggregate.html": ("Hydraulikaggregate bis über 300 bar – ab Stückzahl 1",
        "Hydraulikaggregate aus dem ITB-Baukasten: Tank, Pumpe, Motor, Ventilblock, Filter. Bis über 300 bar, 0,12–22 kW, montiert, geprüft, dokumentiert – auch als Einzelstück.",
        "Hydraulikaggregate",
        ["Baukasten-Übersicht Hydraulikaggregate", "Beispiel-Hydraulikschaltplan", "Fragebogen zur Aggregat-Auslegung"]),
    "kuehl-filtermodule.html": ("Kühl-, Filter- und Schmiermodule für Öl & Wasser-Glykol",
        "Einbaufertige Kühl-, Filter- und Schmiermodule von ITB: mit Plattenwärmetauscher, Filtration bis 3 µm, Tanks von 6,5 bis 100 l, AC- und DC-Antrieb.",
        "Kühl- & Filtermodule",
        ["Übersicht Kühl- und Filtermodule", "Fragebogen zur Kühlmodul-Auslegung"]),
    "motor-pumpen-kombinationen.html": ("Motor-Pumpen-Kombinationen AC 0,12–22 kW & DC 12–48 V",
        "Motor-Pumpen-Kombinationen von ITB: Normmotoren 230/400 V bis ca. 22 kW oder bürstenlos DC 12/24/48 V, bis über 300 bar, über 40.000 h Lebensdauer, bis IP68.",
        "Motor-Pumpen-Kombinationen",
        ["Motor-Pumpen-Kombinationen AC", "Motor-Pumpen-Kombinationen DC mit Ansteuerelektronik"]),
    "komponenten.html": ("Hydraulik-Komponenten & Ersatzteile: Pumpen, Filter, Schalter",
        "Zahnrad-, Axialkolben-, Flügelzellen- und Schraubenspindelpumpen, Filter, Niveau- und Druckschalter einzeln – und Ersatz für vorhandene Geräte. ITB Radolfzell.",
        "Komponenten & Ersatz",
        ["Pumpen-Übersicht", "Filter und Zubehör"]),
}

LEGAL_PAGES = {
    "impressum.html": ("Impressum", "Impressum der ITB Industrie Technik Briechle, Radolfzell."),
    "datenschutz.html": ("Datenschutzerklärung", "Datenschutzerklärung der ITB Industrie Technik Briechle."),
    "404.html": ("Seite nicht gefunden", "Diese Seite gibt es nicht (mehr)."),
}


def partial(name: str) -> str:
    return (SHARED / "partials" / f"{name}.html").read_text(encoding="utf-8").strip()


def expand(html: str) -> str:
    return re.sub(r"<!-- include:([\w-]+) -->", lambda m: partial(m.group(1)), html)


def between(html: str, name: str) -> str:
    m = re.search(rf"<!-- {name}:start -->(.*?)<!-- {name}:end -->", html, re.S)
    if not m:
        raise SystemExit(f"Marker '{name}' fehlt")
    return m.group(1).strip()


def legal_page(file: str, head: str, header: str, footer: str, theme: str, body_class: str) -> str:
    title, desc = LEGAL_PAGES[file]
    content = partial(file.replace(".html", ""))
    # Vorschau-noindex steckt im gemeinsamen head-Block; 404 bleibt auch live noindex
    robots = '\n<meta name="robots" content="noindex">' if file == "404.html" else ""
    canonical = "" if file == "404.html" else f'\n<link rel="canonical" href="{DOMAIN}/{file}">'
    return f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} – ITB Industrie Technik Briechle</title>
<meta name="description" content="{desc}">{robots}{canonical}
<meta name="theme-color" content="{theme}">
{head}
</head>
<body class="{body_class} page-legal">
<a class="skip-link" href="#inhalt">Zum Inhalt springen</a>
{header}
<main id="inhalt" class="legal">
<div class="legal__inner">
{content}
</div>
</main>
{footer}
<script src="assets/main.js" defer></script>
</body>
</html>
"""


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace('"', "&quot;")


def product_extras(file: str) -> str:
    """Datenblätter, Ansprechpartner-CTA und verwandte Produkte unter jeder Produktseite."""
    from urllib.parse import quote
    _, _, name, docs = PRODUCTS[file]
    parts = []
    if docs:
        items = []
        for doc in docs:
            msg = quote(f"Bitte senden Sie mir das Datenblatt: {doc}")
            items.append(
                f'    <li class="pp-doc"><span class="pp-doc__icon" aria-hidden="true">PDF</span>'
                f'<span class="pp-doc__name">{esc(doc)}<small>Download folgt – bis dahin schicken wir es Ihnen gern zu</small></span>'
                f'<a class="pp-doc__get" href="./?anliegen=datenblatt&amp;nachricht={msg}#kontakt">Anfordern<span class="visually-hidden">: {esc(doc)}</span></a>'
                f'<!-- [[ERSETZEN: PDF unter assets/docs/ ablegen und hier als Download verlinken]] --></li>'
            )
        parts.append('<section class="pp-section pp-docs" id="datenblaetter" aria-labelledby="pp-docs-title">\n'
                     '  <h2 id="pp-docs-title">Datenblätter &amp; Downloads</h2>\n'
                     '  <ul class="pp-doclist">\n' + "\n".join(items) + '\n  </ul>\n</section>')
    parts.append(f"""<section class="pp-cta" aria-labelledby="pp-cta-title">
  <div>
    <h2 id="pp-cta-title">Fragen zu {esc(name)}?</h2>
    <p>Beschreiben Sie Ihre Anwendung in ein paar Stichworten oder rufen Sie an – wir legen aus und schicken Ihnen ein Angebot.</p>
    <div class="pp-actions">
      <a class="btn btn--primary" href="./#kontakt">Anfrage stellen</a>
      <a class="pp-link" href="./#baukasten">Im Baukasten zusammenstellen</a>
    </div>
  </div>
  {partial("contact-person")}
</section>""")
    others = [f for f in PRODUCTS if f not in (file, "produkte.html")][:6]
    links = "\n".join(f'    <li><a href="{f}">{esc(PRODUCTS[f][2])}</a></li>' for f in others)
    parts.append(f'<nav class="pp-related" aria-label="Weitere Produkte">\n  <h2>Weitere Produkte</h2>\n  <ul>\n{links}\n  </ul>\n</nav>')
    return "\n\n".join(parts)


def product_page(file: str, head: str, header: str, footer: str, theme: str, body_class: str) -> str:
    title, desc, name, _ = PRODUCTS[file]
    content = (SHARED / "products" / file).read_text(encoding="utf-8").strip()
    crumbs = [("Start", f"{DOMAIN}/")]
    if file != "produkte.html":
        crumbs.append(("Produkte", f"{DOMAIN}/produkte.html"))
    crumbs.append((name, f"{DOMAIN}/{file}"))
    items = ",".join(
        f'{{"@type":"ListItem","position":{i},"name":"{n}","item":"{u}"}}' for i, (n, u) in enumerate(crumbs, 1)
    )
    header = header.replace('href="produkte.html"', 'href="produkte.html" aria-current="page"')
    return f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} – ITB Radolfzell</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{DOMAIN}/{file}">
<meta name="theme-color" content="{theme}">
<meta property="og:type" content="website">
<meta property="og:locale" content="de_DE">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{DOMAIN}/{file}">
{head}
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{items}]}}</script>
</head>
<body class="{body_class} page-product">
<a class="skip-link" href="#inhalt">Zum Inhalt springen</a>
{header}
<main id="inhalt" class="pp">
<div class="pp__inner">
{content}

{product_extras(file)}
</div>
</main>
{footer}
<script src="assets/main.js" defer></script>
</body>
</html>
"""


def redirect_stub(target: str) -> str:
    return f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8"><title>Weiterleitung – ITB</title>
<meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0; url={target}">
<link rel="canonical" href="{DOMAIN}/{target.lstrip('./')}">
</head><body><p>Diese Seite ist umgezogen: <a href="{target}">weiter zur neuen Seite</a>.</p></body></html>
"""


def build_variant(name: str) -> None:
    src = SRC / name
    out = OUT / name
    if out.exists():
        shutil.rmtree(out)
    (out / "assets" / "fonts").mkdir(parents=True)

    index = expand((src / "index.html").read_text(encoding="utf-8"))
    css = (src / "style.css").read_text(encoding="utf-8")
    (out / "index.html").write_text(index, encoding="utf-8")
    (out / "style.css").write_text(css, encoding="utf-8")

    head, header, footer = (between(index, n) for n in ("head", "header", "footer"))
    theme = re.search(r'name="theme-color" content="([^"]+)"', index).group(1)
    body_class = re.search(r'<body class="([^"]*)"', index).group(1)
    for file in LEGAL_PAGES:
        (out / file).write_text(legal_page(file, head, header, footer, theme, body_class), encoding="utf-8")
    for file in PRODUCTS:
        (out / file).write_text(expand(product_page(file, head, header, footer, theme, body_class)), encoding="utf-8")
    for old, target in OLD_URLS.items():
        (out / old).write_text(redirect_stub(target), encoding="utf-8")

    # Nur die Schriften kopieren, die das Stylesheet wirklich nutzt
    for font in set(re.findall(r"assets/fonts/([\w.-]+\.woff2)", css)):
        shutil.copy(SHARED / "fonts" / font, out / "assets" / "fonts" / font)
    shutil.copytree(SHARED / "img", out / "assets" / "img")
    shutil.copy(SHARED / "main.js", out / "assets" / "main.js")
    shutil.copy(SHARED / "components.css", out / "assets" / "components.css")
    if (src / "extra.js").exists():
        shutil.copy(src / "extra.js", out / "assets" / "extra.js")
    for icon in ("favicon.svg", "favicon-32.png", "apple-touch-icon.png"):
        if (SHARED / icon).exists():
            shutil.copy(SHARED / icon, out / icon)

    (out / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {DOMAIN}/sitemap.xml\n", encoding="utf-8")
    urls = "".join(f"  <url><loc>{DOMAIN}/{p}</loc></url>\n" for p in ("", *PRODUCTS, "impressum.html", "datenschutz.html"))
    (out / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n',
        encoding="utf-8",
    )
    print(f"✓ {name}")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    for name in VARIANTS:
        build_variant(name)
    shutil.copy(SRC / "overview.html", OUT / "index.html")
    # GitHub Pages nutzt nur die 404.html im Wurzelordner
    shutil.copy(SRC / "root-404.html", OUT / "404.html")
    (OUT / ".nojekyll").write_text("")
    print("✓ Übersicht docs/index.html")


if __name__ == "__main__":
    main()
