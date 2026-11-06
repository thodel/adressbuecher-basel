"""01_render_pages.py — Seitenbilder der Basler Adressbücher übernehmen.

Die Lieferung des Staatsarchivs Basel-Stadt (Digitaler Lesesaal) ist je Band ein Ordner
mit einem JPEG je Seite (400 dpi, RGB, ~2400×3400 px) und einem Deckblatt
`01_Inhalt.pdf` mit Signatur, Titel und Permalink. Es gibt nichts zu rendern: die
Bilder werden **byteidentisch kopiert** und unter dem Seitenschlüssel
`<jahr>_p<nnn>` abgelegt; die Reihenfolge ist die der Dateinamen (`…_0001.jpg` …).
Ein PDF-Band (wie in Aarau) würde über denselben Weg laufen: eingebettetes Bild
extrahieren, sonst 300 dpi rendern.

Schreibt:
  <out>/<jahr>/<jahr>_p<nnn>.jpg          die Seitenbilder (nicht im Git)
  <csv>/00_volumes.csv                     Band, Quellordner, Seitenzahl, SHA-256 über
                                           alle Seitendateien (sortiert, Hash der Hashes),
                                           Signatur und Permalink aus 01_Inhalt.pdf
  <csv>/01_pages.csv                       eine Zeile je Seite; Abschnitt leer, wird in
                                           Welle 0 halbautomatisch gefüllt.
Vorhandene Abschnittsangaben in 01_pages.csv bleiben erhalten (Merge über volume,page).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import re
import shutil
from pathlib import Path

from PIL import Image

SECTIONS = ("vorspann", "gebaeude", "einwohner", "berufe", "firmen", "behoerden",
            "inserate", "leer", "sonst")

PAGE_FIELDS = ["volume", "page", "image", "width", "height", "source",
               "printed_page", "section", "typeface", "columns", "note"]
VOL_FIELDS = ["volume", "pdf", "pages", "sha256", "shelfmark", "title", "dls_url"]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def year_of(name: str) -> str:
    m = re.search(r"(18\d\d|19\d\d)", name)
    if not m:
        raise SystemExit(f"kein Jahr im Namen: {name}")
    return m.group(1)


def read_existing(csv_path: Path) -> dict[tuple[str, str], dict]:
    if not csv_path.exists():
        return {}
    with csv_path.open(newline="", encoding="utf-8") as fh:
        return {(r["volume"], r["page"]): r for r in csv.DictReader(fh)}


def cover_sheet(folder: Path) -> dict:
    """Signatur, Titel, Permalink aus 01_Inhalt.pdf (Textlayer)."""
    out = {"shelfmark": "", "title": "", "dls_url": ""}
    pdf = folder / "01_Inhalt.pdf"
    if not pdf.exists():
        return out
    try:
        import pymupdf
        text = "\n".join(p.get_text() for p in pymupdf.open(pdf))
    except Exception:
        return out
    m = re.search(r"Signatur:\s*\n?\s*(.+)", text)
    if m:
        out["shelfmark"] = m.group(1).strip()
    m = re.search(r"Titel:\s*\n?\s*(.+)", text)
    if m:
        out["title"] = m.group(1).strip()
    m = re.search(r"(https://dls\.staatsarchiv\.bs\.ch/records/\d+)", text)
    if m:
        out["dls_url"] = m.group(1)
    return out


def copy_folder(folder: Path, out_dir: Path, year: str) -> tuple[list[dict], str]:
    files = sorted(p for p in folder.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".tif", ".tiff"))
    out_dir.mkdir(parents=True, exist_ok=True)
    rows, digest = [], hashlib.sha256()
    for i, src in enumerate(files, start=1):
        ext = "jpg" if src.suffix.lower() in (".jpg", ".jpeg") else src.suffix.lower().lstrip(".")
        target = out_dir / f"{year}_p{i:03d}.{ext}"
        if not target.exists() or target.stat().st_size != src.stat().st_size:
            shutil.copyfile(src, target)
        digest.update(sha256_file(src).encode())
        with Image.open(target) as im:
            w, h = im.size
        rows.append({"volume": year, "page": str(i),
                     "image": str(target.relative_to(out_dir.parent)),
                     "width": str(w), "height": str(h), "source": f"copied:{src.name}",
                     "printed_page": "", "section": "", "typeface": "",
                     "columns": "", "note": ""})
    return rows, digest.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--src-dir", required=True, type=Path, help="Ordner mit einem Unterordner je Band")
    ap.add_argument("--out", default=Path("data/pages"), type=Path)
    ap.add_argument("--csv", default=Path("data/csv"), type=Path)
    args = ap.parse_args()

    folders = sorted(p for p in args.src_dir.iterdir() if p.is_dir() and re.search(r"18\d\d|19\d\d", p.name))
    if not folders:
        raise SystemExit(f"keine Bandordner in {args.src_dir}")
    args.csv.mkdir(parents=True, exist_ok=True)
    pages_csv = args.csv / "01_pages.csv"
    existing = read_existing(pages_csv)

    volumes, pages = [], []
    for folder in folders:
        year = year_of(folder.name)
        rows, digest = copy_folder(folder, args.out / year, year)
        for r in rows:
            old = existing.get((r["volume"], r["page"]))
            if old:
                for k in ("printed_page", "section", "typeface", "columns", "note"):
                    r[k] = old.get(k, "")
        pages.extend(rows)
        volumes.append({"volume": year, "pdf": folder.name, "pages": str(len(rows)),
                        "sha256": digest, **cover_sheet(folder)})
        print(f"{year}: {len(rows)} Seiten → {args.out / year}")

    with (args.csv / "00_volumes.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=VOL_FIELDS)
        w.writeheader(); w.writerows(volumes)
    with pages_csv.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=PAGE_FIELDS)
        w.writeheader(); w.writerows(pages)
    print(f"{len(pages)} Seiten in {pages_csv}")


if __name__ == "__main__":
    main()
