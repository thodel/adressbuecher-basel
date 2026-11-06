"""05_buildings.py — Gebäudeverzeichnis parsen: Gebäude, Eigentümer, Bewohner (Stufe 5).

Grammatik der Bände (Gemini-Lesung im GT-Format):

    Rathausgasse.                         ← Strassentitel (keine Ziffer, endet mit . oder :)
    356. Hunziker, Emil Guido, Rentier.   ← Gebäudenummer [* oder †] Eigentümer[, Gebäudeart]
      Käser-Kähr, Ulrich, Kutscher, von Melchnau (Bern).   ← eingerückt: Bewohner
    357.† Derselbe. Remise.               ← Ditto-Eigentümer (Derselbe/Dieselbe/Dieselben/„), Gebäudeart
    365. u. 366.† Dieselbe. Scheune.      ← mehrere Nummern
    119a Rohr-Häfig, Emma, Wittwe, …      ← 1884: zweispaltig, ohne Punkt nach der Nummer

`*` = der Eigentümer wohnt selbst im Haus; `†` = Nebengebäude (Scheune, Remise, …).
1892/1899 setzen vor der Bewohnerzeile «—» für den wiederholten Familiennamen des
Eigentümers; das übernimmt `04_parse.parse_entry` mit dem Eigentümernamen als Vorgabe.

    python scripts/05_buildings.py --run basel-probe-gemini-v1 --reader gemini-3.8-flash
    python scripts/05_buildings.py --text data/gt/1884_p070.txt --volume 1884 --page 70

Schreibt data/csv/05_buildings.csv (ein Gebäude je Zeile) und data/csv/05_residents.csv
(eine Person je Zeile, geparst wie ein Einwohnereintrag, mit `building_no`).
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
_p = import_module("04_parse")
parse_entry, prenormalise, FIELDS = _p.parse_entry, _p.prenormalise, _p.FIELDS

CSV_DIR = Path("data/csv")
B_FIELDS = ["building_id", "volume", "page", "line", "building_no", "building_nos", "marker",
            "street_raw", "owner_text", "owner_same_as_prev", "owner_surname", "owner_entry",
            "building_type", "phone_flag", "parse_confidence", "note"]

NUM_RE = re.compile(r"^\s*(?P<nos>\d+\s?[a-z]?(?:\s*(?:\.|,)?\s*(?:u\.|und|-|–)\s*\d+\s?[a-z]?)*)\s*\.?\s*(?P<mark>[*†+]|\(\*\))?\s*(?P<rest>.*)$")
DITTO_RE = re.compile(r"^(Derselbe|Dieselbe|Dieselben|Dieselb\.|„|\"|''|Ders\.|Dies\.)\s*[.,]?\s*(?P<type>.*)$")
STREET_RE = re.compile(r"^[A-ZÄÖÜ][^\d,]{2,60}[.:]?$")
HEADER_RE = re.compile(r"^(Haus[-=]?|Nr\.|—\s*\d+\s*—|\d+)\s*$")
TYPE_WORDS = ("Scheune", "Remise", "Waschhaus", "Holzhaus", "Holzschopf", "Schopf", "Magazin",
              "Fabrik", "Werkstätte", "Stall", "Gartenhaus", "Sommerhaus", "Eiskeller", "Keller",
              "Schuppen", "gebäude", "Hintergebäude", "Trinkhalle", "Brunnenhaus", "Bureau",
              "Comptoir", "Kapelle", "Turnhaus", "Pfarrhaus", "Kirche", "Schulhaus", "Spritzenhaus",
              "Badanstalt", "Lagerhaus", "Erbschaft", "häuschen", "Rebhaus", "Wagenschopf",
              "Wohngebäude", "Wohnhaus", "Oekonomiegebäude", "Abgetragen")


def split_type(owner: str) -> tuple[str, str]:
    """'Gemeinde Aarau, Brunnenhaus.' → ('Gemeinde Aarau', 'Brunnenhaus')"""
    parts = [p.strip(" .") for p in owner.split(",")]
    if len(parts) >= 2 and any(w.lower() in parts[-1].lower() for w in TYPE_WORDS) and not re.search(r"\bvon\b", parts[-1]):
        return ", ".join(parts[:-1]), parts[-1]
    m = re.match(r"^(?P<o>.+?)\.\s+(?P<t>[A-ZÄÖÜ][\w-]+(?:gebäude|haus|schopf|keller|halle|stall)?)\.?$", owner)
    if m and any(w.lower() in m.group("t").lower() for w in TYPE_WORDS):
        return m.group("o"), m.group("t")
    return owner.strip(" ."), ""


def parse_building_page(text: str, volume: str, page: int, street: str = "", prev_owner: dict | None = None):
    buildings, residents = [], []
    cur = None
    prev = prev_owner or {}
    for i, raw in enumerate(prenormalise(text).split("\n"), start=1):
        line = raw.rstrip()
        s = line.strip()
        if not s or s == "[spalte 2]" or HEADER_RE.match(s):
            continue
        m = NUM_RE.match(s) if not line.startswith("  ") or re.match(r"^\s{0,8}\d", line) else None
        if m and re.match(r"^(Verzeichnis|Alphabetisches|Gebäude|Haus)", m.group("rest") or ""):
            continue                                   # Kolumnentitel mit Seitenzahl
        if m and m.group("nos") and (m.group("rest") or m.group("mark")):
            nos = re.sub(r"\s+", " ", m.group("nos")).strip()
            first = re.match(r"\d+\s?[a-z]?", nos).group(0).replace(" ", "")
            rest = m.group("rest").strip()
            phone = "1" if "[tel]" in rest else ""
            rest = rest.replace("[tel]", "").strip()
            d = DITTO_RE.match(rest)
            if d:
                owner_text, same, btype = prev.get("owner_text", ""), "1", d.group("type").strip(" .")
                surname, oentry = prev.get("owner_surname", ""), prev.get("owner_entry", "")
                conf = "high" if owner_text else "review"
            else:
                owner_text, btype = split_type(rest)
                same = ""
                e = parse_entry(owner_text, prev.get("owner_surname", ""))
                surname = e["surname"]
                oentry = json.dumps({k: e[k] for k in ("surname", "alliance_name", "forename", "occupation_raw", "origin_raw", "civil_status") if e.get(k)}, ensure_ascii=False)
                conf = "high" if surname else "medium"
            cur = {"building_id": f"{volume}-B-{first}", "volume": volume, "page": str(page), "line": i,
                   "building_no": first, "building_nos": nos, "marker": (m.group("mark") or "").strip("()"),
                   "street_raw": street, "owner_text": owner_text, "owner_same_as_prev": same,
                   "owner_surname": surname, "owner_entry": oentry, "building_type": btype,
                   "phone_flag": phone, "parse_confidence": conf, "note": ""}
            buildings.append(cur)
            prev = cur
        elif cur is not None and volume == "1884" and line.startswith("  "):
            # 1884 (zweispaltig, ohne Bewohnerzeilen): Einzug = Fortsetzung des Eigentümers
            joined = (cur["owner_text"][:-1] + s) if cur["owner_text"].endswith("-") and s[:1].islower() \
                else (cur["owner_text"] + ("" if cur["owner_text"].endswith("-") else " ") + s)
            cur["owner_text"], cur["building_type"] = split_type(joined.strip())
            e = parse_entry(cur["owner_text"], "")
            cur["owner_surname"] = e["surname"]
            cur["owner_entry"] = json.dumps({k: e[k] for k in ("surname", "alliance_name", "forename", "occupation_raw", "origin_raw", "civil_status") if e.get(k)}, ensure_ascii=False)
        elif cur is not None and (line.startswith("  ") or s.startswith("—")):
            if buildings and residents and residents[-1]["building_id"] == cur["building_id"] and line.startswith("    "):
                # tiefer eingerückt: Fortsetzung der letzten Bewohnerzeile
                r = residents[-1]
                r["text"] = r["text"] + " " + s
                residents[-1] = {**r, **{k: v for k, v in parse_entry(r["text"], cur["owner_surname"]).items() if k in FIELDS and k != "text"},
                                 "building_id": cur["building_id"], "building_no": cur["building_no"], "street_raw": street}
                continue
            e = parse_entry(s, cur["owner_surname"])
            e = {k: v for k, v in e.items() if k != "_addresses"}
            if e["surname"] and e["parse_confidence"] == "medium" and "adresse ohne nummer" in e["residual"]:
                e["parse_confidence"], e["residual"] = "high", ""     # Adresse ist das Gebäude
            e.update({"entry_id": f"{volume}-gebaeude-{page:03d}-{len(residents)+1:03d}", "volume": volume,
                      "page": str(page), "section": "gebaeude", "line_from": i, "line_to": i,
                      "building_id": cur["building_id"], "building_no": cur["building_no"], "street_raw": street})
            residents.append(e)
        elif STREET_RE.match(s) and not s.startswith("—"):
            street = s.rstrip(".:").strip()
        else:
            if cur is not None:
                cur["note"] = (cur["note"] + " | " if cur["note"] else "") + f"unzugeordnet Z{i}: {s[:60]}"
    return buildings, residents, street, prev


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--text", type=Path); ap.add_argument("--volume"); ap.add_argument("--page", type=int)
    ap.add_argument("--run"); ap.add_argument("--reader")
    ap.add_argument("--out-buildings", type=Path, default=CSV_DIR / "05_buildings.csv")
    ap.add_argument("--out-residents", type=Path, default=CSV_DIR / "05_residents.csv")
    args = ap.parse_args()

    pages = []
    if args.text:
        pages.append((args.volume, args.page, args.text.read_text(encoding="utf-8")))
    else:
        meta = {}
        with (CSV_DIR / "01_pages.csv").open(encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                meta[f"{r['volume']}_p{int(r['page']):03d}"] = r
        for jp in sorted((Path("data/atr") / args.run / args.reader).glob("*.json")):
            m = meta.get(jp.stem)
            if m and m["section"] == "gebaeude":
                pages.append((m["volume"], int(m["page"]), json.loads(jp.read_text(encoding="utf-8")).get("text") or ""))

    all_b, all_r = [], []
    street, prev, last = "", None, (None, None)
    for vol, page, text in pages:
        if not (vol == last[0] and page == last[1] + 1):
            street, prev = "", None            # Strasse/Eigentümer nur über direkte Folgeseiten mitführen
        b, r, street, prev = parse_building_page(text, vol, page, street, prev)
        all_b.extend(b); all_r.extend(r)
        last = (vol, page)
    for path, rows, fields in ((args.out_buildings, all_b, B_FIELDS),
                               (args.out_residents, all_r, ["building_id", "building_no"] + FIELDS)):
        with path.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
            w.writeheader(); w.writerows(rows)
    conf = {}
    for b in all_b:
        conf[b["parse_confidence"]] = conf.get(b["parse_confidence"], 0) + 1
    print(f"{len(all_b)} Gebäude ({conf}), {len(all_r)} Bewohner → {args.out_buildings}, {args.out_residents}")


if __name__ == "__main__":
    main()
