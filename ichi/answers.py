"""The reviewer's answers to Could Not Evaluate findings (answers.json).

Facts (net clear data per window type) are applied before the rules run, in
pipeline.run, so the tested rules decide the verdict. Decisions are applied here,
after the rules, and only to findings that are still Could Not Evaluate:

- a decision on a finding the rules already decided is marked Disputed, not applied
- a decision whose fingerprint no longer matches the row is marked stale, not applied

JSON rather than YAML because the tool is stdlib-only.
"""
from __future__ import annotations

import json
from pathlib import Path

from .models import CNE, VERDICTS, Finding, RunNotes


def load(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def apply_decisions(findings: list[Finding], answers: dict, notes: RunNotes) -> None:
    by_id = {f.id: f for f in findings}
    for fid, d in (answers.get("decisions") or {}).items():
        f = by_id.get(fid)
        verdict = d.get("verdict")
        who = d.get("by", "reviewer")
        if f is None:
            notes.observations.append(f"Answer for {fid} doesn't match any finding; ignored.")
            continue
        if verdict not in VERDICTS:
            notes.observations.append(f"Answer for {fid} has verdict '{verdict}', which isn't one of the four; ignored.")
            continue
        if d.get("fingerprint") and d["fingerprint"] != f.fingerprint:
            f.flags.append(f"Stale answer: {who}'s decision ({verdict}) was made for a different version of this row "
                           f"({d['fingerprint']}); not applied.")
            continue
        if f.verdict != CNE:
            if verdict != f.verdict:
                f.flags.append(f"Disputed: {who} answered {verdict}, but the rules give {f.verdict}. Not applied; "
                               "if the reviewer is right, the rule needs fixing (with a test).")
            continue
        f.verdict = verdict
        f.verdict_source = "checker decision"
        f.reason = f"{verdict} by {who}: {d.get('why', 'no reason given')}. (Before: {f.reason})"
        f.next_step = None


def template(findings: list[Finding]) -> dict:
    """A fill-in-the-blanks answers file for every open Could Not Evaluate finding."""
    types: dict[str, dict] = {}
    decisions: dict[str, dict] = {}
    for f in findings:
        if f.verdict != CNE:
            continue
        if f.reason_code in ("NET_CLEAR_UNKNOWN", "SILL_AT_LIMIT", "HUNG_HEIGHT_AT_LIMIT", "DIMENSION_AT_LIMIT") and f.check == "egress-window":
            mark = next((e.raw for e in f.evidence if e.label == "Type mark"), "?")
            types.setdefault(mark, {"net_clear_width_in": None, "net_clear_height_in": None,
                                    "sill_to_clear_opening_in": None, "source": "", "by": "",
                                    "_for": []})["_for"].append(f.subject)
        elif f.reason_code in ("NO_EERO_DESIGNATED", "AMBIGUOUS_SLEEPING_ROOM", "NO_EGRESS_COLUMN", "OPERATION_UNKNOWN"):
            decisions[f.id] = {"verdict": None, "why": "", "by": "", "fingerprint": f.fingerprint,
                               "_question": f.next_step or f.reason}
    return {"facts": {"types": types}, "decisions": decisions}
