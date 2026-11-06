"""gt_diff.py — Abweichungen zweier Leser je Zeile, mit Bildausschnitten zum Entscheiden.

    python scripts/gt_diff.py --key 1884_p022 --a basel-probe-gemini-v1/gemini-3.8-flash \
        --b basel-probe-v1/kraken-german_print --out <ordner>

Richtet die normalisierten Zeilen beider Leser mit difflib aus, listet die Paare, die
sich unterscheiden, und schneidet für jede abweichende kraken-Zeile (die eine bbox hat)
den Streifen aus dem Seitenbild, zweifach vergrössert, als <key>_diff_<n>.png. Der
Text mit den Abweichungen steht in <key>_diff.txt. Schreibt keine Ground Truth; die
entsteht von Hand aus der Lesung A und den Entscheidungen.
"""
from __future__ import annotations

import argparse
import difflib
import json
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from importlib import import_module
normalise = import_module("03_compare_readers").normalise  # noqa: E402


def lines_of(run_model: str, key: str) -> tuple[list[str], list[dict]]:
    d = json.loads((Path("data/atr") / run_model / f"{key}.json").read_text(encoding="utf-8"))
    raw = d.get("lines") or []
    if raw:
        raw = sorted(raw, key=lambda x: x.get("order", 0))
        texts = [normalise(l.get("text", "")) for l in raw]
    else:
        texts = [normalise(t) for t in (d.get("text") or "").split("\n")]
        texts = [t for t in texts if t]
    return texts, raw


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", required=True)
    ap.add_argument("--a", required=True, help="run/model mit Zeilen ohne Geometrie (z. B. gemini)")
    ap.add_argument("--b", required=True, help="run/model mit bbox (kraken)")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    a_lines, _ = lines_of(args.a, args.key)
    b_lines, b_raw = lines_of(args.b, args.key)
    vol = args.key.split("_")[0]
    img = Image.open(next(Path(f"data/pages/{vol}").glob(f"{args.key}.*")))

    sm = difflib.SequenceMatcher(a=a_lines, b=b_lines, autojunk=False)
    report, n = [], 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        n += 1
        report.append(f"--- #{n} {tag}  A[{i1}:{i2}] / B[{j1}:{j2}]")
        for t in a_lines[i1:i2]:
            report.append(f"A: {t}")
        for t in b_lines[j1:j2]:
            report.append(f"B: {t}")
        boxes = [l.get("bbox") for l in b_raw[j1:j2] if l.get("bbox")]
        if boxes:
            y0 = max(0, int(min(b[1] for b in boxes)) - 6)
            y1 = min(img.height, int(max(b[3] for b in boxes)) + 6)
            crop = img.crop((0, y0, img.width, y1))
            crop = crop.resize((crop.width * 2, crop.height * 2), Image.LANCZOS)
            crop.save(args.out / f"{args.key}_diff_{n:02d}.png")
            report.append(f"   bild: {args.key}_diff_{n:02d}.png (y {y0}-{y1})")
    (args.out / f"{args.key}_diff.txt").write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))
    print(f"\n{n} Abweichungsblöcke; A={len(a_lines)} Zeilen, B={len(b_lines)} Zeilen")


if __name__ == "__main__":
    main()
