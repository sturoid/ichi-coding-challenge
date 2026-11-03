"""Header -> field, for tables whose column names and order change between projects.

Two layers, so a header guess never goes unchecked:
1. Synonyms (compacted, so 'SCREE N' == 'SCREEN'), with a fuzzy fallback that is logged.
2. Content: each column's values must look like what the header claims. Content
   also settles headers that say nothing ('TYPE' twice: operation words vs. letters).

Columns that content can't tell apart (nominal / rough-opening / net-clear sizes all
parse as feet-inches) are decided by header text alone. If that's unclear the column
is reported as ambiguous instead of guessed, because nominal-as-clear-opening is the
mistake this whole check exists to avoid.
"""
from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field

from .grid import Grid, build_grid
from .models import Correction, RunNotes
from .values import compact, looks_like_length, parse_flag, parse_operation

# field -> (kind of content expected, header patterns on the compacted header path)
FIELDS: dict[str, tuple[str, list[str]]] = {
    "net_clear_width":  ("length", [r"(NETCLEAR|NETCLR|CLEAROPENING|CLROPNG|NETOPNG|CLEAR).*(WIDTH|W)$"]),
    "net_clear_height": ("length", [r"(NETCLEAR|NETCLR|CLEAROPENING|CLROPNG|NETOPNG|CLEAR).*(HEIGHT|HGT|HT|(?<!WIDT)H)$"]),
    "net_clear_area":   ("number", [r"(NETCLEAR|NETCLR|CLEAR).*(AREA|SF|SQ)"]),
    "rough_width":      ("length", [r"(ROUGH|RGH).*(WIDTH|W)$", r"^R\.?O\.?(WIDTH|WD|W)$"]),
    "rough_height":     ("length", [r"(ROUGH|RGH).*(HEIGHT|HGT|HT|(?<!WIDT)H)$", r"^R\.?O\.?(HEIGHT|HGT|HT|H)$"]),
    "sill_height":      ("length", [r"SILL"]),
    "head_height":      ("length", [r"HEAD", r"^HD\.?HT\.?$"]),
    "width":            ("length", [r"^(NOMINAL|NOM\.?|SIZE|UNIT|NOMINALSIZE)*(WIDTH|W|WD)$"]),
    "height":           ("length", [r"^(NOMINAL|NOM\.?|SIZE|UNIT|NOMINALSIZE)*(HEIGHT|HGT|H|HT)$"]),
    "symbol":           ("id",     [r"^(SYMBOL|SYM\.?|NO\.?|#|NUMBER|WINDOWNO\.?|WIN\.?NO\.?|ID|TAG)$"]),
    "location":         ("text",   [r"^(LOCATION|ROOM|SPACE|ROOMNAME|LOC\.?)$"]),
    "operation":        ("operation", [r"^(OPERATION|OPER\.?|OP\.?|SASH|STYLE|WINDOWTYPE|TYPE)$"]),
    "type_mark":        ("mark",   [r"^(TYPE|MARK|MK\.?|TYPEMARK|WINDOWTYPE)$"]),
    "egress":           ("flag",   [r"EGRESS|EERO|ESCAPE"]),
    "screen":           ("flag",   [r"^SCREEN"]),
    "safety":           ("text",   [r"SAFETY|TEMP"]),
    "glass_type":       ("text",   [r"GLASS|GLAZINGTYPE|^GLZG\.?$|^GLAZING$"]),
    "hardware":         ("text",   [r"HARDWARE|HDWR"]),
    "manufacturer":     ("text",   [r"MANUFACTUR|MFR|MFG"]),
    "notes":            ("text",   [r"NOTES?|REMARKS|COMMENTS"]),
}
# Header words we know, for the logged fuzzy fallback.
KNOWN_WORDS = ["SYMBOL", "LOCATION", "WIDTH", "HEIGHT", "OPERATION", "TYPE", "HEADHEIGHT",
               "SILLHEIGHT", "EGRESS", "SCREEN", "SAFETY", "HARDWARE", "MANUFACTURER", "NOTES"]


@dataclass
class Column:
    index: int
    header: str            # header path joined with " / ", as printed
    target: str | None = None
    how: str = ""
    values: list[str] = field(default_factory=list)


@dataclass
class WindowRow:
    index: int             # body row number, 1-based
    cells: dict[str, str]  # field -> raw text
    units: dict[str, str] = field(default_factory=dict)  # field -> "in" where the header says bare numbers are inches


def _kind(values: list[str]) -> str:
    """What a column's non-blank values look like."""
    vals = [v for v in values if v.strip()]
    if not vals:
        return "blank"
    def share(pred):
        return sum(1 for v in vals if pred(v)) / len(vals)
    if share(looks_like_length) >= 0.8:
        return "length"
    if share(lambda v: parse_operation(v) is not None) >= 0.8:
        return "operation"
    if share(lambda v: parse_flag(v) is True) >= 0.8:
        return "flag"
    if share(lambda v: re.fullmatch(r"[A-Z]{1,2}\d?", v.strip().upper()) is not None) >= 0.8:
        return "mark"
    if share(lambda v: re.fullmatch(r"[A-Z]{0,3}-?\d{1,4}[A-Z]?|[A-Z]{1,2}-[A-Z0-9]{1,3}", v.strip().upper()) is not None) >= 0.8:
        return "id"
    if share(lambda v: re.fullmatch(r"\d+(\.\d+)?", v.strip()) is not None) >= 0.8:
        return "number"
    if share(lambda v: re.search(r"[A-Z]{3,}.*\d{2,4}", v.upper()) is not None) >= 0.8:
        return "room"
    return "text"


def _inch_header(path: list[str]) -> bool:
    return bool(re.search(r"\(IN\.?\)|INCH|\bIN\.?$", " ".join(path).upper()))


def _compatible(expected: str, kind: str, inches: bool = False) -> bool:
    if kind == "blank":
        return True        # an empty column contradicts nothing
    return {
        "length": kind == "length" or (inches and kind in ("number", "id")),
        "number": kind in ("text", "id"),
        "id": kind in ("id", "mark"),
        "text": kind in ("text", "room", "mark", "id", "operation", "flag"),
        "operation": kind == "operation",
        "mark": kind in ("mark", "id"),
        "flag": kind == "flag",
    }[expected]


def _candidates(path: list[str]) -> list[str]:
    joined = "".join(compact(h) for h in path)
    last = compact(path[-1]) if path else ""
    out = []
    for name, (_, pats) in FIELDS.items():
        if any(re.search(p, joined) or re.search(p, last) for p in pats):
            out.append(name)
    return out


def map_window_schedule(html: str, notes: RunNotes, source: str = "window schedule") -> tuple[list[WindowRow], dict[str, Column]]:
    grid: Grid = build_grid(html)
    columns: list[Column] = []
    for c in range(grid.width):
        path = grid.header_path(c)
        values = [(row[c].text if row[c] else "") for row in grid.body()]
        columns.append(Column(c, " / ".join(path) or "(blank header)", values=values))

    taken: dict[str, Column] = {}
    for col in columns:
        path = col.header.split(" / ") if col.header != "(blank header)" else []
        kind = _kind(col.values)
        cands = _candidates(path)
        how = "header"
        if not cands and path:
            guess = difflib.get_close_matches(compact(path[-1]), KNOWN_WORDS, n=1, cutoff=0.8)
            if guess:
                cands = _candidates([guess[0]])
                how = f"fuzzy header match '{path[-1]}' -> {guess[0]}"
                notes.corrections.append(Correction(f"{source}, column {col.index + 1}", path[-1], guess[0], "header matched by spelling similarity"))
        if any(c.startswith(("net_clear", "rough")) for c in cands):
            # 'NET CLR OPNG / W' also ends in W: the specific reading wins over plain nominal width.
            cands = [c for c in cands if c not in ("width", "height")]
        inches = _inch_header(path)
        fits = [f for f in cands if _compatible(FIELDS[f][0], kind, inches) and f not in taken]
        if len(fits) > 1:
            # 'TYPE' could be operation or mark: let the contents decide.
            by_content = [f for f in fits if FIELDS[f][0] == kind]
            fits = by_content or fits
        if not fits and not cands and kind == "operation" and "operation" not in taken:
            fits, how = ["operation"], "content only (values are window operations)"
        if len(fits) == 1:
            col.target = fits[0]
            if how != "header":
                col.how = how
            elif kind == "blank":
                col.how = "header (column empty)"
            else:
                col.how = f"header, contents agree ({kind})"
            taken[fits[0]] = col
        elif len(fits) > 1:
            col.how = f"ambiguous: could be {', '.join(fits)}"
            notes.not_read.append(f"Column {col.index + 1} '{col.header}': {col.how} (COLUMN_AMBIGUOUS)")
        elif cands:
            col.how = f"header says {', '.join(cands)} but contents look like {kind}; not used"
            notes.not_read.append(f"Column {col.index + 1} '{col.header}': {col.how} (COLUMN_NOT_READ)")
        else:
            col.how = "no matching header"
            if any(v.strip() for v in col.values):
                notes.not_read.append(f"Column {col.index + 1} '{col.header}': not recognized (COLUMN_NOT_READ)")
        notes.header_map.append((col.header, col.target or "-", col.how))

    if "symbol" not in taken and "type_mark" in taken:
        marks = [v.strip() for v in taken["type_mark"].values if v.strip()]
        if marks and len(set(marks)) == len(marks):
            taken["symbol"] = taken["type_mark"]
            notes.observations.append(f"No window number column; the '{taken['type_mark'].header}' values are unique per row, "
                                      "so they're used as window IDs.")
    if "symbol" not in taken:
        notes.observations.append("No window number column; windows are identified by row number.")
    inch_fields = {name for name, col in taken.items()
                   if FIELDS[name][0] == "length" and _inch_header(col.header.split(" / "))}
    rows: list[WindowRow] = []
    for i, row in enumerate(grid.body(), start=1):
        cells = {name: (row[col.index].text if row[col.index] else "") for name, col in taken.items()}
        rows.append(WindowRow(i, cells, {f: "in" for f in inch_fields}))
    return rows, taken


# ---------- code analysis: a two-column label/value sheet ----------

CODE_FIELDS: dict[str, list[str]] = {
    "occupancy": [r"OCCUPANCY"],
    "construction": [r"CONSTRUCTION", r"CONST\.?TYPE"],
    "sprinklers": [r"SPRINKLE", r"FIRESUPPRESSION"],
    "height": [r"BUILDINGHEIGHT", r"BLDG\.?HEIGHT", r"^HEIGHT", r"HEIGHTABOVEGRADE"],
    "allowable_height": [r"ALLOWABLEHEIGHT", r"ALLOW\.?HEIGHT"],
    "stories": [r"NUMBEROFSTORIES", r"^STORIES"],
    "room_numbering": [r"ROOMNUMBERING"],
    "grade_plane": [r"^GRADEPLANE"],
    "egress_note": [r"EMERGENCYESCAPE", r"EERO"],
    "project": [r"^PROJECT"],
    "code": [r"APPLICABLECODE", r"^CODE"],
}


def map_code_analysis(html: str) -> dict[str, tuple[str, str]]:
    """-> field: (label as printed, value). Labels are matched with whitespace removed
    because OCR splits words ('FIRE SPRINKLE RS')."""
    grid = build_grid(html, header_rows=0)
    out: dict[str, tuple[str, str]] = {}
    for row in grid.cells:
        cells = [c for i, c in enumerate(row) if c and (i == 0 or c is not row[i - 1])]
        if len(cells) < 2:
            continue
        label, value = cells[0].text, cells[1].text
        key = compact(label)
        for name, pats in CODE_FIELDS.items():
            if name not in out and any(re.search(p, key) for p in pats):
                # 'ALLOWABLE HEIGHT' also contains HEIGHT: check the more specific field first.
                if name == "height" and "ALLOW" in key:
                    continue
                out[name] = (label, value)
                break
    return out
