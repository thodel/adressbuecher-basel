"""05_buildings.py — Gebäudeverzeichnis parsen: Gebäude, Eigentümer, Bewohner (Stufe 5).

Basel (Gemini-Lesung im GT-Format), gewählt über `volume`:

    1841/1850 Nummernbuch (stadtweite Nummern; 1850 Kleinbasel ab 1, Teilhäuser «A 751», «BC 754»):
    Spahlen-Vorstadt.                      ← Strassentitel
    515 * Wagner, Jungfer, Anna Margaretha, gehörend.   ← Nummer [*] Eigentümer (* 1841 = nicht selbst bewohnt)
      Burckhardt, geb. Iselin, Wittwe.     ← eingerückt: Bewohner
    A 751 Mieg, J. J., Med. et Chir. Dr.   ← 1850: Buchstabe vor der Nummer = Teilhaus
    533 Hinterhaus von Nro. 602, Friedr. Gottl. Mende geh.
    1862 Häuserverzeichnis als Tabelle (neue Nummer je Strasse, Quartier I–VIII, alte Nummer, Hausname):
    81 | I. | 1 | St. Johannthor. | Staat.
      Sulger-Wohnlich, J. Ludw. Rud.       ← eingerückt: Bewohner (kleinere Schrift)

Aarau (Grammatik der Bände 1884–1899):

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
            "house_no_new", "house_no_old", "quarter", "house_name", "city_part",
            "street_raw", "owner_text", "owner_same_as_prev", "owner_surname", "owner_entry",
            "building_type", "phone_flag", "parse_confidence", "note"]

NUM_RE = re.compile(r"^\s*(?:\.\s*)?(?:(?P<pre>[A-Z]{1,3})\s+)?(?P<nos>\d+(?:\s?[a-z](?![.\w]))?(?:\s*(?:\.|,)?\s*(?:u\.|und|bis|-|–)\s*\d+(?:\s?[a-z](?![.\w]))?)*)\s*\.?\s*(?P<mark>[*†+]|\(\*\))?\s*(?P<rest>.*)$")
TABLE_RE = re.compile(r"^(?P<new>[^|]*)\|(?P<quarter>[^|]*)\|(?P<old>[^|]*)\|(?P<name>[^|]*)\|(?P<rest>.*)$")
CITY_PART_RE = re.compile(r"^(Gro(ß|ss)e Stadt|Kleine Stadt|Gro(ß|ss)-Basel|Klein-Basel)\b")
DITTO_RE = re.compile(r"^(Derselbe|Dieselbe|Dieselben|Dieselb\.|„|\"|''|Ders\.|Dies\.)\s*[.,]?\s*(?P<type>.*)$")
STREET_RE = re.compile(r"^[A-ZÄÖÜ][^\d,]{2,60}[.:]?$")
HEADER_RE = re.compile(r"^(Haus[-=]?|Nr\.|Nro\.|—\s*\d+\s*—|\d+)\s*$|^Neue Haus-Nr\.|^Handlungsfirma\.")
RUNHEAD_RE = re.compile(r"^(\d+\s+)?[A-ZÄÖÜ][^|]{2,80}\.\s*(—\s*[A-ZÄÖÜ][^|]{2,80}\.\s*)*(\d+)?$")
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


def _owner_fields(owner_text: str, prev_surname: str = "") -> tuple[str, str]:
    e = parse_entry(owner_text, prev_surname, addresses_override=[])
    oentry = json.dumps({k: e[k] for k in ("surname", "alliance_name", "forename", "occupation_raw", "origin_raw", "civil_status", "maiden_name") if e.get(k)}, ensure_ascii=False)
    return e["surname"], oentry


def _resident(s: str, cur: dict, volume: str, page: int, i: int, n: int, street: str) -> dict:
    e = parse_entry(s, cur["owner_surname"], addresses_override=[])
    e = {k: v for k, v in e.items() if k != "_addresses"}
    if e["surname"] and e["parse_confidence"] != "review":
        e["parse_confidence"] = "high"
    e.update({"entry_id": f"{volume}-gebaeude-{page:03d}-{n:03d}", "volume": volume,
              "page": str(page), "section": "gebaeude", "line_from": i, "line_to": i,
              "building_id": cur["building_id"], "building_no": cur["building_no"], "street_raw": street,
              "building_no_system": "neu" if volume == "1862" else "alt", "city_part": cur.get("city_part", "")})
    return e


def parse_building_page_basel(text: str, volume: str, page: int, street: str = "",
                              prev_owner: dict | None = None, city_part: str = ""):
    """1841/1850 Nummernbuch und 1862 Tabelle. Rückgabe wie parse_building_page plus city_part."""
    buildings, residents = [], []
    cur = None
    prev = prev_owner or {}
    lines = prenormalise(text).split("\n")
    for i, raw in enumerate(lines, start=1):
        line = raw.rstrip()
        s = line.strip()
        if not s or s == "[spalte 2]" or HEADER_RE.match(s):
            continue
        if i <= 3 and not line.startswith("  ") and (re.match(r"^\d+\s*$", s) or (RUNHEAD_RE.match(s) and "|" not in s and "," not in s)):
            # Kolumnentitel: «Steinen-Quartier. 33», «74 St. Johann-Vorstadt. — Kanonengasse.»
            if not street and volume == "1862" and "—" in s:
                street = re.sub(r"^\d+\s+", "", s).split("—")[0].strip().rstrip(".")   # erste Strasse der Seite
            continue
        m_cp = CITY_PART_RE.match(s)
        if m_cp and "|" not in s and "," not in s:
            city_part = m_cp.group(1); continue
        indented = line.startswith("  ")
        tm = TABLE_RE.match(s) if volume == "1862" and "|" in s else None
        nm = None if indented else NUM_RE.match(s)
        if tm:
            new, quarter, old, name, rest = (tm.group(k).strip() for k in ("new", "quarter", "old", "name", "rest"))
            if not new and not old and not rest:
                continue
            rest = rest.strip()
            owner_text, btype = split_type(rest) if rest else ("", "")
            d = DITTO_RE.match(owner_text) if owner_text else None
            if d:
                owner_text, same = prev.get("owner_text", ""), "1"
                surname, oentry = prev.get("owner_surname", ""), prev.get("owner_entry", "")
            else:
                same = ""
                surname, oentry = _owner_fields(owner_text) if owner_text else ("", "")
            first = re.sub(r"\s+", "", new.split("u.")[0].split("—")[0]) if new else ("alt" + re.sub(r"\s+", "", old))
            key = re.sub(r"[^\wäöüÄÖÜ-]+", "", street.replace(" ", "-"))[:40]
            cur = {"building_id": f"{volume}-B-{key}-{first}", "volume": volume, "page": str(page), "line": i,
                   "building_no": first, "building_nos": re.sub(r"\s+", " ", new), "marker": "",
                   "house_no_new": re.sub(r"\s+", " ", new), "house_no_old": re.sub(r"\s+", " ", old),
                   "quarter": quarter.rstrip("."), "house_name": name.rstrip("."), "city_part": city_part,
                   "street_raw": street, "owner_text": owner_text, "owner_same_as_prev": same,
                   "owner_surname": surname, "owner_entry": oentry, "building_type": btype,
                   "phone_flag": "", "parse_confidence": "high" if (surname or not owner_text) else "medium", "note": ""}
            if not new:
                cur["note"] = "neue Nummer fehlt"
            buildings.append(cur); prev = cur
        elif nm and nm.group("nos") and (nm.group("rest") or nm.group("mark")) and "|" not in s:
            nos = re.sub(r"\s+", " ", nm.group("nos")).strip()
            first = re.match(r"\d+\s?[a-z]?", nos).group(0).replace(" ", "")
            pre = (nm.group("pre") or "").strip()
            rest = nm.group("rest").strip()
            hs = re.findall(r"\[handschriftlich:[^\]]*\]", rest)
            rest = re.sub(r"\s*\[handschriftlich:[^\]]*\]", "", rest).strip()
            d = DITTO_RE.match(rest) or re.match(r"^(dito|Dito)\b\s*(?P<type>.*)$", rest)
            if d:
                owner_text, same, btype = prev.get("owner_text", ""), "1", (d.group("type") or "").strip(" .„”\"")
                surname, oentry = prev.get("owner_surname", ""), prev.get("owner_entry", "")
                conf = "high" if owner_text else "review"
            else:
                owner_text, btype = split_type(rest)
                same = ""
                pm = re.match(r"^\((?P<t>[^)]+)\)\s*(?P<o>.*)$", owner_text)   # «(Stallung.) Plattner, … geh.»
                if pm:
                    btype, owner_text = pm.group("t").strip(" ."), pm.group("o").strip(" .")
                surname, oentry = _owner_fields(owner_text)
                conf = "high" if surname else "medium"
                if owner_text.startswith(("”", "„", "\"")):                     # Ditto-Zeichen in Teilen der Zeile
                    conf, same = "medium", "teil"
            cp_key = "KB" if re.search(r"Klein", city_part or "") else ("GB" if city_part else "")
            bid = f"{volume}-B-" + (cp_key + "-" if cp_key else "") + (pre + "-" if pre else "") + first
            cur = {"building_id": bid, "volume": volume, "page": str(page), "line": i,
                   "building_no": (pre + " " if pre else "") + first, "building_nos": (pre + " " if pre else "") + nos,
                   "marker": (nm.group("mark") or "").strip("()"),
                   "house_no_new": "", "house_no_old": (pre + " " if pre else "") + first, "quarter": "",
                   "house_name": "", "city_part": city_part,
                   "street_raw": street, "owner_text": owner_text, "owner_same_as_prev": same,
                   "owner_surname": surname, "owner_entry": oentry, "building_type": btype,
                   "phone_flag": "", "parse_confidence": conf, "note": "; ".join(hs)}
            buildings.append(cur); prev = cur
        elif cur is not None and indented and re.match(r"^\(?(Siehe|siehe|Vergl\.)\b", s):
            cur["note"] = (cur["note"] + " | " if cur["note"] else "") + s.rstrip(".")
        elif cur is not None and indented:
            s = s.rstrip(".") if not s.endswith("..") else s
            if line.startswith("    ") or (residents and residents[-1]["building_id"] == cur["building_id"] and s[:1].islower()):
                # tiefer eingerückt oder Kleinbuchstabe: Fortsetzung der letzten Zeile (Bewohner oder Eigentümer)
                if residents and residents[-1]["building_id"] == cur["building_id"]:
                    r = residents[-1]
                    joined = (r["text"][:-1] + s) if r["text"].endswith("-") and s[:1].islower() else (r["text"] + " " + s)
                    residents[-1] = {**r, **{k: v for k, v in _resident(joined, cur, volume, page, r["line_from"], len(residents), street).items()}, "line_to": i}
                else:
                    joined = (cur["owner_text"][:-1] + s) if cur["owner_text"].endswith("-") and s[:1].islower() else (cur["owner_text"] + " " + s)
                    cur["owner_text"], cur["building_type"] = split_type(joined.strip())
                    cur["owner_surname"], cur["owner_entry"] = _owner_fields(cur["owner_text"])
                continue
            residents.append(_resident(s, cur, volume, page, i, len(residents) + 1, street))
        elif STREET_RE.match(s) and "|" not in s:
            street = s.rstrip(".:").strip()
        else:
            if cur is not None:
                cur["note"] = (cur["note"] + " | " if cur["note"] else "") + f"unzugeordnet Z{i}: {s[:60]}"
    return buildings, residents, street, prev, city_part


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
    street, prev, last, city_part = "", None, (None, None), ""
    for vol, page, text in pages:
        if not (vol == last[0] and page == last[1] + 1):
            street, prev, city_part = "", None, ""   # Strasse/Eigentümer nur über direkte Folgeseiten mitführen
        if vol in ("1841", "1850", "1862"):
            b, r, street, prev, city_part = parse_building_page_basel(text, vol, page, street, prev, city_part)
        else:
            b, r, street, prev = parse_building_page(text, vol, page, street, prev)
        all_b.extend(b); all_r.extend(r)
        last = (vol, page)
    for path, rows, fields in ((args.out_buildings, all_b, B_FIELDS),
                               (args.out_residents, all_r, ["building_id", "building_no"] + [f for f in FIELDS if f not in ("building_no",)])):
        with path.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
            w.writeheader(); w.writerows(rows)
    conf = {}
    for b in all_b:
        conf[b["parse_confidence"]] = conf.get(b["parse_confidence"], 0) + 1
    print(f"{len(all_b)} Gebäude ({conf}), {len(all_r)} Bewohner → {args.out_buildings}, {args.out_residents}")


if __name__ == "__main__":
    main()
