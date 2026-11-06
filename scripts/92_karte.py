"""92_karte.py — Kartenseite: Gebäude und Strassen der Basler Adressbücher auf OpenStreetMap.

    python scripts/92_karte.py --out web/karte.html

Aufbau wie die Aarauer Kartenseite (Bedienfeld links mit Ansicht, Band, Zähleiste und
Rangliste; Karte rechts; Klick führt zu den gefilterten Einträgen der Kontrollseite).
Bettet data/geo/buildings_<jahr>.geojson (scripts/11_geojson.py) und data/geo/summary.json
ein und fasst die Gebäude zusätzlich je Band und Strasse zusammen (Schwerpunkt der
verorteten Gebäude). Historische Pläne als Overlay aus dem WMS des Kantons Basel-Stadt
(Löffelplan 1862 voreingestellt). Leaflet von cdnjs (feste Version), Kacheln von
OpenStreetMap (Attribution Pflicht).
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

GEO_DIR = Path("data/geo")

TEMPLATE = r"""<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Basel Gebäude und Strassen</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&display=swap">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">
<style>
/* Layout: Karte füllt die Fläche; links ein schmales Bedienfeld mit Ansicht, Band, Plan, Zähleiste und Rangliste. */
:root {
  --bg: #f6f5f1; --paper: #ffffff; --fg: #1d2129; --muted: #5c6370; --line: #d9d7cf;
  --accent: #7a2e2e; --accent-2: #2f5f8f; --font-body: "Source Sans 3", "Segoe UI", system-ui, sans-serif;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --bg: #15171b; --paper: #1d2026; --fg: #e8e6df; --muted: #a39f94; --line: #353942; --accent: #d08a84; --accent-2: #7fb0dc; color-scheme: dark } }
:root[data-theme="dark"] { --bg: #15171b; --paper: #1d2026; --fg: #e8e6df; --muted: #a39f94; --line: #353942; --accent: #d08a84; --accent-2: #7fb0dc; color-scheme: dark }
html, body { height: 100%; margin: 0; }
body { background: var(--bg); color: var(--fg); font-family: var(--font-body); font-size: 15px; line-height: 1.4; display: flex; flex-direction: column;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); padding-block: 12px; box-sizing: border-box; gap: 10px; }
header { display: flex; flex-wrap: wrap; align-items: baseline; gap: 6px 18px; }
.nav { font-size: 0.9rem; color: var(--muted); }
.nav a { color: var(--accent); font-weight: 600; text-decoration: none; }
.nav a:hover, .nav a:focus-visible { text-decoration: underline; }
h1 { font-size: 1.25rem; margin: 0; font-weight: 700; }
.sub { color: var(--muted); font-size: 0.88rem; margin: 0; }
.sub a { color: var(--accent); }
.main { flex: 1 1 auto; min-height: 0; display: flex; gap: 12px; }
.panel { flex: 0 0 270px; display: flex; flex-direction: column; gap: 10px; min-width: 0; overflow: auto; }
.card { background: var(--paper); border: 1px solid var(--line); border-radius: 8px; padding: 10px 12px; }
.card h2 { font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); margin: 0 0 6px; }
.seg { display: flex; gap: 4px; flex-wrap: wrap; }
.seg button { font: inherit; font-weight: 600; border: 1px solid var(--line); background: transparent; color: var(--muted); border-radius: 999px; padding: 3px 11px; cursor: pointer; }
.seg button[aria-pressed="true"] { background: var(--accent); border-color: var(--accent); color: #fff; }
.seg button:focus-visible, select:focus-visible, input:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
select, input[type="range"] { font: inherit; width: 100%; box-sizing: border-box; }
select { padding: 4px 6px; border: 1px solid var(--line); border-radius: 6px; background: var(--paper); color: var(--fg); }
.stat { display: flex; justify-content: space-between; gap: 8px; font-variant-numeric: tabular-nums; font-size: 0.92rem; padding: 2px 0; border-bottom: 1px dashed var(--line); }
.stat:last-child { border: 0; }
.stat span:first-child { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bar { height: 6px; background: var(--accent); border-radius: 3px; }
#map { flex: 1 1 auto; min-width: 0; border: 1px solid var(--line); border-radius: 8px; background: var(--paper); }
.leaflet-popup-content { font-family: var(--font-body); font-size: 13.5px; max-height: 280px; overflow: auto; }
.leaflet-popup-content b { color: var(--accent); }
.leaflet-popup-content a { color: #7a2e2e; font-weight: 600; }
.leaflet-popup-content ul { margin: 4px 0 0; padding-left: 16px; }
#top a { color: var(--fg); text-decoration: none; border-bottom: 1px dotted var(--muted); }
#top a:hover, #top a:focus-visible { color: var(--accent); }
.legend { font-size: 0.85rem; color: var(--muted); }
@media (max-width: 760px) { .main { flex-direction: column; } .panel { flex: 0 0 auto; max-height: 40%; } #map { min-height: 360px; } }
@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
.leaflet-control-zoom-in, .leaflet-control-zoom-out { color: #000 !important; }
</style>
<header>
  <nav class="nav"><a href="./">Kontrolle</a> · <a href="karte.html">Karte: Gebäude und Strassen</a> · <a href="https://thodel.github.io/adressbuecher-aarau/">Adressbücher Aarau</a> · <a href="https://thodel.github.io/adressbuecher-aarau/karte.html">Karte Aarau</a> · <a href="https://github.com/thodel/adressbuecher-basel">Repo</a></nav>
  <h1>Adressbücher Basel: Gebäude und Strassen</h1>
  <p class="sub">Stand __DATE__ · Gebäude über die Dossiers des Historischen Grundbuchs Basel verortet (Projekt «Ökonomien des Raums», Uni Basel); <b>Lizenz der Standortpunkte offen</b>, Anzeige soweit als möglich</p>
</header>
<div class="main">
  <div class="panel">
    <div class="card"><h2>Ansicht</h2><div class="seg" id="mode"><button data-m="buildings" aria-pressed="true">Gebäude</button><button data-m="streets" aria-pressed="false">Strassen</button></div></div>
    <div class="card"><h2>Band</h2><div class="seg" id="vol"></div></div>
    <div class="card"><h2>Historischer Plan</h2>
      <select id="wms" aria-label="Historischer Plan"><option value="">keiner</option><option value="HP_Situationsplan_Basel_1862" selected>Löffelplan 1862 (Situationsplan)</option><option value="HP_Uebersichtsplan_Basel_1860">Übersichtsplan 1860</option><option value="HP_Katasterplan_Innerstadt_1865">Katasterplan Innerstadt 1865</option><option value="HP_Landeskarte_Basel_1836">Landeskarte 1836</option><option value="HP_Uebersichtsplan_Basel_1820">Übersichtsplan 1820</option><option value="HP_Uebersichtsplan_Basel_1786">Übersichtsplan 1786</option><option value="HP_Uebersichtsplan_Basel_1896">Übersichtsplan 1896</option></select>
      <label class="legend">Deckkraft <input type="range" id="wmsop" min="0" max="100" value="75" aria-label="Deckkraft des Plans"></label></div>
    <div class="card"><h2>Verortet</h2><div id="stats"></div></div>
    <div class="card" id="topcard"><h2 id="toptitle">Gebäude mit den meisten Bewohnern</h2><div id="top"></div></div>
    <p class="legend">Kreisfläche ∝ Zahl der Bewohner (Gebäude) bzw. der Gebäude und Bewohner (Strassen). Klick auf einen Kreis oder einen Namen in der Liste führt zu den zugehörigen Einträgen der Kontrollseite. Verortung über Strasse + Nummer (1862) bzw. die alte Hausnummer (1841, 1850); Kleinbasel und die Bänne zählen je ab 1.</p>
  </div>
  <div id="map" role="application" aria-label="Karte"></div>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<script>
const BUILDINGS = __BUILDINGS__;
const STREETS = __STREETS__;
const SUMMARY = __SUMMARY__;
const DLS = __DLS__;
const vols = Object.keys(BUILDINGS).sort();
let mode = location.hash === '#streets' ? 'streets' : 'buildings';
let vol = vols[vols.length - 1];
const $ = id => document.getElementById(id);
const fmt = n => n.toLocaleString('de-CH');
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const map = L.map('map', { preferCanvas: true }).setView([47.5585, 7.5895], 15);
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>-Mitwirkende' }).addTo(map);
let wmsLayer = null;
function setPlan() {
  if (wmsLayer) map.removeLayer(wmsLayer); wmsLayer = null;
  const name = $('wms').value; if (!name) return;
  wmsLayer = L.tileLayer.wms('https://wms.geo.bs.ch/', { layers: name, format: 'image/png', transparent: true, maxZoom: 20, opacity: $('wmsop').value / 100, attribution: 'Historische Pläne: Geodaten Kanton Basel-Stadt' }).addTo(map);
}
$('wms').onchange = setPlan;
$('wmsop').oninput = () => { if (wmsLayer) wmsLayer.setOpacity($('wmsop').value / 100); };
setPlan();
let layer = L.layerGroup().addTo(map);
$('vol').innerHTML = vols.map(v => `<button data-v="${v}" aria-pressed="${v === vol}">${v}</button>`).join('');
// Link auf die Kontrollseite, gefiltert (wie Aarau: ?tab=…&col=…&val=…&vol=…)
function url(tab, col, val, label) { const u = new URLSearchParams({ tab, col, val, vol }); if (label) u.set('label', label); return './?' + u.toString(); }
function bPopup(p) {
  let h = `<b>${esc(p.street)} ${esc(p.no)}</b>${p.old && p.vol === '1862' ? ' (alte Nr. ' + esc(p.old) + ')' : ''}${p.name ? ' «' + esc(p.name) + '»' : ''}<br>Band ${p.vol}, <a href="${esc(DLS[p.vol] || '#')}" target="_blank" rel="noopener">PDF-S. ${p.page}</a>${p.part ? ', ' + esc(p.part) : ''}`;
  h += `<br>Eigentümer: ${esc(p.owner || '–')}${p.type ? ' (' + esc(p.type) + ')' : ''}${p.marker ? ' ' + esc(p.marker) : ''}`;
  if (p.residents.length) h += `<br>Bewohner (${p.residents.length}):<ul>` + p.residents.map(r => `<li>${esc(r)}</li>`).join('') + '</ul>';
  h += `<br><a href="${url('gebaeude', 'building_id', p.id)}">Gebäudezeile</a> · <a href="${url('gebaeude', 'street_raw', p.street, p.street)}">alle Gebäude ${esc(p.street)}</a>`;
  h += `<br><small>Verortung ${esc(p.method)} (${esc(p.conf)}) · HGB ${p.link ? '<a href="' + esc(p.link) + '" target="_blank" rel="noopener">' + esc(p.dossier) + '</a>' : esc(p.dossier)}: ${esc(p.hgb)}</small>`;
  return h;
}
function sPopup(p) {
  let h = `<b>${esc(p.street)}</b>, Band ${p.vol}<br>${fmt(p.buildings)} Gebäude verortet, ${fmt(p.residents)} Bewohnerzeilen`;
  if (p.owners.length) h += `<br><small>Eigentümer (Auswahl): ${p.owners.map(esc).join('; ')}</small>`;
  h += `<br>Einträge: <a href="${url('gebaeude', 'street_raw', p.street, p.street)}">Gebäudeverzeichnis</a>${p.vol !== '1850' ? ` · <a href="${url('einwohner', 'street_raw', p.street, p.street)}">Einwohnerverzeichnis</a>` : ''}`;
  return h;
}
function render() {
  for (const b of $('mode').children) b.setAttribute('aria-pressed', b.dataset.m === mode);
  for (const b of $('vol').children) b.setAttribute('aria-pressed', b.dataset.v === vol);
  layer.clearLayers();
  if (mode === 'buildings') {
    const feats = BUILDINGS[vol].features.slice().sort((a, b) => b.properties.n - a.properties.n);
    for (const f of feats) {
      const p = f.properties, [lon, lat] = f.geometry.coordinates;
      L.circleMarker([lat, lon], { radius: 3 + 2.2 * Math.sqrt(p.n), color: '#7a2e2e', weight: 1, fillOpacity: p.conf === 'high' ? 0.6 : 0.3 })
        .bindPopup(bPopup(p), { maxWidth: 360 }).bindTooltip(`${p.street} ${p.no} (${p.n})`).addTo(layer);
    }
    $('toptitle').textContent = 'Gebäude mit den meisten Bewohnern';
    $('top').innerHTML = feats.slice(0, 12).map(f => `<div class="stat"><span><a href="${url('gebaeude', 'building_id', f.properties.id)}">${esc(f.properties.street)} ${esc(f.properties.no)}</a></span><span>${fmt(f.properties.n)}</span></div>`).join('');
  } else {
    const feats = STREETS[vol].slice().sort((a, b) => b.weight - a.weight), maxN = Math.max(1, ...feats.map(f => f.weight));
    for (const p of feats) {
      L.circleMarker([p.lat, p.lon], { radius: 3 + 26 * Math.sqrt(p.weight / maxN), color: '#2f5f8f', weight: 1, fillOpacity: 0.45 })
        .bindPopup(sPopup(p), { maxWidth: 340 }).bindTooltip(`${p.street} (${fmt(p.weight)})`).addTo(layer);
    }
    $('toptitle').textContent = 'Strassen mit den meisten Gebäuden und Bewohnern';
    $('top').innerHTML = feats.slice(0, 12).map(p => `<div class="stat"><span><a href="${url('gebaeude', 'street_raw', p.street, p.street)}">${esc(p.street)}</a></span><span>${fmt(p.weight)}</span></div>`).join('');
  }
  const s = SUMMARY[vol] || { located: 0, total: 0, high: 0 }, pct = s.total ? Math.round(100 * s.located / s.total) : 0;
  $('stats').innerHTML = `<div class="stat"><span>${mode === 'buildings' ? 'Gebäude' : 'Strassen'} auf der Karte</span><span>${fmt(mode === 'buildings' ? BUILDINGS[vol].features.length : STREETS[vol].length)}</span></div><div class="stat"><span>Gebäude verortet</span><span>${fmt(s.located)} von ${fmt(s.total)} (${pct} %)</span></div><div class="bar" style="width:${pct}%"></div><div class="stat"><span>davon eindeutig</span><span>${fmt(s.high)}</span></div><div class="stat"><span>ohne Koordinate (nicht auf der Karte)</span><span>${fmt(s.total - s.located)}</span></div>`;
}
$('mode').addEventListener('click', e => { const b = e.target.closest('button'); if (!b) return; mode = b.dataset.m; history.replaceState(null, '', mode === 'streets' ? '#streets' : '#'); render(); });
$('vol').addEventListener('click', e => { const b = e.target.closest('button'); if (!b) return; vol = b.dataset.v; render(); });
render();
</script>
"""

DLS = {"1841": "https://dls.staatsarchiv.bs.ch/records/1225921", "1850": "https://dls.staatsarchiv.bs.ch/records/1225925",
       "1862": "https://dls.staatsarchiv.bs.ch/records/1225927"}


def streets_of(fc: dict) -> list[dict]:
    """Gebäude je Strasse zusammenfassen: Schwerpunkt, Zahl der Gebäude und Bewohner."""
    g = defaultdict(list)
    for f in fc["features"]:
        p = f["properties"]
        if p["street"]:
            g[p["street"]].append(f)
    out = []
    for street, fs in g.items():
        lon = sum(f["geometry"]["coordinates"][0] for f in fs) / len(fs)
        lat = sum(f["geometry"]["coordinates"][1] for f in fs) / len(fs)
        res = sum(f["properties"]["n"] for f in fs)
        owners = sorted({f["properties"]["owner"] for f in fs if f["properties"]["owner"]})[:6]
        out.append({"street": street, "vol": fs[0]["properties"]["vol"], "lat": round(lat, 6), "lon": round(lon, 6),
                    "buildings": len(fs), "residents": res, "weight": len(fs) + res, "owners": owners})
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    buildings = {p.stem.replace("buildings_", ""): json.loads(p.read_text(encoding="utf-8"))
                 for p in sorted(GEO_DIR.glob("buildings_*.geojson"))}
    streets = {v: streets_of(fc) for v, fc in buildings.items()}
    summary = json.loads((GEO_DIR / "summary.json").read_text(encoding="utf-8"))
    html = (TEMPLATE.replace("__BUILDINGS__", json.dumps(buildings, ensure_ascii=False, separators=(",", ":")))
            .replace("__STREETS__", json.dumps(streets, ensure_ascii=False, separators=(",", ":")))
            .replace("__SUMMARY__", json.dumps(summary, ensure_ascii=False))
            .replace("__DLS__", json.dumps(DLS))
            .replace("__DATE__", date.today().strftime("%d.%m.%Y")))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(html, encoding="utf-8")
    print(f"→ {args.out} ({args.out.stat().st_size / 1e6:.2f} MB; "
          + ", ".join(f"{v}: {len(fc['features'])} Gebäude, {len(streets[v])} Strassen" for v, fc in buildings.items()) + ")")


if __name__ == "__main__":
    main()
