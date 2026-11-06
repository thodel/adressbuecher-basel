"""90_erstblick.py — Kontrollansicht der Welle-2-Daten als statische Seite (GitHub Pages).

    python scripts/90_erstblick.py --out web/index.html

Liest data/csv/04_entries.csv, 04_berufe.csv, 05_buildings.csv, 05_residents.csv,
05_buildings_geo.csv (was vorhanden ist) sowie data/review/flags.csv und bettet alles als JSON in eine Seite
mit Reitern, Volltextfilter, Bandfilter und **Flagging je Zeile** ein:

- Ein Flag (Grund + Notiz) wird im Browser gespeichert (localStorage) und als CSV
  exportiert (Download auf Pages; Zwischenablage, wo der Download gesperrt ist).
  `scripts/91_merge_flags.py` mischt den Export nach `data/review/flags.csv`; die Seite
  zeigt diese Flags beim nächsten Bau als «gemeldet».
- Je Zeile ein Link, der ein vorausgefülltes GitHub-Issue öffnet (Repo-URL unten).

Kein Server, keine externen Daten; die Seitenbilder (Staatsarchiv Basel-Stadt, gemeinfrei)
sind nicht eingebettet, dafür verweist jede Zeile auf die Seite im Digitalen Lesesaal; die
Verortung verweist auf das HGB-Dossier im Archivkatalog (ld.bs.ch).
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path

CSV_DIR = Path("data/csv")
REVIEW = Path("data/review/flags.csv")
REPO_URL = "https://github.com/thodel/adressbuecher-basel"
DLS = {"1841": "https://dls.staatsarchiv.bs.ch/records/1225921", "1850": "https://dls.staatsarchiv.bs.ch/records/1225925",
       "1862": "https://dls.staatsarchiv.bs.ch/records/1225927"}

TABS = [
    ("einwohner", "Einwohner", ["04_entries.csv"], "entry_id",
     ["entry_id", "volume", "page", "owner_flag", "surname", "alliance_name", "maiden_name", "forename",
      "civil_status", "relation", "occupation_raw", "origin_raw", "street_raw", "building_no",
      "building_no_system", "city_part", "address_role", "heading", "entry_type", "parse_confidence", "residual", "text"]),
    ("gebaeude", "Gebäude", ["05_buildings.csv"], "building_id",
     ["building_id", "volume", "page", "building_nos", "marker", "house_no_old", "quarter", "house_name",
      "city_part", "street_raw", "owner_text", "building_type", "owner_same_as_prev", "parse_confidence", "note"]),
    ("bewohner", "Bewohner", ["05_residents.csv"], "entry_id",
     ["entry_id", "volume", "page", "building_no", "surname", "alliance_name", "maiden_name", "forename",
      "civil_status", "relation", "occupation_raw", "origin_raw", "parse_confidence", "residual", "text"]),
    ("berufe", "Berufe", ["04_berufe.csv"], "entry_id",
     ["entry_id", "volume", "page", "heading", "surname", "alliance_name", "forename", "occupation_raw",
      "street_raw", "building_no", "entry_type", "parse_confidence", "residual", "text"]),
    ("telefon", "Telefonbuch", ["20_phonebook_links.csv"], "pb_id",
     ["pb_id", "year", "batch", "surname", "alliance_name", "forename", "occupation_raw", "street_raw",
      "building_no", "entry_type", "match_level", "n_refs", "match_refs", "parse_confidence"]),
    ("geo", "Verortung", ["05_buildings_geo.csv"], "building_id",
     ["building_id", "volume", "street_raw", "building_no", "house_no_old", "space", "match_method",
      "n_candidates", "dossier_id", "dossier_title", "check_old_no", "geo_confidence", "lat", "lon"]),
]

LABELS = {"entry_id": "ID", "building_id": "ID", "volume": "Band", "page": "PDF-S.", "owner_flag": "*",
          "building_no_system": "Nr.-System", "city_part": "Stadtteil", "house_no_old": "alte Nr.", "quarter": "Quartier",
          "house_name": "Hausname", "space": "Nummernraum", "match_method": "Methode", "n_candidates": "Dossiers",
          "dossier_id": "HGB-Dossier", "dossier_title": "Adresse 1862 (HGB)", "check_old_no": "alte Nr. ✓",
          "geo_confidence": "Geo-Konf.", "lat": "Lat", "lon": "Lon", "pb_id": "ID", "year": "Jahr", "batch": "Batch",
          "match_level": "Treffer 1862", "n_refs": "Anz.", "match_refs": "Einträge 1862",
          "surname": "Name", "alliance_name": "Allianz", "maiden_name": "geb.", "forename": "Vorname",
          "civil_status": "Stand", "relation": "Bezug", "occupation_raw": "Beruf", "origin_raw": "Heimatort",
          "origin_canton": "Kt.", "street_raw": "Strasse", "building_no": "Nr.", "address_role": "Adressrolle",
          "phone_flag": "Tel.", "entry_type": "Typ", "parse_confidence": "Konfidenz", "residual": "Rest/Notiz",
          "text": "ATR-Zeile", "building_nos": "Nr.", "marker": "Marke", "owner_text": "Eigentümer",
          "building_type": "Gebäudeart", "owner_same_as_prev": "Ditto", "note": "Notiz", "heading": "Rubrik"}

REASONS = ["ATR-Lesefehler", "Parser: Feld falsch", "Parser: Eintrag falsch getrennt", "Abschnitt/Rubrik falsch",
           "Quelle: Druckfehler", "Dublette", "Anderes"]


def load(files: list[str], cols: list[str]) -> list[list[str]]:
    rows = []
    for f in files:
        p = CSV_DIR / f
        if not p.exists():
            continue
        with p.open(encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if f.startswith("20_") and r.get("match_level") not in ("name_addr", "name_street"):
                    continue                                   # Telefon-Reiter: nur Namenstreffer
                row = [r.get(c, "") for c in cols]
                if cols[0] == "entry_id" and r.get("address_seq") and r["address_seq"] not in ("", "1"):
                    row[0] = f"{row[0]}#{r['address_seq']}"
                rows.append(row)
    return rows


GEO_DIR = Path("data/geo")


def analyses(data: dict) -> dict:
    """Kennzahlen aus den CSV, reproduzierbar beim Bau der Seite."""
    from collections import Counter, defaultdict
    out = {"bands": sorted({r[1] for k in data for r in data[k]["rows"]})}
    counts = {k: Counter(r[1] for r in data[k]["rows"]) for k in data if k != "geo"}
    out["counts"] = {k: {b: counts[k].get(b, 0) for b in out["bands"]} for k in counts}
    # Berufe je Band: roh (keine Normalisierung vorhanden), Schlusspunkt weg, aus Einwohner + Bewohner
    occ = defaultdict(Counter)
    for k in ("einwohner", "bewohner"):
        if k not in data:
            continue
        ci = data[k]["cols"].index("occupation_raw")
        for r in data[k]["rows"]:
            o = (r[ci] or "").strip().rstrip(".")
            if o:
                occ[r[1]][o] += 1
    out["occupations"] = {b: occ[b].most_common(25) for b in out["bands"]}
    out["occupations_total"] = {b: sum(occ[b].values()) for b in out["bands"]}
    # Bewohner je Gebäude
    if "bewohner" in data and "gebaeude" in data:
        bi = data["bewohner"]["cols"].index("building_no"); per = defaultdict(Counter)
        res_by_b = defaultdict(int)
        for r in data["bewohner"]["rows"]:
            res_by_b[(r[1], r[0].rsplit("-", 2)[0], r[bi])] += 1
        # genauer über building_id der Bewohner-CSV
        res_ids = Counter()
        with (CSV_DIR / "05_residents.csv").open(encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                res_ids[r["building_id"]] += 1
        dist = defaultdict(Counter)
        for r in data["gebaeude"]["rows"]:
            n = res_ids.get(r[0], 0)
            dist[r[1]]["6+" if n >= 6 else str(n)] += 1
        out["residents_per_building"] = {b: {c: dist[b].get(c, 0) for c in ("0", "1", "2", "3", "4", "5", "6+")} for b in out["bands"]}
    # Strassen nach Einträgen (Register 1841/1862; 1850 aus dem Nummernbuch, das Register nennt keine Strasse)
    streets = defaultdict(Counter)
    si = data["einwohner"]["cols"].index("street_raw")
    for r in data["einwohner"]["rows"]:
        if r[si]:
            streets[r[1]][r[si].rstrip(".")] += 1
    if "gebaeude" in data:
        gi = data["gebaeude"]["cols"].index("street_raw")
        for r in data["gebaeude"]["rows"]:
            if r[1] == "1850" and r[gi]:
                streets["1850"][r[gi]] += 1
    out["streets"] = {b: streets[b].most_common(20) for b in out["bands"]}
    out["streets_source"] = {"1841": "Register", "1850": "Nummernbuch", "1862": "Einwohnerverzeichnis"}
    # Sternanteile je Band (der Stern bedeutet in Basel nicht Bürgerrecht)
    star = {}
    if "gebaeude" in data:
        mi = data["gebaeude"]["cols"].index("marker")
        for b in out["bands"]:
            rows = [r for r in data["gebaeude"]["rows"] if r[1] == b]
            star[b] = {"n": len(rows), "star": sum(1 for r in rows if "*" in (r[mi] or ""))}
    out["star"] = star
    kb = Counter()
    ci = data["einwohner"]["cols"].index("city_part")
    for r in data["einwohner"]["rows"]:
        if r[1] == "1850":
            kb["Kleinbasel" if r[ci] == "Kleinbasel" else "Grossbasel"] += 1
    out["kleinbasel_1850"] = dict(kb)
    try:
        out["geo"] = json.loads((GEO_DIR / "summary.json").read_text(encoding="utf-8"))
    except Exception:
        out["geo"] = {}
    out["phone"] = []
    if (CSV_DIR / "20_phonebook_summary.csv").exists():
        with (CSV_DIR / "20_phonebook_summary.csv").open(encoding="utf-8") as fh:
            out["phone"] = [{k: (int(v) if v.isdigit() else v) for k, v in r.items()} for r in csv.DictReader(fh)]
    return out


def load_geo() -> dict:
    geo = {}
    for p in sorted(GEO_DIR.glob("buildings_*.geojson")):
        geo[p.stem.replace("buildings_", "")] = json.loads(p.read_text(encoding="utf-8"))
    return geo


def load_flags() -> list[dict]:
    if not REVIEW.exists():
        return []
    with REVIEW.open(encoding="utf-8") as fh:
        return [{"table": r["table"], "id": r["id"], "reason": r["reason"], "note": r["note"],
                 "by": r.get("by", ""), "date": r.get("date", "")}
                for r in csv.DictReader(fh) if r.get("status", "open") != "fixed"]


TEMPLATE = r"""<title>Basel Adressdaten Kontrolle</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&family=Source+Code+Pro:wght@400;600&display=swap">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<style>
/* Layout: Werkzeug — Kopf mit Filtern und Flag-Leiste, darunter eine Tabelle, die den Rest füllt. */
:root {
  --bg: #f6f5f1; --paper: #ffffff; --fg: #1d2129; --muted: #5c6370; --line: #d9d7cf;
  --accent: #7a2e2e; --accent-soft: #f1e3e1; --ok: #2f6f4e; --warn: #9a6b11; --bad: #a33a2a; --flag: #fff3c4;
  --font-body: "Source Sans 3", "Segoe UI", system-ui, sans-serif;
  --font-data: "Source Code Pro", ui-monospace, Menlo, monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #15171b; --paper: #1d2026; --fg: #e8e6df; --muted: #a39f94; --line: #353942;
  --accent: #d08a84; --accent-soft: #3a2626; --ok: #7fc39d; --warn: #d9b35a; --bad: #e08a79; --flag: #3b3418; color-scheme: dark } }
:root[data-theme="dark"] {
  --bg: #15171b; --paper: #1d2026; --fg: #e8e6df; --muted: #a39f94; --line: #353942;
  --accent: #d08a84; --accent-soft: #3a2626; --ok: #7fc39d; --warn: #d9b35a; --bad: #e08a79; --flag: #3b3418; color-scheme: dark }
html, body { height: 100%; }
body { background: var(--bg); color: var(--fg); font-family: var(--font-body); font-size: 15px; line-height: 1.4;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px));
  padding-block: 16px; display: flex; flex-direction: column; gap: 10px; box-sizing: border-box; margin: 0; }
header { display: flex; flex-wrap: wrap; align-items: baseline; gap: 6px 20px; }
h1 { font-size: 1.3rem; margin: 0; font-weight: 700; letter-spacing: -0.01em; text-wrap: balance; }
.sub { color: var(--muted); font-size: 0.88rem; margin: 0; }
.toolbar { display: flex; flex-wrap: wrap; gap: 8px 12px; align-items: center; }
nav.sites { display: flex; flex-wrap: wrap; gap: 4px 14px; font-size: 0.86rem; color: var(--muted); }
nav.sites a { color: var(--accent); text-decoration: none; font-weight: 600; }
nav.sites a:hover, nav.sites a:focus-visible { text-decoration: underline; }
nav.sites .here { color: var(--fg); font-weight: 600; }
.tabs { display: flex; gap: 4px; flex-wrap: wrap; }
button { font: inherit; cursor: pointer; }
.tabs button { font-weight: 600; background: transparent; color: var(--muted); border: 1px solid var(--line); border-radius: 999px; padding: 4px 12px; }
.tabs button[aria-selected="true"] { background: var(--accent); border-color: var(--accent); color: #fff; }
button:focus-visible, input:focus-visible, select:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
input[type="search"], select, input[type="text"] { font: inherit; padding: 5px 9px; border: 1px solid var(--line); border-radius: 6px; background: var(--paper); color: var(--fg); min-width: 0; }
input[type="search"] { flex: 1 1 220px; }
.count { color: var(--muted); font-variant-numeric: tabular-nums; font-size: 0.9rem; }
.flagbar { display: flex; flex-wrap: wrap; gap: 8px 12px; align-items: center; padding: 8px 12px; border: 1px solid var(--line); border-radius: 8px; background: var(--paper); font-size: 0.9rem; }
.flagbar .n { font-weight: 700; color: var(--accent); font-variant-numeric: tabular-nums; }
.btn { border: 1px solid var(--line); background: var(--paper); color: var(--fg); border-radius: 6px; padding: 4px 10px; }
.btn.primary { background: var(--accent); border-color: var(--accent); color: #fff; }
.wrap { flex: 1 1 auto; min-height: 0; overflow: auto; border: 1px solid var(--line); border-radius: 8px; background: var(--paper); }
table { border-collapse: collapse; width: max-content; min-width: 100%; font-size: 13.5px; }
th, td { text-align: left; padding: 4px 8px; border-bottom: 1px solid var(--line); vertical-align: top; white-space: nowrap; max-width: 32ch; overflow: hidden; text-overflow: ellipsis; }
td.wide { white-space: normal; max-width: 48ch; }
th { position: sticky; top: 0; background: var(--paper); font-size: 0.76rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); z-index: 1; }
td.num, td.id { font-family: var(--font-data); font-variant-numeric: tabular-nums; font-size: 12.5px; }
tr.flagged td { background: var(--flag); }
tr.reported td:first-child::before { content: "✓ "; color: var(--ok); font-weight: 700; }
.pill { display: inline-block; border-radius: 999px; padding: 0 8px; font-size: 0.74rem; font-weight: 600; line-height: 1.5; }
.pill.high { background: color-mix(in srgb, var(--ok) 18%, transparent); color: var(--ok); }
.pill.medium { background: color-mix(in srgb, var(--warn) 18%, transparent); color: var(--warn); }
.pill.review { background: color-mix(in srgb, var(--bad) 18%, transparent); color: var(--bad); }
.star { color: var(--accent); font-weight: 700; }
td.act { white-space: nowrap; }
td.act select, td.act input { font-size: 12.5px; padding: 2px 5px; }
td.act input[type="text"] { width: 14ch; }
td.act a { color: var(--muted); font-size: 12px; margin-left: 6px; }
.more { display: block; width: 100%; padding: 8px; background: var(--accent-soft); color: var(--fg); border: 0; }
.legend { color: var(--muted); font-size: 0.84rem; margin: 0; }
.legend b { color: var(--fg); }
#toast { position: fixed; bottom: calc(12px + env(safe-area-inset-bottom, 0px)); right: calc(12px + env(safe-area-inset-right, 0px)); background: var(--fg); color: var(--bg); padding: 8px 14px; border-radius: 8px; font-size: 0.9rem; }
.chip { display: inline-flex; gap: 6px; align-items: center; background: var(--accent-soft); border: 1px solid var(--accent); border-radius: 999px; padding: 2px 4px 2px 10px; font-size: 0.88rem; }
.chip button { border: 0; background: transparent; color: var(--accent); font-weight: 700; padding: 0 6px; cursor: pointer; }
.chip .tabhit { text-decoration: underline; font-weight: 600; }
.leaflet-popup-content a.flt { display: inline-block; margin: 2px 8px 0 0; color: var(--accent); font-weight: 600; }
.panel { flex: 1 1 auto; min-height: 0; overflow: auto; border: 1px solid var(--line); border-radius: 8px; background: var(--paper); padding: 12px 16px; }
.panel h2 { font-size: 1.05rem; margin: 14px 0 6px; }
.panel h2:first-child { margin-top: 0; }
.panel p { margin: 4px 0 8px; color: var(--muted); font-size: 0.9rem; max-width: 80ch; }
.charts { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 14px 24px; }
.chart h3 { font-size: 0.9rem; margin: 0 0 4px; color: var(--muted); font-weight: 600; }
.bars { display: grid; grid-template-columns: minmax(10ch, max-content) 1fr max-content; gap: 2px 8px; align-items: center; font-size: 13px; }
.bars .lbl { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 24ch; }
.bars .bar { height: 12px; background: var(--accent); border-radius: 2px; min-width: 1px; }
.bars .val { font-family: var(--font-data); font-size: 12px; color: var(--muted); font-variant-numeric: tabular-nums; }
.kpi { display: flex; flex-wrap: wrap; gap: 10px 22px; margin: 6px 0 10px; }
.kpi div { font-size: 0.9rem; color: var(--muted); } .kpi b { display: block; font-size: 1.3rem; color: var(--fg); font-variant-numeric: tabular-nums; }
#mapwrap { flex: 1 1 auto; min-height: 420px; display: flex; flex-direction: column; gap: 8px; }
#mapwrap[hidden], .panel[hidden], .wrap[hidden] { display: none; }
#map { flex: 1 1 auto; min-height: 400px; border: 1px solid var(--line); border-radius: 8px; }
.mapbar { display: flex; flex-wrap: wrap; gap: 8px 14px; align-items: center; font-size: 0.9rem; }
.mapbar .sw { display: inline-block; width: 11px; height: 11px; border-radius: 50%; margin-right: 4px; vertical-align: middle; }
.leaflet-popup-content { font-family: var(--font-body); font-size: 13px; line-height: 1.35; max-height: 260px; overflow: auto; }
.leaflet-popup-content ul { margin: 4px 0 0; padding-left: 16px; }
@media (max-width: 600px) { body { font-size: 14px; } th, td { max-width: 22ch; } td.act input[type="text"] { width: 9ch; } }
@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
</style>
<nav class="sites" aria-label="Schwesterprojekte"><span class="here">Adressbücher Basel</span><a href="https://thodel.github.io/adressbuecher-aarau/">Adressbücher Aarau</a><a href="https://thodel.github.io/adressbuecher-aarau/karte.html">Karte Aarau</a><a href="__REPO__">Repo Basel</a><a href="https://github.com/thodel/adressbuecher-aarau">Repo Aarau</a></nav>
<header>
  <h1>Adressbücher Basel 1841–1862: Kontrolle der Datensätze</h1>
  <p class="sub">Stand __DATE__ · Rohdaten aus der ATR-Lesung (Gemini 3.8 Flash), regelbasiert geparst, ohne Normalisierung; Verortung über das Historische Grundbuch Basel (Lizenz der Standortpunkte offen, siehe Reiter Karte). Fehler hier markieren; die Flags gehen per CSV oder Issue ins Repo.</p>
</header>
<div class="toolbar">
  <div class="tabs" role="tablist" id="tabs"></div>
  <select id="vol" aria-label="Band"><option value="">alle Bände</option></select>
  <select id="conf" aria-label="Konfidenz"><option value="">alle Konfidenzen</option><option value="high">high</option><option value="medium">medium</option><option value="review">review</option></select>
  <label><input type="checkbox" id="onlyflag"> nur markierte</label>
  <span id="colfilter" class="chip" hidden></span>
  <input id="q" type="search" placeholder="Suchen: Name, Beruf, Strasse, Heimatort, ID …" aria-label="Suchen">
  <span class="count" id="count"></span>
</div>
<div class="flagbar">
  <span><span class="n" id="nflags">0</span> Flags in diesem Browser · <span id="nreported">0</span> bereits im Repo gemeldet</span>
  <button class="btn primary" id="dl">Flags als CSV herunterladen</button>
  <button class="btn" id="copy">CSV in die Zwischenablage</button>
  <button class="btn" id="clear">Flags löschen</button>
  <span class="sub">Danach: <code>python scripts/91_merge_flags.py &lt;datei.csv&gt;</code> und committen.</span>
</div>
<p class="legend"><b>*</b> im Register 1841 (Nachtrag) = Häuserkauf während des Drucks · <b>Marke *</b> im Nummernbuch 1841 = Gebäude <i>nicht</i> vom Eigentümer bewohnt · <b>Stadtteil «Kleinbasel»</b> im Register 1850 = Stern vor der Nummer (Kleinbasel zählt ab 1) · <b>Nr.-System</b>: alt = stadtweite Hausnummer (1841/1850), neu = Nummer je Strasse (1862) · <b>Verortung</b>: über die HGB-Dossiers (Adresse 1862 ↔ alte Nummer), Methode street_no/old_no = eindeutig, _multi = Schwerpunkt, _base = Hauptnummer ohne Buchstaben · <b>Konfidenz</b>: high = Zeile ging vollständig auf, medium = Hinweis in Rest/Notiz, review = nicht zuordenbar · <b>✓</b> = Flag schon im Repo · <b>Seite</b> öffnet den Band im Digitalen Lesesaal des Staatsarchivs.</p>
<div class="wrap" id="tablewrap"><table id="t"><thead></thead><tbody></tbody></table><button class="more" id="more" hidden>weitere Zeilen zeigen</button></div>
<div class="panel" id="analysen" hidden></div>
<div id="mapwrap" hidden>
  <div class="mapbar">
    <label>Band <select id="mapvol"></select></label>
    <label>Farbe <select id="mapcolor"><option value="n">Bewohner je Gebäude</option><option value="conf">Konfidenz der Verortung</option></select></label>
    <label>Historischer Plan <select id="wms"><option value="">keiner</option><option value="HP_Situationsplan_Basel_1862" selected>Löffelplan 1862 (Situationsplan)</option><option value="HP_Uebersichtsplan_Basel_1860">Übersichtsplan 1860</option><option value="HP_Katasterplan_Innerstadt_1865">Katasterplan Innerstadt 1865</option><option value="HP_Landeskarte_Basel_1836">Landeskarte 1836</option><option value="HP_Uebersichtsplan_Basel_1820">Übersichtsplan 1820</option><option value="HP_Uebersichtsplan_Basel_1786">Übersichtsplan 1786</option><option value="HP_Uebersichtsplan_Basel_1896">Übersichtsplan 1896</option></select></label>
    <label>Deckkraft <input type="range" id="wmsop" min="0" max="100" value="80" style="width:80px"></label>
    <span id="mapcount" class="count"></span>
    <span id="maplegend"></span>
  </div>
  <div id="map"></div>
  <p class="legend">Historische Pläne als Overlay aus dem WMS des Kantons Basel-Stadt (<code>wms.geo.bs.ch</code>): der <b>Löffelplan</b> (Situationsplan 1862, Ludwig Löffel) zeigt die neuen Hausnummern des Bandes 1862; Übersichtsplan 1860, Landeskarte 1836 und Übersichtsplan 1820 passen zu 1841/1850. Punkte = HGB-Dossier-Standorte des Projekts «Ökonomien des Raums» (Uni Basel; Georeferenzierung Grundbuch- und Vermessungsamt BS, am Löffelplan 1862 geprüft), über Strasse + Nummer (1862) bzw. alte Hausnummer (1841/1850) zugeordnet. <b>Lizenz der Standortpunkte offen</b> (Repo ohne Datenlizenz, Dump CC BY 4.0) – Anzeige «soweit als möglich», vor einer Weiterverwendung beim Projekt nachfragen. Grundkarte © OpenStreetMap-Mitwirkende.</p>
</div>
<div id="toast" hidden></div>
<script>
const DATA = __DATA__;
const ANA = __ANA__;
const GEO = __GEO__;
const LABELS = __LABELS__;
const REASONS = __REASONS__;
const REPORTED = __REPORTED__;
const REPO = "__REPO__";
const PAGE = 300;
const KEY = 'basel.flags.v1';
const DLS = __DLS__;
const P = new URLSearchParams(location.search);
const hashTab = location.hash.replace('#','');
let tab = P.get('tab') && (DATA[P.get('tab')] || ['analysen','karte'].includes(P.get('tab'))) ? P.get('tab') : ((hashTab in DATA || ['analysen','karte'].includes(hashTab)) ? hashTab : Object.keys(DATA)[0]);
let colF = P.get('col') || '', valF = P.get('val') || '', labelF = P.get('label') || '';
let shown = PAGE;
let flags = {};
try { flags = JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) { flags = {}; }
const reported = {}; for (const f of REPORTED) reported[f.table + '|' + f.id] = f;
const $ = id => document.getElementById(id);
const tabsEl = $('tabs'), q = $('q'), vol = $('vol'), conf = $('conf'), onlyflag = $('onlyflag');
const thead = document.querySelector('#t thead'), tbody = document.querySelector('#t tbody'), more = $('more'), count = $('count');
const vols = new Set(); for (const k in DATA) if (k !== 'telefon') for (const r of DATA[k].rows) vols.add(r[1]);
[...vols].sort().forEach(v => { const o = document.createElement('option'); o.value = v; o.textContent = v; vol.appendChild(o); });
for (const k in DATA) { const b = document.createElement('button'); b.setAttribute('role', 'tab'); b.textContent = `${DATA[k].label} (${DATA[k].rows.length.toLocaleString('de-CH')})`; b.dataset.k = k; b.onclick = () => { tab = k; shown = PAGE; render(); }; tabsEl.appendChild(b); }
for (const [k, label] of [['analysen', 'Analysen'], ['karte', 'Karte']]) { const b = document.createElement('button'); b.setAttribute('role', 'tab'); b.textContent = label; b.dataset.k = k; b.onclick = () => { tab = k; render(); }; tabsEl.appendChild(b); }

function esc(s) { return String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }
function save() { try { localStorage.setItem(KEY, JSON.stringify(flags)); } catch (e) {} }
function toast(msg) { const t = $('toast'); t.textContent = msg; t.hidden = false; setTimeout(() => { t.hidden = true; }, 2500); }
function issueUrl(k, r) {
  const d = DATA[k], id = r[0];
  const body = `Tabelle: ${d.label}\nID: ${id}\nBand ${r[1]}${d.cols[2] === 'page' ? ', PDF-Seite ' + r[2] : ''}\n\nATR-Zeile:\n${r[d.cols.indexOf('text')] ?? r[d.cols.indexOf('owner_text')] ?? r[d.cols.indexOf('dossier_title')] ?? ''}\n\nProblem:\n`;
  return `${REPO}/issues/new?title=${encodeURIComponent('Flag ' + id)}&labels=${encodeURIComponent('review')}&body=${encodeURIComponent(body)}`;
}
function cell(k, col, v, r) {
  if (col === 'parse_confidence') return `<td><span class="pill ${esc(v)}">${esc(v)}</span></td>`;
  if (col === 'owner_flag' || col === 'phone_flag' || col === 'owner_same_as_prev') return `<td class="num">${v === '1' ? '<span class="star">' + (col === 'owner_flag' ? '*' : col === 'phone_flag' ? '☏' : '„') + '</span>' : (v ? esc(v) : '')}</td>`;
  if (col === 'match_level') return `<td><span class="pill ${v === 'name_addr' ? 'high' : v === 'name_street' ? 'medium' : 'review'}">${esc(v)}</span></td>`;
  if (col === 'year' || col === 'n_refs') return `<td class="num">${esc(v)}</td>`;
  if (col === 'match_refs') return `<td class="wide id">${esc(v)}</td>`;
  if (col === 'page') return `<td class="num">${v ? `<a href="${esc(DLS[r[1]] || '#')}" target="_blank" rel="noopener" title="Band im Digitalen Lesesaal">${esc(v)}</a>` : ''}</td>`;
  if (col === 'dossier_id') return `<td class="id">${esc(v)}</td>`;
  if (col === 'lat' || col === 'lon') return `<td class="num">${esc(v)}</td>`;
  if (col === 'marker') return `<td class="num star">${esc(v)}</td>`;
  if (col === 'entry_id' || col === 'building_id') return `<td class="id">${esc(v)}</td>`;
  if (['page','building_no','building_nos','volume'].includes(col)) return `<td class="num">${esc(v)}</td>`;
  if (['residual','note','owner_text','occupation_raw','text'].includes(col)) return `<td class="wide">${esc(v)}</td>`;
  return `<td>${esc(v)}</td>`;
}
function actCell(k, r) {
  const key = k + '|' + r[0], f = flags[key] || {};
  const opts = ['<option value="">— Flag —</option>'].concat(REASONS.map(x => `<option value="${esc(x)}" ${f.reason === x ? 'selected' : ''}>${esc(x)}</option>`)).join('');
  return `<td class="act"><select data-key="${esc(key)}" data-f="reason" aria-label="Grund">${opts}</select> <input type="text" data-key="${esc(key)}" data-f="note" placeholder="Notiz" value="${esc(f.note || '')}" aria-label="Notiz"><a href="${issueUrl(k, r)}" target="_blank" rel="noopener">Issue</a></td>`;
}
function render() {
  for (const b of tabsEl.children) b.setAttribute('aria-selected', b.dataset.k === tab);
  const special = tab === 'analysen' || tab === 'karte';
  $('tablewrap').hidden = special; $('analysen').hidden = tab !== 'analysen'; $('mapwrap').hidden = tab !== 'karte';
  if (special) $('colfilter').hidden = true;
  for (const el of [q, vol, conf, onlyflag, count]) el.closest('label') ? (el.closest('label').style.display = special ? 'none' : '') : (el.style.display = special ? 'none' : '');
  try { localStorage.setItem('basel.tab', tab); } catch (e) {}
  if (tab === 'analysen') { renderAnalysen(); return; }
  if (tab === 'karte') { renderMap(); return; }
  const d = DATA[tab], needle = q.value.trim().toLowerCase(), v = vol.value, c = conf.value, ci = d.cols.indexOf('parse_confidence');
  const fi = colF ? d.cols.indexOf(colF) : -1;
  const chip = $('colfilter');
  if (colF && valF) {
    const hits = Object.keys(DATA).map(k => { const j = DATA[k].cols.indexOf(colF); return [k, j < 0 ? 0 : DATA[k].rows.filter(r => r[j] === valF && (!vol.value || k === 'telefon' || r[1] === vol.value)).length]; }).filter(([k, n]) => n > 0);
    const other = hits.filter(([k]) => k !== tab).map(([k, n]) => `<button type="button" class="tabhit" data-k="${k}">${esc(DATA[k].label)}: ${n}</button>`).join('');
    chip.hidden = false;
    chip.innerHTML = `${esc(LABELS[colF] || colF)} = <b>${esc(labelF || valF)}</b>${other ? ' · Treffer auch in ' + other : ''}<button type="button" id="clearcol" aria-label="Filter entfernen">✕</button>`;
    $('clearcol').onclick = () => { colF = valF = labelF = ''; history.replaceState(null, '', location.pathname + '#' + tab); shown = PAGE; render(); };
    for (const b of chip.querySelectorAll('.tabhit')) b.onclick = () => { tab = b.dataset.k; shown = PAGE; render(); };
  } else { chip.hidden = true; }
  const rows = d.rows.filter(r => (!v || tab === 'telefon' || r[1] === v) && (!c || r[ci] === c) && (!colF || !valF || fi < 0 || r[fi] === valF) && (!onlyflag.checked || flags[tab + '|' + r[0]] || reported[tab + '|' + r[0]]) && (!needle || r.join(' ').toLowerCase().includes(needle)));
  thead.innerHTML = '<tr><th>Flag</th>' + d.cols.map(cc => `<th>${esc(LABELS[cc] || cc)}</th>`).join('') + '</tr>';
  tbody.innerHTML = rows.slice(0, shown).map(r => {
    const key = tab + '|' + r[0];
    const cls = (flags[key] && flags[key].reason ? 'flagged ' : '') + (reported[key] ? 'reported' : '');
    return `<tr class="${cls}" title="${reported[key] ? esc('gemeldet: ' + reported[key].reason + ' ' + reported[key].note) : ''}">${actCell(tab, r)}${r.map((vv, i) => cell(tab, d.cols[i], vv, r)).join('')}</tr>`;
  }).join('');
  more.hidden = rows.length <= shown;
  count.textContent = `${Math.min(shown, rows.length).toLocaleString('de-CH')} von ${rows.length.toLocaleString('de-CH')} Zeilen`;
  $('nflags').textContent = Object.values(flags).filter(f => f.reason).length;
  $('nreported').textContent = REPORTED.length;
  try { localStorage.setItem('basel.tab', tab); } catch (e) {}
}
tbody.addEventListener('change', e => {
  const el = e.target, key = el.dataset.key; if (!key) return;
  flags[key] = flags[key] || {}; flags[key][el.dataset.f] = el.value;
  if (!flags[key].reason && !flags[key].note) delete flags[key];
  save(); const tr = el.closest('tr'); tr.classList.toggle('flagged', !!(flags[key] && flags[key].reason)); $('nflags').textContent = Object.values(flags).filter(f => f.reason).length;
});
function flagsCsv() {
  const q2 = s => '"' + String(s ?? '').replace(/"/g, '""') + '"';
  const lines = ['table,id,reason,note,by,date'];
  const today = new Date().toISOString().slice(0, 10);
  for (const key in flags) { const f = flags[key]; if (!f.reason) continue; const [t, id] = key.split('|'); lines.push([t, id, f.reason, f.note || '', '', today].map(q2).join(',')); }
  return lines.join('\n') + '\n';
}
$('dl').onclick = () => {
  const blob = new Blob(['﻿' + flagsCsv()], { type: 'text/csv;charset=utf-8' });
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `flags_${new Date().toISOString().slice(0, 10)}.csv`; document.body.appendChild(a); a.click(); a.remove();
  toast('CSV wird heruntergeladen (falls gesperrt: Zwischenablage nutzen)');
};
$('copy').onclick = () => {
  const text = flagsCsv();
  if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(() => toast('CSV kopiert'), () => fallbackCopy(text)); else fallbackCopy(text);
};
function fallbackCopy(text) { const ta = document.createElement('textarea'); ta.value = text; document.body.appendChild(ta); ta.select(); try { document.execCommand('copy'); toast('CSV kopiert'); } catch (e) { toast('Kopieren nicht möglich: Text ist markiert'); } ta.remove(); }
$('clear').onclick = () => { if (!Object.keys(flags).length) return; flags = {}; save(); render(); toast('Flags gelöscht'); };
more.onclick = () => { shown += PAGE; render(); };
for (const el of [q, vol, conf, onlyflag]) el.addEventListener(el === q ? 'input' : 'change', () => { shown = PAGE; render(); });
// ---- Analysen: alles aus ANA (beim Bau aus den CSV berechnet)
function bars(title, pairs, total) {
  const max = Math.max(1, ...pairs.map(p => p[1]));
  return `<div class="chart"><h3>${esc(title)}</h3><div class="bars">` + pairs.map(([l, v]) => `<span class="lbl" title="${esc(l)}">${esc(l)}</span><span class="bar" style="width:${(100 * v / max).toFixed(1)}%"></span><span class="val">${v.toLocaleString('de-CH')}${total ? ' (' + (100 * v / total).toFixed(1) + ' %)' : ''}</span>`).join('') + '</div></div>';
}
function renderAnalysen() {
  const el = $('analysen'); if (el.dataset.done) return; el.dataset.done = 1;
  const B = ANA.bands; let h = '';
  h += '<h2>Einträge je Band</h2><p>Zeilen der Welle-2-Tabellen (ohne Normalisierung, ohne Identität über Bände). Personen in mehreren Bänden werden erst nach der Personenidentifikation (Welle 3) gezählt.</p><div class="kpi">';
  for (const k in ANA.counts) for (const b of B) if (ANA.counts[k][b]) h += `<div><b>${ANA.counts[k][b].toLocaleString('de-CH')}</b>${esc(DATA[k] ? DATA[k].label : k)} ${b}</div>`;
  h += '</div>';
  if (ANA.geo && Object.keys(ANA.geo).length) { h += '<h2>Verortung über das HGB</h2><div class="kpi">'; for (const b of B) if (ANA.geo[b]) h += `<div><b>${ANA.geo[b].located.toLocaleString('de-CH')} von ${ANA.geo[b].total.toLocaleString('de-CH')}</b>${b}: Gebäude verortet (${(100 * ANA.geo[b].located / ANA.geo[b].total).toFixed(0)} %, davon ${ANA.geo[b].high} eindeutig)</div>`; h += '</div>'; }
  h += '<h2>Die 25 häufigsten Berufe je Band</h2><p>Berufsangabe wie gedruckt (occupation_raw aus Einwohnerregister und Bewohnerzeilen, Schlusspunkt entfernt); Schreibvarianten und Abkürzungen («Kfm.», «Kaufmann») sind noch nicht zusammengeführt.</p><div class="charts">';
  for (const b of B) h += bars(`${b} (${ANA.occupations_total[b].toLocaleString('de-CH')} Angaben)`, ANA.occupations[b], ANA.occupations_total[b]);
  h += '</div>';
  if (ANA.residents_per_building) { h += '<h2>Bewohner je Gebäude</h2><p>Eingerückte Bewohnerzeilen unter einem Gebäude im Nummernbuch (1841, 1850) bzw. Häuserverzeichnis (1862); 0 = nur der Eigentümer genannt.</p><div class="charts">'; for (const b of B) h += bars(b, Object.entries(ANA.residents_per_building[b]), ANA.counts.gebaeude[b]); h += '</div>'; }
  h += '<h2>Strassen nach Zahl der Einträge</h2><p>1841 und 1862 aus dem Register (Adresse je Eintrag), 1850 aus dem Nummernbuch (das Register nennt nur die Hausnummer). Strassennamen wie gedruckt.</p><div class="charts">';
  for (const b of B) h += bars(`${b} (${esc(ANA.streets_source[b] || '')})`, ANA.streets[b]);
  h += '</div>';
  if (ANA.phone && ANA.phone.length) {
    h += '<h2>Abgleich mit den PTT-Telefonbüchern (historic.localsearch, DHBern/PTT_phonebook_data_tsv)</h2><p>Basler Netz: 1881–1910 nur als OCR-Seitentext (Batch A, hier grob segmentiert, meist ohne Adresse), 1911–1937 als segmentierte Einträge mit Strasse (Batch B). Abgleich über Familienname, normalisierte Strasse und Hausnummer gegen das Adressbuch 1862 (Einwohner, Eigentümer, Bewohner): <b>name_addr</b> = gleicher Name an derselben Adresse, <b>name_street</b> = gleicher Name in derselben Strasse, <b>addr</b> = dieselbe Adresse mit anderem Namen (Hauskontinuität). Abonnenten ohne Adresse können nicht abgeglichen werden.</p>';
    const ph = ANA.phone.filter(r => r.entries > 100);
    h += bars('Abonnenten je Jahr (davon mit Adresse)', ph.map(r => [`${r.year} (${r.with_address} m. Adr.)`, r.entries]));
    h += '<div class="charts">' + bars('Namenstreffer an derselben Adresse 1862 (name_addr)', ph.map(r => [String(r.year), r.name_addr])) + bars('Namenstreffer in derselben Strasse (name_street)', ph.map(r => [String(r.year), r.name_street])) + bars('Adresse 1862 belegt, anderer Name (addr)', ph.map(r => [String(r.year), r.addr])) + '</div>';
  }
  h += '<h2>Sterne und Stadtteile</h2><p>Der Stern bedeutet in Basel kein Bürgerrecht: im Nummernbuch 1841 markiert er Gebäude, die nicht vom Eigentümer bewohnt sind (Berichtigung im Band); im Register 1850 steht er vor Kleinbasler Hausnummern. Ein Bürgeranteil lässt sich aus diesen Bänden nicht ablesen.</p><div class="kpi">';
  for (const b of B) if (ANA.star[b] && ANA.star[b].n) h += `<div><b>${ANA.star[b].star.toLocaleString('de-CH')} von ${ANA.star[b].n.toLocaleString('de-CH')}</b>${b}: Gebäude mit Stern (${(100 * ANA.star[b].star / ANA.star[b].n).toFixed(1)} %)</div>`;
  if (ANA.kleinbasel_1850 && ANA.kleinbasel_1850.Kleinbasel) h += `<div><b>${ANA.kleinbasel_1850.Kleinbasel.toLocaleString('de-CH')} von ${(ANA.kleinbasel_1850.Kleinbasel + ANA.kleinbasel_1850.Grossbasel).toLocaleString('de-CH')}</b>1850: Registereinträge in Kleinbasel (${(100 * ANA.kleinbasel_1850.Kleinbasel / (ANA.kleinbasel_1850.Kleinbasel + ANA.kleinbasel_1850.Grossbasel)).toFixed(1)} %)</div>`;
  h += '</div>';
  el.innerHTML = h;
}
// ---- Karte: Leaflet, OSM, optional WMS Situationsplan 1862, Punkte aus GEO
let map = null, layer = null, wmsLayer = null;
const COLORS_N = [['0', '#9aa0a6'], ['1–2', '#2f6f4e'], ['3–5', '#9a6b11'], ['6+', '#a33a2a']];
const COLORS_C = [['high', '#2f6f4e'], ['medium', '#9a6b11'], ['low', '#a33a2a']];
function colorFor(p, mode) { if (mode === 'conf') return (COLORS_C.find(c => c[0] === p.conf) || COLORS_C[2])[1]; const n = p.n; return n === 0 ? COLORS_N[0][1] : n <= 2 ? COLORS_N[1][1] : n <= 5 ? COLORS_N[2][1] : COLORS_N[3][1]; }
function popup(p) {
  const title = `${esc(p.street)} ${esc(p.no)}${p.old ? ' (alte Nr. ' + esc(p.old) + ')' : ''}${p.name ? ' «' + esc(p.name) + '»' : ''}`;
  let h = `<b>${title}</b><br>Band ${p.vol}, PDF-S. ${p.page}${p.part ? ', ' + esc(p.part) : ''}<br><b>Eigentümer:</b> ${esc(p.owner || '–')}${p.type ? ' (' + esc(p.type) + ')' : ''}${p.marker ? ' <span class="star">' + esc(p.marker) + '</span>' : ''}`;
  if (p.residents.length) h += `<br><b>Bewohner (${p.residents.length}):</b><ul>` + p.residents.map(r => `<li>${esc(r)}</li>`).join('') + '</ul>';
  const u = (t, col, val, label) => { const s = new URLSearchParams({ tab: t, col, val, vol: p.vol }); if (label) s.set('label', label); return './?' + s.toString(); };
  h += `<br><a class="flt" href="${u('gebaeude', 'building_id', p.id)}">Gebäudezeile</a><a class="flt" href="${u('bewohner', 'building_no', p.no)}">Bewohner Nr. ${esc(p.no)}</a>${p.street ? `<a class="flt" href="${u('einwohner', 'street_raw', p.street)}">Einwohner ${esc(p.street)}</a>` : ''}`;
  h += `<br><span class="sub">Verortung ${esc(p.method)} (${esc(p.conf)}), HGB ${esc(p.hgb)}${p.dossier ? ' · ' + (p.link ? '<a href="' + esc(p.link) + '" target="_blank" rel="noopener">' + esc(p.dossier) + '</a>' : esc(p.dossier)) : ''} · <a href="${esc(DLS[p.vol] || '#')}" target="_blank" rel="noopener">Seite im Lesesaal</a></span>`;
  return h;
}
function renderMap() {
  const vols = Object.keys(GEO).sort();
  if (!map) {
    if (typeof L === 'undefined') { $('mapcount').textContent = 'Leaflet konnte nicht geladen werden (offline?).'; return; }
    map = L.map('map').setView([47.5565, 7.5880], 15);
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>-Mitwirkende' }).addTo(map);
    const mkWms = name => L.tileLayer.wms('https://wms.geo.bs.ch/', { layers: name, format: 'image/png', transparent: true, attribution: 'Historische Pläne: Geodaten Kanton Basel-Stadt', maxZoom: 20, opacity: $('wmsop').value / 100 });
    wmsLayer = mkWms($('wms').value); wmsLayer.addTo(map);
    const sel = $('mapvol'); for (const v of vols) { const o = document.createElement('option'); o.value = v; o.textContent = v; sel.appendChild(o); }
    sel.value = vols[vols.length - 1];
    sel.onchange = drawPoints; $('mapcolor').onchange = drawPoints;
    $('wms').onchange = () => { if (wmsLayer) map.removeLayer(wmsLayer); wmsLayer = null; if ($('wms').value) { wmsLayer = mkWms($('wms').value); wmsLayer.addTo(map); } };
    $('wmsop').oninput = () => { if (wmsLayer) wmsLayer.setOpacity($('wmsop').value / 100); };
  }
  setTimeout(() => map.invalidateSize(), 50);
  drawPoints();
}
function drawPoints() {
  const v = $('mapvol').value, mode = $('mapcolor').value, fc = GEO[v];
  if (layer) map.removeLayer(layer);
  layer = L.layerGroup();
  for (const f of fc.features) {
    const p = f.properties, [lon, lat] = f.geometry.coordinates;
    L.circleMarker([lat, lon], { radius: 4 + Math.min(p.n, 8) * 0.6, color: colorFor(p, mode), weight: 1, fillOpacity: 0.75 }).bindPopup(popup(p), { maxWidth: 360 }).addTo(layer);
  }
  layer.addTo(map);
  const s = (ANA.geo || {})[v];
  $('mapcount').textContent = s ? `${s.located.toLocaleString('de-CH')} von ${s.total.toLocaleString('de-CH')} Gebäuden verortet (${(100 * s.located / s.total).toFixed(0)} %); ${(s.total - s.located).toLocaleString('de-CH')} ohne Koordinate sind nicht auf der Karte` : `${fc.features.length} Punkte`;
  $('maplegend').innerHTML = (mode === 'conf' ? COLORS_C : COLORS_N).map(c => `<span class="sw" style="background:${c[1]}"></span>${esc(c[0])} `).join(' ');
}
try { const t = localStorage.getItem('basel.tab'); if (!location.hash && !P.get('tab') && t && (DATA[t] || t === 'analysen' || t === 'karte')) tab = t; } catch (e) {}
if (P.get('vol')) vol.value = P.get('vol');
if (P.get('conf')) conf.value = P.get('conf');
if (P.get('q')) q.value = P.get('q');
render();
</script>
"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    data = {}
    for key, label, files, _id, cols in TABS:
        rows = load(files, cols)
        if rows:
            data[key] = {"label": label, "cols": cols, "rows": rows}
            print(f"{label}: {len(rows)} Zeilen")
    reported = load_flags()
    ana = analyses(data)
    geo = load_geo()
    print("Karte:", {k: len(v["features"]) for k, v in geo.items()})
    html = (TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
            .replace("__ANA__", json.dumps(ana, ensure_ascii=False, separators=(",", ":")))
            .replace("__GEO__", json.dumps(geo, ensure_ascii=False, separators=(",", ":")))
            .replace("__LABELS__", json.dumps(LABELS, ensure_ascii=False))
            .replace("__REASONS__", json.dumps(REASONS, ensure_ascii=False))
            .replace("__REPORTED__", json.dumps(reported, ensure_ascii=False))
            .replace("__REPO__", REPO_URL)
            .replace("__DLS__", json.dumps(DLS))
            .replace("__DATE__", date.today().strftime("%d.%m.%Y")))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(html, encoding="utf-8")
    print(f"{len(reported)} gemeldete Flags → {args.out} ({args.out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
