"""Shared test helpers: fixture paths and minimal HTML builders.

Expected values in the tests are derived from the code text (instructions/fixtures/code),
the README worked examples and extras/PLAN.md section 2, never from the rule implementations.
"""
from __future__ import annotations

import html as _html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "instructions" / "fixtures"
CODE_ANALYSIS_HTML = (FIXTURES / "project" / "code-analysis.html").read_text(encoding="utf-8")
SCHEDULE_HTML = (FIXTURES / "project" / "window-schedule.html").read_text(encoding="utf-8")
TABLE_HTML = (FIXTURES / "code" / "table-504.3.html").read_text(encoding="utf-8")

PASS, FAIL, CNE, NA = "Pass", "Fail", "Could Not Evaluate", "Not Applicable"

# The fixture schedule, as a list of (top header, sub header or None, values per row).
# Transcribed from window-schedule.html by hand so mutations can be built from it.
FIXTURE_ROWS = [
    # symbol, location, width, height, operation, mark, head, glass, safety, screen, hardware, egress, mfr, notes
    ("1", "BEDROOM 101", "2' - 6\"", "4' - 0\"", "L.H. CASM'T", "A", "6' - 8\"", "DBL.", "", "Y", "", "Y", "", "SEE ELEVATIONS"),
    ("2", "BEDROOM 101", "3' - 0\"", "4' - 0\"", "FIXED", "B", "6' - 8\"", "DBL.", "", "", "", "", "", "SEE ELEVATIONS"),
    ("3", "BEDROOM 101", "2' - 6\"", "4' - 0\"", "R.H. CASM'T", "A", "6' - 8\"", "DBL.", "", "Y", "", "Y", "", "SEE ELEVATIONS"),
    ("4", "OFFICE 102", "3' - O\"", "5' - 0\"", "L.H. CASM'T", "C", "7' - 0\"", "DBL.", "", "Y", "", "", "", "SEE ELEVATIONS"),
    ("5", "LIVING 103", "6' - 0\"", "5' - 0\"", "FIXED", "D", "7' - 0\"", "DBL.", "T", "", "", "", "", "SEE ELEVATIONS"),
    ("6", "KITCHEN 104", "3' - 0\"", "3' - 0\"", "AWNING", "E", "7' - 0\"", "DBL.", "", "Y", "", "", "", "SEE ELEVATIONS"),
    ("7", "ADU BEDROOM 107", "2'-6\"", "3' - 0\"", "L.H. CASM'T", "F", "6' - 8\"", "DBL.", "", "Y", "", "Y", "", "SEE ELEVATIONS"),
    ("8", "LAUNDRY 108", "2' - 0\"", "3' - 0\"", "SLIDER", "G", "6' - 8\"", "DBL.", "", "Y", "", "", "", "SEE ELEVATIONS"),
    ("10", "BEDROOM 203", "2' - 0\"", "2' - 6\"", "L.H. CASM'T", "H", "6' - 8\"", "DBL.", "", "Y", "", "Y", "", "SEE ELEVATIONS"),
    ("11", "BEDROOM 203", "3' - 0\"", "2' - 6\"", "FIXED", "I", "6' - 8\"", "DBL.", "", "", "", "", "", "SEE ELEVATIONS"),
    ("12", "BEDRROM 205", "3' - 0\"", "4' - 0\"", "S.H.", "J", "6' - 8\"", "DBL.", "", "Y", "", "Y", "", "SEE ELEVATIONS"),
    ("13", "BEDROOM 205", "4' - 0\"", "4' - 0\"", "FIXED", "K", "6' - 8\"", "DBL.", "", "", "", "Y", "", "SEE ELEVATIONS"),
    ("14", "BATH 206", "2' - 0\"", "2' - 0\"", "AWNING", "L", "7' - 0\"", "DBL.", "T", "Y", "", "", "", "SEE ELEVATIONS"),
    ("20", "BEDROOM 301", "2' - 6\"", "3' - 0\"", "L.H. CASM'T", "F", "8' - 0\"", "DBL.", "", "Y", "", "Y", "", "SEE ELEVATIONS"),
    ("21", "GUEST BED 303", "2' - 6\"", "4' - 0\"", "L.H. CASM'T", "A", "6' - 8\"", "DBL.", "", "Y", "", "", "", "SEE ELEVATIONS"),
    ("22", "HALL 302", "2' - 0\"", "6' - 0\"", "FIXED", "M", "7' - 0\"", "DBL.", "T", "", "", "", "", "SEE ELEVATIONS"),
    ("23", "STAIR S1", "2' - 0\"", "6' - 0\"", "FIXED", "M", "9' - 0\"", "DBL.", "T", "", "", "", "", "SEE ELEVATIONS"),
]
FIXTURE_HEADERS = [
    ("SYMBOL", None), ("LOCATION", None), ("NOMINAL SIZE", "WIDTH"), ("NOMINAL SIZE", "HEIGHT"),
    ("TYPE", None), ("TYPE", None), ("HEAD HEIGHT", None), ("GLAZING", "GLASS TYPE"), ("GLAZING", "SAFETY"),
    ("", "SCREEN"), ("", "HARDWARE"), ("EGRESS", None), ("", "MANUFACTURE"), ("", "NOTES"),
]


def fixture_columns() -> list[tuple[str, str | None, list[str]]]:
    """The fixture schedule as columns: (top header, sub header, values)."""
    return [(top, sub, [row[i] for row in FIXTURE_ROWS]) for i, (top, sub) in enumerate(FIXTURE_HEADERS)]


def schedule_html(columns: list[tuple[str, str | None, list[str]]]) -> str:
    """Build a two-row-header window schedule like the fixture.

    columns: (top header, sub header or None, values). Adjacent columns with the same
    non-empty top header are merged under one colspan cell; single-level columns get
    rowspan=2. An empty top header with a sub header gives an empty <th> like the fixture.
    """
    n = len(columns[0][2])
    assert all(len(c[2]) == n for c in columns)
    top_cells: list[str] = []
    i = 0
    while i < len(columns):
        top, sub, _ = columns[i]
        if sub is None:
            top_cells.append(f'<th rowspan="2">{_html.escape(top)}</th>')
            i += 1
            continue
        j = i
        while j + 1 < len(columns) and columns[j + 1][1] is not None and columns[j + 1][0] == top and top:
            j += 1
        span = j - i + 1
        attr = f' colspan="{span}"' if span > 1 else ""
        top_cells.append(f"<th{attr}>{_html.escape(top)}</th>")
        i = j + 1
    sub_cells = [f"<td>{_html.escape(sub)}</td>" for _, sub, _ in columns if sub is not None]
    out = ['<table border="1"><tbody>', "<tr>" + "".join(top_cells) + "</tr>"]
    if sub_cells:
        out.append("<tr>" + "".join(sub_cells) + "</tr>")
    out.append(f'<tr><td colspan="{len(columns)}"></td></tr>')
    for r in range(n):
        out.append("<tr>" + "".join(f"<td>{_html.escape(c[2][r])}</td>" for c in columns) + "</tr>")
    out.append("</tbody></table>")
    return "\n".join(out)


def simple_schedule(headers: list[str], rows: list[list[str]]) -> str:
    """A flat one-row-header schedule (README-style worked examples)."""
    out = ['<table border="1"><tbody>', "<tr>" + "".join(f"<th>{_html.escape(h)}</th>" for h in headers) + "</tr>"]
    for r in rows:
        assert len(r) == len(headers)
        out.append("<tr>" + "".join(f"<td>{_html.escape(c)}</td>" for c in r) + "</tr>")
    out.append("</tbody></table>")
    return "\n".join(out)


def windows_of(result) -> list:
    """Window findings in schedule order (ids depend on whether the SYMBOL column was read)."""
    return [f for f in result.findings if f.check == "egress-window"]


def rooms_of(result) -> dict:
    """Room findings keyed by the room text they carry (e.g. 'BEDROOM 2' or '205')."""
    return {f.room: f for f in result.findings if f.check == "egress-room"}


def the_room(result):
    rooms = [f for f in result.findings if f.check == "egress-room"]
    assert len(rooms) == 1, [f.id for f in rooms]
    return rooms[0]


def permute_R_subrows(table_html: str, order: tuple[str, ...]) -> str:
    """Reorder the three sprinklered sub-rows of row R (S13D, S13R, S) in table-504.3.html.
    The R label cell (rowspan=4) lives in the NS row, so these three rows carry no label and
    moving them is a pure reordering of the same table."""
    blocks = list(re.finditer(r"<tr>.*?</tr>", table_html, flags=re.S))
    start = next(i for i, m in enumerate(blocks) if "R<sup>h</sup>" in m.group(0))
    subs = blocks[start + 1:start + 4]
    by_name = {}
    for m in subs:
        name = next(n for n in ("S13D", "S13R") if f">{n}<" in m.group(0)) if ("S13D" in m.group(0) or "S13R" in m.group(0)) else "S"
        by_name[name] = m.group(0)
    assert set(by_name) == {"S13D", "S13R", "S"}, by_name.keys()
    out = table_html
    for m, name in reversed(list(zip(subs, order))):   # replace in place, from the end, keeping the gaps
        out = out[:m.start()] + by_name[name] + out[m.end():]
    return out


def code_analysis_html(rows: list[tuple[str, str]]) -> str:
    body = "".join(f"<tr><td>{_html.escape(k)}</td><td>{_html.escape(v)}</td></tr>" for k, v in rows)
    return f'<table border="1"><tbody>{body}</tbody></table>'


def readme_building(occupancy: str | None = "B", construction: str | None = "II-B",
                    sprinklers: str | None = "NONE", height: str | None = "52'-0\"") -> str:
    """The README's worked-example code analysis, with the README's own labels."""
    rows = []
    if occupancy is not None:
        rows.append(("OCCUPANCY GROUP", occupancy))
    if construction is not None:
        rows.append(("CONSTRUCTION TYPE", construction))
    if sprinklers is not None:
        rows.append(("SPRINKLERS", sprinklers))
    if height is not None:
        rows.append(("BUILDING HEIGHT", height))
    return code_analysis_html(rows)


# A minimal R-3 code analysis for the README's window examples (the README gives no
# numbering or stories; 1030.1 item 2 makes it apply to R-3 regardless).
R3_CODE_ANALYSIS = code_analysis_html([
    ("OCCUPANCY GROUP", "R-3"),
    ("CONSTRUCTION TYPE", "V-B"),
    ("SPRINKLERS", "NONE"),
    ("BUILDING HEIGHT", "30'-0\""),
])

README_WINDOW_HEADERS = ["SYMBOL", "LOCATION", "NOMINAL WIDTH", "NOMINAL HEIGHT", "TYPE", "HEAD HEIGHT", "EGRESS"]
W_A = ["W-A", "BEDROOM 2", "2'-0\"", "2'-0\"", "CASEMENT", "6'-8\"", "Y"]
W_B = ["W-B", "BEDROOM 2", "3'-0\"", "3'-6\"", "CASEMENT", "7'-0\"", "Y"]


def fixture_symbols() -> list[str]:
    """Every symbol in the fixture schedule, read straight from the HTML (first <td> of each
    body row after the separator), independent of the tool's parser."""
    rows = re.findall(r"<tr>(.*?)</tr>", SCHEDULE_HTML, flags=re.S)
    symbols = []
    for r in rows:
        tds = re.findall(r"<td[^>]*>(.*?)</td>", r, flags=re.S)
        if tds and re.fullmatch(r"\d+", tds[0].strip()):
            symbols.append(tds[0].strip())
    return symbols


def swap_tr_blocks(table_html: str, text_a: str, text_b: str) -> str:
    """Swap the two <tr>...</tr> blocks that contain text_a and text_b (first occurrence each)."""
    blocks = list(re.finditer(r"<tr>.*?</tr>", table_html, flags=re.S))
    a = next(m for m in blocks if text_a in m.group(0))
    b = next(m for m in blocks if text_b in m.group(0))
    first, second = sorted((a, b), key=lambda m: m.start())
    return (table_html[:first.start()] + second.group(0) + table_html[first.end():second.start()]
            + first.group(0) + table_html[second.end():])
