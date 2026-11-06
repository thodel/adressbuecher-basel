"""04_parse.py — Einträge der Einwohnerregister aus Seitentext parsen (Stufe 3+4).

Regelbasierter Parser, aus Aarau übernommen und auf die drei Basler Grammatiken erweitert
(Auswahl über `volume`):

    1841  [*] Name[-Allianz], Vorname, [geb. Name,] [Status,] [von Ort,] [Beruf]. Nummer[ a][ u. N] Strasse. [U. B.|O. B.]
    1850  Name[-Allianz], Vorname[, Beruf] [*]Nummer[A]        (zweispaltig, Nummer rechts; * = Kleinbasel)
            -Allianz, Vorname[, Beruf] Nummer                    (eingerückt: Familienname wie oben)
            Wittwe, Elis. Nummer  /  u. Steigmeyer Nummer
    1862  (Name[-Allianz] | — [-Allianz]), Vorname, [Status,] [Beruf]. Strasse Nummer.
    Aarau [*] (Name[-Allianz] | — [-Allianz] | — geb. Name), Vorname[n], [Status], [Beruf …],
          [von|v. Heimatort [(Kanton)]], Strasse Nummer[; Rolle Strasse Nummer].

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
          "building_no_system", "city_part", "phone_flag", "heading", "parse_method",
          "parse_confidence", "residual", "text"]

STATUS = {"Sohn", "Tochter", "Wittwe", "Witwe", "Wwe.", "Wwe", "Wb.", "Frau", "Fräulein", "Frl.",
          "Jungfer", "Jungfrau", "Jgfr.", "Jgfr", "Vater", "älter", "jünger", "sel.", "sel. Wittwe",
          "Part.", "Partik.", "Partikular", "Partikularin", "Privatin", "Privatier", "Rentier",
          "Rentierin", "Rentière", "Rentner"}
RELATION = {"Sohn", "Tochter", "Vater"}
STATUS_PREFIX = ("Wb. ", "Wittwe ", "Frau ", "Jgfr. ", "Jungfer ", "Jungfrau ", "Fräulein ", "Frl. ")
# Basel 1841: «… Beruf. 292 Spahlen-Vorstadt.» — Nummer vor der Strasse, Bann-Zusatz am Ende
BANN_RE = re.compile(r"\s+(?P<bann>[UO]\.\s?B\.)\s*$")
ADDR_1841_RE = re.compile(r"^(?P<head>.+?)[.,;]?\s+(?P<no>\d{1,4}(?:\s?[a-z](?![\w]))*(?:\s*(?:u\.|und|bis|-|–|—)\s*\d{1,4}(?:\s?[a-z](?![\w]))*)*)(?:\s*\(\d+\))?\.?\s*(?P<star>\*)?\s+(?P<street>[A-ZÄÖÜa-z][^\d]*?)\.?$")
STREET_ONLY_1841_RE = re.compile(r"^(?P<head>.+?)\.\s+(?P<street>(?:(?:St|Hint|Vord|Unt|Ob|Gr|Kl|Aeuss|Inn)\.\s?)?(?:d\.\s)?[A-ZÄÖÜ][\wäöüß.\- ]{2,40}?)\.?$")
ABBR_END_RE = re.compile(r"(^|\s)(St|Kl|Gr|Unt|Ob|Mittl|Vord|Hint|Aeuss|Inn|d|u)$")
SEL_RE = re.compile(r"^(?P<n>.+?)\s+(?P<s>sel\.\s+(?:Wittwe|Wwe\.|Erben|Witwe)|Wittwe|Erben|sel\. Erben)\.?$")
INSTITUTION_RE = re.compile(r"Loge|Zunft|Bureau|Buchhandlung|Gesellschaft|Verein|Anstalt|Stiftung|'sche|Kirche|Spital|Schule|Magazin|Lager|Fabrik\b|Handlung\b|Gebr\.|Geschwister|Consort", re.I)
# Basel 1850: «Halter, N., Bettfedhdlg. 1526», «Hanthon, Karl, Partik. *79», «Heimlicher, I.I., Dr. J. 1083B»
NO_1850_RE = re.compile(r"^(?P<head>.+?)\s+(?P<star>\*)?(?P<no>\d{1,4}\s?[A-Z]{0,3}(?:\s*[–—-]\s*\d{1,4}[A-Z]{0,3})?)\s*$")
ROLE_1850_RE = re.compile(r"^(?P<a>.+?\d[A-Z]{0,3})\.?\s+(?P<role>Comptoir|Magazin|Laden|Werkstätte|Bureau|Fabrik|Wohnung)\s+(?P<star>\*)?(?P<no>\d{1,4}[A-Z]{0,3})\s*$")
SPLIT_1850_RE = re.compile(r"(?<=\d)([A-Z]{1,3})?\s+(?=(?:[A-ZÄÖÜ][\wäöüß]*|-[A-ZÄÖÜ]|—)[^\d]*\d)")
INITIALS_RE = re.compile(r"^(?:[A-ZÄÖÜ]\.\s?)+$")
# Basel 1862: Adresse nach dem letzten «. », «Strasse Nr.» mit optionalem «St. »-Vorsatz
ADDR_1862_RE = re.compile(r"^(?:(?:St|Kl|Gr|Unt|Ob|Mittl|Vord|Hint|Aeuss|Inn)\.\s?)?[A-ZÄÖÜ][^\d.;]*?\s\d{1,4}\s?[a-zA-Z]?(?:\.\s?\d{1,4})*\.?$")
TITLES = {"Dr.", "Dr. med.", "Dr. phil.", "Dr. jur.", "Prof.", "Regt.", "Pfr."}
ADDR_RE = re.compile(r"^(?P<street>.+?)\s+(?P<no>\d+\s?[a-z]?\.?(?:\s?[a-z]\.?)?)\.?$")
ROLE_RE = re.compile(r"^(Wohnung|Werkstätte|Geschäft|Magazin|Bureau|Laden|Comptoir|Atelier)\s*[:,]?\s*", re.I)
ORIGIN_RE = re.compile(r"^(?:von|v\.)\s+(?P<place>.+?)(?:\s*\((?P<canton>[^)]+)\))?$")
RUNNING_HEAD = re.compile(r"^\d+\s*$|^[—-]\s*\d+\s*[—-]$|^(\d+\s+(—\s+)?)?[A-ZÄÖÜ][\w-]+\.?\s+—\s+[A-ZÄÖÜ][\w-]+\.?(\s+\d+)?$|^Alphabetisches Verzeichni|^(\d+\s+)?Verzeichni(ß|ss|s)\b|^Nro\.$|^[A-ZÄÖÜ]\.$")
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


def page_to_entries(text: str, own_entry=None) -> list[tuple[int, int, str]]:
    """Zeilen → (line_from, line_to, Eintragstext); Fortsetzungen angehängt.
    `own_entry(line)` sagt, ob eine eingerückte Zeile ein eigener Eintrag ist (1850:
    Zeile endet auf eine Hausnummer); solche Einträge bekommen das Präfix «— »."""
    entries: list[tuple[int, int, str]] = []
    for i, raw in enumerate(text.split("\n"), start=1):
        if not raw.strip() or raw.strip() == "[spalte 2]":
            continue
        line = raw.rstrip()
        if RUNNING_HEAD.match(line.strip()):
            continue
        if (line.startswith("  ") or line.startswith("\t")) and own_entry and not line.startswith("    ") and own_entry(line.strip()):
            entries.append((i, i, "— " + line.strip()))
            continue
        # nicht eingerückte Fortsetzung (Lesung ohne Einzug): reine Adresszeile «319 Spahlen-Vorstadt.»
        # oder Kleinbuchstabe nach Trennstrich der Vorzeile
        if entries and not line.startswith("  ") and not own_entry and (
                re.match(r"^\d{1,4}(?:\s?[a-z])?(?:\s*(?:u\.|und|bis|-|–|—)\s*\d{1,4})?\.?\s+[A-ZÄÖÜa-z][^\d]*\.?$", line.strip())
                or (entries[-1][2].endswith("-") and line.strip()[:1].islower())):
            line = "  " + line.strip()
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
                forenames: set[str] | None = None,
                addresses_override: list[tuple[str, str, str]] | None = None) -> dict:
    """`addresses_override`: Adresse(n) schon abgetrennt (Basel 1841/1850/1862); dann wird
    kein Adress-Schwanz vom Text abgezogen."""
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
        sm = SEL_RE.match(head)                       # «Bischoff-Frey sel. Wittwe»
        if sm:
            head, rec["civil_status"] = sm.group("n").strip(), sm.group("s")
        m = re.match(r"^(?P<s>\S+)\s+geb\.\s+(?P<g>.+)$", head)
        if m:
            rec["surname"], rec["maiden_name"] = m.group("s"), m.group("g")
        elif "-" in head and not head.startswith("-") and not re.search(r"\s(und|u\.)\s", head):
            rec["surname"], rec["alliance_name"] = head.split("-", 1)
        else:
            rec["surname"] = head
        if INSTITUTION_RE.search(head) and not rec["alliance_name"]:
            rec["entry_type"] = "firma"
    segs = [s.strip() for s in re.split(r",\s*", t) if s.strip()]
    if not segs and addresses_override is None:
        rec["parse_confidence"] = "review"; rec["residual"] = "; ".join(notes + [t])
        rec["_addresses"] = []
        return rec
    addresses: list[tuple[str, str, str]] = []
    if addresses_override is not None:
        addresses = list(addresses_override)
    elif idem_n and prev and not re.search(r"\d", segs[-1]):
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
    if segs and segs[0] not in STATUS and not ORIGIN_RE.match(segs[0]) and not segs[0].startswith("geb. "):
        rec["forename"] = segs.pop(0)
        for pre in STATUS_PREFIX:                       # «Wb. Maria», «Jgfr. Lisette»
            if rec["forename"].startswith(pre):
                rec["civil_status"], rec["forename"] = pre.strip(), rec["forename"][len(pre):].strip()
                break
    rest = []
    for s in segs:
        m = ORIGIN_RE.match(s)
        if s.startswith("geb. ") and not rec["maiden_name"]:      # «Link, geb. Meiry, Wittwe»
            rec["maiden_name"] = s[5:].strip()
        elif m and not rec["origin_raw"]:
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
    if not rec["forename"] and rec["maiden_name"] and rest and not rec["dash_prefix"] \
            and re.match(r"^[A-ZÄÖÜ][\wäöü]*\.?(\s[A-ZÄÖÜ][\wäöü]*\.?)?$", rest[0]) and rest[0] not in STATUS:
        rec["forename"] = rest.pop(0)                 # «Völlmy, geb. Känner, Kath., Wittwe»
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


def _fold(s: str) -> str:
    s = s.lower().replace("ä", "a").replace("ö", "o").replace("ü", "u").replace("ß", "ss")
    return re.sub(r"[^a-z]", "", s.split("-")[0])


def split_1850_line(t: str) -> list[str]:
    """Zwei Einträge in einer Lesungszeile («Klipfel, Hch., Weinhdlg. 15-16 Martin, Weinhdlg. 754BC»)."""
    if t.startswith("("):
        return []
    parts, pos = [], 0
    for m in SPLIT_1850_RE.finditer(t):
        if ROLE_1850_RE.match(t[pos:]):
            continue
        parts.append(t[pos:m.end(1) if m.group(1) else m.start()].strip()); pos = m.end()
    parts.append(t[pos:].strip())
    return [p for p in parts if p]


def _first_segment_1850(t: str) -> str:
    m = NO_1850_RE.match(t.strip())
    head = (m.group("head") if m else t).strip().rstrip(".")
    return re.split(r",\s*", head)[0].strip()


def _surely_inherited(first: str, forenames: set[str] | None) -> bool:
    """Erstes Segment ist Vorname/Stand/Allianz, also kein neuer Familienname."""
    if not first or first.startswith(("-", "—")):
        return True
    toks = [x for x in first.split() if x]
    if INITIALS_RE.match(first) or first in STATUS:
        return True
    if toks[0].rstrip(".") in ("u", "und", "Gebr", "Geschw", "Hr", "HH", "Wittwe", "Wwe", "Wb", "Jgfr", "Jgfrn", "Jungfer", "Frau", "Dr", "Prof"):
        return True
    def ok(x: str) -> bool:
        b = x.rstrip(".")
        return (b in (forenames or ()) or b in ("u", "und", "de", "von", "et")
                or bool(INITIALS_RE.match(x)) or (x.endswith(".") and len(b) <= 5 and b[:1].isupper()))
    return all(ok(x) for x in toks)


def mark_inherited_1850(entries: list[tuple[int, int, str]], prev_surname: str,
                        forenames: set[str] | None) -> list[tuple[int, int, str]]:
    """Das Register 1850 ist alphabetisch und wiederholt den Familiennamen nicht. Die
    Lesung rückt Folgeeinträge nicht zuverlässig ein, darum: sichere Folgeeinträge über
    Vorname/Stand/Abkürzung erkennen, die übrigen als Kandidaten nehmen und davon nur die
    längste nicht fallende (alphabetische) Teilfolge als neue Familiennamen akzeptieren."""
    firsts = [_first_segment_1850(e[2]) for e in entries]
    cand = [i for i, f in enumerate(firsts) if not _surely_inherited(f, forenames) and not entries[i][2].startswith("—")]
    keys = [_fold(firsts[i]) for i in cand]
    base = _fold(prev_surname) if prev_surname else ""
    # längste nicht fallende Teilfolge (mit base als Untergrenze)
    n = len(keys); best = [1] * n; back = [-1] * n
    for i in range(n):
        if keys[i] < base:
            best[i] = 0
        for j in range(i):
            if best[j] and keys[j] <= keys[i] and best[j] + 1 > best[i]:
                best[i], back[i] = best[j] + 1, j
    keep = set()
    if n:
        i = max(range(n), key=lambda k: best[k])
        while i >= 0 and best[i] > 0:
            keep.add(cand[i]); i = back[i]
    out = []
    for i, (lf, lt, txt) in enumerate(entries):
        if i in cand and i in keep or txt.startswith("—"):
            out.append((lf, lt, txt))
        else:
            out.append((lf, lt, "— " + txt))
    return out


def split_addr_1862(t: str) -> tuple[str, list[tuple[str, str, str]]] | None:
    """«…, Dr., Lehrer an der Gewerbeschule. Heuberg 33.» → (Kopf, [(role, street, no)]).
    Sucht von rechts das «. », nach dem nur noch «Strasse Nr.» steht; mehrere Adressen
    «Nadelberg 1. — Neue Vorstadt 3.» werden am « — » getrennt."""
    s = t.strip().rstrip(".")
    parts = [p.strip().rstrip(".") for p in re.split(r"\s+—\s+(?=[A-ZÄÖÜ])", s)]
    first, extra = parts[0], parts[1:]
    pos = [m.start() for m in re.finditer(r"\.\s", first)]
    for i in reversed(pos):
        tail = first[i + 1:].strip()
        head = first[:i].strip()
        if re.search(r"(^|\s)(St|Kl|Gr|Unt|Ob|Mittl|Vord|Hint|Aeuss|Inn)$", head):
            continue                                   # «… Part. St. Peters-Gasse 11»: das «St.» gehört zur Adresse
        if ADDR_1862_RE.match(tail):
            addrs = []
            for a in [tail] + extra:
                m = ADDR_RE.match(a.rstrip("."))
                if m:
                    addrs.append(("", m.group("street").strip(" ,"), m.group("no").replace(" ", "").rstrip(".")))
                else:
                    addrs.append(("", a, ""))
            return head, addrs
    return None


def parse_entry_basel(text: str, volume: str, prev_surname: str, prev: dict | None = None,
                      forenames: set[str] | None = None) -> dict:
    """Adresse nach Bandgrammatik abtrennen, Kopf mit `parse_entry` zerlegen."""
    t = text.strip()
    t = re.sub(r"\bI\.(?=[\s,]|$)", "J.", t)        # Fraktur-Initiale «I.» ist «J.» (J. J., J. Rud.)
    t = re.sub(r"\bI\.I\.", "J.J.", t)
    t = re.sub(r"(?<=\d)_(?=[a-z])", " ", t)           # «1695_a»
    notes, city_part = [], ""
    if volume == "1841":
        m = BANN_RE.search(t)
        if m:
            city_part = m.group("bann").replace(" ", ""); t = t[:m.start()].strip()
        m = ADDR_1841_RE.match(t)
        if m:
            no = re.sub(r"\s+", " ", m.group("no")).strip()
            street, house = m.group("street").strip(" ,."), ""
            # Hausname/Zusatz nach der Strasse: «Freie Straße. Zunft der Hausgenossen»
            for pm in re.finditer(r"\.\s+", street):
                if not ABBR_END_RE.search(street[:pm.start()]):
                    street, house = street[:pm.start()].strip(), street[pm.end():].strip(" .")
                    break
            rec = parse_entry(m.group("head"), prev_surname, prev, forenames,
                              addresses_override=[("", street, no)])
            if m.group("star"):
                rec["owner_flag"] = "1"
            if house:
                notes.append("hausname/zusatz: " + house)
        else:
            sm = STREET_ONLY_1841_RE.match(t)
            if sm and not re.search(r"\d", sm.group("street")):
                rec = parse_entry(sm.group("head"), prev_surname, prev, forenames,
                                  addresses_override=[("", sm.group("street").strip(" ."), "")])
                notes.append("adresse ohne nummer")
            else:
                rec = parse_entry(t, prev_surname, prev, forenames, addresses_override=[])
                notes.append("adresse nicht erkannt")
    elif volume == "1850":
        extra = []
        rm = ROLE_1850_RE.match(t)                       # «Joh. 869. Comptoir 1202»
        if rm:
            extra = [(rm.group("role").lower(), "", rm.group("no"))]
            t = rm.group("a")
        m = NO_1850_RE.match(t)
        if m:
            no = m.group("no").replace(" ", "")
            if m.group("star"):
                city_part = "Kleinbasel"
            head = m.group("head").strip().rstrip(".")
            if re.match(r"^—\s*(u\.|und)\s", head):           # «— u. Steigmeyer 1542»: Firmenzusatz
                rec = parse_entry(head, prev_surname, prev, forenames, addresses_override=[("", "", no)] + extra)
                rec["entry_type"] = "firma"; notes.append("Firmenzusatz zur Vorzeile")
            else:
                rec = parse_entry(head, prev_surname, prev, forenames, addresses_override=[("", "", no)] + extra)
        else:
            rec = parse_entry(t, prev_surname, prev, forenames, addresses_override=[])
            notes.append("adresse nicht erkannt")
    else:  # 1862 und Aarau-ähnliche Grammatik
        sp = split_addr_1862(t)
        if sp:
            rec = parse_entry(sp[0], prev_surname, prev, forenames, addresses_override=sp[1])
        else:
            rec = parse_entry(t, prev_surname, prev, forenames)
    rec["city_part"] = city_part
    rec["text"] = text
    if notes:
        rec["residual"] = "; ".join([rec["residual"]] + notes) if rec["residual"] else "; ".join(notes)
        if "adresse nicht erkannt" in notes:
            rec["parse_confidence"] = "review" if not rec["surname"] else "medium"
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
    basel = volume in ("1841", "1850", "1862")
    own = (lambda s: bool(NO_1850_RE.match(s))) if volume == "1850" else None
    raw_entries = page_to_entries(prenormalise(text), own_entry=own)
    if volume == "1850":
        raw_entries = [(lf, lt, part) for lf, lt, t in raw_entries for part in split_1850_line(t)]
        raw_entries = mark_inherited_1850(raw_entries, prev_surname, forenames)
    for n, (lf, lt, t) in enumerate(raw_entries, start=1):
        if section == "berufe" or basel:
            if CROSSREF_RE.match(t):
                continue
            if HEADING_RE.match(t) and "," not in t and not re.search(r"\d", t):
                heading = t.rstrip(".:").strip()     # Rubrik, Stadtteil («Klein-Basel», «A. Groß-Basel-Bann»)
                if section == "berufe":
                    prev = ""
                continue
        rec = parse_entry_basel(t, volume, prev, prev_rec, forenames) if basel else parse_entry(t, prev, prev_rec, forenames)
        rec["heading"] = heading
        if basel:
            rec["building_no_system"] = "neu" if volume == "1862" else "alt"
            if not rec.get("city_part") and heading and re.search(r"Basel|Bann", heading):
                rec["city_part"] = heading
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
