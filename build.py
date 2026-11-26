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

# Alte URLs der bisherigen Website -> neue Sprungziele (Weiterleitungs-Stubs)
OLD_URLS = {
    "index.htm": "./",
    "plattenwaermetauscher.html": "./#waermetauscher",
    "hydraulikaggregate.html": "./#aggregate",
    "kontakt.html": "./#kontakt",
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
    urls = "".join(f"  <url><loc>{DOMAIN}/{p}</loc></url>\n" for p in ("", "impressum.html", "datenschutz.html"))
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
