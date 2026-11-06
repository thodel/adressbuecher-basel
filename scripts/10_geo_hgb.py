"""10_geo_hgb.py — Gebäude über das Historische Grundbuch Basel (HGB) verorten.

Die HGB-Dossiers des Staatsarchivs (data/ext/hgb/, Projekt «Ökonomien des Raums») tragen
als Titel die Adresse nach dem Adressbuch 1862 («Kanonengasse 9»), die alte stadtweite
Hausnummer («754 L») und einen Standort in LV95. Damit:

    1862  Strasse + neue Nummer  → Dossier → Standort
    1841/1850  alte Nummer       → Dossier (oldHousenumber) → Standort
    Prüfung: die alte Nummer aus der 1862er Tabelle (house_no_old) gegen oldHousenumber

    python scripts/10_geo_hgb.py --buildings data/csv/05_buildings.csv --out data/csv/05_buildings_geo.csv

Schreibt eine Zeile je Gebäude: building_id, dossier_id, dossier_title, match_method
(`street_no` exakt, `street_no_multi` Dossier mit mehreren Nummern, `old_no` eindeutig,
`old_no_multi` mehrere Dossiers mit derselben alten Nummer → Schwerpunkt), lat, lon (WGS84),
e, n (LV95), geo_confidence, check_old_no (1862: stimmt die alte Nummer mit dem HGB überein).
"""
from __future__ import annotations

import argparse
import csv
import math
import re
from collections import defaultdict
from pathlib import Path

EXT = Path("data/ext/hgb")


def lv95_to_wgs84(e: float, n: float) -> tuple[float, float]:
    """Näherungsformel von swisstopo (Genauigkeit ~1 m)."""
    y = (e - 2600000) / 1e6
    x = (n - 1200000) / 1e6
    lon = 2.6779094 + 4.728982 * y + 0.791484 * y * x + 0.1306 * y * x * x - 0.0436 * y ** 3
    lat = 16.9023892 + 3.238272 * x - 0.270978 * y * y - 0.002528 * x * x - 0.0447 * y * y * x - 0.0140 * x ** 3
    return lat * 100 / 36, lon * 100 / 36


def norm_street(s: str) -> str:
    s = s.lower().replace("ß", "ss").replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
    s = s.replace("strasse", "str").replace("gaesslein", "gaessl").replace("gässlein", "gaessl")
    s = re.sub(r"\bst\.?\s*", "st", s)
    s = re.sub(r"[^a-z0-9]", "", s)
    s = re.sub(r"s(?=str|gasse|graben|berg|platz|weg|vorstadt)", "", s)  # Johanns-Vorstadt / Johann-Vorstadt
    return s


def numbers_in_title(title: str) -> list[str]:
    """«Kanonengasse 3 / 5 bis 19 u. Kohlenberggasse 24-28» → Nummern des ersten Strassenteils."""
    t = title.split(":")[0]
    t = re.split(r"\s(?:u\.|und)\s+[A-ZÄÖÜ][a-zäöü]+(?:gasse|strasse|graben|berg|platz|weg|vorstadt|rain)", t)[0]
    return [re.sub(r"\s", "", m) for m in re.findall(r"\b\d{1,4}\s?[a-zA-Z]?\b", t)]


def old_numbers(s: str) -> list[str]:
    s = re.sub(r"\((?:Bann|bann)\)", "", s or "")
    return [re.sub(r"\s", "", m).upper() for m in re.findall(r"\b\d{1,4}(?:\s?[A-Za-z](?![\w]))?", s)]


def load_hgb():
    series = {r["serieId"]: r["title"] for r in csv.DictReader(EXT.joinpath("stabs_serie.csv").open(encoding="utf-8"))}
    geo = {}
    for r in csv.DictReader(EXT.joinpath("dossiergeomshifted_202607151617.csv").open(encoding="utf-8")):
        m = re.match(r"POINT \(([\d.]+) ([\d.]+)\)", r["locationshifted"] or "")
        if m:
            geo[r["dossierid"]] = (float(m.group(1)), float(m.group(2)))
    dossiers = []
    for r in csv.DictReader(EXT.joinpath("stabs_dossier.csv").open(encoding="utf-8")):
        if ":" in r["title"]:
            continue
        street = series.get(r["serieId"], "")
        d = {"id": r["dossierId"], "title": r["title"], "street": street, "street_norm": norm_street(street),
             "new": numbers_in_title(r["title"]), "old": old_numbers(r["oldHousenumber"]),
             "old_raw": r["oldHousenumber"], "part": bool(re.search(r"Th(eil|\.)\s*v", r["title"] + " " + (r["oldHousenumber"] or ""))),
             "bann": bool(re.search(r"bann", r["oldHousenumber"] or "", re.I)),
             "en": geo.get(r["dossierId"])}
        dossiers.append(d)
    return dossiers


def space_of_building(b: dict) -> str:
    cp = (b.get("city_part") or "")
    if re.search(r"Klein|KB", cp) or b.get("quarter") in ("VII", "VIII"):
        return "kb"
    if re.search(r"Bann|U\.B|O\.B", cp):
        return "bann"
    return "gb"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--buildings", type=Path, default=Path("data/csv/05_buildings.csv"))
    ap.add_argument("--out", type=Path, default=Path("data/csv/05_buildings_geo.csv"))
    args = ap.parse_args()

    dossiers = load_hgb()
    buildings = list(csv.DictReader(args.buildings.open(encoding="utf-8")))
    # Kleinbasler Strassen aus den eigenen Tabellen (Zwischentitel «Kleine Stadt», Quartier VII/VIII):
    # die alten Nummern zählen in Grossbasel, Kleinbasel und in den Bännen je ab 1
    kb_streets = {norm_street(b["street_raw"]) for b in buildings if space_of_building(b) == "kb" and b["street_raw"]}
    for d in dossiers:
        d["space"] = "bann" if d["bann"] else ("kb" if d["street_norm"] in kb_streets else "gb")
    by_new: dict[tuple[str, str], list[dict]] = defaultdict(list)
    by_old: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for d in dossiers:
        for n in d["new"]:
            by_new[(d["street_norm"], n.lower())].append(d)
        for o in d["old"]:
            by_old[(d["space"], o)].append(d)

    rows, stats = [], defaultdict(int)
    for b in buildings:
        cands, method = [], ""
        if b["volume"] == "1862":
            key = (norm_street(b["street_raw"]), b["building_no"].lower())
            cands = [d for d in by_new.get(key, []) if not d["part"]] or by_new.get(key, [])
            exact = [d for d in cands if len(d["new"]) == 1]
            if exact:
                cands, method = exact, "street_no"
            elif cands:
                method = "street_no_multi"
        else:
            old = re.sub(r"\s", "", b["house_no_old"]).upper()
            cands = [d for d in by_old.get((space_of_building(b), old), []) if not d["part"]] or by_old.get((space_of_building(b), old), [])
            if cands:
                method = "old_no" if len(cands) == 1 else "old_no_multi"
        located = [d for d in cands if d["en"]]
        if cands and not located:
            method = "no_location"
        cands = located
        row = {"building_id": b["building_id"], "volume": b["volume"], "street_raw": b["street_raw"],
               "building_no": b["building_no"], "house_no_old": b["house_no_old"], "dossier_id": "",
               "dossier_title": "", "match_method": method, "n_candidates": len(cands), "e": "", "n": "",
               "lat": "", "lon": "", "geo_confidence": "", "check_old_no": "", "space": ""}
        if cands:
            e = sum(d["en"][0] for d in cands) / len(cands)
            n = sum(d["en"][1] for d in cands) / len(cands)
            lat, lon = lv95_to_wgs84(e, n)
            row.update({"dossier_id": ";".join(d["id"] for d in cands[:5]), "dossier_title": " | ".join(d["title"] for d in cands[:3]),
                        "e": f"{e:.1f}", "n": f"{n:.1f}", "lat": f"{lat:.6f}", "lon": f"{lon:.6f}",
                        "geo_confidence": "high" if method in ("street_no", "old_no") else "medium"})
            if b["volume"] == "1862" and b["house_no_old"]:
                ours = {x.upper() for x in old_numbers(b["house_no_old"])}
                theirs = {o for d in cands for o in d["old"]}
                row["check_old_no"] = "ok" if ours & theirs else ("hgb_leer" if not theirs else "abweichend")
        stats[(b["volume"], method or "none")] += 1
        row["space"] = space_of_building(b)
        rows.append(row)
    with args.out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    for k in sorted(stats):
        print(f"  {k[0]} {k[1]:16s} {stats[k]}")
    chk = defaultdict(int)
    for r in rows:
        if r["check_old_no"]:
            chk[r["check_old_no"]] += 1
    print("  1862 alte Nummer gegen HGB:", dict(chk))
    print(f"{len(rows)} Gebäude → {args.out}")


if __name__ == "__main__":
    main()
