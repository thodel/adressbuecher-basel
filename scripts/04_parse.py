"""04_parse.py — Einträge des Einwohnerverzeichnisses aus Seitentext parsen (Stufe 3+4).

Erster regelbasierter Parser für die Eintragsgrammatik der Bände 1884–1899:

    [*] (Name[-Allianz] | — [-Allianz] | — geb. Name | Name geb. Name), Vorname[n],
        [Status], [Beruf …], [von|v. Heimatort [(Kanton)]], Strasse Nummer[; Rolle Strasse Nummer].

Eingabe ist ein Seitentext im GT-Format (eine gedruckte Zeile je Zeile, Fortsetzungen
mit zwei Leerzeichen eingerückt, `[spalte 2]` zwischen Spalten). Zeilen werden zu
Einträgen zusammengesetzt, der Familienname bei «—» aus dem vorangehenden Eintrag
geerbt, dann die Felder getrennt. Was nicht zuzuordnen ist, landet in `residual`,
und `parse_confidence` sagt, wie sauber die Zeile aufging.

    python scripts/04_parse.py --text data/gt/1884_p022.txt --volume 1884 --page 22
    python scripts/04_parse.py --run basel-probe-gemini-v1 --reader gemini-3.8-flash --section einwohner

Schreibt data/csv/04_entries.csv (oder --out), eine Zeile je Adresse eines Eintrags.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

CSV_DIR = Path("data/csv")
FIELDS = ["entry_id", "volume", "page", "section", "line_from", "line_to", "entry_type", "owner_flag",
          "dash_prefix", "surname", "surname_inherited", "alliance_name", "maiden_name",
          "forename", "title", "civil_status", "relation", "occupation_raw", "origin_raw",
          "origin_canton", "address_seq", "address_role", "street_raw", "building_no",
          "phone_flag", "heading", "parse_method", "parse_confidence", "residual", "text"]

STATUS = {"Sohn", "Tochter", "Wittwe", "Witwe", "Wwe.", "Wwe", "Frau", "Fräulein", "Frl.",
          "Part.", "Partik.", "Privatin", "Privatier", "Rentier", "Rentierin", "Rentner"}
RELATION = {"Sohn", "Tochter"}
TITLES = {"Dr.", "Dr. med.", "Dr. phil.", "Dr. jur.", "Prof.", "Regt.", "Pfr."}
ADDR_RE = re.compile(r"^(?P<street>.+?)\s+(?P<no>\d+\s?[a-z]?\.?(?:\s?[a-z]\.?)?)\.?$")
ROLE_RE = re.compile(r"^(Wohnung|Werkstätte|Geschäft|Magazin|Bureau|Laden|Comptoir|Atelier)\s*[:,]?\s*", re.I)
ORIGIN_RE = re.compile(r"^(?:von|v\.)\s+(?P<place>.+?)(?:\s*\((?P<canton>[^)]+)\))?$")
RUNNING_HEAD = re.compile(r"^\d+\s*$|^(\d+\s+(—\s+)?)?[A-ZÄÖÜ][\w-]+\.?\s+—\s+[A-ZÄÖÜ][\w-]+\.?(\s+\d+)?$|^Alphabetisches Verzeichnis")
FIRM_RE = re.compile(r"&\s*(Cie|Co|Comp|Sohn|Söhne)\b|\bCie\.|\bGebr(üder|\.)|\bSöhne\b|^\S*fabrik\.|\bAktiengesellschaft\b|\bA\.-G\.", re.I)
IDEM_RE = re.compile(r"\b(id\.|idem|dito|do\.)\s*", re.I)


def prenormalise(text: str) -> str:
    """Gemini-Rohtext → GT-Konventionen: ⸗/= → -, Tabs → Leerzeichen, * an den Anfang."""
    t = text.replace("ſ", "s").replace("⸗", "-").replace("­", "")
    t = re.sub(r"(?<=[\s—])=(?=\S)", "-", t)
    t = re.sub(r"(?<=[A-Za-zäöüÄÖÜß])=(?=[A-Za-zäöüÄÖÜß])", "-", t)   # Stigeler=Schaub
    t = re.sub(r"^(\s*)\*\s*", r"\1*", t, flags=re.M)
    t = re.sub(r"^\*\t", "*", t, flags=re.M)
    t = re.sub(r"\t+", "  ", t)
    return t


def page_to_entries(text: str) -> list[tuple[int, int, str]]:
    """Zeilen → (line_from, line_to, Eintragstext); Fortsetzungen angehängt."""
    entries: list[tuple[int, int, str]] = []
    for i, raw in enumerate(text.split("\n"), start=1):
        if not raw.strip() or raw.strip() == "[spalte 2]":
            continue
        line = raw.rstrip()
        if RUNNING_HEAD.match(line.strip()):
            continue
        if (line.startswith("  ") or line.startswith("\t")) and entries:
            lf, lt, t = entries[-1]
            t = (t[:-1] + t[-1].rstrip("-") + line.strip()) if t.endswith("-") else (t + " " + line.strip())
            entries[-1] = (lf, i, t)
        else:
            entries.append((i, i, line.strip()))
    return entries


def split_addresses(tail: str) -> list[tuple[str, str, str]]:
    """'Wohnung, Zollrain 181; Werkstätte Hammer 1295' → [(role, street, no), …]"""
    out = []
    for part in re.split(r";\s*", tail):
        part = part.strip().rstrip(".")
        role = ""
        m = ROLE_RE.match(part)
        if m:
            role = m.group(1).lower()
            part = part[m.end():].strip(" ,")
        m = ADDR_RE.match(part)
        if m:
            out.append((role, m.group("street").strip(" ,"), m.group("no").replace(" ", "").rstrip(".")))
        else:
            out.append((role, part, ""))
    return out


def parse_entry(text: str, prev_surname: str, prev: dict | None = None,
                forenames: set[str] | None = None) -> dict:
    t = text.strip()
    rec = {k: "" for k in FIELDS}
    rec["text"] = text
    rec["parse_method"] = "rule"
    rec["entry_type"] = "firma" if FIRM_RE.search(t) else "person"
    notes = []
    # 1888: «id.» = wie im vorangehenden Eintrag (Heimatort, Adresse)
    idem_n = len(IDEM_RE.findall(t))
    if idem_n:
        t = IDEM_RE.sub("", t).strip().rstrip(",").strip()
        notes.append(f"id.×{idem_n} aus Vorzeile")
    hs = re.findall(r"\[handschriftlich:[^\]]*\]", t)
    if hs:
        notes.append("handschriftlich:" + "|".join(hs))
        t = re.sub(r"\s*\[handschriftlich:[^\]]*\]\s*", " ", t).strip()
    if "[tel]" in t:
        rec["phone_flag"] = "1"
        t = t.replace("[tel]", "").replace("  ", " ")
    if t.startswith("*"):
        rec["owner_flag"] = "1"
        t = t[1:].strip()
    if t.startswith("—"):
        rec["dash_prefix"] = "1"
        rec["surname"] = prev_surname
        rec["surname_inherited"] = "1"
        t = t[1:].strip()
        if t.startswith("-"):                       # — -Graden, … (Allianzname zum geerbten Namen)
            head, _, t = t[1:].partition(",")
            rec["alliance_name"] = head.strip()
        elif t.startswith("geb."):                  # — geb. Hauenstein, Elisabeth, …
            head, _, t = t[4:].partition(",")
            rec["maiden_name"] = head.strip()
    else:
        head, _, t = t.partition(",")
        head = head.strip()
        m = re.match(r"^(?P<s>\S+)\s+geb\.\s+(?P<g>.+)$", head)
        if m:
            rec["surname"], rec["maiden_name"] = m.group("s"), m.group("g")
        elif "-" in head and not head.startswith("-"):
            rec["surname"], rec["alliance_name"] = head.split("-", 1)
        else:
            rec["surname"] = head
    segs = [s.strip() for s in re.split(r",\s*", t) if s.strip()]
    if not segs:
        rec["parse_confidence"] = "review"; rec["residual"] = "; ".join(notes + [t])
        rec["_addresses"] = []
        return rec
    addresses: list[tuple[str, str, str]] = []
    if idem_n and prev and not re.search(r"\d", segs[-1]):
        # keine eigene Adresse: Heimatort/Adresse der Vorzeile übernehmen
        rec["origin_raw"], rec["origin_canton"] = prev.get("origin_raw", ""), prev.get("origin_canton", "")
        addresses = list(prev.get("_addresses") or [])
    else:
        # Adresse: vom Ende her alles, was mit einer Nummer endet (inkl. «; Werkstätte …»)
        addr_tail = segs.pop()
        while segs and not ADDR_RE.match(addr_tail.split(";")[0].strip().rstrip(".")) and re.search(r"\d", addr_tail):
            addr_tail = segs.pop() + ", " + addr_tail
        # Rollenwort «Wohnung» steht als eigenes Segment davor
        if segs and ROLE_RE.match(segs[-1] + " x"):
            addr_tail = segs.pop() + ", " + addr_tail
        addresses = split_addresses(addr_tail)
    # Vorname: erstes Segment, sofern es nicht Status/Beruf ist
    if segs and segs[0] not in STATUS and not ORIGIN_RE.match(segs[0]):
        rec["forename"] = segs.pop(0)
    rest = []
    for s in segs:
        m = ORIGIN_RE.match(s)
        if m and not rec["origin_raw"]:
            rec["origin_raw"] = m.group("place").strip()
            rec["origin_canton"] = (m.group("canton") or "").strip()
        elif s in RELATION:
            rec["relation"] = s
        elif s in STATUS or s.endswith("Wittwe") or s.endswith("Witwe"):
            rec["civil_status"] = (rec["civil_status"] + " " + s).strip()
        elif s in TITLES:
            rec["title"] = s
        else:
            rest.append(s)
    rec["occupation_raw"] = ", ".join(rest)
    # «— geb. Schmid Elisabeth, …»: Komma fehlt, letzter Token ist der Vorname
    if rec["maiden_name"] and not rec["forename"] and len(rec["maiden_name"].split()) >= 2:
        parts = rec["maiden_name"].split()
        rec["maiden_name"], rec["forename"] = " ".join(parts[:-1]), parts[-1]
        notes.append("vorname aus geb.-Name abgetrennt")
    # «— Leutwyler, Samuel, Taglöhner»: Allianzname ohne Bindestrich — der «Vorname» ist
    # ein Nachname. Erkannt über das Vornamenlexikon der nicht-Gedankenstrich-Einträge:
    # ein Vorname, der dort nie vorkommt, gefolgt von einem Segment, das ein Vorname ist.
    first_rest = rest[0] if rest else ""
    if (forenames and rec["dash_prefix"] and not rec["alliance_name"] and rec["forename"]
            and rec["forename"].rstrip(".") not in forenames
            and first_rest.rstrip(".") in forenames):
        notes.append(f"allianz/vorname unsicher: {rec['forename']} | {first_rest}")
    bad = [a for a in addresses if not a[2]]
    rec["parse_confidence"] = "high" if not bad and rec["surname"] else ("medium" if rec["surname"] else "review")
    if rec["entry_type"] == "firma" and rec["parse_confidence"] == "high":
        rec["parse_confidence"] = "medium"
    if any(n.startswith(("allianz/vorname", "id.")) for n in notes) and rec["parse_confidence"] == "high":
        rec["parse_confidence"] = "medium"
    if bad:
        notes.append("adresse ohne nummer:" + "|".join(a[1] for a in bad))
    rec["residual"] = "; ".join(notes)
    rec["_addresses"] = addresses
    return rec


def forename_lexicon(texts: list[str]) -> set[str]:
    """Vornamen aus Einträgen ohne Gedankenstrich (dort ist der Vorname-Slot zuverlässig)."""
    lex: dict[str, int] = {}
    for text in texts:
        for _, _, t in page_to_entries(prenormalise(text)):
            r = parse_entry(t, "")
            if not r["dash_prefix"] and r["forename"] and r["entry_type"] == "person":
                for tok in r["forename"].split():
                    lex[tok.rstrip(".")] = lex.get(tok.rstrip("."), 0) + 1
    return {k for k, v in lex.items() if v >= 2}


HEADING_RE = re.compile(r"^(?!—)[A-ZÄÖÜ][^\d,;]{2,70}[.:]?$")
CROSSREF_RE = re.compile(r"^\(?\s*(Siehe|siehe|Im weitern siehe|Vergl\.|S\.)\b")


def parse_page(text: str, volume: str, page: int, section: str = "einwohner",
               prev_surname: str = "", forenames: set[str] | None = None,
               heading: str = "") -> list[dict]:
    """Einwohner- und Berufsregister. Im Berufsregister setzt eine Zeile ohne Komma und
    Ziffer (z. B. «Hafnereien.») die Rubrik, die jeder folgende Eintrag in `heading`
    trägt; Querverweise «(Siehe …)» werden als Notiz an die Rubrik gehängt."""
    rows, prev, prev_rec = [], prev_surname, None
    for n, (lf, lt, t) in enumerate(page_to_entries(prenormalise(text)), start=1):
        if section == "berufe":
            if CROSSREF_RE.match(t):
                continue
            if HEADING_RE.match(t) and "," not in t:
                heading = t.rstrip(".:").strip()
                prev = ""
                continue
        rec = parse_entry(t, prev, prev_rec, forenames)
        rec["heading"] = heading
        prev = rec["surname"] or prev
        prev_rec = rec
        addrs = rec.get("_addresses") or [("", "", "")]
        rec = {k: v for k, v in rec.items() if k != "_addresses"}
        for seq, (role, street, no) in enumerate(addrs, start=1):
            row = dict(rec)
            row.update({"entry_id": f"{volume}-{section}-{page:03d}-{n:03d}", "volume": volume,
                        "page": str(page), "section": section, "line_from": lf, "line_to": lt,
                        "address_seq": seq, "address_role": role, "street_raw": street, "building_no": no})
            rows.append(row)
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--text", type=Path, help="eine Seite im GT-Format")
    ap.add_argument("--volume"); ap.add_argument("--page", type=int)
    ap.add_argument("--run"); ap.add_argument("--reader")
    ap.add_argument("--section", default="einwohner")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    rows: list[dict] = []
    if args.text:
        text = args.text.read_text(encoding="utf-8")
        rows = parse_page(text, args.volume, args.page, args.section, forenames=forename_lexicon([text]))
    elif args.run and args.reader:
        meta = {}
        with (CSV_DIR / "01_pages.csv").open(encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                meta[f"{r['volume']}_p{int(r['page']):03d}"] = r
        pages = []
        for jp in sorted((Path("data/atr") / args.run / args.reader).glob("*.json")):
            m = meta.get(jp.stem)
            if not m or m["section"] != args.section:
                continue
            d = json.loads(jp.read_text(encoding="utf-8"))
            pages.append((m["volume"], int(m["page"]), d.get("text") or ""))
        lex = forename_lexicon([p[2] for p in pages])
        prev_vol, prev_page, prev_surname, heading = None, None, "", ""
        for vol, page, text in pages:
            # Familienname und Rubrik über die Seitengrenze nur bei direkt aufeinanderfolgenden Seiten
            consecutive = (vol == prev_vol and page == prev_page + 1)
            carry = prev_surname if consecutive else ""
            heading = heading if consecutive else ""
            page_rows = parse_page(text, vol, page, args.section, prev_surname=carry, forenames=lex, heading=heading)
            rows.extend(page_rows)
            prev_vol, prev_page = vol, page
            prev_surname = next((r["surname"] for r in reversed(page_rows) if r["surname"]), "")
            heading = next((r["heading"] for r in reversed(page_rows) if r.get("heading")), heading)
    else:
        sys.exit("--text oder --run/--reader angeben")

    out = args.out or (CSV_DIR / "04_entries.csv")
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)
    conf = {}
    for r in rows:
        conf[r["parse_confidence"]] = conf.get(r["parse_confidence"], 0) + 1
    print(f"{len(rows)} Adresszeilen → {out}; Konfidenz {conf}")


if __name__ == "__main__":
    main()
