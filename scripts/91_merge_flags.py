"""91_merge_flags.py — exportierte Flags der Kontrollseite nach data/review/flags.csv mischen.

    python scripts/91_merge_flags.py ~/Downloads/flags_2026-11-06.csv [--by "T. Hodel"]

Schlüssel ist (table, id): ein neuer Export überschreibt einen älteren Flag derselben
Zeile; ein Flag mit leerem Grund löscht ihn. Danach `make erstblick` und committen,
damit die Seite die Flags als «gemeldet» zeigt.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date
from pathlib import Path

REVIEW = Path("data/review/flags.csv")
FIELDS = ["table", "id", "reason", "note", "by", "date", "status"]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("export", type=Path)
    ap.add_argument("--by", default="")
    ap.add_argument("--status", default="open", choices=["open", "fixed"],
                    help="«fixed»: die Flags sind erledigt (z. B. nach einem Parser-Fix); die Seite zeigt sie nicht mehr")
    ap.add_argument("--note", default="", help="Notiz, die an jeden Flag dieses Exports angehängt wird")
    args = ap.parse_args()

    existing: dict[tuple[str, str], dict] = {}
    if REVIEW.exists():
        with REVIEW.open(encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                existing[(r["table"], r["id"])] = r
    added = updated = removed = 0
    with args.export.open(encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            key = (r["table"], r["id"])
            if not r.get("reason"):
                if key in existing:
                    del existing[key]; removed += 1
                continue
            row = {k: r.get(k, "") for k in FIELDS}
            row["by"] = row["by"] or args.by
            row["date"] = row["date"] or date.today().isoformat()
            row["status"] = args.status
            if args.note:
                row["note"] = (row["note"] + " | " if row["note"] else "") + args.note
            if key in existing:
                updated += 1
            else:
                added += 1
            existing[key] = row
    REVIEW.parent.mkdir(parents=True, exist_ok=True)
    with REVIEW.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(sorted(existing.values(), key=lambda x: (x["table"], x["id"])))
    print(f"{added} neu, {updated} aktualisiert, {removed} entfernt → {REVIEW} ({len(existing)} Flags)")


if __name__ == "__main__":
    main()
