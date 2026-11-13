"""81_baende.py — dieselbe Person bzw. Firma in den beiden Bänden finden.

    python scripts/81_baende.py

Vergleicht jeden Eintrag (Einwohner und Berufsregister) mit den Einwohner-Einträgen des anderen Bandes
derselben Gemeinde und schreibt den besten Treffer nach web/baende.csv.

Regeln (Familienname immer gleich nach Faltung: Kleinschreibung, ohne Akzente, ß → ss):
- Vorname: gleich (+3), einer ist Abkürzung des anderen («Joh.» / «Johann», +2), nur Initiale (+1);
  widersprechen sich die Vornamen, kein Treffer. Fehlt einer, 0.
- Allianzname gleich (+2), Beruf gleich in den ersten fünf Buchstaben (+2), gleiche Strasse (+2),
  gleiche Strasse und Hausnummer (+1 dazu).
- Personen brauchen einen passenden Vornamen; passt *nur* der Vorname, zählt der Treffer nur, wenn der
  Familienname im anderen Band höchstens dreimal vorkommt.
- Stufe: **sicher** ab 6 Punkten, **wahrscheinlich** ab 4, **möglich** ab 3. Haben zwei Kandidaten im
  anderen Band dieselbe beste Punktzahl, gilt der Treffer als **mehrdeutig** und wird nicht verlinkt.

Die Daten in data/csv bleiben unverändert.
"""
from __future__ import annotations

import csv
import importlib
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
try:  # Baden, Bern, Lausanne: Normalisierung aus 10_geo; Aarau, Basel: einfache Fassung
    norm_street = importlib.import_module("10_geo").norm_street
except (ModuleNotFoundError, AttributeError):
    def norm_street(s: str) -> str:
        return re.sub(r"\s+", " ", s.replace("ß", "ss")).strip(" .,;")

CSV_DIR = Path("data/csv")
OUT = Path("web/baende.csv")


def fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.replace("ß", "ss")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z ]", "", s).strip()


def forename_score(a: str, b: str) -> int | None:
    """Punkte für zwei Vornamen; None = Widerspruch."""
    ta, tb = fold(a).split(), fold(b).split()
    if not ta or not tb:
        return 0
    pts = []
    for x, y in zip(ta, tb):  # jeder Vorname, der in beiden steht, muss passen
        if x == y:
            pts.append(3 if len(x) > 2 else 2)
        elif x[0] != y[0]:
            return None
        elif len(x) == 1 or len(y) == 1:
            pts.append(1)
        elif (x.startswith(y) or y.startswith(x)) and min(len(x), len(y)) <= 4:
            pts.append(2)  # Abkürzung («Joh.» / «Johann»); zwei volle Namen wie «Louis» / «Louise» widersprechen sich
        else:
            return None
    return pts[0]


def load() -> list[dict]:
    rows = []
    for f in sorted(p.name for p in CSV_DIR.glob("04_*.csv") if "probe" not in p.name):  # Einwohner, Berufe, ggf. Gemeinden
        with (CSV_DIR / f).open(encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                r["tab"] = tab = r["section"]
                r["municipality"] = r.get("municipality") or Path.cwd().name.removeprefix("adressbuecher-").capitalize()
                r["k_sur"] = fold(r["surname"]).replace(" ", "")
                r["k_occ"] = fold(r["occupation_raw"] or (r["heading"] if tab == "berufe" else ""))[:5]
                r["k_st"] = norm_street(r["street_raw"]).lower() if r["street_raw"] else ""
                r["k_no"] = re.sub(r"\s", "", r["building_no"]).lower()
                rows.append(r)
    return rows


def score(a: dict, b: dict) -> tuple[int, list[str]] | None:
    fs = forename_score(a["forename"], b["forename"])
    if fs is None:
        return None
    s, ev = fs, [f"vorname+{fs}"] if fs else []
    if a["alliance_name"] and fold(a["alliance_name"]) == fold(b["alliance_name"]):
        s += 2; ev.append("allianz")
    if a["k_occ"] and a["k_occ"] == b["k_occ"]:
        s += 2; ev.append("beruf")
    if a["k_st"] and a["k_st"] == b["k_st"]:
        s += 2; ev.append("strasse")
        if a["k_no"] and a["k_no"] == b["k_no"]:
            s += 1; ev.append("nr")
    return s, ev


def tier(s: int) -> str:
    return "sicher" if s >= 6 else "wahrscheinlich" if s >= 4 else "möglich" if s >= 3 else ""


def main() -> None:
    rows = load()
    vols = sorted({r["volume"] for r in rows})
    index = defaultdict(list)  # (Band, Gemeinde, Name) → Einwohner-Einträge
    for r in rows:
        if r["tab"] in ("einwohner", "gemeinden"):
            index[(r["volume"], r["municipality"], r["k_sur"])].append(r)
    out, stats = [], Counter()
    for a in rows:
        for v in vols:
            if v == a["volume"] or not a["k_sur"]:
                continue
            cands = []
            pool = index.get((v, a["municipality"], a["k_sur"]), [])
            for b in pool:
                sc = score(a, b)
                if not sc:
                    continue
                has_fn = bool(sc[1]) and sc[1][0].startswith("vorname")
                if a["entry_type"] == "person" and not has_fn:
                    continue  # Person ohne passenden Vornamen: kein Treffer
                if has_fn and len(sc[1]) == 1 and len(pool) > 3:
                    continue  # nur der Vorname passt: nur bei seltenem Familiennamen
                if sc and tier(sc[0]):
                    cands.append((sc[0], sc[1], b))
            if not cands:
                continue
            cands.sort(key=lambda c: -c[0])
            if len(cands) > 1 and cands[1][0] == cands[0][0]:
                stats["mehrdeutig"] += 1
                continue
            s, ev, b = cands[0]
            stats[tier(s)] += 1
            out.append({"entry_id": a["entry_id"], "other_volume": v, "other_id": b["entry_id"], "tier": tier(s),
                        "score": s, "evidence": ";".join(ev), "other_text": b["text"][:160]})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    print(f"{len(rows)} Einträge → {len(out)} Treffer im anderen Band: " +
          ", ".join(f"{k} {v}" for k, v in stats.most_common()) + f" → {OUT}")


if __name__ == "__main__":
    main()
