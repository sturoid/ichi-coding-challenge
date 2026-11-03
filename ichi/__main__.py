"""python -m ichi CODE_ANALYSIS.html WINDOW_SCHEDULE.html [-o REPORT.md] [--answers answers.json]"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import answers as answers_mod
from .pipeline import DEFAULT_CODE_DIR, run
from .report import render


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m ichi", description="Check building height (IBC Table 504.3) and bedroom escape windows (IBC 1030).")
    p.add_argument("code_analysis", type=Path)
    p.add_argument("window_schedule", type=Path)
    p.add_argument("-o", "--out", type=Path, default=Path("REPORT.md"))
    p.add_argument("--code-dir", type=Path, default=DEFAULT_CODE_DIR, help="folder holding table-504.3.html")
    p.add_argument("--answers", type=Path, help="reviewer answers (JSON); see answers.template.json")
    p.add_argument("--json", type=Path, help="also write findings as JSON (default: next to the report)")
    a = p.parse_args(argv)

    ca_text = a.code_analysis.read_text(encoding="utf-8")
    ws_text = a.window_schedule.read_text(encoding="utf-8")
    table_text = (a.code_dir / "table-504.3.html").read_text(encoding="utf-8")
    ans = answers_mod.load(a.answers) if a.answers else None
    res = run(ca_text, ws_text, table_text, ans)

    def show(path: Path) -> str:
        try:
            return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
        except ValueError:
            return path.as_posix()
    inputs = {"ca": (show(a.code_analysis), ca_text), "ws": (show(a.window_schedule), ws_text),
              "table": (show(a.code_dir / "table-504.3.html"), table_text)}
    if ans:
        inputs["answers"] = (show(a.answers), a.answers.read_text(encoding="utf-8"))
    a.out.write_text(render(res, inputs, table_text), encoding="utf-8", newline="\n")
    json_path = a.json or a.out.with_name("findings.json")
    json_path.write_text(json.dumps([f.to_dict() for f in res.findings], indent=2) + "\n", encoding="utf-8", newline="\n")
    tmpl_path = a.out.with_name("answers.template.json")
    tmpl_path.write_text(json.dumps(answers_mod.template(res.findings), indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {a.out}, {json_path.name}, {tmpl_path.name}: "
          + ", ".join(f"{sum(1 for f in res.findings if f.verdict == v)} {v}" for v in ("Fail", "Could Not Evaluate", "Pass", "Not Applicable")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
