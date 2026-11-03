"""Text -> values. Every OCR fix is returned so the report can show "read X as Y"."""
from __future__ import annotations

import difflib
import re

from .models import Correction

ROMAN = {"1": "I", "2": "II", "3": "III", "4": "IV", "5": "V"}


def compact(text: str) -> str:
    return re.sub(r"\s+", "", text or "").upper()


# ---------- dimensions ----------

_FT_IN = re.compile(r"^\s*(?:(\d+(?:\.\d+)?)\s*['’]\s*-?\s*)?(?:(\d+(?:\.\d+)?)\s*(?:\"|''|”|IN)?)?\s*$", re.I)


def parse_length(raw: str, source: str = "") -> tuple[float | None, list[Correction]]:
    """Feet-inches text -> inches. Fixes letter O read for zero, and says so."""
    fixes: list[Correction] = []
    text = (raw or "").strip()
    if not text:
        return None, fixes
    fixed = re.sub(r"(?<=[\d\s'-])[Oo](?=[\s\"'”]|$)", "0", text)
    if fixed != text:
        fixes.append(Correction(source, raw, fixed, "letter O in a dimension read as zero"))
    m = _FT_IN.match(fixed)
    if not m or (m.group(1) is None and m.group(2) is None):
        return None, fixes
    feet = float(m.group(1) or 0)
    inches = float(m.group(2) or 0)
    if m.group(1) is None and "'" not in fixed and '"' not in fixed:
        return None, fixes          # a bare number isn't a dimension we can trust
    return feet * 12 + inches, fixes


def fmt_in(inches: float) -> str:
    ft, rem = divmod(round(inches, 2), 12)
    rem_s = f"{rem:g}"
    return f"{int(ft)}'-{rem_s}\" ({inches:g} in)"


def looks_like_length(raw: str) -> bool:
    v, _ = parse_length(raw)
    return v is not None


# ---------- code analysis values ----------

def parse_construction(raw: str) -> tuple[str, str] | None:
    """'V-B' / 'TYPE V-B' / 'VB' / '5B' / 'IV-HT' -> ('V', 'B')."""
    m = re.search(r"\b(?:TYPE\s*)?(IV|V|III|II|I|[1-5])\s*-?\s*(HT|A|B)\b", (raw or "").upper())
    if not m:
        return None
    major = ROMAN.get(m.group(1), m.group(1))
    return major, m.group(2)


def parse_sprinklers(raw: str) -> tuple[str | None, str]:
    """Sprinkler text -> Table 504.3 sub-row (NS/S/S13R/S13D), with the reasoning.

    NFPA text and the 903.3.1.x citation are read separately; if they disagree the
    answer is None (Could Not Evaluate) rather than picking one.
    """
    t = (raw or "").upper()
    if not t.strip():
        return None, "no sprinkler entry"
    if re.match(r"^\s*(NONE|NO\b|N/A|NOT SPRINKLERED|UNSPRINKLERED)", t):
        return "NS", "states no sprinkler system"
    by_nfpa = by_sec = None
    m = re.search(r"NFPA\s*13\s*([RD])?\b", t)
    if m:
        by_nfpa = {"R": "S13R", "D": "S13D", None: "S"}[m.group(1)]
    m = re.search(r"903\.3\.1\.([123])", t)
    if m:
        by_sec = {"1": "S", "2": "S13R", "3": "S13D"}[m.group(1)]
    if by_nfpa and by_sec and by_nfpa != by_sec:
        return None, f"NFPA text says {by_nfpa} but the code citation says {by_sec}"
    sub = by_nfpa or by_sec
    if sub:
        basis = " and ".join(x for x in [
            f"NFPA {'13' + ({'S13R': 'R', 'S13D': 'D'}.get(by_nfpa, ''))}" if by_nfpa else "",
            f"Section 903.3.1.{ {'S': 1, 'S13R': 2, 'S13D': 3}[by_sec] }" if by_sec else "",
        ] if x)
        return sub, f"{basis} -> {sub} per the Table 504.3 legend"
    if re.match(r"^\s*YES", t):
        return None, "says sprinklered but not which system (NFPA 13 / 13R / 13D)"
    return None, "sprinkler entry not understood"


def parse_room_numbering(raw: str) -> dict[str, int]:
    """'1XX = FIRST FLOOR, 2XX = SECOND FLOOR' -> {'1': 1, '2': 2}."""
    words = {"FIRST": 1, "SECOND": 2, "THIRD": 3, "FOURTH": 4, "FIFTH": 5, "GROUND": 1}
    out = {}
    for d, rest in re.findall(r"(\d)XX\s*=\s*([^,;]+)", (raw or "").upper()):
        word = next((w for w in re.findall(r"[A-Z]+", rest) if w in words), None)
        num = re.search(r"\d+", rest)
        if word:
            out[d] = words[word]
        elif num:
            out[d] = int(num.group(0))
    return out


# ---------- window schedule values ----------

SLEEPING_WORDS = {"BEDROOM", "BED", "BDRM", "BR", "BEDRM", "SLEEPING", "NURSERY", "BUNK"}
AMBIGUOUS_WORDS = {"OFFICE", "DEN", "LOFT", "STUDY", "BONUS", "FLEX", "LIBRARY", "SUITE", "PLAYROOM", "GUEST"}


def split_room(raw: str) -> tuple[str, str | None]:
    """'BEDROOM 101' -> ('BEDROOM', '101'). OCR letters in the number ('DEN lO2') are read as digits."""
    text = (raw or "").strip()
    m = re.match(r"^(.*?)[\s#-]+([\dlIoO]{2,4}[A-Za-z]?)\s*$", text)
    if m and re.search(r"\d", m.group(2)):
        num = m.group(2).upper()
        num = num[:3].replace("L", "1").replace("I", "1").replace("O", "0") + num[3:]
        return m.group(1).strip().upper(), num
    return text.upper(), None


def classify_room(raw: str, source: str = "") -> tuple[str, str, list[Correction]]:
    """Room name -> ('sleeping' | 'ambiguous' | 'other', why, corrections)."""
    name, _ = split_room(raw)
    words = re.findall(r"[A-Z]+", name)
    joined = "".join(words)
    for w in words:
        if w in SLEEPING_WORDS:
            return "sleeping", f"name contains '{w}'", []
    for w in ("BEDROOM", "SLEEPING", "NURSERY"):
        if w in joined:
            # OCR split the word across a line ('NURS ERY').
            return "sleeping", f"name contains '{w}' once OCR line breaks are joined", [
                Correction(source, raw, w, "word split across a line by OCR, read joined")]
    for w in words:
        if len(w) == 4 and sorted(w) == sorted("BDRM"):
            return "sleeping", f"'{w}' is BDRM with letters swapped", [
                Correction(source, raw, raw.upper().replace(w, "BDRM"), f"'{w}' read as BDRM (transposed letters)")]
    for w in words:
        if len(w) >= 5 and difflib.SequenceMatcher(None, w, "BEDROOM").ratio() >= 0.85:
            fix = Correction(source, raw, raw.upper().replace(w, "BEDROOM"),
                             f"'{w}' read as BEDROOM (one-letter OCR difference)")
            return "sleeping", f"'{w}' is BEDROOM with an OCR error", [fix]
    for w in words:
        if w in AMBIGUOUS_WORDS:
            return "ambiguous", f"'{w}' rooms are sometimes slept in", []
    return "other", "not a sleeping-room name", []


OPERATIONS = [
    ("fixed", r"\b(FIXED|FX|PICTURE|FIX)\b"),
    ("single hung", r"\b(S\.?\s*H\.?|SINGLE\s*HUNG|SGL\.?\s*HUNG)\b"),
    ("double hung", r"\b(D\.?\s*H\.?|DOUBLE\s*HUNG|DBL\.?\s*HUNG)\b"),
    ("slider", r"\b(SLIDER|SLIDING|SLDR|H\.?\s*S\.?|XO|OX)\b"),
    ("casement", r"\b(CASM'?T|CASEMENT|CSMT|CASE|CAS)\b"),
    ("awning", r"\b(AWNING|AWN)\b"),
    ("hopper", r"\b(HOPPER|HOP)\b"),
]


def parse_operation(raw: str) -> str | None:
    t = (raw or "").upper()
    for name, pat in OPERATIONS:
        if re.search(pat, t):
            return name
    return None


def parse_flag(raw: str) -> bool | None:
    """EGRESS-style cell -> True / False; None if it holds something else."""
    t = (raw or "").strip().upper()
    if t in ("", "-", "—", "N", "NO"):
        return False
    if t in ("Y", "YES", "X", "✓", "✔", "EERO", "E"):
        return True
    return None


def first_length(raw: str, source: str = "") -> tuple[float | None, str, list[Correction]]:
    """The first feet-inches dimension inside longer text: '41' - 6" (TO AVG. HT...)'."""
    m = re.search(r"\d+(?:\.\d+)?\s*['’]\s*-?\s*(?:[\dOo]+(?:\.\d+)?\s*[\"”])?", raw or "")
    if not m:
        return None, "", []
    v, fixes = parse_length(m.group(0), source)
    return v, m.group(0).strip(), fixes
