"""One call from HTML to findings, used by the CLI and the tests."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .mapping import map_code_analysis, map_window_schedule
from .models import Finding, RunNotes
from .rules.egress import build_windows, check_windows, missing_symbols
from .rules.height import Table504, check_height
from .values import parse_room_numbering

DEFAULT_CODE_DIR = Path(__file__).resolve().parent.parent / "instructions" / "fixtures" / "code"


@dataclass
class Result:
    findings: list[Finding]
    notes: RunNotes
    code_analysis: dict = field(default_factory=dict)
    inputs: dict = field(default_factory=dict)

    def by_id(self) -> dict[str, Finding]:
        return {f.id: f for f in self.findings}


def run(code_analysis_html: str, schedule_html: str, table_html: str | None = None) -> Result:
    if table_html is None:
        table_html = (DEFAULT_CODE_DIR / "table-504.3.html").read_text(encoding="utf-8")
    notes = RunNotes()
    ca = map_code_analysis(code_analysis_html)
    height = check_height(ca, Table504(table_html))

    rows, cols = map_window_schedule(schedule_html, notes)
    numbering = parse_room_numbering(ca.get("room_numbering", ("", ""))[1])
    windows = build_windows(rows, "egress" in cols, numbering, notes)
    win, rooms = check_windows(windows, ca, notes)

    gaps = missing_symbols(windows)
    if gaps:
        notes.observations.append(f"Window symbols {', '.join(gaps)} are missing from the schedule. Rows dropped, or windows deleted? Confirm on the window schedule sheet.")
    for key in ("width", "height", "operation", "egress"):
        if key not in cols:
            notes.observations.append(f"No {key.upper()} column was found; findings that need it are Could Not Evaluate.")
    findings = [height] + rooms + win
    return Result(findings, notes, ca, {"windows": windows})


def run_files(code_analysis: Path, schedule: Path, code_dir: Path | None = None) -> Result:
    code_dir = code_dir or DEFAULT_CODE_DIR
    return run(Path(code_analysis).read_text(encoding="utf-8"), Path(schedule).read_text(encoding="utf-8"),
               (Path(code_dir) / "table-504.3.html").read_text(encoding="utf-8"))
