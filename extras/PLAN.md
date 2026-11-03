# Plan: Ichi plan-review take-home

**Team:** Opus, Fable, Sonnet. **Requirements:** `instructions/README.md`. **Rev 8** (updated after the build; changes marked *build*).

## 1. Goal

Show the process of making the tool **as accurate as possible and trustworthy to a professional plan checker**, and **why** each decision was made (§8). When two options tie, pick the one that's easier to audit.

**Deliverables:**
- **Source code.**
- **`REPORT.md`**, exactly as generated.
- **A short `NOTES.md`** with:
  - how to run it and how it works
  - code vs. model, with the accuracy/speed/cost reasoning
  - a one-line-per-decision log: choice → reason → test (from §8)
  - **AI catches**: where the assistant went wrong and what caught it, logged *during* the build
  - what we couldn't verify, and what document would settle it
  - another day: the answer ruleset, a model classifier, image cross-checks, scaling to 200 sheets
- **Extras:** `findings.json`, an eval scorer, a generalization fixture.

**Run:**
```
python -m ichi instructions/fixtures/project/code-analysis.html instructions/fixtures/project/window-schedule.html -o REPORT.md [--answers answers.json]
```

## 2. Verdicts

**Rule:**
- **Fail** only if it fails under the most favorable reading: zero frame loss, the most generous head-height datum.
- **Pass** only if it passes under the least favorable reading.
- Everything else is **Could Not Evaluate (CNE)**, with:
  - the **margin in inches** (never a percentage)
  - a tag: `boundary` (≈0, likely Fail) or `open`
  - the document that settles it
  - a draft information request

The schedule never gives the net clear opening, so **no window can Pass from these documents**. The report says so up front. Boundary CNEs appear in the Fails table as **"Likely Fail — confirm"**.

### Check 1: Building height is a Fail

`R-3` → row R. `NFPA 13D (903.3.1.3)` → sub-row S13D. `V-B` → column V/B. The cell is **40 ft**, and the building is 41'-6", so it's **over by 1'-6"**. (Sub-rows: NS = not sprinklered, S = full NFPA 13, S13R = NFPA 13R, S13D = NFPA 13D.)

- The architect's "60' per 504.3" is wrong: 60 is the S13R or S cell. It's flagged as a separate discrepancy.
- The height is the architect's claim; the grade-plane calc is on a sheet we don't have.

### Check 2: Escape windows

**Applicability:** 1030.1 item 2 covers R-3. All rooms are on stories 1–3, below the 4th story. There's no basement, so Exceptions 1, 3 and 4 are N/A. Exception 2 (a door to the outside) can't be seen, so every room Fail says "verify Exception 2 on the floor plan".

**Sill height** = head height − nominal height. This assumes head height is measured to the top of the unit; the true datum is open question 1. Operation factors (½ for a hung sash, and so on) apply to **area as well as height**.

| # | Room | Window | Verdict | Why |
|---|---|---|---|---|
| 1, 3 | Bedroom 101 | casement 2'6"×4'0" (10 sf), sill 32" | CNE (open) `NET_CLEAR_UNKNOWN` | Nominal passes; net clear unknown |
| 4 | Office 102 | casement 3'0"×5'0", not designated | N/A (*build*: the doubt is on room 102) | `3' - O"` read as 3'-0" (logged). |
| 7 | ADU Bedroom 107 | casement 2'6"×3'0" (7.5 sf), sill **44.0"** | CNE (boundary) `SILL_AT_LIMIT` | 1030.3: exactly at the 44" limit, so any frame fails it. Area needs net clear ≥ 76% of nominal (67% if grade floor). |
| 10 | Bedroom 203 | casement 2'0"×2'6" (**5.0 sf**), sill **50"** | **Fail** | 1030.2: under 5.7 sf even at nominal (floor 2, so the grade-floor 5.0 doesn't apply). 1030.3: sill > 44". |
| 12 | `BEDRROM 205` | single hung 3'0"×4'0", sill 32" | CNE (boundary) `HUNG_HEIGHT_AT_LIMIT` | 1030.2.1: operable height at best ½ × 48 = 24.0", the exact minimum (assumes equal sashes). Area at best ½ × 12 = 6.0 sf, so it needs ≥ 95% of that. |
| 13 | Bedroom 205 | **fixed** 4'0"×4'0", marked EGRESS | **Fail** | 1030.1.1 / 1030.2.1 "normal operation": it doesn't open. The Y is in the EGRESS column, not shifted OCR. |
| 20 | Bedroom 301 | casement 2'6"×3'0", sill **60"** | **Fail** | 1030.3: 16" over, under any datum |
| 21 | Guest Bed 303 | casement 2'6"×4'0", not designated | N/A (*build*: named as the candidate on room 303) | Same unit as #1 |
| 2, 11 | bedrooms | fixed, not designated | N/A | |
| 5, 6, 8, 14, 22, 23 | non-sleeping rooms | | N/A | |

**Room rollup:** Pass if any designated window passes. Fail only if every designated window Fails. Otherwise CNE. A room with no designated window is CNE `NO_EERO_DESIGNATED`.

| Room | Verdict |
|---|---|
| 101 | CNE |
| 102 | CNE `AMBIGUOUS_SLEEPING_ROOM` |
| 107 | CNE (likely Fail) |
| 203 | **Fail** |
| 205 | CNE (likely Fail): #13 fails, #12 is boundary |
| 301 | **Fail** |
| 303 | CNE `NO_EERO_DESIGNATED`, which contradicts the code analysis's "provided at all sleeping rooms"; #21 is a candidate |

**Also for the checker:**
- Symbols 9 and 15–19 are missing.
- The 5.0 sf grade-floor allowance relieves **area only, never the 44" sill**. It's plausible on floor 1 but unverified, so a Pass needs 5.7 and a Fail on area needs < 5.0.
- The 20" minimum width can't be proven from nominal sizes.
- 1030.5 screens and "opens to a public way" need other sheets.

**Open questions** (two at most, emailed, non-blocking):
1. What datum does HEAD HEIGHT use? It decides W7.
2. A bedroom with no designated window: Fail or CNE?

### Reason codes and the reviewer's answers

Every CNE has a reason code and a one-line **Next step**. The four verdict words are never renamed.

| Code | Example | Needed |
|---|---|---|
| `NET_CLEAR_UNKNOWN` | W1, W3 | net clear for type A |
| `SILL_AT_LIMIT` | W7 | sill offset or the HEAD HEIGHT datum |
| `HUNG_HEIGHT_AT_LIMIT` | W12 | operable sash height |
| `NO_EERO_DESIGNATED` | Room 303 | decision: designate #21, or Fail |
| `AMBIGUOUS_SLEEPING_ROOM` | Office 102 | decision: sleeping room? |
| `COLUMN_AMBIGUOUS` | other projects | which size column is the clear opening |
| `COLUMN_NOT_READ` | other projects | what an unrecognized column holds |

**`answers.json` (`--answers`; *build*: JSON, because the tool is stdlib-only):** the reviewer's answers to CNEs.
- **Facts first**, keyed by window type (`type F: net_clear 26×31, source: cut sheet`). The rules then decide the verdict.
- **Decisions** only where no fact exists.
- **A bare override** is allowed but shown as weaker.

**Guardrails:**
- Answers apply only to CNEs.
- An answer that contradicts a rule verdict → **Disputed**.
- A changed window row (symbol + room + size + type) → **stale**, and the finding reverts to CNE.

The tool generates `answers.template.json`, and `extras/examples/answers.sample.json` (type A net clear) shows W1, W3 and Room 101 resolving. The submitted `REPORT.md` uses no answers.

## 3. Architecture

Python 3.12, stdlib only, deterministic. **No model calls.** Table 504.3 is **parsed from `fixtures/code` at run time**, never hard-coded.

```
html → grid.py → mapping.py → values.py → rules/ → findings → report.py → REPORT.md + findings.json
```

| Module | Job | Key traps it handles |
|---|---|---|
| `models.py` | shared types | the finding record (below); written first so the rule and report owners can work in parallel |
| `grid.py` | HTML → rectangular grid | rowspan/colspan on body cells; `colspan=""` = 1; header depth = max rowspan in row 1 (504.3 has no `<th>`); blank upper header filled from below; empty separator row dropped; read text content through `changed_ICC` spans; `<sup>` text goes into a separate `footnotes` field so `R<sup>h</sup>` matches `R` (S13D/S13R/UL kept intact) |
| `mapping.py` | header → field | synonyms + fuzzy match (logged); **content inference** confirms each column (feet-inches, Y/blank, operation words, letters); the two TYPE columns are split by content; nominal vs. rough vs. net clear decided by header only, else `COLUMN_AMBIGUOUS`; unmatched → "Not read" |
| `values.py` | text → values | feet-inches with OCR `O`→`0`; sprinkler → NS/S/S13R/S13D (`NONE`/`NO` → NS; a conflict with the code citation → CNE); room → floor via the ROOM NUMBERING row; sleeping-room keywords + fuzzy; OFFICE/DEN/LOFT → `AMBIGUOUS_SLEEPING_ROOM` |
| `rules/height.py` | 504.3 lookup | returns the value *and* its provenance; `UL` → Pass; checks the architect's claim; footnote d/h flag for an NS lookup on a new R building |
| `rules/egress.py` | 1030 bounds | operation factors as upper bounds on area and height (casement 1, hung ½H, slider ½W, awning ≤1, fixed 0, unknown → CNE); room rollup (§2) |
| `answers.py` | apply `answers.json` | facts, decisions, stale, disputed |
| `report.py` | templated Markdown | no model prose, so it's reproducible |

**Finding record:** `id, fingerprint, check, subject, verdict, verdict_source (rule | supplied fact | checker decision), reason_code, tag, margin_in, code_ref, evidence[raw → parsed], derivation, assumptions, settles_with, next_step, draft_comment`.

**Missing data degrades to CNE, never a guess:**
- no EGRESS column → rooms CNE
- no operation column → windows CNE
- no construction type → Check 1 CNE

**Model seam:** a stub returning "unknown". A model classifier (e.g. Jev, a cheap classification model on Vercel's AI Gateway) is a NOTES.md design and isn't built (§8).

## 4. Report layout

1. **Header + how to read it** ("no window can Pass without net-clear data").
2. **Fails and likely Fails, by room:** verdict, code section, reason, margin, what settles it, draft correction. No duplicates.
3. **Needs your eyes:** OCR corrections ("schedule says X → read as Y"), missing symbols, disputes, stale answers. *(Build: moved ahead of the open questions after Sonnet's report review, so OCR doubts are seen first.)*
4. **Open questions:** each CNE that isn't at a limit (including Office 102), with its reason, what settles it, and a draft information request.
5. **Check 1 detail:** the lookup trace `R › S13D › V-B = 40` vs. the architect's 60'.
6. **Check 2 detail:** by room, each window with its evidence and arithmetic.
7. **Not checked:** 504.4, screens, public way, Exception 2, grade floor.
8. **Appendix:** data as read, the header mapping, the 504.3 slice.

## 5. Verification

| Test | Catches |
|---|---|
| **Discriminating 504.3 cells:** R/S13D/V-B=40, R/S13R/V-B=60, R/S13D/V-A=50, I-1 Cond.2/S II-A=85 vs II-B=55, H-1/S/II-B=55 (merged cell), plus README cells B/NS/II-B=55, I-4/NS/III-B=55 | wrong row, sub-row or column; README cells alone can't, because the NS and S rows repeat |
| README worked examples: W-A Fail, W-B CNE, Bedroom 2 CNE, 52' Pass, 56' Fail, missing type → CNE | the rules match Ichi's own answers |
| **Mutation tests:** shuffle columns, drop EGRESS, drop operation, reorder 504.3 sub-rows | position dependence; graceful degradation |
| **Generalization fixture:** renamed/abbreviated/reordered/missing columns (`MK`, `OPER.`, `R.O. W`, `NET CLR H`, no EGRESS), `MSTR BDRM`/`NURSERY`/`LOFT`/`DEN`, hung + slider, an unsprinklered R building, new OCR errors; verdicts hand-derived first | README line 92: "we may try your tool on" another project |
| **Nothing disappears:** every input column and room shows up in the report | silent drops |
| **No Pass from nominal sizes** on the fixtures | the README's top trap |
| Answers: a stale row reverts to CNE; a contradicting answer → Disputed | answers overriding rules |
| **Hand audit** of every verdict against the drawing images | all of the above being wrong together |

`eval/expected.json` is a regression guard, not independent ground truth.

**README follow-up questions → evidence:** wrong 504.3 cell → discriminating tests. Other projects → mutation tests + generalization fixture. Code vs. model → §3 and §8. What we couldn't verify → NOTES.md.

## 6. Timebox (~3.5 h)

| Time | Owner | Work |
|---|---|---|
| 0:00–0:10 | Opus | `models.py` (finding record) |
| 0:10–0:40 | Opus | grid, mapping, values (+ grid tests) |
| 0:40–2:00 | Fable | height and egress rules, rule and mutation tests |
| 0:40–2:00 | Sonnet | report, findings.json, eval, generalization fixture with hand-derived verdicts |
| 0:40–2:00 | Opus | cli, answers.py + sample, integration, model stub |
| 2:00–2:45 | All | run, **hand audit**, fix |
| 2:45–3:30 | All | report polish, NOTES.md, push |

If time runs short, cut in this order: polish → the answers sample → the generalization fixture's extra cases. **Never cut the hand audit.**

## 7. Decision log

| Decision | Why | Rejected | Raised by | Backed by |
|---|---|---|---|---|
| Boundary cases (W7, W12) → CNE, shown as "Likely Fail" | A false Fail costs a redesign and credibility; W12 may be a cottage sash; W7 hinges on an unknown datum | Fail (Fable, conceded) | Sonnet | hand audit; W7/W12 rule tests |
| Margin in inches, not % confidence | No distribution behind a percentage; inches are checkable | Confidence score | Fable, Sonnet | margin values in rule tests |
| Ask the reviewer for **facts**, not verdicts | Facts are checkable, cover every window of a type, and run through tested rules | SME Pass/Fail as the main path | Opus, Fable, Sonnet | answers sample test |
| Answer ruleset is design only | One checker's call isn't a rule (jurisdiction, edition, liability) | Build a precedent engine | Fable | — (scope) |
| Separate Next-step field | The README forbids renaming verdicts | "Needs clarification" verdict | Opus, Sonnet | — |
| Fingerprint = symbol + room + size + type | A symbol alone mis-binds; a raw hash is too strict | Symbol or raw hash | Sonnet, Fable | stale-answer test |
| Discriminating 504.3 tests | README cells can't detect a wrong-row read | README cells only | Fable | the tests themselves |
| Degrade to CNE on missing data | A guess is worse than an honest unknown | Infer defaults | Fable, Sonnet | mutation tests |
| No model in the verdict path; 504.3 never a model | The README's Gemini example reads the wrong cell | LLM fallback | Sonnet, Fable | deterministic re-run |
| **Jev not built**; design in NOTES.md | Graders likely have no key, so it would never run; content inference already decides what it would | Opt-in classifier (user; Opus 45-min proposal) | Sonnet | — |
| Content inference + `COLUMN_AMBIGUOUS` | Generalizes without a key; nominal vs. net clear is the README's top trap, so ambiguity → CNE | Model guesses headers | Sonnet, Opus | generalization fixture |
| Any future classifier may only *add* rooms to checks | A false "not sleeping" hides a real Fail | Symmetric labels | Opus | — (design) |
| Office 102 → CNE, not a guess | README: "say so in the report instead of quietly guessing" | N/A or treat as bedroom | Sonnet, Fable | hand audit |
| *Build:* undesignated windows → N/A; the room carries the doubt | README asks for a finding per EGRESS window plus one per room; avoids raising Office 102 twice | W4/W21 as CNE | Opus (Fable's tests agreed; Sonnet's fixture disagreed, recorded) | W4, WB1, WE1 tests |
| *Build:* Pass with net clear uses the worst-case opening position | Net clear W×H doesn't give the opening's bottom edge | Unit sill as the opening sill | Opus | D1, K1 in the generalization fixture |
