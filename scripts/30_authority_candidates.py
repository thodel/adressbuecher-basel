"""30_authority_candidates.py — Personen für den Abgleich mit HLS/Metagrid auswählen.

Zwei Quellen:
  1. Amtsträger aus den Behördenverzeichnissen (1862 PDF 10–39, 1850 PDF 158–159), aus der
     Gemini-Lesung: Zeilen «Hr. [Titel] Vorname Name[-Allianz], Amt.» bzw. «„ …» (Ditto
     für «Hr.»); die Behörde ist der letzte Zwischentitel. Alle Ämter einer Person werden
     zusammengeführt (Schlüssel: Familienname + Allianzname + erster Vorname-Buchstabe).
  2. Einträge der Register (04_entries.csv) mit akademischem Titel oder einem Stand, der
     auf Notabilität deutet (Professor, Pfarrer, Rathsherr, Bürgermeister, Oberst,
     Bandfabrikant, Banquier, Staatsschreiber …).

Schreibt data/csv/30_authority_candidates.csv: cand_id, surname, alliance_name, forename,
title, volumes, roles, sources, n_mentions, example_ids.
"""
from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path

CSV_DIR = Path("data/csv")
ATR = Path("data/atr/basel-gemini-v1/gemini-3.8-flash")
OUT = CSV_DIR / "30_authority_candidates.csv"

TITLE_TOKENS = r"(?:eidg\.|Oberst|Oberstl(?:ieut)?\.?|Major|Hauptm(?:ann)?\.?|Stadtrath|Rathsherr|Rathshr\.|Raths-?herr|Prof\.|Professor|Dr\.|Notar|Pfarrer|Pfr\.|Antistes|Architekt|Bürgermeister|Amtsbürgermeister|Statthalter|Oberstlt\.|Lic\.|Th\.|alt|Ingenieur|Präsident|Direktor|Bauinspektor|Oberlehrer|Rektor|Med\.)"
PERSON_LINE = re.compile(r"^(?:\S+?:\s+)?(?:Hr\.|Herr|HH\.|„|\")\s+(?P<rest>.+)$")
NOTABLE_OCC = re.compile(r"Professor|Prof\.|Pfarrer|Antistes|Helfer|Rathsherr|Rathshr|Stadtrath|Bürgermeister|Staatsschreiber|Rathschreiber|Oberst|Major|Appellationsrath|Gerichtspräsident|Präsident|Bandfabrikant|Banquier|Bankier|Seidenfabrikant|Fabrikant|Großrath|Grossrath|Arzt|Dr\b|Direktor|Rektor|Architekt|Ingenieur|Advokat|Notar|J\.\s?U\.\s?D", re.I)


NOT_NAME = re.compile(r"^(?:" + TITLE_TOKENS + r"|Alt\S*|alt\S*|Rathsh\.?|Hrn?\.|HH\.|Jgfr\.?|Jungfer|Wwe\.?|Wb\.?|Wittwe|Frau|Sohn|Vater|älter|jünger|Gebr\.?|J\.U\.D\.?|U\.|D\.?|Ph\.|Lic\.?|Cand\.|S\.M\.C\.?|M\.|Ch\.|zum|zur|des|der|=|„|\")$")
FIRST_FORMS = {"joh": "joh", "johann": "joh", "johannes": "joh", "hans": "joh", "jak": "jak", "jakob": "jak", "jacob": "jak",
               "carl": "kar", "karl": "kar", "christoph": "chr", "christof": "chr", "chr": "chr", "wilh": "wil", "wilhelm": "wil",
               "rud": "rud", "rudolf": "rud", "rudolph": "rud", "eman": "ema", "em": "ema", "eml": "ema", "emanuel": "ema", "immanuel": "imm",
               "friedr": "fri", "friedrich": "fri", "fr": "fri", "fritz": "fri", "heinr": "hei", "heinrich": "hei", "hch": "hei", "hrch": "hei",
               "leonh": "leo", "leonhard": "leo", "nikl": "nik", "niklaus": "nik", "nicolaus": "nik", "niclaus": "nik", "theod": "the", "theodor": "the",
               "ludw": "lud", "ludwig": "lud", "aug": "aug", "august": "aug", "andr": "and", "andreas": "and", "hieron": "hie", "hieronymus": "hie"}


def first_form(forename: str) -> str:
    toks = [x.rstrip(".").lower() for x in forename.split() if x]
    if not toks:
        return "_"
    f = toks[0].replace("i", "j", 1) if len(toks[0]) == 1 and toks[0] == "i" else toks[0]   # I. = J.
    return FIRST_FORMS.get(f, f[:3])


def clean_forename(forename: str) -> str:
    toks = [x for x in forename.replace("=", " ").split() if x and not NOT_NAME.match(x)]
    toks = [x for x in toks if re.match(r"^(?:[A-ZÄÖÜ][a-zäöüé]*\.?|[A-ZÄÖÜ]\.)$", x)]
    return " ".join("J." if x == "I." else x for x in toks)


def fold(s: str) -> str:
    s = s.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    return re.sub(r"[^a-z]", "", s)


def split_name(name: str) -> tuple[str, str, str, str]:
    """«eidg. Oberst N. Paravicini» → (title, forename, surname, alliance)"""
    name = re.sub(r"\s+", " ", name.strip(" .,"))
    title = []
    while True:
        m = re.match(r"^" + TITLE_TOKENS + r"\s+", name)
        if not m:
            break
        title.append(m.group(0).strip()); name = name[m.end():]
    toks = name.split(" ")
    if not toks or not toks[-1]:
        return " ".join(title), "", "", ""
    # Familienname: letztes Token, bei «Im Hof-Forkart», «von Speyr», «De Bary» mit Partikel
    last = toks[-1]; i = len(toks) - 1
    if i >= 1 and toks[i - 1].lower() in ("von", "de", "la", "le", "im", "vonder", "zum", "von der"):
        last = toks[i - 1] + " " + last; i -= 1
    forename = clean_forename(" ".join(toks[:i]))
    surname, _, alliance = last.partition("-")
    return " ".join(title), forename.strip(), surname.strip(), alliance.strip()


def behoerden(volume: str, pages: list[int]) -> list[dict]:
    out = []
    for p in pages:
        f = ATR / f"{volume}_p{p:03d}.txt"
        if not f.exists():
            continue
        heading = ""
        lines = f.read_text(encoding="utf-8").split("\n")
        joined: list[str] = []
        for raw in lines:                                # Fortsetzungszeilen anhängen
            s = raw.strip()
            if not s or s == "[spalte 2]":
                continue
            if raw.startswith("  ") and joined:
                joined[-1] = (joined[-1][:-1] + s) if joined[-1].endswith("-") else joined[-1] + " " + s
            else:
                joined.append(s)
        for n, s in enumerate(joined, start=1):
            m = PERSON_LINE.match(s)
            if not m:
                if not re.search(r"\d", s) and len(s) < 70 and "," not in s:
                    heading = s.rstrip(".:")
                continue
            rest = m.group("rest").strip()
            if rest in ("„", '"') or not re.search(r"[A-ZÄÖÜ][a-zäöü]", rest):
                continue
            name, _, role = rest.partition(",")
            title, forename, surname, alliance = split_name(name)
            if not surname or len(surname) < 3 or not surname[0].isupper():
                continue
            out.append({"volume": volume, "page": p, "line": n, "title": title, "forename": forename,
                        "surname": surname, "alliance_name": alliance,
                        "role": (role.strip(" .") + (" — " if role.strip(" .") else "") + heading).strip(" —"),
                        "source": "behoerden", "id": f"{volume}-behoerden-{p:03d}-L{n:03d}"})
    return out


def registers() -> list[dict]:
    out = []
    with (CSV_DIR / "04_entries.csv").open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r.get("address_seq") not in ("", "1") or r["entry_type"] != "person" or not r["surname"]:
                continue
            occ = r["occupation_raw"] + " " + r["title"]
            if r["title"] or NOTABLE_OCC.search(occ):
                out.append({"volume": r["volume"], "page": r["page"], "line": r["line_from"], "title": r["title"],
                            "forename": clean_forename(r["forename"]), "surname": r["surname"], "alliance_name": r["alliance_name"],
                            "role": r["occupation_raw"], "source": "register", "id": r["entry_id"]})
    return out


def main() -> None:
    rows = behoerden("1862", list(range(10, 40))) + behoerden("1850", [158, 159]) + registers()
    groups: dict[str, dict] = {}
    for r in rows:
        if not r["forename"] and not r["alliance_name"]:
            continue                                     # «Herr Burckhardt» allein ist nicht identifizierbar
        key = f"{fold(r['surname'])}|{fold(r['alliance_name'])}|{first_form(r['forename'])}"
        g = groups.setdefault(key, {"surname": r["surname"], "alliance_name": r["alliance_name"], "forename": r["forename"],
                                    "title": set(), "volumes": set(), "office_volumes": set(), "roles": [], "sources": set(), "ids": []})
        if len(r["forename"]) > len(g["forename"]):
            g["forename"] = r["forename"]                # die ausführlichste Vornamensform
        if r["title"]:
            g["title"].add(r["title"])
        g["volumes"].add(r["volume"]); g["sources"].add(r["source"])
        if r["source"] == "behoerden":
            g["office_volumes"].add(r["volume"])
        if r["role"] and r["role"] not in g["roles"]:
            g["roles"].append(r["role"])
        g["ids"].append(r["id"])
    out = []
    for i, (key, g) in enumerate(sorted(groups.items()), start=1):
        out.append({"cand_id": f"C{i:05d}", "surname": g["surname"], "alliance_name": g["alliance_name"],
                    "forename": g["forename"], "title": "; ".join(sorted(g["title"])),
                    "volumes": ";".join(sorted(g["volumes"])), "office_volumes": ";".join(sorted(g["office_volumes"])),
                    "roles": " | ".join(g["roles"][:8]),
                    "sources": ";".join(sorted(g["sources"])), "n_mentions": len(g["ids"]),
                    "example_ids": ";".join(g["ids"][:5])})
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
    from collections import Counter
    print(f"{len(rows)} Nennungen → {len(out)} Kandidaten → {OUT}")
    print("  Quellen:", Counter(r["source"] for r in rows), "| Kandidaten mit Behördenamt:", sum(1 for o in out if "behoerden" in o["sources"]))


if __name__ == "__main__":
    main()
