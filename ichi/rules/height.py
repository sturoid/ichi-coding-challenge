"""Check 1: building height against IBC 2018 Table 504.3.

The table is parsed from the code fixture at run time, never typed in, and every
lookup returns where the number came from so a wrong-cell read is visible.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from ..grid import build_grid
from ..models import CNE, FAIL, PASS, Evidence, Finding
from ..values import first_length, parse_construction, parse_sprinklers

CODE = "IBC 2018 Table 504.3"
SUBROWS = ("NS", "S", "S13R", "S13D")
SPRINKLER_NAMES = {"S": "an NFPA 13 system (IBC 903.3.1.1)", "S13R": "an NFPA 13R system (IBC 903.3.1.2)",
                   "S13D": "an NFPA 13D system (IBC 903.3.1.3)", "NS": "no sprinklers"}


@dataclass
class Lookup:
    value: str
    row_label: str
    row_footnotes: list[str]
    subrow: str
    subrow_footnotes: list[str]
    column: str
    source_row: int          # <tr> index (0-based) of the cell the value came from
    merged: bool             # value cell spans more than one sub-row


class Table504:
    def __init__(self, html: str):
        self.grid = build_grid(html)
        self.columns: dict[tuple[str, str], int] = {}
        for c in range(self.grid.width):
            path = self.grid.header_path(c)
            major = next((m.group(1) for h in path if (m := re.fullmatch(r"TYPE\s+(IV|V|III|II|I)", h.strip().upper()))), None)
            minor = path[-1].strip().upper() if path else ""
            if major and minor in ("A", "B", "HT"):
                self.columns[(major, minor)] = c
        # rows: (row label cell, sub-row cell, body row index)
        self.rows: list[tuple[str, list[str], str, list[str], int]] = []
        for i, row in enumerate(self.grid.body()):
            label, sub = row[0], row[1]
            if not label or not sub:
                continue
            self.rows.append((label.text, label.footnotes, sub.text.strip().upper(), sub.footnotes, i))

    def row_labels(self) -> list[str]:
        seen: list[str] = []
        for label, *_ in self.rows:
            if label not in seen:
                seen.append(label)
        return seen

    def match_occupancy(self, occ: str) -> tuple[str | None, str]:
        """'R-3' -> 'R'; 'B' -> 'A, B, E, F, M, S, U'; 'I-1' (no condition) -> ambiguous."""
        o = re.sub(r"\s+", " ", occ.strip().upper())
        exact, prefix = [], []
        for label in self.row_labels():
            tokens = [t.strip().upper() for t in label.split(",")]
            if o in tokens:
                exact.append(label)
            elif any(t.startswith(o + " ") for t in tokens):
                prefix.append(label)          # 'I-1' vs 'I-1 CONDITION 1' and 'I-1 CONDITION 2'
            elif re.match(r"^[A-Z]", o) and o.split("-")[0] in tokens:
                prefix.append(label)          # 'R-3' -> row 'R'; 'S-1' -> 'S' in the first row
        if len(exact) == 1:
            return exact[0], f"'{o}' is listed in row '{exact[0]}'"
        if len(prefix) == 1 and not exact:
            return prefix[0], f"'{o}' falls under row '{prefix[0]}'"
        if len(prefix) > 1:
            return None, f"'{o}' matches more than one row ({'; '.join(prefix)}); the condition is needed"
        return None, f"no Table 504.3 row for occupancy '{o}'"

    def lookup(self, row_label: str, subrow: str, column: tuple[str, str]) -> Lookup | None:
        c = self.columns.get(column)
        if c is None:
            return None
        for label, lf, sub, sf, i in self.rows:
            if label == row_label and sub == subrow:
                cell = self.grid.body()[i][c]
                if cell is None:
                    return None
                body_row_of_cell = next(j for j, r in enumerate(self.grid.body()) if r[c] is cell)
                return Lookup(cell.text, label, lf, sub, sf, f"Type {column[0]}-{column[1]}",
                              cell.row, merged=cell.rowspan > 1 or body_row_of_cell != i)
        return None


def _ftin(inches: float) -> str:
    ft, rem = divmod(inches, 12)
    return f"{int(ft)}'-{rem:g}\" ({inches:g} in)" if ft else f"{inches:g} in"


def check_height(ca: dict[str, tuple[str, str]], table: Table504, src: str = "code analysis") -> Finding:
    f = Finding("H1", "height", "Building", CNE, CODE, "", reason_code=None)
    ev = f.evidence

    def need(key: str, what: str) -> str | None:
        if key not in ca or not ca[key][1].strip():
            f.reason = f"The code analysis doesn't give the {what}, so the Table 504.3 cell can't be chosen."
            f.reason_code = f"MISSING_{key.upper()}"
            f.settles_with = f"the {what} on the code analysis sheet"
            f.next_step = f"Ask the architect to state the {what} on the code analysis."
            f.draft_comment = f"Provide the {what} on the code analysis so the allowable height under IBC Table 504.3 can be verified."
            return None
        label, value = ca[key]
        return value

    occ = need("occupancy", "occupancy group")
    if occ is None:
        return f
    ev.append(Evidence("Occupancy", occ, "", f"{src}, '{ca['occupancy'][0]}'"))
    row, why = table.match_occupancy(occ)
    ev[-1].parsed = f"row '{row}'" if row else why
    if row is None:
        f.reason, f.reason_code = f"Can't place the occupancy in the table: {why}.", "OCCUPANCY_ROW_UNCLEAR"
        f.next_step = "Confirm the occupancy group (and condition, for I-1)."
        return f
    f.derivation.append(f"Occupancy {occ} -> {why}.")

    cons_raw = need("construction", "construction type")
    if cons_raw is None:
        return f
    cons = parse_construction(cons_raw)
    ev.append(Evidence("Construction type", cons_raw, f"Type {cons[0]}-{cons[1]}" if cons else "not understood",
                       f"{src}, '{ca['construction'][0]}'"))
    if cons is None or cons not in table.columns:
        f.reason, f.reason_code = f"Construction type '{cons_raw}' isn't a Table 504.3 column.", "MISSING_CONSTRUCTION"
        return f
    f.derivation.append(f"Construction {cons_raw} -> column TYPE {cons[0]} / {cons[1]}.")

    spr_raw = need("sprinklers", "sprinkler system")
    if spr_raw is None:
        return f
    sub, spr_why = parse_sprinklers(spr_raw)
    ev.append(Evidence("Sprinklers", spr_raw, f"sub-row {sub}" if sub else spr_why, f"{src}, '{ca['sprinklers'][0]}'"))
    if sub is None:
        f.reason, f.reason_code = f"Can't tell which sprinkler sub-row applies: {spr_why}.", "SPRINKLER_UNCLEAR"
        f.settles_with = "the fire sprinkler system type (NFPA 13, 13R or 13D) on the code analysis"
        f.next_step = "Confirm the sprinkler system standard."
        f.draft_comment = "Clarify the automatic sprinkler system type (NFPA 13 / 13R / 13D) so the Table 504.3 sub-row can be determined."
        return f
    f.derivation.append(f"Sprinklers: {spr_why}.")

    h_raw = need("height", "building height")
    if h_raw is None:
        return f
    h_in, h_txt, _ = first_length(h_raw, src)
    ev.append(Evidence("Building height", h_raw, f"{h_in / 12:g} ft" if h_in else "not understood", f"{src}, '{ca['height'][0]}'"))
    if h_in is None:
        f.reason, f.reason_code = "The building height couldn't be read.", "MISSING_HEIGHT"
        return f

    lk = table.lookup(row, sub, cons)
    if lk is None:
        f.reason, f.reason_code = f"No Table 504.3 cell for row '{row}' / {sub} / Type {cons[0]}-{cons[1]}.", "TABLE_CELL_MISSING"
        return f
    cell_ref = f"row '{lk.row_label}' / sub-row {lk.subrow} / column {lk.column}"
    f.code_ref = f"{CODE}, {cell_ref}"
    ev.append(Evidence("Table 504.3 cell", lk.value, f"{lk.value} ft" if lk.value != "UL" else "unlimited",
                       f"table-504.3.html, {cell_ref}" + (" (merged cell spanning sub-rows)" if lk.merged else "")))
    f.derivation.append(f"Lookup {lk.row_label} > {lk.subrow} > {lk.column} = {lk.value}.")
    f.assumptions.append("The building height is the architect's stated value; the grade-plane calculation it depends on (civil sheet) wasn't provided.")
    if "d" in lk.subrow_footnotes and "NEW" in ca.get("project", ("", ""))[1].upper():
        f.flags.append("Footnote d: the NS value is only for evaluating existing buildings. A new building in this group must be sprinklered, so this limit isn't a clean answer.")

    h_ft = h_in / 12
    if lk.value.upper() == "UL":
        f.verdict, f.reason = PASS, f"Table 504.3 gives no height limit (UL) for {cell_ref}."
    else:
        limit = float(lk.value)
        diff_in = h_in - limit * 12
        if diff_in > 0:
            f.verdict = FAIL
            f.reason = f"The building is {h_txt} ({h_ft:g} ft); Table 504.3 allows {limit:g} ft, so it's over by {_ftin(diff_in)}."
            f.margin = f"{_ftin(diff_in)} over"
            f.draft_comment = (f"Building height of {h_txt} exceeds the {limit:g} ft maximum in IBC Table 504.3 for "
                               f"Group {occ} ({lk.row_label} row), {lk.subrow} sprinkler sub-row, Type {cons[0]}-{cons[1]} construction. "
                               "Reduce the building height, or revise the construction type or sprinkler system and update the code analysis.")
            fixes = [s for s in SUBROWS if s != lk.subrow and (o := table.lookup(row, s, cons))
                     and (o.value.upper() == "UL" or float(o.value) * 12 >= h_in)]
            by_value: dict[str, list[str]] = {}
            for s in fixes:
                by_value.setdefault(table.lookup(row, s, cons).value, []).append(SPRINKLER_NAMES[s])
            if by_value:
                f.draft_comment += (" For reference, Table 504.3 allows " + "; ".join(
                    f"{v} ft with {' or '.join(names)}" for v, names in by_value.items()) + " in this row and column.")
        else:
            f.verdict = PASS
            f.reason = f"The building is {h_txt} ({h_ft:g} ft); Table 504.3 allows {limit:g} ft."
            f.margin = f"{_ftin(-diff_in)} under"
        f.derivation.append(f"{h_ft:g} ft {'>' if diff_in > 0 else '<='} {limit:g} ft.")

    if "allowable_height" in ca:
        a_raw = ca["allowable_height"][1]
        a_in, a_txt, _ = first_length(a_raw, src)
        ev.append(Evidence("Architect's stated allowable", a_raw, f"{a_in / 12:g} ft" if a_in else "not understood",
                           f"{src}, '{ca['allowable_height'][0]}'"))
        if a_in is not None and lk.value.upper() != "UL" and abs(a_in / 12 - float(lk.value)) > 1e-6:
            other = [s for s in SUBROWS if (o := table.lookup(row, s, cons)) and o.value == f"{a_in / 12:g}"]
            hint = (f"{a_in / 12:g} ft is the {' and '.join(other)} value in the same column, not {lk.subrow}."
                    if other else f"{a_in / 12:g} ft doesn't match any sub-row in this column.")
            msg = (f"The code analysis says the allowable height is {a_txt} per Table 504.3, but the table gives "
                   f"{lk.value} ft for this building ({cell_ref}). {hint}")
            f.flags.append(msg)
            stated = f"Correct the allowable height on the code analysis: it states {a_txt}; Table 504.3 gives {lk.value} ft."
            f.draft_comment = f"{f.draft_comment} {stated}" if f.draft_comment else stated
    return f
