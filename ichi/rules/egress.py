"""Check 2: bedroom emergency escape and rescue openings (EERO), IBC 2018 Section 1030.

Verdict principle (extras/PLAN.md §2):
- Fail only if the window fails even in the best case: no frame or sash loss, the
  most generous reading of the head height.
- Pass only if it passes with real clear-opening numbers (a
  net-clear column). Nominal sizes are never treated as the clear opening.
- Everything else is Could Not Evaluate, with the margin in inches or square feet.
  A margin of exactly zero is tagged "boundary": any frame at all makes it fail.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..mapping import WindowRow
from ..models import CNE, FAIL, NA, PASS, Correction, Evidence, Finding, RunNotes
from ..values import classify_room, parse_flag, parse_length, parse_operation, parse_room_numbering, split_room

MIN_AREA, GRADE_AREA, MIN_H, MIN_W, MAX_SILL = 5.7, 5.0, 24.0, 20.0, 44.0
# Upper bounds on the share of the unit that opens, by operation (width, height).
FACTORS = {
    "casement": (1.0, 1.0), "awning": (1.0, 1.0), "hopper": (1.0, 1.0),
    "single hung": (1.0, 0.5), "double hung": (1.0, 0.5), "slider": (0.5, 1.0),
}
REF_AREA, REF_DIMS, REF_SILL, REF_OPS = "IBC 1030.2", "IBC 1030.2.1", "IBC 1030.3", "IBC 1030.2.1"
EXC2 = ("Exception 2 to 1030.1: no EERO is needed if the room has an exit door opening directly to a public way, "
        "yard or court. Not visible in these documents; verify on the floor plan before issuing.")


@dataclass
class Window:
    row: WindowRow
    symbol: str
    location: str
    room_key: str
    room_name: str
    room_class: str
    room_why: str
    floor: int | None
    designated: bool | None          # None = no EGRESS column at all
    operation: str | None
    op_raw: str
    mark: str
    width: float | None
    height: float | None
    head: float | None
    sill: float | None
    sill_derived: bool
    net_w: float | None = None       # net clear opening, when the schedule gives it
    net_h: float | None = None
    evidence: list[Evidence] = field(default_factory=list)

    @property
    def label(self) -> str:
        return f"Window {self.symbol}"


@dataclass
class Assessment:
    verdict: str
    reason: str
    code_ref: str
    reason_code: str | None = None
    tag: str | None = None
    margin: str | None = None
    settles_with: str | None = None
    derivation: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)


def _ft(inches: float | None) -> str:
    if inches is None:
        return "?"
    ft, rem = divmod(inches, 12)
    return f"{int(ft)}'-{rem:g}\""


def build_windows(rows: list[WindowRow], has_egress_col: bool, numbering: dict[str, int],
                  notes: RunNotes, src: str = "window schedule") -> list[Window]:
    out = []
    for r in rows:
        c = r.cells
        sym = c.get("symbol", "").strip() or f"row {r.index}"
        where = f"{src}, symbol {sym}"
        loc = c.get("location", "")
        cls, why, fixes = classify_room(loc, f"{where}, LOCATION")
        notes.corrections.extend(fixes)
        name, num = split_room(loc)
        if fixes and fixes[0].read_as != fixes[0].raw and " " in fixes[0].read_as:
            name = split_room(fixes[0].read_as)[0]
        tail = loc.strip().split(" ")[-1].upper() if loc.strip() else ""
        if num and tail != num and re.search(r"\d", tail):
            notes.corrections.append(Correction(f"{where}, LOCATION", loc, f"room {num}", "letters in the room number read as digits (l/I as 1, O as 0)"))
        floor = numbering.get(num[0]) if num else None
        lens = {}
        for key in ("width", "height", "head_height", "sill_height"):
            v, fx = parse_length(c.get(key, ""), f"{where}, {key.replace('_', ' ').upper()}")
            notes.corrections.extend(fx)
            lens[key] = v
        net = {}
        for key in ("net_clear_width", "net_clear_height"):
            raw_v = c.get(key, "").strip()
            v, fx = parse_length(raw_v, f"{where}, {key.replace('_', ' ').upper()}")
            if v is None and r.units.get(key) == "in" and re.fullmatch(r"\d+(\.\d+)?", raw_v):
                v = float(raw_v)
            notes.corrections.extend(fx)
            net[key] = v
        sill, derived = lens["sill_height"], False
        if sill is None and lens["head_height"] is not None and lens["height"] is not None:
            sill, derived = lens["head_height"] - lens["height"], True
        designated = parse_flag(c.get("egress", "")) if has_egress_col else None
        w = Window(r, sym, loc, num or name, name, cls, why, floor, designated,
                   parse_operation(c.get("operation", "")), c.get("operation", ""), c.get("type_mark", "").strip(),
                   lens["width"], lens["height"], lens["head_height"], sill, derived,
                   net["net_clear_width"], net["net_clear_height"])
        w.evidence = [
            Evidence("Location", loc, f"{name} (room {num}, floor {floor or '?'}): {cls}, {why}", f"{where}, LOCATION"),
            Evidence("Nominal size", f"{c.get('width', '')} x {c.get('height', '')}",
                     f"{_ft(w.width)} x {_ft(w.height)}" + (f" = {w.width * w.height / 144:g} sf" if w.width and w.height else ""),
                     f"{where}, NOMINAL SIZE"),
            Evidence("Operation", w.op_raw, w.operation or "not recognized", f"{where}, TYPE (operation)"),
            Evidence("Type mark", w.mark, w.mark or "-", f"{where}, TYPE (mark)"),
            Evidence("Head height", c.get("head_height", ""), _ft(w.head), f"{where}, HEAD HEIGHT"),
            *([Evidence("Net clear opening", f"{c.get('net_clear_width', '')} x {c.get('net_clear_height', '')}",
                        f"{w.net_w:g} x {w.net_h:g} in", f"{where}, NET CLEAR")] if w.net_w and w.net_h else []),
            Evidence("Egress", c.get("egress", "") if has_egress_col else "(no EGRESS column)",
                     {True: "designated EERO", False: "not designated", None: "unknown"}[designated], f"{where}, EGRESS"),
        ]
        out.append(w)
    return out


def floor_above_grade(ca: dict) -> float | None:
    """First-floor level above the grade plane, in inches, from 'GRADE PLANE EL. 100.0' ... F.F. EL. 101.0''."""
    els = re.findall(r"EL\.?\s*(\d+(?:\.\d+)?)\s*'", ca.get("grade_plane", ("", ""))[1].upper())
    return (float(els[1]) - float(els[0])) * 12 if len(els) >= 2 else None


def assess(w: Window, ff_above_grade: float | None = None) -> Assessment:
    """Best-case bounds for one window, or exact checks when the schedule gives net clear sizes.
    `ff_above_grade` (inches) only changes wording: the grade plane is an average, so it can't rule
    out a grade-floor opening, and verdicts keep the 5.0 sf Fail threshold on floor 1."""
    if w.operation != "fixed" and (w.operation is None or w.width is None or w.height is None) \
            and w.sill is not None and w.sill > MAX_SILL:
        # The sill fails whatever the size or operation turns out to be (the opening can't start below the unit).
        a = Assessment(FAIL, f"Sill {w.sill:g} in > {MAX_SILL:g} in max, {w.sill - MAX_SILL:g} in over before any frame (1030.3). "
                       "Size or operation couldn't be read, but no window can open below its own sill.", REF_SILL,
                       margin=f"sill {w.sill - MAX_SILL:g} in too high")
        a.failures.append(f"sill {w.sill:g} in > {MAX_SILL:g} in max (1030.3)")
        if w.sill_derived:
            a.derivation.append(f"Sill = head height {_ft(w.head)} - nominal height {_ft(w.height)} = {w.sill:g} in above the floor.")
        return a
    if w.operation is None:
        return Assessment(CNE, f"Window operation '{w.op_raw}' isn't recognized, so the opening can't be bounded.",
                          REF_DIMS, "OPERATION_UNKNOWN", "open", settles_with="the window type / operation")
    if w.operation == "fixed":
        a = Assessment(FAIL, "Fixed window: it doesn't open, so it provides no clear opening under normal operation.",
                       REF_OPS, margin="no operable opening")
        a.failures.append("fixed unit, does not open, so normal operation gives no clear opening (1030.2.1)")
        a.code_ref = REF_OPS
        return a
    if w.width is None or w.height is None:
        return Assessment(CNE, "Nominal size couldn't be read.", REF_AREA, "SIZE_UNREADABLE", "open",
                          settles_with="the window size on the schedule")

    fw, fh = FACTORS[w.operation]
    exact = bool(w.net_w and w.net_h)
    a = Assessment(CNE, "", f"{REF_AREA}, {REF_DIMS}, {REF_SILL}")
    if exact:
        cw, ch = w.net_w, w.net_h
        a.derivation.append(f"Net clear {cw:g} x {ch:g} in from the net clear columns on the window schedule.")
    else:
        cw, ch = w.width * fw, w.height * fh
        a.derivation.append(f"Best-case clear opening = nominal x operation factor ({w.operation}: width x{fw:g}, height x{fh:g}) "
                            f"= {cw:g} x {ch:g} in.")
        a.assumptions.append("Best case: no frame or sash loss, so the real clear opening is smaller than this.")
        if w.operation in ("single hung", "double hung"):
            a.assumptions.append("Hung window: only one sash opens; assumed to be half the unit height (equal sashes). "
                                 "A cottage-style unit with a taller bottom sash would open more.")
        if w.operation == "slider":
            a.assumptions.append("Slider: one panel opens; assumed to be half the unit width.")
        if w.operation == "awning":
            a.assumptions.append("Awning: the opening depends on the hinge hardware; the full unit is an upper bound only.")
    area = cw * ch / 144
    grade_possible = w.floor in (1, None)
    fail_area = GRADE_AREA if grade_possible else MIN_AREA
    # Rough grade-floor estimate: sill above the grade plane (an average of adjacent grade, so an estimate only).
    sill_above_grade = (w.sill + ff_above_grade) if (w.floor == 1 and w.sill is not None and ff_above_grade is not None) else None
    grade_likely = grade_possible and (sill_above_grade is None or sill_above_grade <= MAX_SILL)
    grade_note = None
    if sill_above_grade is not None:
        grade_note = (f"Sill about {sill_above_grade:g} in above the grade plane (sill {w.sill:g} in + first floor "
                            f"{ff_above_grade:g} in above grade plane): "
                            + ("within 44 in, so possibly a grade-floor opening (5.0 sf)." if grade_likely
                               else "more than 44 in, so probably not a grade-floor opening; 5.7 sf applies unless grade at this wall is higher."))
    a.derivation.append(f"Area = {cw:g} x {ch:g} / 144 = {area:.2f} sf.")

    sill_bottom, sill_worst = w.sill, None
    if sill_bottom is not None and exact:
        hung = w.operation in ("single hung", "double hung")
        loss = max(0.0, w.height - 2 * ch) if hung else max(0.0, w.height - ch)
        sill_worst = sill_bottom + loss
        a.assumptions.append(
            f"Worst case for the sill: the opening sits as high in the unit as the net clear data allows, {loss:g} in above the unit sill"
            + (" (a hung sash opens below a sash at least as tall as the opening)." if hung else "."))
    sill_exact = sill_worst is not None
    if w.sill is not None and w.sill_derived:
        a.derivation.append(f"Sill = head height {_ft(w.head)} - nominal height {_ft(w.height)} = {w.sill:g} in above the floor.")
        a.assumptions.append("Head height is taken as the top of the unit, the usual schedule convention. If it's measured to "
                             "the clear opening instead, the real sill is higher; any Pass here relies on this convention.")
    if grade_note:
        a.derivation.append(grade_note)

    margins, boundary, open_items = [], [], []
    short: list[str] = []
    loss_txt = "" if exact else " even with no frame loss"
    # 1030.2 area
    if area < fail_area:
        a.failures.append(f"area {area:.2f} sf < {fail_area:g} sf{loss_txt} (1030.2)")
        short.append(f"area {fail_area - area:.2f} sf short")
    elif exact and area >= MIN_AREA:
        margins.append(f"area {area:.2f} sf >= {MIN_AREA:g} sf")
    elif exact:
        open_items.append(f"area: net clear {area:.2f} sf meets {GRADE_AREA:g} sf only if this is a grade-floor opening, which these documents don't show")
        short.append("area: depends on grade-floor status")
    else:
        need = MIN_AREA / area
        txt = f"area: best case {area:.2f} sf vs {MIN_AREA:g} sf required, so net clear must be at least {need:.0%} of it"
        if grade_likely:
            txt += f" ({GRADE_AREA / area:.0%} if it's a grade-floor opening)"
        (boundary if abs(area - MIN_AREA) < 1e-9 else open_items).append(txt)
        short.append(f"area: needs {need:.0%} of nominal as net clear")
    # 1030.2.1 dimensions
    for dim, val, req in (("height", ch, MIN_H), ("width", cw, MIN_W)):
        if val < req:
            a.failures.append(f"clear {dim} {val:g} in < {req:g} in{loss_txt} (1030.2.1)")
            short.insert(0, f"clear {dim} {req - val:g} in short")
        elif exact:
            margins.append(f"clear {dim} {val:g} in >= {req:g} in")
        elif abs(val - req) < 1e-9:
            boundary.append(f"clear {dim}: best case exactly {req:g} in, so any frame or rail loss fails it (1030.2.1)")
            short.insert(0, f"clear {dim}: 0 in to spare")
        else:
            open_items.append(f"clear {dim}: best case {val:g} in vs {req:g} in minimum ({val - req:g} in to spare before frame loss)")
    # 1030.3 sill
    if sill_bottom is None:
        open_items.append("sill height: no head height or sill to work from (1030.3)")
    elif sill_bottom > MAX_SILL:
        a.failures.append(f"sill {sill_bottom:g} in > {MAX_SILL:g} in max, {sill_bottom - MAX_SILL:g} in over before any frame (1030.3)")
        short.insert(0, f"sill {sill_bottom - MAX_SILL:g} in too high")
    elif sill_exact and sill_worst <= MAX_SILL:
        margins.append(f"clear-opening bottom at most {sill_worst:g} in <= {MAX_SILL:g} in")
    elif abs(sill_bottom - MAX_SILL) < 1e-9:
        boundary.append(f"sill: best case exactly {MAX_SILL:g} in, so any frame loss puts the opening above {MAX_SILL:g} in (1030.3)")
        short.insert(0, "sill: 0 in to spare")
    elif sill_exact:
        open_items.append(f"sill: clear-opening bottom between {sill_bottom:g} and {sill_worst:g} in; the {MAX_SILL:g} in max falls in that range")
        short.append("sill: needs the sill-to-opening dimension")
    else:
        open_items.append(f"sill: {sill_bottom:g} in, {MAX_SILL - sill_bottom:g} in under the max before the sill frame is added")

    a.derivation += [f"Fails: {x}" for x in a.failures] + [f"At the limit: {x}" for x in boundary] + [f"Open: {x}" for x in open_items]
    if a.failures:
        a.verdict = FAIL
        a.reason = "; ".join(a.failures).capitalize() + "."
        a.margin = "; ".join(x for x in short if "short" in x or "too high" in x)
        refs = sorted({m.group(1) for x in a.failures if (m := re.search(r"\((1030[\d.]*)", x))})
        a.code_ref = "IBC " + ", ".join(refs)
    elif not boundary and not open_items:
        a.verdict, a.reason = PASS, "Supplied clear-opening data meets 1030.2, 1030.2.1 and 1030.3: " + "; ".join(margins) + "."
    elif boundary:
        a.tag = "boundary"
        a.reason = "At the limit even in the best case: " + "; ".join(boundary) + "."
        a.margin = "; ".join(short)
        a.reason_code = ("SILL_AT_LIMIT" if any(b.startswith("sill") for b in boundary)
                         else "HUNG_HEIGHT_AT_LIMIT" if w.operation in ("single hung", "double hung") else "DIMENSION_AT_LIMIT")
        if open_items:
            a.reason += " Also open: " + "; ".join(open_items) + "."
        a.settles_with = f"manufacturer data or a detail for type {w.mark or '?'}: net clear width/height and the sill-to-clear-opening offset"
    else:
        a.tag = "open"
        items = "; ".join(open_items)
        a.reason = ("The net clear data doesn't settle it: " + items if exact
                    else "Nominal size would comply, but the schedule doesn't give the net clear opening. " + items[:1].upper() + items[1:]) + "."
        a.reason_code = "NET_CLEAR_UNKNOWN"
        a.margin = "; ".join(short) or None
        a.settles_with = f"manufacturer net clear opening (width, height) for window type {w.mark or '?'}, or a net-clear column on the schedule"
    return a


def check_windows(windows: list[Window], ca: dict, notes: RunNotes) -> tuple[list[Finding], list[Finding]]:
    occ = ca.get("occupancy", ("", ""))[1].strip().upper()
    if occ.startswith(("R-3", "R-4")):
        applies, app_why = True, f"Group {occ}: 1030.1 item 2 requires EEROs in sleeping rooms below the fourth story."
    elif occ.startswith("R-2"):
        applies, app_why = None, "Group R-2: 1030.1 item 1 applies only to stories with one exit, which these documents don't show."
    else:
        applies, app_why = False, f"Group {occ or '?'} isn't listed in 1030.1."
    win_findings: list[Finding] = []
    results: dict[str, tuple[Window, Assessment | None]] = {}
    ff = floor_above_grade(ca)

    for w in windows:
        f = Finding(f"W{w.symbol}", "egress-window", w.label, NA, "IBC 1030.1", "", evidence=list(w.evidence),
                    room=w.room_name + (f" {w.room_key}" if w.room_key != w.room_name else ""),
                    windows=[w.symbol])
        win_findings.append(f)
        a = assess(w, ff) if w.room_class in ("sleeping", "ambiguous") else None
        results[w.symbol] = (w, a)
        if applies is False:
            f.reason = app_why
            continue
        if w.room_class == "other":
            f.reason = f"{w.room_name} isn't a sleeping room ({w.room_why}), so 1030 doesn't require an EERO here."
            continue
        if w.floor is not None and w.floor >= 4:
            f.reason = f"1030.1 covers sleeping rooms below the fourth story; this room is on floor {w.floor}."
            continue
        if w.designated is False:
            f.reason = (f"Not marked EGRESS, so it isn't the room's escape opening. As an alternative it "
                        f"{_as_candidate(a)} (see the {f.room} finding).")
            continue
        if w.designated is None and "egress" in w.row.cells:
            f.verdict, f.reason, f.reason_code = CNE, f"EGRESS cell '{w.row.cells['egress']}' isn't Y or blank.", "EGRESS_UNREADABLE"
            continue
        if w.designated is None:
            f.verdict, f.reason, f.reason_code = CNE, "The schedule has no EGRESS column, so it's unknown whether this is the escape window.", "NO_EGRESS_COLUMN"
            f.next_step = "Ask which window in this room is the emergency escape and rescue opening."
            continue
        if applies is None:
            f.verdict, f.reason, f.reason_code = CNE, app_why, "APPLICABILITY_UNCLEAR"
            continue
        # A designated window in a sleeping (or possibly sleeping) room: check it.
        f.verdict, f.reason, f.code_ref = a.verdict, a.reason, a.code_ref
        f.reason_code, f.tag, f.margin, f.settles_with = a.reason_code, a.tag, a.margin, a.settles_with
        f.derivation, f.assumptions = a.derivation, a.assumptions
        if w.net_w and w.net_h and w.operation != "fixed":
            f.verdict_source = "rule + schedule net clear data"
        if w.floor == 1:
            f.assumptions.append("First floor: may be a grade-floor opening (5.0 sf). Finished grade at each window isn't given, "
                                 "so Pass needs 5.7 sf; a Fail on area is only called below 5.0 sf.")
        if f.verdict == FAIL:
            f.draft_comment = (f"Window {w.symbol} ({f.room}), the designated emergency escape and rescue opening, does not comply: "
                               f"{'; '.join(a.failures)}. Provide a compliant opening per IBC 1030.")
        elif f.verdict == CNE:
            f.next_step = f"Provide {a.settles_with}." if a.settles_with else None
            f.draft_comment = (f"Window {w.symbol} ({f.room}): provide manufacturer data for window type {w.mark or '?'} showing the net clear "
                               "opening width and height and the height of the bottom of the clear opening above the finished floor, "
                               "to verify IBC 1030.2, 1030.2.1 and 1030.3.")
    return win_findings, _rooms(windows, results, win_findings, ca, applies, app_why, notes)


def _rooms(windows, results, win_findings, ca, applies, app_why, notes) -> list[Finding]:
    by_room: dict[str, list[Window]] = {}
    for w in windows:
        by_room.setdefault(w.room_key, []).append(w)
    fmap = {f.windows[0]: f for f in win_findings}
    egress_note = ca.get("egress_note", ("", ""))[1]
    out = []
    for key, ws in by_room.items():
        classes = {w.room_class for w in ws}
        if "sleeping" in classes:
            cls = "sleeping"
        elif "ambiguous" in classes:
            cls = "ambiguous"
        else:
            continue
        name = next(w.room_name for w in ws if w.room_class == cls)
        label = f"{name} {key}" if key != name else name
        f = Finding("R" + re.sub(r"\W+", "-", key).strip("-"), "egress-room", f"Room {key}" if key != name else name, CNE, "IBC 1030.1", "",
                    room=label, windows=[w.symbol for w in ws])
        out.append(f)
        f.evidence = [Evidence("Windows in room", ", ".join(f"{w.symbol} ({w.op_raw}, {'EGRESS' if w.designated else 'not designated'})" for w in ws),
                               label, "window schedule, LOCATION")]
        if applies is False:
            f.verdict, f.reason = NA, app_why
            continue
        floor = ws[0].floor
        if floor is not None and floor >= 4:
            f.verdict, f.reason = NA, f"Floor {floor}: 1030.1 covers sleeping rooms below the fourth story."
            continue
        designated = [w for w in ws if w.designated]
        candidates = [w for w in ws if not w.designated and w.operation != "fixed"]
        cand_txt = "; ".join(f"window {w.symbol} ({w.op_raw}) {_as_candidate(results[w.symbol][1])}"
                             for w in candidates) or "none"
        if cls == "ambiguous":
            f.reason_code, f.tag = "AMBIGUOUS_SLEEPING_ROOM", "open"
            f.reason = (f"'{name}' isn't named as a bedroom, but {ws[0].room_why}. If it's a sleeping room it needs an EERO; "
                        f"designated: {', '.join(w.symbol for w in designated) or 'none'}; possible: {cand_txt}.")
            f.settles_with = "the floor plan / the architect's intended use of the room"
            f.next_step = f"Decide whether {label} is a sleeping room."
            f.draft_comment = f"Clarify the use of {label}. If it is a sleeping room, designate a compliant emergency escape and rescue opening per IBC 1030."
            continue
        if not designated:
            if any(w.designated is None for w in ws):
                f.reason_code = "NO_EGRESS_COLUMN"
                f.reason = f"The schedule doesn't mark escape windows, so the EERO for this room is unknown. Possible: {cand_txt}."
            else:
                f.reason_code = "NO_EERO_DESIGNATED"
                f.reason = (f"Sleeping room with no window marked EGRESS. Possible: {cand_txt}."
                            + (f" The code analysis says EEROs are '{egress_note}'." if egress_note else ""))
            f.tag = "open"
            f.settles_with = "the architect designating an escape window (and its net clear data)"
            pick = ", ".join(w.symbol for w in candidates)
            f.next_step = (f"Ask the architect to designate an escape window{f' (window {pick} is a candidate)' if pick else ''} "
                           "and give its net clear opening. If none is designated, the room doesn't meet 1030.1.")
            f.draft_comment = (f"{label}: no emergency escape and rescue opening is designated on the window schedule. "
                               "Designate a compliant opening per IBC 1030 and provide its net clear dimensions.")
            continue
        wf = [fmap[w.symbol] for w in designated]
        f.derivation = [f"Window {x.windows[0]}: {x.verdict}" + (" (at the limit)" if x.tag == "boundary" else "") for x in wf]
        if any(x.verdict == PASS for x in wf):
            ok = next(x for x in wf if x.verdict == PASS)
            f.verdict, f.reason = PASS, f"Designated window {ok.windows[0]} complies."
            f.verdict_source, f.code_ref = ok.verdict_source, _room_ref([ok])
        elif all(x.verdict == FAIL for x in wf):
            f.verdict = FAIL
            f.reason = f"Every designated escape window fails ({', '.join(x.windows[0] for x in wf)}), so the room has no compliant EERO."
            f.code_ref = _room_ref(wf)
            f.flags.append(EXC2)
            f.draft_comment = (f"{label} has no compliant emergency escape and rescue opening: "
                               + "; ".join(f"window {x.windows[0]}: {x.reason.rstrip('.')[:1].lower()}{x.reason.rstrip('.')[1:]}" for x in wf)
                               + ". Provide a compliant opening per IBC 1030.")
        else:
            rest = [x for x in wf if x.verdict == CNE]
            f.tag = "boundary" if all(x.tag == "boundary" for x in rest) else "open"
            f.reason_code = rest[0].reason_code
            f.reason = ("No designated window is shown to comply: "
                        + "; ".join(f"window {x.windows[0]} {'fails' if x.verdict == FAIL else 'is at the limit' if x.tag == 'boundary' else 'needs net clear data'}" for x in wf) + ".")
            f.margin = rest[0].margin
            f.code_ref = _room_ref(wf)
            f.settles_with = rest[0].settles_with
            f.next_step = rest[0].next_step
            f.draft_comment = rest[0].draft_comment
            if len(rest) > 1 and f.tag == "open":
                syms = [x.windows[0] for x in rest]
                marks = sorted({w.mark or "?" for w in designated if w.symbol in syms})
                f.draft_comment = (f"Windows {', '.join(syms[:-1])} and {syms[-1]} ({label}): provide manufacturer data for window "
                                   f"type{'s' if len(marks) > 1 else ''} {', '.join(marks)} showing the net clear opening width and height "
                                   "and the height of the bottom of the clear opening above the finished floor, to verify IBC 1030.2, "
                                   "1030.2.1 and 1030.3.")
            if f.tag == "boundary":
                f.flags.append(EXC2)
    return out


def _as_candidate(a: Assessment) -> str:
    if a.verdict == FAIL:
        return "couldn't serve: " + a.failures[0].split(" (")[0]
    if a.tag == "boundary":
        return "would be at the limit"
    return "could comply in the best case"


def _room_ref(wf: list[Finding]) -> str:
    refs = {"1030.1"}
    for x in wf:
        refs.update(re.findall(r"1030[\d.]*\d", x.code_ref))
    return "IBC " + ", ".join(sorted(refs, key=lambda r: [int(p) for p in r.split(".")]))


def missing_symbols(windows: list[Window]) -> list[str]:
    nums = sorted(int(w.symbol) for w in windows if w.symbol.isdigit())
    if not nums:
        return []
    return [str(n) for n in range(nums[0], nums[-1] + 1) if n not in nums]
