"""02_atr_batch.py — ATR-Läufe von tei holen und in 02_lines.csv überführen.

Der Lauf selbst wird über den MCP-ATR-Server von agentic_historian gestartet
(`start_batch` mit source = Ordner unter data/nextcloud/adressbuecher-basel auf tei);
dieses Skript holt die Ergebnisse und macht daraus die Zeilen-CSV.

    python scripts/02_atr_batch.py fetch --run basel-probe-v1
    python scripts/02_atr_batch.py lines --run basel-probe-v1 [--run weitere]

`fetch` spiegelt data/vlm_test/<run>/ von tei nach data/atr/<run>/ (JSON, TXT,
manifest.jsonl, report.*; keine Bilder). `lines` liest alle <model>/<key>.json und
schreibt data/csv/02_lines.csv im Langformat: eine Zeile je Leser und erkannter Zeile.
Leser mit Geometrie (kraken) liefern bbox und Reihenfolge; Seitenleser (vLLM) liefern
nur Text, der an Zeilenumbrüchen geteilt wird — bei ihnen bleibt die Geometrie leer.

Seitenschlüssel: <volume>_p<nnn> (aus 01_render_pages.py), also 1884_p022.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path

TEI = "dh@tei.dh.unibe.ch"
TEI_RUNS = "agentic_historian/agentic_historian/data/vlm_test"
ATR_DIR = Path("data/atr")
CSV_DIR = Path("data/csv")

LINE_FIELDS = ["volume", "page", "key", "run_id", "reader", "engine", "line",
               "x0", "y0", "x1", "y1", "text", "line_confidence",
               "page_confidence", "truncated", "quality_verdict", "timing_ms"]

KEY_RE = re.compile(r"^(?P<volume>\d{4})_p(?P<page>\d{3})$")


def fetch(run: str) -> Path:
    dest = ATR_DIR / run
    dest.mkdir(parents=True, exist_ok=True)
    cmd = ["rsync", "-a", "--info=stats1",
           "--include=*/", "--include=*.json", "--include=*.jsonl", "--include=*.txt",
           "--include=*.md", "--exclude=*",
           f"{TEI}:{TEI_RUNS}/{run}/", f"{dest}/"]
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)
    return dest


def _rows_for(run: str, model_dir: Path, json_path: Path) -> list[dict]:
    d = json.loads(json_path.read_text(encoding="utf-8"))
    key = d.get("source", {}).get("key") or json_path.stem
    m = KEY_RE.match(key)
    volume, page = (m.group("volume"), str(int(m.group("page")))) if m else ("", "")
    base = {"volume": volume, "page": page, "key": key, "run_id": run,
            "reader": d.get("model") or model_dir.name, "engine": d.get("engine", ""),
            "page_confidence": d.get("confidence", ""), "truncated": int(bool(d.get("truncated"))),
            "quality_verdict": (d.get("quality") or {}).get("verdict", ""),
            "timing_ms": d.get("timing_ms", "")}
    rows = []
    lines = d.get("lines") or []
    if lines:
        for ln in sorted(lines, key=lambda x: x.get("order", 0)):
            bbox = ln.get("bbox") or ["", "", "", ""]
            rows.append({**base, "line": ln.get("order", len(rows) + 1),
                         "x0": bbox[0], "y0": bbox[1], "x1": bbox[2], "y1": bbox[3],
                         "text": ln.get("text", ""), "line_confidence": ln.get("confidence", "")})
    else:
        for i, t in enumerate((d.get("text") or "").split("\n"), start=1):
            if t.strip():
                rows.append({**base, "line": i, "x0": "", "y0": "", "x1": "", "y1": "",
                             "text": t, "line_confidence": ""})
    return rows


def lines(runs: list[str]) -> Path:
    out = CSV_DIR / "02_lines.csv"
    rows: list[dict] = []
    for run in runs:
        run_dir = ATR_DIR / run
        if not run_dir.exists():
            sys.exit(f"{run_dir} fehlt — zuerst `fetch --run {run}`")
        for model_dir in sorted(p for p in run_dir.iterdir() if p.is_dir()):
            for jp in sorted(model_dir.glob("*.json")):
                rows.extend(_rows_for(run, model_dir, jp))
    rows.sort(key=lambda r: (r["volume"], int(r["page"] or 0), r["run_id"], r["reader"], int(r["line"])))
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=LINE_FIELDS)
        w.writeheader(); w.writerows(rows)
    readers = sorted({r["reader"] for r in rows})
    pages = len({(r["volume"], r["page"]) for r in rows})
    print(f"{len(rows)} Zeilen, {pages} Seiten, Leser: {', '.join(readers)} → {out}")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch"); f.add_argument("--run", required=True)
    l = sub.add_parser("lines"); l.add_argument("--run", action="append", required=True)
    args = ap.parse_args()
    if args.cmd == "fetch":
        fetch(args.run)
    else:
        lines(args.run)


if __name__ == "__main__":
    main()
