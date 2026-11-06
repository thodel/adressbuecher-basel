"""11_geojson.py — GeoJSON je Band aus der HGB-Verortung (Stufe 10) für die Karte.

Liest 05_buildings.csv, 05_residents.csv, 05_buildings_geo.csv und schreibt
data/geo/buildings_<jahr>.geojson: ein Punkt je verortetem Gebäude (WGS84) mit
Eigentümer, Bewohnern, Zahl der Bewohner, Methode und Konfidenz der Verortung; dazu
data/geo/summary.json mit «verortet von gesamt» je Band, damit die Karte die
nicht verorteten Gebäude ausweisen kann.

    python scripts/11_geojson.py
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

CSV_DIR, GEO_DIR = Path("data/csv"), Path("data/geo")


def load(name: str) -> list[dict]:
    with (CSV_DIR / name).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def person(r: dict) -> str:
    name = r["surname"] + ("-" + r["alliance_name"] if r["alliance_name"] else "")
    parts = [name, r["forename"], r["civil_status"], r["occupation_raw"]]
    return ", ".join(p for p in parts if p)


def main() -> None:
    GEO_DIR.mkdir(parents=True, exist_ok=True)
    residents = defaultdict(list)
    for r in load("05_residents.csv"):
        residents[r["building_id"]].append(person(r))
    geo = {g["building_id"]: g for g in load("05_buildings_geo.csv")}
    feats, summary = defaultdict(list), {}
    for b in load("05_buildings.csv"):
        g = geo.get(b["building_id"], {})
        summary.setdefault(b["volume"], {"total": 0, "located": 0, "high": 0})
        summary[b["volume"]]["total"] += 1
        if not g.get("lat"):
            continue
        summary[b["volume"]]["located"] += 1
        summary[b["volume"]]["high"] += g["geo_confidence"] == "high"
        props = {"id": b["building_id"], "vol": b["volume"], "page": int(b["page"]), "street": b["street_raw"],
                 "no": b["building_no"], "old": b["house_no_old"], "name": b["house_name"], "part": b["city_part"],
                 "owner": b["owner_text"], "type": b["building_type"], "marker": b["marker"],
                 "residents": residents.get(b["building_id"], []), "n": len(residents.get(b["building_id"], [])),
                 "method": g["match_method"], "conf": g["geo_confidence"], "dossier": g["dossier_id"].split(";")[0],
                 "hgb": g["dossier_title"]}
        feats[b["volume"]].append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [float(g["lon"]), float(g["lat"])]},
                                   "properties": props})
    for vol, fs in feats.items():
        out = GEO_DIR / f"buildings_{vol}.geojson"
        out.write_text(json.dumps({"type": "FeatureCollection", "features": fs}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print(f"{vol}: {len(fs)} Punkte von {summary[vol]['total']} Gebäuden → {out}")
    (GEO_DIR / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
