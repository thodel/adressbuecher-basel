"""31_metagrid_match.py — Kandidaten (30_authority_candidates.csv) über Metagrid mit HLS, GND, Wikidata verknüpfen.

Metagrid (https://api.metagrid.ch, ohne Schlüssel) liefert je Suchtreffer eine Konkordanz:
Name, Lebensdaten und die Normdaten aller beteiligten Anbieter (hls-dhs-dss, gnd, wikidata,
hfls, elites-suisses …). Bewertung je Konkordanz:

    Name      Familienname muss passen; hat der Eintrag einen Allianznamen, muss er im
              Metagrid-Namen stehen (Basler Doppelnamen sind trennscharf); zwei verschiedene
              Allianznamen schliessen sich aus.
    Vorname   jede Vornamensform des Eintrags («Joh. Jak.», «Wilh.») muss einen Metagrid-Vornamen
              als Präfix treffen (C/K, I/J, ph/f, y/i gleichgesetzt).
    Daten     geboren spätestens 16 Jahre vor dem ersten Band, gestorben nicht vor dem letzten
              Band (soweit bekannt).

Stufen: `sicher` (genau eine datierte Person, Vorname ausgeschrieben, beide Lebensdaten passen),
`wahrscheinlich` (genau eine, aber nur Initialen oder ein Lebensdatum), `mehrdeutig` (mehrere
datierte Personen passen; Alternativen gelistet), `unsicher` (nur undatierte Namensgleichheit),
`kein`. Konkordanzen mit gleichem Namen und gleichen Lebensjahren gelten als eine Person. Antworten werden in data/ext/metagrid_cache.json
zwischengespeichert. Schreibt data/csv/31_links_metagrid.csv.

    python scripts/31_metagrid_match.py [--workers 4]
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import threading
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

CSV_DIR = Path("data/csv")
CACHE = Path("data/ext/metagrid_cache.json")
API = "https://api.metagrid.ch/search"
UA = "adressbuecher-basel/1.0 (Universitaet Bern, Digital Humanities; research)"
OUT = CSV_DIR / "31_links_metagrid.csv"
FIELDS = ["cand_id", "surname", "alliance_name", "forename", "title", "volumes", "roles", "sources", "n_mentions",
          "level", "n_matches", "mg_id", "mg_name", "birth", "death", "hls_url", "hls_article", "gnd", "wikidata",
          "providers", "alternatives", "query"]
lock = threading.Lock()


def fold(s: str) -> str:
    s = s.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss").replace("é", "e").replace("è", "e")
    s = s.replace("ph", "f").replace("th", "t").replace("c", "k").replace("y", "i").replace("ck", "k")
    return re.sub(r"[^a-z]", "", s)


def year(d: str) -> int | None:
    m = re.search(r"(\d{4})", d or "")
    return int(m.group(1)) if m else None


def forename_ok(cand: str, mg: str) -> tuple[bool, bool]:
    """(passt, ausgeschrieben). Jede Form des Eintrags muss Präfix eines Metagrid-Vornamens sein."""
    ctoks = [t for t in re.split(r"[\s.]+", cand) if t]
    if not ctoks:
        return True, False
    mtoks = [x for x in (fold(t) for t in re.split(r"[\s\-]+", mg or "")) if x]
    if not mtoks:
        return False, False
    full = all(len(t) > 2 for t in ctoks)
    for t in ctoks:
        ft = fold("j" + t[1:] if t[0] in "Ii" and len(t) <= 3 else t)
        if not any(m.startswith(ft) or (len(ft) > 3 and ft.startswith(m)) for m in mtoks):
            return False, full
    return True, full


def search(q: str, cache: dict) -> list[dict]:
    with lock:
        if q in cache:
            return cache[q]
    url = API + "?" + urllib.parse.urlencode({"query": q, "group": 1, "take": 25})
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read().decode("utf-8"))
            res = data.get("concordances", [])
            break
        except Exception:
            time.sleep(2 + 3 * attempt)
            res = None
    if res is None:
        return []
    slim = []
    for c in res:
        md = next((x.get("metadata") for x in c.get("resources", []) if x.get("metadata", {}).get("last_name")), {}) or {}
        links = {}
        for x in c.get("resources", []):
            links.setdefault(x["provider"]["slug"], x.get("link", {}).get("uri", ""))
        slim.append({"id": c.get("id"), "name": c.get("name", ""), "first": md.get("first_name", ""), "last": md.get("last_name", ""),
                     "birth": md.get("birth_date", ""), "death": md.get("death_date", ""), "links": links})
    with lock:
        cache[q] = slim
    time.sleep(0.25)
    return slim


def evaluate(c: dict, conc: list[dict]) -> list[tuple[dict, bool, bool]]:
    s, a = fold(c["surname"]), fold(c["alliance_name"])
    vols = [int(v) for v in c["volumes"].split(";") if v]
    y0, y1 = min(vols), max(vols)
    out = []
    for k in conc:
        parts = [fold(p) for p in re.split(r"[-(+)]", k["last"]) if p.strip()]
        if not parts or parts[0] != s:
            continue
        if a and a not in parts[1:]:
            continue
        if not a and len(parts) > 1 and parts[1]:
            pass                                          # Eintrag ohne Allianz: Metagrid-Allianz erlaubt (Allianz oft nicht gedruckt)
        ok, full = forename_ok(c["forename"], k["first"])
        if not ok:
            continue
        b, d = year(k["birth"]), year(k["death"])
        if b is not None and b > y0 - 16:
            continue
        if d is not None and d < y1:
            continue
        if b is not None and b < y0 - 95:
            continue
        out.append((k, full, b is not None and d is not None))
    return out


def merge_same(matches):
    """Konkordanzen derselben Person zusammenführen (gleicher Familienname und beide Lebensjahre gleich;
    ohne Daten: gleiche Vornamen), HLS und mehr Normdaten bevorzugen. Datierte Treffer verdrängen undatierte."""
    best = {}
    for k, full, dated in matches:
        b, d = year(k["birth"]), year(k["death"])
        last0 = fold(re.split(r"[-(]", k["last"])[0])
        key = (last0, b, d) if (b and d) else (fold(k["first"]), fold(k["last"]), b, d)
        prev = best.get(key)
        if prev is None or (("hls-dhs-dss" in k["links"]) and "hls-dhs-dss" not in prev[0]["links"]) or len(k["links"]) > len(prev[0]["links"]):
            best[key] = (k, full, dated)
    vals = list(best.values())
    both = [v for v in vals if year(v[0]["birth"]) and year(v[0]["death"])]
    one = [v for v in vals if (year(v[0]["birth"]) or year(v[0]["death"])) and v not in both]
    return both or one or vals


def queries(c: dict) -> list[str]:
    name = c["surname"] + ("-" + c["alliance_name"] if c["alliance_name"] else "")
    first = [t for t in c["forename"].split() if len(t.rstrip(".")) > 2 and not t.endswith(".")]
    qs = []
    if first:
        qs.append(" ".join(first) + " " + name)
    if c["alliance_name"]:
        qs.append(name)
    qs.append((first[0] + " " if first else "") + c["surname"])
    if not first:
        qs.append(c["surname"])
    return list(dict.fromkeys(qs))


def match(c: dict, cache: dict) -> dict:
    found, used = [], []
    for q in queries(c):
        used.append(q)
        found = merge_same(evaluate(c, search(q, cache)))
        if found:
            break
    row = {k: c[k] for k in ("cand_id", "surname", "alliance_name", "forename", "title", "volumes", "roles", "sources", "n_mentions")}
    row.update({"level": "kein", "n_matches": len(found), "query": " || ".join(used)})
    if found:
        found.sort(key=lambda x: (("hls-dhs-dss" not in x[0]["links"]), -len(x[0]["links"])))
        k, full, dated = found[0]
        any_date = year(k["birth"]) or year(k["death"])
        if not any_date:
            row["level"] = "unsicher"                     # nur Namensgleichheit, keine Lebensdaten
        elif len(found) > 1:
            row["level"] = "mehrdeutig"
        else:
            row["level"] = "sicher" if full and dated else "wahrscheinlich"
        hls = k["links"].get("hls-dhs-dss", "")
        m = re.search(r"/articles/(\d+)", hls)
        row.update({"mg_id": k["id"], "mg_name": k["name"], "birth": k["birth"], "death": k["death"], "hls_url": hls,
                    "hls_article": m.group(1) if m else "", "gnd": k["links"].get("gnd", ""), "wikidata": k["links"].get("wikidata", ""),
                    "providers": ";".join(sorted(k["links"])),
                    "alternatives": " | ".join(f"{x[0]['name']}" for x in found[1:6])})
    return row


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    with (CSV_DIR / "30_authority_candidates.csv").open(encoding="utf-8") as fh:
        cands = list(csv.DictReader(fh))
    if args.limit:
        cands = cands[: args.limit]
    rows, done = [], 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for row in ex.map(lambda c: match(c, cache), cands):
            rows.append(row); done += 1
            if done % 100 == 0:
                print(f"  {done}/{len(cands)}", flush=True)
                with lock:
                    CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    from collections import Counter
    lv = Counter(r["level"] for r in rows)
    print(f"{len(rows)} Kandidaten → {OUT}: {dict(lv)}; mit HLS-Artikel {sum(1 for r in rows if r.get('hls_article'))}")


if __name__ == "__main__":
    main()
