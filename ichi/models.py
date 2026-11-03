"""Shared types. Every finding carries enough evidence to trace it back to a cell."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict

PASS = "Pass"
FAIL = "Fail"
CNE = "Could Not Evaluate"
NA = "Not Applicable"
VERDICTS = (PASS, FAIL, CNE, NA)


@dataclass
class Evidence:
    """One thing the tool read: where, the raw text, and what it took it to mean."""
    label: str
    raw: str
    parsed: str
    source: str  # e.g. "window-schedule.html, symbol 7, column EGRESS"


@dataclass
class Correction:
    """A place the tool read the text as something other than what it literally says."""
    source: str
    raw: str
    read_as: str
    why: str


@dataclass
class Finding:
    id: str
    check: str          # "height" | "egress-window" | "egress-room"
    subject: str        # "Building", "Window 7", "Room 205"
    verdict: str
    code_ref: str
    reason: str         # one line, plain words
    evidence: list[Evidence] = field(default_factory=list)
    derivation: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    reason_code: str | None = None
    tag: str | None = None          # "boundary" (likely Fail) | "open" | None
    margin: str | None = None       # physical margin, e.g. "0.0 in at the sill"
    settles_with: str | None = None
    next_step: str | None = None
    draft_comment: str | None = None  # correction text (Fail) or information request (CNE)
    room: str | None = None
    windows: list[str] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)
    verdict_source: str = "rule"    # "rule" | "rule + supplied fact" | "checker decision"
    fingerprint: str | None = None

    def __post_init__(self):
        assert self.verdict in VERDICTS, self.verdict

    @property
    def likely_fail(self) -> bool:
        return self.verdict == CNE and self.tag == "boundary"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RunNotes:
    """Things the checker should see that aren't findings: OCR fixes, columns not read, gaps."""
    corrections: list[Correction] = field(default_factory=list)
    not_read: list[str] = field(default_factory=list)
    observations: list[str] = field(default_factory=list)
    header_map: list[tuple[str, str, str]] = field(default_factory=list)  # (header, field, how)
