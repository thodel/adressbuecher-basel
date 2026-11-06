"""20_phonebook.py — Basler Abonnenten aus den PTT-Telefonbüchern ins Adressbuch-Schema bringen.

Quelle: DHBern/PTT_phonebook_data_tsv (historic.localsearch; OCR, automatisch segmentiert),
lokaler Klon unter --src (Standard ~/Repos/PTT_phonebook_data_tsv/tsv). Zwei Batches:

    A  1881–1910  nur Seitentext (`AggregatedContent`), Felder leer → hier grob segmentiert:
                  Einträge beginnen mit «Name[-Allianz], …»; 1899 ff. mit Telefonnummer «NN NN»
                  davor; Adresse am Ende «Strasse Nr.», wo die Seite eine nennt. Konfidenz «low».
    B  1911–1937  je Eintrag EntityName1 (Name[-Allianz] oder Firma), EntityName2 (Vorname/Titel),
                  Supplement (Beruf), Street («Gerberg. 39»), PhoneNumber.

Schreibt data/csv/20_phonebook_basel.csv mit den Spalten des Einwohnerregisters, soweit
die Quelle sie hergibt (surname, alliance_name, forename, occupation_raw, street_raw,
building_no), dazu year, batch, phone, file, page, text, parse_confidence.

    python scripts/20_phonebook.py [--src ~/Repos/PTT_phonebook_data_tsv/tsv] [--max-year 1937]
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

csv.field_size_limit(1 << 28)
OUT = Path("data/csv/20_phonebook_basel.csv")
FIELDS = ["pb_id", "year", "batch", "surname", "alliance_name", "forename", "occupation_raw",
          "street_raw", "building_no", "phone", "entry_type", "parse_confidence", "file", "page", "text"]
ADDR_RE = re.compile(r"(?P<street>(?:St\.\s?)?[A-ZÄÖÜ][\wäöüß.\-]*(?:\s[A-ZÄÖÜa-z][\wäöüß.\-]*){0,2})\s(?P<no>\d{1,4}\s?[a-z]?)\s*\.?$")
FIRM_RE = re.compile(r"&|\bC(ie|o|omp)\b|Söhne|Gebr|A\.-?G\.|Bank|Verein|Fabrik|Brauerei|Gesellschaft|Hotel|Apotheke|Bureau|Amt\b|Departement|Anstalt|Spital|Comptoir|handlung|werk", re.I)
ENTRY_SPLIT_RE = re.compile(r"(?:(?<=\.\s)|(?<=\.\s\s)|(?<=^))(?=(?:\d{2}\s\d{2}\s)?[A-ZÄÖÜ][a-zäöüß]{2,}(?:-[A-ZÄÖÜ][a-zäöüß]+)?[,\s])")


def split_name(name: str) -> tuple[str, str]:
    name = name.strip(" .,")
    if "-" in name and not FIRM_RE.search(name):
        a, b = name.split("-", 1)
        return a.strip(), b.strip()
    return name, ""


def parse_street(s: str) -> tuple[str, str]:
    s = s.strip(" .,")
    m = ADDR_RE.search(s)
    if m:
        return m.group("street").strip(" .,"), m.group("no").replace(" ", "")
    return s, ""


def batch_b(src: Path, max_year: int) -> list[dict]:
    rows = []
    for f in sorted(src.glob("b*.tsv")):
        with f.open(encoding="utf-8", errors="replace", newline="") as fh:
            rd = csv.reader(fh, delimiter="\t", quoting=csv.QUOTE_NONE)
            next(rd, None)
            for i, r in enumerate(rd):
                if len(r) < 10 or not r[4].startswith("Basel"):
                    continue
                try:
                    year = int(r[6])
                except ValueError:
                    continue
                if year > max_year or not r[0].strip():
                    continue
                surname, alliance = split_name(r[0])
                street, no = parse_street(r[3]) if r[3].strip() else ("", "")
                forename = r[1].strip(" .,")
                occ = r[2].strip(" .,")
                # «Dr. Alfred», «Wwe. E. M.», «Jean. Confis.»: Titel/Stand bleiben im Vornamen-Feld der Quelle
                etype = "firma" if FIRM_RE.search(r[0]) or (not forename and not alliance and " " in surname) else "person"
                conf = "high" if street and no and surname else ("medium" if surname else "review")
                rows.append({"pb_id": f"{year}-{Path(r[8]).stem}-{r[7]}-{i}", "year": year, "batch": "B",
                             "surname": surname, "alliance_name": alliance, "forename": forename,
                             "occupation_raw": occ, "street_raw": street, "building_no": no, "phone": r[5].strip(),
                             "entry_type": etype, "parse_confidence": conf, "file": r[8], "page": r[7],
                             "text": " | ".join(x.strip() for x in r[:4] if x.strip())})
    return rows


def batch_a(src: Path) -> list[dict]:
    rows = []
    f = src / "a1_2.tsv"
    with f.open(encoding="utf-8", errors="replace", newline="") as fh:
        rd = csv.reader(fh, delimiter="\t", quoting=csv.QUOTE_NONE)
        next(rd, None)
        for r in rd:
            if len(r) < 11 or "Basel" not in r[9]:
                continue
            year = int(r[6]) if r[6].isdigit() else 0
            text = r[10].strip().strip('"')
            text = re.sub(r"\.{3,}", ". ", text)
            text = re.sub(r"(\s\.){2,}", " ", text)
            text = re.sub(r"\s+", " ", text)
            parts = [p.strip(" .") for p in ENTRY_SPLIT_RE.split(text) if p and p.strip(" .")]
            for n, p in enumerate(parts):
                m = re.match(r"^(?P<phone>\d{2}\s\d{2})\s+(?P<rest>.*)$", p)
                phone, body = (m.group("phone"), m.group("rest")) if m else ("", p)
                if len(body) < 4 or not re.match(r"^[A-ZÄÖÜ]", body):
                    continue
                street, no = parse_street(body)
                head = body
                if no:
                    head = body[:body.rfind(street)].strip(" .,")
                elif street:
                    street = ""
                segs = [s.strip() for s in head.split(",")]
                surname, alliance = split_name(segs[0])
                forename = segs[1] if len(segs) > 1 else ""
                occ = ", ".join(segs[2:]) if len(segs) > 2 else ""
                if len(surname) > 40 or len(segs) > 6 or not surname or not re.match(r"^[A-ZÄÖÜ][a-zäöüß]", surname):
                    continue                           # Spaltensalat der OCR (Adressspalte ohne Namen)
                etype = "firma" if FIRM_RE.search(head) else "person"
                rows.append({"pb_id": f"{year}-{Path(r[8]).stem}-{r[7]}-{n}", "year": year, "batch": "A",
                             "surname": surname, "alliance_name": alliance, "forename": forename,
                             "occupation_raw": occ, "street_raw": street, "building_no": no, "phone": phone,
                             "entry_type": etype, "parse_confidence": "low", "file": r[8], "page": r[7], "text": p[:200]})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--src", type=Path, default=Path.home() / "Repos/PTT_phonebook_data_tsv/tsv")
    ap.add_argument("--max-year", type=int, default=1937)
    args = ap.parse_args()
    rows = batch_a(args.src) + batch_b(args.src, args.max_year)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
    from collections import Counter
    c = Counter((r["batch"], r["year"]) for r in rows)
    print(f"{len(rows)} Einträge → {OUT}")
    print("  A:", {y: n for (b, y), n in sorted(c.items()) if b == "A"})
    print("  B:", {y: n for (b, y), n in sorted(c.items()) if b == "B"})


if __name__ == "__main__":
    main()
