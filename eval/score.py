"""Score a run against hand-derived expected verdicts.

    python eval/score.py                       # the README fixtures
    python eval/score.py eval/expected_generalization.json

The expected files were written by hand before (fixtures) or without (generalization)
looking at the tool's output. It's a regression guard, not independent ground truth:
the same team wrote the rules and the expectations.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ichi.pipeline import run_files  # noqa: E402


def score(expected_path: Path) -> int:
    exp = json.loads(expected_path.read_text(encoding="utf-8"))
    fx = ROOT / exp["fixture"]
    res = run_files(fx / "code-analysis.html", fx / "window-schedule.html")
    got = res.by_id()
    rows, bad = [], 0
    for fid, want in exp["findings"].items():
        have = got[fid].verdict if fid in got else "(missing)"
        ok = have == want
        bad += not ok
        rows.append(f"{'ok  ' if ok else 'MISS'} {fid:6} expected {want:20} got {have}")
    extra = sorted(set(got) - set(exp["findings"]))
    print("\n".join(rows))
    if extra:
        print(f"not in expected file: {', '.join(extra)}")
    total = len(exp["findings"])
    print(f"\n{total - bad}/{total} match ({expected_path.name})")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(score(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "eval" / "expected.json"))
