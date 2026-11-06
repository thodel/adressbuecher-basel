"""gt_entries_check.py — Abnahme des Parsers: Feldgenauigkeit gegen handgeprüfte Gold-Tabellen.

Gold-Tabellen in data/gt/: entries_<key>.csv (Einwohnerregister), buildings_<key>.csv und
residents_<key>.csv (Gebäudeverzeichnis), je mit denselben Spalten wie die Parser-Ausgabe
plus `gold_note`. Verglichen wird die Parser-Ausgabe aus dem GT-Text (misst den Parser)
und aus der Gemini-Lesung (misst Parser + ATR) — zeilenweise nach Reihenfolge, je Feld.

    python scripts/gt_entries_check.py --parsed-dir <ordner mit parse_gt_<key>.csv, parse_gemini_<key>.csv>
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

GT = Path("data/gt")
FIELDS_E = ["surname", "alliance_name", "maiden_name", "forename", "title", "civil_status", "relation",
            "occupation_raw", "origin_raw", "street_raw", "building_no", "city_part", "entry_type"]
FIELDS_B = ["building_no", "house_no_old", "quarter", "house_name", "street_raw", "owner_text",
            "owner_surname", "building_type"]
FIELDS_R = ["building_no", "surname", "alliance_name", "forename", "civil_status", "occupation_raw", "origin_raw"]


def load(p: Path) -> list[dict]:
    with p.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def norm(v: str) -> str:
    return " ".join((v or "").replace(" ", " ").split()).rstrip(".").strip()


def compare(gold: list[dict], parsed: list[dict], fields: list[str], label: str) -> tuple[int, int, int, Counter]:
    """Zeilen nach Reihenfolge; Längenunterschied zählt als Segmentierungsfehler."""
    n = min(len(gold), len(parsed))
    cells_ok, rows_ok, errs = 0, 0, Counter()
    for g, p in zip(gold[:n], parsed[:n]):
        ok = True
        for f in fields:
            if norm(g.get(f, "")) == norm(p.get(f, "")):
                cells_ok += 1
            else:
                ok, errs[f] = False, errs[f] + 1
        rows_ok += ok
    seg = abs(len(gold) - len(parsed))
    print(f"  {label:34s} Einträge {len(gold):3d} | feldgenau {rows_ok:3d} ({100 * rows_ok / len(gold):5.1f} %) | "
          f"Zellen {100 * cells_ok / (len(gold) * len(fields)):5.1f} % | Segmentierung ±{seg}"
          + (f" | Fehler: {dict(errs)}" if errs else ""))
    return len(gold), rows_ok, cells_ok, errs


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--parsed-dir", type=Path, required=True)
    args = ap.parse_args()
    for source in ("gt", "gemini"):
        print(f"== Parser auf {'GT-Text' if source == 'gt' else 'Gemini-Lesung'}")
        tot = Counter()
        for gp in sorted(GT.glob("entries_*.csv")):
            key = gp.stem.replace("entries_", "")
            pp = args.parsed_dir / f"parse_{source}_{key}.csv"
            if pp.exists():
                n, r, c, _ = compare(load(gp), load(pp), FIELDS_E, f"{key} Einträge")
                tot["n"] += n; tot["rows"] += r; tot["cells"] += c; tot["cellsn"] += n * len(FIELDS_E)
        for gp in sorted(GT.glob("buildings_*.csv")):
            key = gp.stem.replace("buildings_", "")
            pp = args.parsed_dir / f"parse_{source}_{key}_buildings.csv"
            if pp.exists():
                n, r, c, _ = compare(load(gp), load(pp), FIELDS_B, f"{key} Gebäude")
                tot["n"] += n; tot["rows"] += r; tot["cells"] += c; tot["cellsn"] += n * len(FIELDS_B)
            rp = GT / f"residents_{key}.csv"; pr = args.parsed_dir / f"parse_{source}_{key}_residents.csv"
            if rp.exists() and pr.exists():
                n, r, c, _ = compare(load(rp), load(pr), FIELDS_R, f"{key} Bewohner")
                tot["n"] += n; tot["rows"] += r; tot["cells"] += c; tot["cellsn"] += n * len(FIELDS_R)
        if tot["n"]:
            print(f"  {'GESAMT':34s} Einträge {tot['n']:3d} | feldgenau {tot['rows']:3d} ({100 * tot['rows'] / tot['n']:5.1f} %) | Zellen {100 * tot['cells'] / tot['cellsn']:5.1f} %")


if __name__ == "__main__":
    main()
