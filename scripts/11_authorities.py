"""11_authorities.py — Personen der Adressbücher mit Wikidata, HLS und Metagrid verknüpfen.

    python scripts/11_authorities.py fetch      # Kandidaten aus Wikidata (SPARQL, Cache data/ext/wikidata/)
    python scripts/11_authorities.py link       # Abgleich → data/csv/10_authority_links.csv
    python scripts/11_authorities.py metagrid   # Metagrid-Konkordanz für Treffer mit HLS-Nummer

Übernommen aus adressbuecher-aarau (gleiche Spalten in 10_authority_links.csv), angepasst an
Basel 1841–1862. **Kandidaten.** Personen in Wikidata (Mensch, geboren 1750–1844, gestorben
1841 oder später bzw. ohne Sterbedatum), die entweder einen Basel-Bezug haben (Geburts-,
Sterbe-, Wohn-, Wirkungs- oder Heimatort Basel, Q78) oder einen HLS-Eintrag (P902). Aus Wikidata kommen Vor- und
Familienname, Lebensdaten, HLS-Nummer, GND, Heimatort (P1321), Geburtsort, Berufe.

**Abgleich je Adressbuch-Eintrag** (Einwohnerverzeichnis, Bewohner des Gebäudeverzeichnisses
und — Basel — Amtsträger der Behördenverzeichnisse 1850/1862 aus 30_authority_candidates.csv,
kind «behoerden», entry_id = cand_id):
- Familienname gleich (normalisiert, Allianzname nicht), erster Vorname gleich oder als
  Initiale/Abkürzung verträglich (Hrch. ~ Heinrich), sonst kein Kandidat.
- Lebensdaten: die Person lebte im Bandjahr und war mindestens 18 (bei «Sohn»/«Tochter»
  mindestens 14); widersprechende Daten schliessen aus.
- Belege: Basel-Bezug in Wikidata (+3), Heimatort des Eintrags = Heimat- oder Geburtsort in
  Wikidata (+3), Allianzname des Eintrags im Wikidata-Namen (+2, Basel), Beruf passt (+1),
  voller Vorname statt Initiale (+1).
- Basel: Amtsträger der Behördenverzeichnisse erhalten «Basler Amt» (+3) wie einen
  Basel-Bezug; ein Allianzname, der dem Allianznamen in Wikidata widerspricht, schliesst aus.
- Basel: Mindestalter 21 (Amtsträger 25); je Person, Band und Art nur der beste Eintrag
  «wahrscheinlich» (Namensvettern, Väter); HLS-Treffer werden am HLS-Artikel über den HLS-MCP
  geprüft (32_hls_check.csv): «falsch» → `verworfen`, «zweifelhaft» → `möglich`; Spalte `hls_check`.
- `tier`: **wahrscheinlich** = Name + Lebensdaten + Basel-Bezug, Basler Amt oder Heimatort, und nur ein
  solcher Kandidat — Basel: bei mehreren Kandidaten nur mit weiterem Beleg (Allianzname, Beruf, Heimatort); **möglich** = Name + Lebensdaten + nur schwache Belege, oder mehrere
  gleich gute Kandidaten. Nur «wahrscheinlich» wird auf der Kontrollseite verlinkt.
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

CSV_DIR = Path("data/csv")
EXT = Path("data/ext/wikidata")
OUT = CSV_DIR / "10_authority_links.csv"
UA = "adressbuecher-basel/0.1 (https://github.com/thodel/adressbuecher-basel)"
SPARQL = "https://query.wikidata.org/sparql"
BASEL = "Q78"

WINDOW = "FILTER(YEAR(?b) >= 1750 && YEAR(?b) <= 1844 && (!BOUND(?d) || YEAR(?d) >= 1841))"
ID_QUERIES = {
    "basel": "SELECT DISTINCT ?p WHERE { VALUES ?rel { wdt:P19 wdt:P20 wdt:P551 wdt:P937 wdt:P1321 } ?p ?rel wd:Q78 . "
             "?p wdt:P31 wd:Q5; wdt:P569 ?b . OPTIONAL { ?p wdt:P570 ?d } " + WINDOW + " }",
    "hls": "SELECT DISTINCT ?p WHERE { ?p wdt:P902 ?h; wdt:P569 ?b . OPTIONAL { ?p wdt:P570 ?d } " + WINDOW + " }",
}
DETAIL = """SELECT ?p (SAMPLE(?lbl) AS ?label) (SAMPLE(?b) AS ?birth) (SAMPLE(?d) AS ?death) (SAMPLE(?hls) AS ?hls)
  (SAMPLE(?gnd) AS ?gnd) (GROUP_CONCAT(DISTINCT ?gn; separator="|") AS ?given) (GROUP_CONCAT(DISTINCT ?fn; separator="|") AS ?family)
  (GROUP_CONCAT(DISTINCT ?occ; separator="|") AS ?occupations) (GROUP_CONCAT(DISTINCT ?orig; separator="|") AS ?origins)
  (SAMPLE(?bpl) AS ?birthplace) (MAX(?basel) AS ?basel_rel) (SAMPLE(?desc) AS ?description)
WHERE {
  VALUES ?p { %s }
  OPTIONAL { ?p wdt:P569 ?b } OPTIONAL { ?p wdt:P570 ?d }
  OPTIONAL { ?p rdfs:label ?lbl FILTER(LANG(?lbl) = "de") }
  OPTIONAL { ?p schema:description ?desc FILTER(LANG(?desc) = "de") }
  OPTIONAL { ?p wdt:P902 ?hls } OPTIONAL { ?p wdt:P227 ?gnd }
  OPTIONAL { ?p wdt:P735 ?g . ?g rdfs:label ?gn FILTER(LANG(?gn) IN ("de","mul","en")) }
  OPTIONAL { ?p wdt:P734 ?f . ?f rdfs:label ?fn FILTER(LANG(?fn) IN ("de","mul","en")) }
  OPTIONAL { ?p wdt:P106 ?o . ?o rdfs:label ?occ FILTER(LANG(?occ) = "de") }
  OPTIONAL { ?p wdt:P1321 ?op . ?op rdfs:label ?orig FILTER(LANG(?orig) = "de") }
  OPTIONAL { ?p wdt:P19 ?bp . ?bp rdfs:label ?bpl FILTER(LANG(?bpl) = "de") }
  OPTIONAL { VALUES ?rel { wdt:P19 wdt:P20 wdt:P551 wdt:P937 wdt:P1321 } ?p ?rel wd:Q78 . BIND(1 AS ?basel) }
} GROUP BY ?p"""


def sparql(q: str) -> list[dict]:
    data = urllib.parse.urlencode({"query": q}).encode()
    req = urllib.request.Request(SPARQL, data=data, headers={"User-Agent": UA, "Accept": "application/sparql-results+json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        res = json.loads(r.read().decode("utf-8"))
    return [{k: v["value"] for k, v in b.items()} for b in res["results"]["bindings"]]


def fetch() -> None:
    EXT.mkdir(parents=True, exist_ok=True)
    for name, q in ID_QUERIES.items():
        out_p = EXT / f"candidates_{name}.json"
        if out_p.exists():
            print(f"{name}: vorhanden ({out_p})"); continue
        ids = sorted({r["p"].rsplit("/", 1)[-1] for r in sparql(q)})
        print(f"{name}: {len(ids)} Kennungen")
        rows = []
        for i in range(0, len(ids), 250):
            batch = " ".join(f"wd:{x}" for x in ids[i:i + 250])
            for attempt in range(3):
                try:
                    rows.extend(sparql(DETAIL % batch)); break
                except Exception as exc:  # noqa: BLE001
                    print(f"   ! Paket {i}: {exc}; neuer Versuch"); time.sleep(10)
            time.sleep(1.5)
            print(f"   {min(i + 250, len(ids))}/{len(ids)}", end="\r")
        out_p.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
        print(f"\n{name}: {len(rows)} Personen mit Angaben → {out_p}")


# ── Namen ────────────────────────────────────────────────────────────────

ABBR = {"hieron": "hieronymus", "leonh": "leonhard", "nikl": "niklaus", "nik": "niklaus", "eman": "emanuel", "eml": "emanuel",
        "andr": "andreas", "ludw": "ludwig", "benedikt": "benedikt", "bened": "benedikt", "dan": "daniel", "matth": "matthias",
        "hrch": "heinrich", "hch": "heinrich", "joh": "johann", "jb": "jakob", "jak": "jakob", "fr": "friedrich",
        "friedr": "friedrich", "gottl": "gottlieb", "gottfr": "gottfried", "rud": "rudolf", "sam": "samuel",
        "wilh": "wilhelm", "ed": "eduard", "alb": "albert", "jos": "josef", "ferd": "ferdinand", "herm": "hermann",
        "theod": "theodor", "carl": "karl", "ulr": "ulrich", "chr": "christian", "christ": "christian",
        "sl": "samuel", "abr": "abraham", "phil": "philipp", "aug": "august", "alfr": "alfred", "em": "emil",
        "gust": "gustav", "ad": "adolf", "conr": "konrad", "konr": "konrad", "max": "max", "jul": "julius"}


def nk(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    s = s.replace("ss", "s").replace("th", "t").replace("ck", "k").replace("y", "i").replace("ph", "f").replace("c", "k")
    return re.sub(r"[^a-z]", "", s)


def uk(s: str) -> str:
    """umlautneutraler Namensschlüssel: «Stähelin» = «Staehelin»"""
    return nk((s or "").lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue"))


def first_forename(s: str) -> tuple[str, bool]:
    """→ (Schlüssel, ist_voll); «Hrch.» → heinrich (voll=False), «J.» → j (Initiale)"""
    tok = (s or "").replace(",", " ").split()
    if not tok:
        return "", False
    t = tok[0].rstrip(".")
    low = t.lower()
    if low in ABBR:
        return nk(ABBR[low]), False
    full = not tok[0].endswith(".") and len(t) > 2
    return nk(t), full


def forename_ok(entry_fk: str, entry_full: bool, cand_given: list[str]) -> tuple[bool, bool]:
    """→ (passt, voll)"""
    for g in cand_given:
        gk = nk(g.split()[0]) if g else ""
        if not gk or not entry_fk:
            continue
        if entry_fk == gk:
            return True, True
        if not entry_full and (gk.startswith(entry_fk) or entry_fk.startswith(gk[:3])) and len(entry_fk) >= 1:
            return True, False
    return False, False


def cand_names(c: dict) -> tuple[list[str], list[str]]:
    given = [g for g in c.get("given", "").split("|") if g]
    family = [f for f in c.get("family", "").split("|") if f]
    lbl = c.get("label", "")
    if lbl and " " in lbl:
        parts = lbl.split()
        if not given:
            given = [parts[0]]
        family = family or [parts[-1]]
        family.append(parts[-1])
    return given, family


def year(s: str) -> int | None:
    m = re.match(r"^-?(\d{4})", s or "")
    return int(m.group(1)) if m else None


def load_candidates() -> list[dict]:
    seen, out = set(), []
    for f in sorted(EXT.glob("candidates_*.json")):
        for c in json.loads(f.read_text(encoding="utf-8")):
            q = c["p"].rsplit("/", 1)[-1]
            if q in seen:
                continue
            seen.add(q)
            c["qid"] = q
            c["by"], c["dy"] = year(c.get("birth", "")), year(c.get("death", ""))
            c["given_l"], c["family_l"] = cand_names(c)
            out.append(c)
    return out


def load_entries() -> list[dict]:
    rows = []
    for f in sorted(glob.glob(str(CSV_DIR / "04_entries*.csv")) + glob.glob(str(CSV_DIR / "05_residents*.csv"))):
        if "_probe" in f:
            continue
        kind = "einwohner" if "04_entries" in f else "bewohner"
        with open(f, encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if r.get("entry_type") == "firma" or not r.get("surname"):
                    continue
                if r.get("address_seq") not in (None, "", "1"):
                    continue
                r["_kind"] = kind
                rows.append(r)
    p = CSV_DIR / "30_authority_candidates.csv"            # Basel: Amtsträger der Behördenverzeichnisse
    if p.exists():
        with p.open(encoding="utf-8") as fh:
            for c in csv.DictReader(fh):
                if "behoerden" not in c["sources"]:
                    continue
                for v in (c.get("office_volumes") or c["volumes"]).split(";"):
                    rows.append({"entry_id": f"{c['cand_id']}-{v}", "volume": v, "surname": c["surname"],
                                 "alliance_name": c["alliance_name"], "forename": c["forename"],
                                 "occupation_raw": c["roles"][:200], "origin_raw": "", "origin_canton": "",
                                 "relation": "", "_kind": "behoerden"})
    origins = {}
    p = CSV_DIR / "06_origins.csv"
    if p.exists():
        with p.open(encoding="utf-8") as fh:
            for o in csv.DictReader(fh):
                origins[(o["origin_raw"], o["origin_canton"])] = o["origin_norm"]
    for r in rows:
        r["_origin"] = origins.get((r.get("origin_raw", ""), r.get("origin_canton", "")), r.get("origin_raw", ""))
    return rows


def occ_match(entry_occ: str, cand_occ: str) -> bool:
    e = nk(entry_occ)
    for o in cand_occ.split("|"):
        ok = nk(o)
        if len(ok) >= 5 and (ok[:6] in e or (len(e) >= 5 and e[:6] in ok)):
            return True
    return False


def link() -> None:
    cands = load_candidates()
    by_fam: dict[str, list[dict]] = defaultdict(list)
    for c in cands:
        for f in set(nk(x) for x in c["family_l"]):
            if f:
                by_fam[f].append(c)
    rows = load_entries()
    out = []
    for r in rows:
        fam = nk(r["surname"])
        pool = by_fam.get(fam, [])
        if not pool:
            continue
        fk, full = first_forename(r.get("forename", ""))
        if not fk:
            continue
        vol = int(r["volume"])
        # Basel: Mindestalter 21 (Amtsträger 25); in der HLS-Prüfung waren 19-/20-jährige Studenten falsch verknüpft
        min_age = 14 if r.get("relation") in ("Sohn", "Tochter") else (25 if r["_kind"] == "behoerden" else 21)
        scored = []
        for c in pool:
            ok, full_match = forename_ok(fk, full, c["given_l"])
            if not ok:
                continue
            if c["by"] is None or c["by"] > vol - min_age or (c["dy"] is not None and c["dy"] < vol):
                continue
            ev, score = [], 0
            if c.get("basel_rel") == "1":
                ev.append("Basel-Bezug"); score += 3
            if r["_kind"] == "behoerden":
                ev.append("Basler Amt"); score += 3      # das Amt im Behördenverzeichnis ist selbst ein Basel-Bezug
            # Allianzname (Basel): mit dem Doppelnamen im Wikidata-Label vergleichen («Rudolf Staehelin-Stockmeyer»),
            # umlautneutral; ein widersprechender Allianzname schliesst aus
            al = uk(r.get("alliance_name", ""))
            wd_al = ""
            for n in [c.get("label", "")] + c.get("family", "").split("|"):
                last = n.split()[-1] if n.split() else ""
                if "-" in last and uk(last.split("-")[0]) == uk(r["surname"]):
                    wd_al = uk(last.split("-", 1)[1]); break
            if al and wd_al:
                if al == wd_al:
                    ev.append("Allianzname"); score += 2
                else:
                    continue
            origin_e = nk(r["_origin"])
            if origin_e and (origin_e in [nk(x) for x in c.get("origins", "").split("|") if x] or origin_e == nk(c.get("birthplace", ""))):
                ev.append("Heimatort"); score += 3
            if r.get("occupation_raw") and c.get("occupations") and occ_match(r["occupation_raw"], c["occupations"]):
                ev.append("Beruf"); score += 1
            if full_match:
                score += 1
            scored.append((score, ev, c, full_match))
        if not scored:
            continue
        scored.sort(key=lambda x: -x[0])
        best = scored[0]
        strong = [s for s in scored if ("Basel-Bezug" in s[1] or "Basler Amt" in s[1] or "Heimatort" in s[1])]
        # Basel: der Basel-Bezug trennt Namensvettern nicht — bei mehreren Kandidaten braucht der beste
        # einen weiteren Beleg (Allianzname, Beruf, Heimatort)
        extra = {"Allianzname", "Beruf", "Heimatort"} & set(best[1])
        if (strong and len([s for s in strong if s[0] == strong[0][0]]) == 1 and best is strong[0]
                and (len(scored) == 1 or extra)):
            tier = "wahrscheinlich"
        else:
            tier = "möglich"
        c = best[2]
        out.append({"entry_id": r["entry_id"], "kind": r["_kind"], "volume": r["volume"], "surname": r["surname"] + (("-" + r["alliance_name"]) if r.get("alliance_name") else ""),
                    "forename": r.get("forename", ""), "occupation": r.get("occupation_raw", ""), "origin": r["_origin"],
                    "qid": c["qid"], "label": c.get("label", ""), "birth": c["by"] or "", "death": c["dy"] or "",
                    "hls_id": c.get("hls", ""), "gnd": c.get("gnd", ""), "wd_description": c.get("description", ""),
                    "wd_occupations": c.get("occupations", "")[:120], "evidence": "+".join(best[1]) or "nur Name+Daten",
                    "score": best[0], "n_candidates": len(scored), "tier": tier})
    # Basel: je Person, Band und Art nur der beste Eintrag «wahrscheinlich» — gleichnamige Väter und Handwerker
    # hängen sonst an der bekannten Person; bei Gleichstand alle «möglich»
    best_sc: dict = defaultdict(list)
    for o in out:
        if o["tier"] == "wahrscheinlich":
            best_sc[(o["qid"], o["volume"], o["kind"])].append(o)
    for grp in best_sc.values():
        if len(grp) > 1:
            top = max(int(o["score"]) for o in grp)
            tops = [o for o in grp if int(o["score"]) == top]
            for o in grp:
                if o not in tops or len(tops) > 1:
                    o["tier"] = "möglich"; o["evidence"] += " (Namensvetter im Band)"
    # Basel: Urteil der HLS-Prüfung über den HLS-MCP (32_hls_check.csv) übernehmen
    chk = {}
    if (CSV_DIR / "32_hls_check.csv").exists():
        with (CSV_DIR / "32_hls_check.csv").open(encoding="utf-8") as fh:
            chk = {r["hls_article"].zfill(6): r for r in csv.DictReader(fh)}
    for o in out:
        h = str(o["hls_id"]).zfill(6) if o["hls_id"] else ""
        v = chk.get(h, {}).get("verdict", "") if h else ""
        o["hls_check"] = (v + ": " + chk[h].get("note", "")) if v else ("ungeprüft" if h else "")
        if o["tier"] == "wahrscheinlich" and v == "falsch":
            o["tier"] = "verworfen"
        elif o["tier"] == "wahrscheinlich" and v == "zweifelhaft":
            o["tier"] = "möglich"
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys()) if out else ["entry_id"])
        w.writeheader(); w.writerows(out)
    c = Counter(x["tier"] for x in out)
    persons = len({x["qid"] for x in out if x["tier"] == "wahrscheinlich"})
    print(f"{len(rows)} Personen-Einträge geprüft, {len(cands)} Wikidata-Kandidaten → {len(out)} Treffer {dict(c)}; "
          f"{persons} verschiedene Personen «wahrscheinlich» → {OUT}")


def metagrid() -> None:
    with OUT.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    cache_p = EXT / "metagrid_cache.json"
    cache = json.loads(cache_p.read_text(encoding="utf-8")) if cache_p.exists() else {}
    ids = sorted({r["hls_id"] for r in rows if r["tier"] == "wahrscheinlich" and r["hls_id"]})
    for h in ids:
        if h in cache:
            continue
        url = f"https://api.metagrid.ch/widget/hls-dhs-dss/person/{int(h)}.json?lang=de&include=true"
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30) as r:
                data = json.loads(r.read().decode("utf-8"))
            links = {k: v["url"] for d in data for k, v in d.items()} if isinstance(data, list) else {}
        except Exception as exc:  # noqa: BLE001
            print(f"  ! {h}: {exc}"); links = None
        if links is not None:
            cache[h] = links
        time.sleep(0.5)
    cache_p.write_text(json.dumps(cache, ensure_ascii=False, indent=0), encoding="utf-8")
    for r in rows:
        r["metagrid"] = json.dumps(cache.get(r["hls_id"], {}), ensure_ascii=False) if r["hls_id"] else ""
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"Metagrid: {len(ids)} HLS-Nummern, {sum(1 for h in ids if cache.get(h))} mit Konkordanz")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["fetch", "link", "metagrid"])
    a = ap.parse_args()
    {"fetch": fetch, "link": link, "metagrid": metagrid}[a.cmd]()


if __name__ == "__main__":
    main()
