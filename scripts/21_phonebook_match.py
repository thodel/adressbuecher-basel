"""21_phonebook_match.py — Telefonbuch-Abonnenten (20_phonebook_basel.csv) gegen das Adressbuch 1862.

Abgleich über normalisierten Familiennamen (umlautfrei, ohne Allianzname), normalisierte
Strasse (wie 10_geo_hgb.norm_street; Abkürzungen «g.», «str.» aufgelöst) und Hausnummer.
Gegenseite: Einwohnerverzeichnis 1862 (04_entries), Eigentümer und Bewohner des
Häuserverzeichnisses 1862 (05_buildings, 05_residents). Stufen:

    name_addr    gleicher Familienname an derselben Adresse (Strasse + Nummer)
    name_street  gleicher Familienname in derselben Strasse
    addr         dieselbe Adresse, anderer Name (Haus-Kontinuität)
    none         kein Treffer

Schreibt data/csv/20_phonebook_links.csv (eine Zeile je Abonnent) und druckt die Deckung je Jahr.
"""
from __future__ import annotations

import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from importlib import import_module
norm_street = import_module("10_geo_hgb").norm_street

CSV_DIR = Path("data/csv")


def fold(s: str) -> str:
    s = s.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss").replace("é", "e").replace("è", "e")
    return re.sub(r"[^a-z]", "", s.split("-")[0])


def street_key(s: str) -> str:
    s = re.sub(r"g\.(?=\s|$)", "gasse", s)
    s = re.sub(r"(?i)str\.(?=\s|$)", "strasse", s)
    s = re.sub(r"(?i)-?vorst\.?(?=\s|$)", "vorstadt", s)
    s = re.sub(r"(?i)pl\.(?=\s|$)", "platz", s)
    return norm_street(s)


def main() -> None:
    by_addr, by_street = defaultdict(set), defaultdict(set)
    def add(surname, street, no, ref):
        if not surname:
            return
        sk = street_key(street) if street else ""
        if sk and no:
            by_addr[(sk, re.sub(r"\s", "", no).lower())].add((fold(surname), ref))
        if sk:
            by_street[sk].add((fold(surname), ref))
    with (CSV_DIR / "04_entries.csv").open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["volume"] == "1862":
                add(r["surname"], r["street_raw"], r["building_no"], r["entry_id"])
    with (CSV_DIR / "05_buildings.csv").open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["volume"] == "1862":
                add(r["owner_surname"], r["street_raw"], r["building_no"], r["building_id"])
    with (CSV_DIR / "05_residents.csv").open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["volume"] == "1862":
                add(r["surname"], r["street_raw"], r["building_no"], r["entry_id"])

    out, stats = [], defaultdict(Counter)
    with (CSV_DIR / "20_phonebook_basel.csv").open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            s, sk, no = fold(r["surname"]), street_key(r["street_raw"]) if r["street_raw"] else "", re.sub(r"\s", "", r["building_no"]).lower()
            level, refs = "none", []
            if sk and no and (sk, no) in by_addr:
                cands = by_addr[(sk, no)]
                hit = [ref for (n, ref) in cands if s and n == s]
                if hit:
                    level, refs = "name_addr", hit
                else:
                    level, refs = "addr", [ref for (_, ref) in cands]
            if level in ("none", "addr") and sk and s and sk in by_street:
                hit = [ref for (n, ref) in by_street[sk] if s and n == s]
                if hit:
                    level, refs = "name_street", hit
            out.append({**{k: r[k] for k in ("pb_id", "year", "batch", "surname", "alliance_name", "forename", "occupation_raw", "street_raw", "building_no", "entry_type", "parse_confidence")},
                        "match_level": level, "match_refs": ";".join(sorted(set(refs))[:5]), "n_refs": len(set(refs))})
            stats[r["year"]][level] += 1
            stats[r["year"]]["with_addr" if (sk and no) else "no_addr"] += 1
    hits = [r for r in out if r["match_level"] != "none"]
    with (CSV_DIR / "20_phonebook_links.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0])); w.writeheader(); w.writerows(hits)
    with (CSV_DIR / "20_phonebook_summary.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["year", "batch", "entries", "with_address", "name_addr", "name_street", "addr"])
        print("Jahr   gesamt mitAdr  name_addr name_street addr")
        for y in sorted(stats):
            c = stats[y]; tot = sum(c[k] for k in ("none", "addr", "name_addr", "name_street"))
            w.writerow([y, "A" if int(y) <= 1910 else "B", tot, c["with_addr"], c["name_addr"], c["name_street"], c["addr"]])
            print(f"{y}  {tot:6d} {c['with_addr']:6d}  {c['name_addr']:6d} {c['name_street']:8d} {c['addr']:6d}")
    print(f"{len(hits)} Treffer von {len(out)} Abonnenten → {CSV_DIR / '20_phonebook_links.csv'}, Übersicht 20_phonebook_summary.csv")


if __name__ == "__main__":
    main()
