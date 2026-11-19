"""Schriften lokal statt Google Fonts (gleiche Datei in allen adressbuecher-*).

Source Sans 3 und Source Code Pro liegen als woff2 in fonts/ (SIL OFL 1.1, Lizenz in fonts/OFL-*.txt), eingebunden über
fonts/fonts.css. Die Seiten verweisen mit LINK darauf; copy() legt den Ordner neben die geschriebene Seite.
"""
from __future__ import annotations

import shutil
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "fonts"
LINK = '<link rel="stylesheet" href="fonts/fonts.css">'


def copy(target: Path) -> None:
    """fonts/ neben eine Seite (target: .html-Datei) oder in einen Zielordner kopieren."""
    d = (target.parent if target.suffix == ".html" else target) / "fonts"
    if d.resolve() == SRC.resolve():
        return
    d.mkdir(parents=True, exist_ok=True)
    for f in SRC.iterdir():
        if f.is_file():
            shutil.copy2(f, d / f.name)
