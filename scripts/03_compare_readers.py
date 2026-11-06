"""03_compare_readers.py — paarweise Abweichung der Leser je Seite, ohne Ground Truth.

Abweichung ist nicht Qualität: ohne handkorrigierte Seiten sagt die Zahl nur, wie
weit zwei Leser auseinanderliegen. Was sie beantwortet: welche Leser sich bei welcher
Satzart nahe sind (dann lohnt sich Abstimmung), und welche Seiten ein Leser ganz
anders liest (dann lohnt sich ein Blick). Mit `--gt data/gt` werden zusätzlich die
handkorrigierten Seiten als Referenz genommen und die CER je Leser ausgegeben.

    python scripts/03_compare_readers.py --run basel-probe-v1 --run basel-probe-gemini-v1

Normalisierung vor dem Vergleich (beide Seiten gleich): ſ→s, ⸗ und = zwischen Namen →
-, Tabs/Mehrfachleerzeichen → ein Leerzeichen, Leerzeilen weg, [spalte 2] weg,
[handschriftlich: …] weg. Gemessen wird die Levenshtein-Distanz auf dem Seitentext,
geteilt durch die Länge des längeren Texts.
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import re
import statistics
from pathlib import Path

from rapidfuzz.distance import Levenshtein

ATR_DIR = Path("data/atr")
CSV_DIR = Path("data/csv")


def normalise(text: str) -> str:
    t = text.replace("ſ", "s").replace("⸗", "-")
    t = re.sub(r"\[handschriftlich:[^\]]*\]", "", t)
    t = re.sub(r"\[stempel:[^\]]*\]", "", t)
    t = t.replace("[spalte 2]", "")
    t = re.sub(r"(?<=\S)=(?=\S)", "-", t)          # Gemini schreibt ⸗ als =
    t = re.sub(r"^\s*[*]\s*", "*", t, flags=re.M)   # Stern direkt an den Zeilenanfang
    t = re.sub(r"[ \t]+", " ", t)
    t = "\n".join(line.strip() for line in t.split("\n") if line.strip())
    return t


def load(runs: list[str]) -> dict[str, dict[str, str]]:
    """{reader: {key: normalised text}}"""
    out: dict[str, dict[str, str]] = {}
    for run in runs:
        for model_dir in sorted(p for p in (ATR_DIR / run).iterdir() if p.is_dir()):
            for jp in model_dir.glob("*.json"):
                d = json.loads(jp.read_text(encoding="utf-8"))
                reader = d.get("model") or model_dir.name
                out.setdefault(reader, {})[jp.stem] = normalise(d.get("text") or "")
    return out


def load_gt(gt_dir: Path) -> dict[str, str]:
    return {p.stem: normalise(p.read_text(encoding="utf-8")) for p in gt_dir.glob("*.txt")}


def cer(a: str, b: str) -> float:
    if not a and not b:
        return 0.0
    return Levenshtein.distance(a, b) / max(len(a), len(b))


def page_meta() -> dict[str, dict]:
    meta = {}
    with (CSV_DIR / "01_pages.csv").open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            meta[f"{r['volume']}_p{int(r['page']):03d}"] = r
    return meta


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--run", action="append", required=True)
    ap.add_argument("--gt", type=Path, default=None, help="Ordner mit <key>.txt als Referenz")
    ap.add_argument("--out", type=Path, default=CSV_DIR / "probe_disagreement.csv")
    args = ap.parse_args()

    readers = load(args.run)
    meta = page_meta()
    names = sorted(readers)
    keys = sorted(set.intersection(*(set(v) for v in readers.values())))
    print(f"{len(names)} Leser, {len(keys)} gemeinsame Seiten\n")

    rows = []
    for a, b in itertools.combinations(names, 2):
        for k in keys:
            rows.append({"key": k, "volume": meta.get(k, {}).get("volume", ""),
                         "section": meta.get(k, {}).get("section", ""),
                         "typeface": meta.get(k, {}).get("typeface", ""),
                         "reader_a": a, "reader_b": b,
                         "chars_a": len(readers[a][k]), "chars_b": len(readers[b][k]),
                         "disagreement": round(cer(readers[a][k], readers[b][k]), 4)})
    with args.out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)

    for tf in sorted({r["typeface"] for r in rows}):
        print(f"== Abweichung, Satz = {tf or '?'} (Median über Seiten)")
        for a, b in itertools.combinations(names, 2):
            vals = [r["disagreement"] for r in rows if r["typeface"] == tf and r["reader_a"] == a and r["reader_b"] == b]
            if vals:
                print(f"  {a:32s} vs {b:32s} {statistics.median(vals):.3f}  (n={len(vals)})")
    print("\n== Zeichen je Seite (Median)")
    for n in names:
        print(f"  {n:32s} {statistics.median(len(readers[n][k]) for k in keys):.0f}")

    if args.gt and args.gt.exists():
        gt = load_gt(args.gt)
        common = [k for k in keys if k in gt]
        print(f"\n== CER gegen Ground Truth ({len(common)} Seiten)")
        for n in names:
            vals = [cer(readers[n][k], gt[k]) for k in common]
            if vals:
                print(f"  {n:32s} mean {statistics.mean(vals):.3f}  "
                      + "  ".join(f"{k}:{v:.3f}" for k, v in zip(common, vals)))
    print(f"\n→ {args.out}")


if __name__ == "__main__":
    main()
