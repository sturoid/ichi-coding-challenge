"""REPORT.md for the plan checker. Templated, no model-written prose, so the same
inputs always give the same report."""
from __future__ import annotations

import hashlib
from collections import Counter

from .models import CNE, FAIL, NA, PASS, VERDICTS, Finding
from .pipeline import Result
from .rules.egress import EXC2, missing_symbols
from .rules.height import SUBROWS, Table504


def _md(text: str | None) -> str:
    return (text or "").replace("|", "\\|").replace("\n", " ")


def _short(text: str, n: int = 140) -> str:
    return text if len(text) <= n else text[: n - 1].rsplit(" ", 1)[0] + "…"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def _verdict(f: Finding) -> str:
    if f.likely_fail:
        return f"**{CNE}** (likely Fail — confirm)"
    return f"**{f.verdict}**" if f.verdict in (FAIL, PASS) else f.verdict


def _room_sort(f: Finding):
    return (f.room or "~", 0 if f.check == "egress-room" else 1, int(f.windows[0]) if f.windows and f.windows[0].isdigit() else 0)


def render(res: Result, inputs: dict[str, tuple[str, str]], table_html: str) -> str:
    """`inputs`: label -> (path as given, file text), for the header and hashes."""
    F = res.findings
    height = next(f for f in F if f.check == "height")
    rooms = [f for f in F if f.check == "egress-room"]
    wins = [f for f in F if f.check == "egress-window"]
    project = res.code_analysis.get("project", ("", ""))[1]
    gaps = missing_symbols(res.inputs.get("windows", []))
    out: list[str] = []
    w = out.append

    # ---------- header ----------
    w("# Plan review: building height and escape windows")
    w("")
    if project:
        w(f"**Project:** {project}  ")
    w(f"**Code:** {res.code_analysis.get('code', ('', 'IBC 2018'))[1]}  ")
    w("**Checks:** building height (IBC 2018 Table 504.3) and emergency escape and rescue openings (EEROs) in sleeping rooms (IBC 2018 Section 1030)  ")
    w("**Inputs:** " + "; ".join(f"`{p}` (sha256 {_sha(t)})" for p, t in inputs.values()))
    w("")
    likely = sum(1 for f in rooms if f.likely_fail)
    w("| | " + " | ".join(VERDICTS) + " |")
    w("|---|" + "---|" * len(VERDICTS))
    for label, group in (("Building", [height]), ("Rooms", rooms), ("Windows", wins)):
        c = Counter(f.verdict for f in group)
        w(f"| {label} | " + " | ".join(str(c.get(v, 0)) for v in VERDICTS) + " |")
    w("")
    w("### How to read this")
    w("")
    w("- **Fail** means the item fails even under the most favorable reading of the drawings (no frame loss, the most generous head-height datum). "
      "**Pass** needs real clear-opening data, so **no window can Pass from this schedule**: it gives nominal unit sizes, not net clear openings.")
    w(f"- **Could Not Evaluate** means the documents don't settle it. Each one says why, by how much, and what would settle it. "
      f"The {likely} room{'s' if likely != 1 else ''} whose escape window is exactly at a limit in the best case, so any real frame makes it fail, "
      "are listed with the Fails as **likely Fail — confirm**.")
    w("- Every finding cites the code section and shows what was read from which cell. Anything the tool corrected (OCR) or couldn't read is under "
      "[Needs your eyes](#2-needs-your-eyes).")
    w("")

    # ---------- 1. fails ----------
    w("## 1. Fails and likely Fails")
    w("")
    fails = [height] if height.verdict == FAIL else []
    room_fails = sorted([f for f in rooms if f.verdict == FAIL or f.likely_fail], key=_room_sort)
    if any(EXC2 in r.flags for r in room_fails):
        w(f"**Before issuing any room comment:** {EXC2}")
        w("")
    w("| Item | Verdict | Code | Problem | What settles it |")
    w("|---|---|---|---|---|")
    for f in fails:
        w(f"| Building height | {_verdict(f)} | {_md(f.code_ref)} | {_md(f.reason)} | — |")
    for r in room_fails:
        ws = _bad_windows(r, wins)
        detail = "<br>".join(f"Window {x.windows[0]}: {_md(_problem(x))}" for x in ws)
        w(f"| **{_md(r.room)}** (window{'s' if len(ws) > 1 else ''} {', '.join(x.windows[0] for x in ws)}) | {_verdict(r)} | {_md(r.code_ref)} | "
          f"{detail or _md(r.reason)} | {_md(r.settles_with or '—')} |")
    if not fails and not room_fails:
        w("| — | none | | | |")
    w("")
    if fails or room_fails:
        w("**Draft comments for the correction letter** (corrections for Fails, information requests for likely Fails; edit before issuing):")
        w("")
        n = 0
        for f in fails + room_fails:
            texts = [f.draft_comment or ""]
            if f.check == "egress-room" and f.likely_fail:
                texts = [x.draft_comment for x in _bad_windows(f, wins) if x.draft_comment]
            for t in texts:
                n += 1
                w(f"{n}. {_md(t)}")
        w("")

    # ---------- 2. eyes ----------
    w("## 2. Needs your eyes")
    w("")
    items = []
    for f in F:
        if f.check == "height":
            continue  # shown in the section 1 comment and in section 4
        for flag in f.flags:
            if flag != EXC2:
                where = f"{f.room}, Window {f.windows[0]}" if f.check == "egress-window" else (f.room or f.subject)
                items.append(f"**{where}:** {flag}")
    items += list(res.notes.observations)
    items += [f"Not read: {n}" for n in res.notes.not_read]
    for i in items:
        w(f"- {i}")
    if res.notes.corrections:
        w("")
        w("**Text the tool read differently from what's printed** (check these against the drawing):")
        w("")
        w("| Where | Printed | Read as | Why |")
        w("|---|---|---|---|")
        for c in res.notes.corrections:
            w(f"| {_md(c.source)} | `{_md(c.raw)}` | `{_md(c.read_as)}` | {_md(c.why)} |")
    w("")

    # ---------- 3. open questions ----------
    open_cne = sorted([f for f in rooms if f.verdict == CNE and not f.likely_fail], key=_room_sort)
    if height.verdict == CNE:
        open_cne.insert(0, height)
    w("## 3. Open questions")
    w("")
    w("Could Not Evaluate items that aren't at a limit. Each needs a fact from the architect or a call from you; "
      "the draft information requests below ask the architect for what's missing.")
    w("")
    if open_cne:
        w("| Item | Why it's open | What settles it |")
        w("|---|---|---|")
        for f in open_cne:
            step = f.next_step if f.next_step and not (f.settles_with and f.settles_with.lower() in f.next_step.lower()) else ""
            w(f"| **{_md(f.room or f.subject)}** | {_md(f.reason)} | {_md(f.settles_with)}" + (f"<br>{_md(step)}" if step else "") + " |")
    else:
        w("None.")
    w("")
    requests = [f.draft_comment for f in open_cne if f.draft_comment]
    if gaps:
        requests.append(f"The window schedule skips symbol{'s' if len(gaps) > 1 else ''} {_ranges(gaps)}. Provide the complete schedule, "
                        "or confirm these windows were deleted, and identify any that serve a sleeping room.")
    if requests:
        w("**Draft information requests:**")
        w("")
        for i, t in enumerate(requests, 1):
            w(f"{i}. {_md(t)}")
        w("")

    # ---------- 4. check 1 ----------
    w("## 4. Check 1: building height")
    w("")
    _detail(w, height)
    lk_slice = _slice(table_html, height, res)
    if lk_slice:
        w("")
        w(lk_slice)
    w("")

    # ---------- 5. check 2 ----------
    w("## 5. Check 2: escape windows, by room")
    w("")
    checked = [x for x in wins if x.verdict != NA]
    common = [a for a, k in Counter(a for x in checked for a in dict.fromkeys(x.assumptions)).items() if k >= 2]
    w("How every window below was worked out:")
    w("")
    w("- Sill height is head height minus nominal height (the schedule has no sill column).")
    w("- Clear openings are upper bounds: nominal size times the share of the unit that opens "
      "(casement and awning 1, hung ½ height, slider ½ width, fixed 0).")
    for a in common:
        w(f"- {a}")
    w("")
    for r in sorted(rooms, key=_room_sort):
        w(f"### {r.room}: {_verdict(r)}")
        w("")
        line = r.reason + (f" Settled by: {r.settles_with}." if r.settles_with else "")
        w(f"{line} *({r.code_ref})*")
        mine = sorted([x for x in wins if x.room == r.room], key=_room_sort)
        for x in [x for x in mine if x.verdict != NA]:
            w("")
            w(f"#### Window {x.windows[0]}: {_verdict(x)}")
            w("")
            _detail(w, x, skip=common)
        rest = [x for x in mine if x.verdict == NA]
        if rest:
            w("")
            w("| Other window | Verdict | Why |")
            w("|---|---|---|")
            for x in rest:
                w(f"| {x.windows[0]} | {x.verdict} | {_md(x.reason)} |")
        w("")
    others = sorted([x for x in wins if not any(x.room == r.room for r in rooms)], key=_room_sort)
    if others:
        w("### Windows in rooms that aren't sleeping rooms")
        w("")
        w("| Window | Room | Verdict | Why |")
        w("|---|---|---|---|")
        for x in others:
            w(f"| {x.windows[0]} | {_md(x.room)} | {x.verdict} | {_md(x.reason)} |")
        w("")

    # ---------- 6. not checked ----------
    w("## 6. Not checked")
    w("")
    w("These need documents the tool wasn't given. They're not verdicts.")
    w("")
    w("- **1030.1 Exception 2** (a bedroom exit door directly to the outside): needs the floor plans. Applies to every room Fail above.")
    w("- **1030.1 opens to a public way, yard or court:** needs the site plan.")
    w("- **1030.5 screens and bars releasable from inside:** the schedule marks screens but not their hardware; needs window details.")
    w("- **1030.2 grade-floor openings (5.0 sf):** needs finished grade at each window. The grade plane and first-floor elevations give an "
      "estimate (shown per window); first-floor windows are still treated as possibly grade-floor when calling a Fail.")
    w("- **Building height measurement:** the 504.3 check uses the architect's stated height; the grade-plane calculation (civil sheet) wasn't provided.")
    w("- **Table 504.4 (stories):** out of scope.")
    w("")

    # ---------- appendix ----------
    w("## Appendix A: how the schedule columns were read")
    w("")
    w("| Header (as printed) | Read as | How |")
    w("|---|---|---|")
    for h, field, how in res.notes.header_map:
        w(f"| `{_md(h)}` | {field} | {_md(how)} |")
    w("")
    w("## Appendix B: code analysis as read")
    w("")
    w("| Field | Label (as printed) | Value |")
    w("|---|---|---|")
    for k, (label, value) in res.code_analysis.items():
        w(f"| {k} | `{_md(label)}` | {_md(value)} |")
    w("")
    return "\n".join(out).rstrip() + "\n"


def _bad_windows(room: Finding, wins: list[Finding]) -> list[Finding]:
    """The room's windows that fail or are at a limit: what the plan checker has to act on."""
    return [x for x in wins if x.room == room.room and (x.verdict == FAIL or x.likely_fail)]


def _problem(x: Finding) -> str:
    if x.verdict == FAIL:
        return x.reason
    return f"at the limit even with no frame loss ({x.margin})"


def _ranges(nums: list[str]) -> str:
    n = sorted(int(x) for x in nums)
    parts, start = [], n[0]
    for a, b in zip(n, n[1:] + [None]):
        if b != a + 1:
            parts.append(str(start) if start == a else f"{start}–{a}")
            start = b
    return ", ".join(parts)


def _detail(w, f: Finding, show_evidence: bool = True, skip: list[str] = ()) -> None:
    w(f"- **Verdict:** {_verdict(f)}" + (f" ({f.verdict_source})" if f.verdict_source != "rule" else ""))
    w(f"- **Code:** {f.code_ref}")
    w(f"- **Why:** {f.reason}")
    if f.margin:
        w(f"- **Margin:** {f.margin}")
    if f.reason_code:
        w(f"- *Reason code: `{f.reason_code}`*")
    if f.settles_with:
        w(f"- **Settled by:** {f.settles_with}")
    if f.next_step and f.next_step.rstrip(".").lower() != f"provide {f.settles_with or ''}".lower():
        w(f"- **Next step:** {f.next_step}")
    if f.flags:
        for fl in f.flags:
            w(f"- **Note:** {fl}")
    if show_evidence and f.evidence:
        w("- **Read from the documents:**")
        for e in f.evidence:
            w(f"  - {e.label}: `{e.raw}` → {e.parsed} *({e.source})*")
    if f.derivation:
        w("- **Worked out:**")
        for d in f.derivation:
            w(f"  - {d}")
    own = [a for a in f.assumptions if a not in skip]
    if own:
        w("- **Assumptions:**")
        for a in own:
            w(f"  - {a}")


def _slice(table_html: str, height: Finding, res: Result) -> str:
    """The table row used, every sub-row, so a wrong-row read is visible at a glance."""
    t = Table504(table_html)
    ev = {e.label: e for e in height.evidence}
    if "Table 504.3 cell" not in ev:
        return ""
    src = ev["Table 504.3 cell"].source
    row = src.split("row '")[1].split("'")[0]
    sub = src.split("sub-row ")[1].split(" ")[0]
    col = src.split("column Type ")[1].split(" ")[0]
    cols = list(t.columns)
    lines = [f"Table 504.3, row `{row}` as parsed (the cell used is in bold):", "",
             "| Sub-row | " + " | ".join(f"{a}-{b}" for a, b in cols) + " |",
             "|---|" + "---|" * len(cols)]
    for s in SUBROWS:
        vals = []
        for c in cols:
            lk = t.lookup(row, s, c)
            if lk is None:
                break
            v = lk.value
            vals.append(f"**{v}**" if s == sub and f"{c[0]}-{c[1]}" == col else v)
        if vals:
            lines.append(f"| {'**' + s + '**' if s == sub else s} | " + " | ".join(vals) + " |")
    return "\n".join(lines)
