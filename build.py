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
# Social-Vorschaubild (WhatsApp, Mail, LinkedIn) braucht eine absolute, erreichbare URL.
# Solange die Entwürfe auf GitHub Pages liegen, zeigt sie dorthin; nach dem Go-live auf DOMAIN umstellen.
OG_BASE = "https://lennertdockweiler.github.io/itb-hydraulik-relaunch/{variant}"  # [[ERSETZEN beim Go-live: DOMAIN]]


def og_image_tags(variant: str) -> str:
    url = OG_BASE.format(variant=variant) + "/assets/og.jpg"
    return (f'<meta property="og:image" content="{url}">\n'
            '<meta property="og:image:width" content="1200">\n'
            '<meta property="og:image:height" content="630">\n'
            '<meta property="og:image:alt" content="ITB Industrie Technik Briechle, Radolfzell – Hydraulikaggregat">\n'
            '<meta name="twitter:card" content="summary_large_image">')

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

# Häufige Fragen je Produktseite: sichtbar als <details> und als FAQPage-JSON-LD.
FAQ = {
    "plattenwaermetauscher.html": [
        ("Welche Angaben brauchen Sie für die Auslegung eines Plattenwärmetauschers?",
         "Die beiden Medien (z. B. Hydrauliköl und Kühlwasser), deren Volumenströme, Ein- und Austrittstemperaturen oder die abzuführende Leistung in kW, den zulässigen Druckverlust und den Betriebsdruck. Fehlt etwas, schätzen wir es mit Ihnen gemeinsam ab."),
        ("Gelöteter oder gedichteter Plattenwärmetauscher – was ist der Unterschied?",
         "Gelötete Plattenwärmetauscher kommen ohne Dichtungen aus. Sie sind deshalb sehr kompakt, druck- und temperaturfest und wartungsarm. Gedichtete Geräte lassen sich zerlegen und mechanisch reinigen, sind aber größer. Für Öl- und Wasserkreisläufe im Maschinenbau ist die gelötete Bauform meist die wirtschaftlichere Wahl."),
        ("Kann man einen gelöteten Plattenwärmetauscher reinigen?",
         "Ja, durch Spülen mit einem geeigneten Reinigungsmittel, idealerweise entgegen der normalen Strömungsrichtung. Ein vorgeschalteter Filter verhindert, dass sich die engen Kanäle überhaupt erst zusetzen."),
        ("Welchen Plattenwärmetauscher brauche ich für ein Schwimmbad?",
         "Für chloridhaltiges Beckenwasser bieten wir den Typ XCR an. Er ist nickelgelötet und aus dem Edelstahl 1.4547 (SMO 254) gefertigt, der deutlich korrosionsbeständiger ist als Standard-Edelstahl."),
    ],
    "waermetauscher-kuehler.html": [
        ("Luftkühler oder wassergekühlter Wärmetauscher – was ist besser?",
         "Ein Luft-Ölkühler braucht kein Kühlwasser, aber Platz und einen freien Luftstrom. Seine Leistung hängt von der Umgebungstemperatur ab. Ein wassergekühlter Wärmetauscher ist kompakter und leistungsstärker, setzt aber einen Kühlwasserkreis voraus. Ist Kühlwasser vorhanden, ist er meist die erste Wahl."),
        ("Wann ist ein Rohrbündel-Wärmetauscher sinnvoll?",
         "Bei verschmutzten Medien, sehr großen Volumenströmen oder Seewasser. Die Rohre lassen sich mechanisch reinigen. Für Schiffe gibt es Marine-Ausführungen aus seewasserbeständigen Werkstoffen."),
        ("Woran merke ich, dass meine Anlage einen Ölkühler braucht?",
         "Steigt die Öltemperatur im Betrieb dauerhaft deutlich über den Bereich, den der Öl- und Komponentenhersteller empfiehlt, altert das Öl schneller und Dichtungen leiden. Ein typisches Zeichen ist, dass die Maschine nach längerer Laufzeit träger oder lauter wird. Wir berechnen, welche Kühlleistung nötig ist."),
    ],
    "hydraulikaggregate.html": [
        ("Bauen Sie auch einzelne Hydraulikaggregate?",
         "Ja. Durch unseren Baukasten lohnt sich auch ein Einzelstück – genauso wie eine Serie."),
        ("Welche Angaben brauchen Sie für ein Angebot?",
         "Benötigter Druck und Fördermenge, wie lange und wie oft das Aggregat läuft, Ihre Stromversorgung, den verfügbaren Einbauraum und welche Bewegungen gesteuert werden sollen. Ein vorhandener Schaltplan hilft – ist aber keine Voraussetzung."),
        ("Kann ich ein vorhandenes Aggregat nachbauen oder ersetzen lassen?",
         "In vielen Fällen ja. Schicken Sie uns Fotos vom Typenschild und vom Aggregat, wenn möglich auch den Schaltplan. Wir prüfen, ob ein Nachbau oder eine verbesserte Ausführung sinnvoll ist."),
        ("Wird das Aggregat einbaufertig geliefert?",
         "Ja. Das Aggregat wird montiert, geprüft und mit Dokumentation ausgeliefert."),
    ],
    "kuehl-filtermodule.html": [
        ("Wozu ein separates Kühl- und Filtermodul?",
         "Ein eigener Kühl- und Filterkreislauf (Nebenstrom) arbeitet unabhängig vom Arbeitskreis der Maschine. Das Öl wird so gleichmäßig gekühlt und gefiltert – auch dann, wenn die Maschine gerade wenig leistet. Zudem lassen sich feinere Filter einsetzen."),
        ("Was bedeutet Filterfeinheit 3 µm?",
         "Der Filter hält Partikel ab etwa 3 Mikrometern zurück, das ist rund ein Zwanzigstel eines Haares. Feinere Filtration schützt Pumpen und Ventile besser, erhöht aber den Druckverlust. Die passende Feinheit legen wir nach Ihren Komponenten aus."),
        ("Gibt es die Module auch für 12 oder 24 Volt?",
         "Ja, neben Wechsel- und Drehstrom gibt es Ausführungen mit Gleichstromantrieb – etwa für Fahrzeuge und mobile Maschinen."),
    ],
    "motor-pumpen-kombinationen.html": [
        ("Was ist eine Motor-Pumpen-Kombination?",
         "Elektromotor und Hydraulikpumpe, die über Pumpenträger und Kupplung fertig miteinander verbunden und ausgerichtet sind. Sie bauen die Einheit nur noch ein und schließen sie an."),
        ("Wann lohnt sich ein bürstenloser Gleichstromantrieb?",
         "Überall dort, wo Batterie- oder Bordspannung von 12, 24 oder 48 V zur Verfügung steht, etwa in Fahrzeugen und mobilen Geräten. Bürstenlose Motoren sind wartungsarm und erreichen über 40.000 Betriebsstunden."),
        ("Wie wähle ich die richtige Motorleistung?",
         "Die Leistung ergibt sich vor allem aus Druck und Fördermenge. Als grobe Faustformel gilt: Leistung in kW ≈ Druck in bar × Fördermenge in l/min ÷ 600, dazu ein Zuschlag für den Wirkungsgrad. Die genaue Auslegung übernehmen wir."),
    ],
    "komponenten.html": [
        ("Welche Angaben brauchen Sie, um ein Ersatzteil zu finden?",
         "Am wichtigsten ist das Typenschild: Hersteller, Typbezeichnung und Seriennummer. Ein Foto des eingebauten Teils hilft zusätzlich bei Anschlüssen und Maßen."),
        ("Liefern Sie nur das Originalteil?",
         "Wir prüfen beides: ob das Originalteil verfügbar ist und ob es einen gleichwertigen Ersatz gibt. Sie entscheiden dann mit unserem Angebot."),
        ("Welche Pumpe passt zu meiner Anwendung?",
         "Das hängt von Druck, Fördermenge, Medium und Geräuschanforderung ab. Die Tabelle oben gibt eine erste Orientierung – die Auslegung übernehmen wir gern für Sie."),
    ],
}


# Dativ für „Fragen zu …?“ – die Kurznamen stehen im Nominativ
DATIVE = {
    "produkte.html": "unseren Produkten",
    "plattenwaermetauscher.html": "Plattenwärmetauschern",
    "waermetauscher-kuehler.html": "Wärmetauschern & Kühlern",
    "hydraulikaggregate.html": "Hydraulikaggregaten",
    "kuehl-filtermodule.html": "Kühl- & Filtermodulen",
    "motor-pumpen-kombinationen.html": "Motor-Pumpen-Kombinationen",
    "komponenten.html": "Komponenten & Ersatzteilen",
}


def product_extras(file: str) -> str:
    """Datenblätter, Ansprechpartner-CTA und verwandte Produkte unter jeder Produktseite."""
    from urllib.parse import quote
    _, _, name, docs = PRODUCTS[file]
    parts = []
    if file in FAQ:
        qa = "\n".join(
            f'    <details class="pp-faq__item"><summary>{esc(q)}</summary><p>{esc(a)}</p></details>'
            for q, a in FAQ[file])
        parts.append('<section class="pp-section pp-faq" aria-labelledby="pp-faq-title">\n'
                     '  <h2 id="pp-faq-title">Häufige Fragen</h2>\n' + qa + '\n</section>')
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
    <h2 id="pp-cta-title">Fragen zu {esc(DATIVE.get(file, name))}?</h2>
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


def faq_ld(pairs) -> str:
    import json
    data = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in pairs]}
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False).replace("</", "<\\/") + "</script>"


def faq_jsonld(file: str) -> str:
    return faq_ld(FAQ[file]) if file in FAQ else ""


def index_faq_jsonld(html: str) -> str:
    """FAQPage-Daten aus den sichtbaren <details>-Fragen der Startseite ableiten – eine Quelle, kein Doppelpflegen."""
    import html as h
    def text(fragment: str) -> str:
        return h.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", fragment))).strip()
    pairs = [(text(q), text(a)) for q, a in re.findall(r"<details[^>]*>\s*<summary[^>]*>(.*?)</summary>(.*?)</details>", html, re.S)]
    return faq_ld(pairs) if pairs else ""


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
<!-- og-image -->
{head}
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{items}]}}</script>
{faq_jsonld(file)}
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

    index = expand((src / "index.html").read_text(encoding="utf-8")).replace("<!-- og-image -->", og_image_tags(name))
    index = index.replace("</head>", index_faq_jsonld(index) + "\n</head>", 1)
    css = (src / "style.css").read_text(encoding="utf-8")
    (out / "index.html").write_text(index, encoding="utf-8")
    (out / "style.css").write_text(css, encoding="utf-8")

    head, header, footer = (between(index, n) for n in ("head", "header", "footer"))
    theme = re.search(r'name="theme-color" content="([^"]+)"', index).group(1)
    body_class = re.search(r'<body class="([^"]*)"', index).group(1)
    for file in LEGAL_PAGES:
        (out / file).write_text(legal_page(file, head, header, footer, theme, body_class), encoding="utf-8")
    for file in PRODUCTS:
        page = expand(product_page(file, head, header, footer, theme, body_class))
        (out / file).write_text(page.replace("<!-- og-image -->", og_image_tags(name)), encoding="utf-8")
    for old, target in OLD_URLS.items():
        (out / old).write_text(redirect_stub(target), encoding="utf-8")

    # Nur die Schriften kopieren, die das Stylesheet wirklich nutzt
    for font in set(re.findall(r"assets/fonts/([\w.-]+\.woff2)", css)):
        shutil.copy(SHARED / "fonts" / font, out / "assets" / "fonts" / font)
    shutil.copytree(SHARED / "img", out / "assets" / "img")
    shutil.copy(SHARED / "main.js", out / "assets" / "main.js")
    shutil.copy(SHARED / "components.css", out / "assets" / "components.css")
    if (src / "og.jpg").exists():
        shutil.copy(src / "og.jpg", out / "assets" / "og.jpg")
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
