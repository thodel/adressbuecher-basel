"""probe_select.py — geschichtete Probeseiten für Welle 1 auswählen.

Liest data/csv/01_pages.csv, nimmt je Band und Abschnitt die gewünschte Zahl Seiten
(gleichmässig über den Abschnitt verteilt, nicht die erste Seite, damit Zwischentitel
und typische Einträge gemischt sind), schreibt data/csv/probe_pages.csv und kopiert die
Bilder nach <probe-dir>, von wo sie per rsync nach tei gehen.

    python scripts/probe_select.py --spec 1841:gebaeude=3,einwohner=3,vorspann=1 \
        --spec 1850:gebaeude=2,einwohner=3,firmen=1 \
        --spec 1862:gebaeude=2,einwohner=3,firmen=1,behoerden=1 --probe-dir data/probe
"""
from __future__ import annotations

import argparse
import csv
import shutil
from pathlib import Path

CSV_DIR = Path("data/csv")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--spec", action="append", required=True)
    ap.add_argument("--probe-dir", type=Path, default=Path("data/probe"))
    args = ap.parse_args()

    with (CSV_DIR / "01_pages.csv").open(encoding="utf-8") as fh:
        pages = list(csv.DictReader(fh))
    chosen = []
    for spec in args.spec:
        vol, _, rest = spec.partition(":")
        for item in rest.split(","):
            sec, _, n = item.partition("=")
            cand = [p for p in pages if p["volume"] == vol and p["section"] == sec]
            n = int(n)
            if not cand:
                raise SystemExit(f"keine Seiten {vol}/{sec}")
            if n >= len(cand):
                pick = cand
            else:
                step = len(cand) / (n + 1)
                pick = [cand[int(round(step * (i + 1)))] for i in range(n)]
            chosen.extend(pick)
    args.probe_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for p in chosen:
        src = Path("data/pages") / p["image"]
        shutil.copyfile(src, args.probe_dir / src.name)
        rows.append({"volume": p["volume"], "page": p["page"], "section": p["section"],
                     "typeface": p["typeface"], "columns": p["columns"], "image": p["image"],
                     "note": p["note"]})
    with (CSV_DIR / "probe_pages.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    for r in rows:
        print(f"{r['volume']} p{int(r['page']):03d}  {r['section']:10s} {r['columns']:>2}  {r['note'][:60]}")
    print(f"{len(rows)} Seiten → {CSV_DIR / 'probe_pages.csv'}, Bilder in {args.probe_dir}")


if __name__ == "__main__":
    main()
