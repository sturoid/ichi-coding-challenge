# Notes

## Run it

Python 3.12, standard library only. No install step, no API keys.

```
python -m ichi instructions/fixtures/project/code-analysis.html instructions/fixtures/project/window-schedule.html -o REPORT.md
```

This writes `REPORT.md`, `findings.json` (every finding with its evidence) and `answers.template.json` (a blank for every open question).

- Tests: `python -m unittest discover -s tests -v`
- Score against hand-derived verdicts: `python eval/score.py`, and `python eval/score.py eval/expected_generalization.json`
- With a reviewer's answers: add `--answers examples/answers.sample.json` (the output is in `examples/`).

## How it works

```
HTML → grid → column mapping → values → rules → findings → REPORT.md + findings.json
```

1. **Grid** (`ichi/grid.py`). Expands rowspan and colspan, including on body cells. Works out the header depth from the first row, because Table 504.3 has no `<th>`. Drops empty separator rows, which would otherwise become a phantom window. Keeps `<sup>` footnote markers apart from the label, so `R` with footnote h still matches row `R`.
2. **Column mapping** (`ichi/mapping.py`). Headers are matched by synonyms with whitespace removed, so `SCREE N` reads as SCREEN. Each match is then checked against the column's contents: dimensions, Y/blank flags, operation words or single letters. The two `TYPE` columns are told apart this way.
   - Nominal, rough-opening and net-clear sizes all look like dimensions, so only the header can separate them. When it can't, the column is reported rather than guessed.
   - Anything unrecognized is listed under "Not read".
3. **Values** (`ichi/values.py`). Feet-inches, sprinkler system to Table 504.3 sub-row, room name to sleeping / ambiguous / other, and window operation. Every OCR repair is logged, for example `3' - O"` read as 3'-0", `BEDRROM` as BEDROOM, `lO2` as 102.
4. **Rules.**
   - `ichi/rules/height.py` reads Table 504.3 from the code fixture at run time and returns the cell together with its row, sub-row and column.
   - `ichi/rules/egress.py` bounds each escape window (see the verdict rule below).
5. **Report** (`ichi/report.py`). The report is filled in from a fixed template, so the same inputs always produce the same report. It is laid out for a plan checker:
   - Fails and likely Fails first, grouped by room, with draft correction text.
   - Then OCR fixes and flags, then the open questions with draft information requests.
   - Then each check in full, showing what was read from which cell and the arithmetic.

**Verdict rule.**
- **Fail** only if the item fails even under the most favorable reading: no frame loss, and the most generous head-height datum.
- **Pass** only with real net-clear data, applied at its worst case.
- **Everything else is Could Not Evaluate**, with the margin in inches or square feet and the document that would settle it.
- A window exactly at a limit in the best case is tagged `boundary` and shown with the Fails as "likely Fail — confirm", because any real frame makes it fail.

The schedule gives nominal sizes only, so no window can Pass from it. The report says so up front.

**Plain code vs. model calls.** There are no model calls at run time. Every verdict is arithmetic on code values that a checker can retrace. The cheap parts a model could help with are mapping unfamiliar headers and room names. On these fixtures, synonyms plus content checks already handle them, and a key-dependent layer wouldn't run for a grader without one. The design is under "Another day". Table 504.3 lookups would never go to a model; the README's Gemini screenshots show why.

## Decisions

The full debates are in [PLAN.md §7](PLAN.md#7-decision-log). One line each:

| Decision | Why | Backed by |
|---|---|---|
| Boundary windows (W7, W12) are Could Not Evaluate, not Fail | A false Fail costs a redesign and credibility; W12 might be a cottage sash, and W7 depends on the head-height datum | rule tests, hand audit |
| Margin in inches, not a confidence % | No distribution exists behind a percentage; inches can be checked | every finding's `margin` |
| Ask the reviewer for facts (net clear per window type), not verdicts | Facts can be checked, cover every window of that type, and run through the tested rules | `examples/answers.sample.json` |
| A reviewer answer can't overrule a rule verdict; a changed row voids old answers | Keeps rules and answers honest | answers tests (Disputed, stale) |
| Table 504.3 parsed at run time, with provenance | A hand-copied table can drift; provenance makes a wrong-cell read visible | discriminating lookup tests |
| Missing columns lead to Could Not Evaluate, never a default | A guess is worse than an honest unknown | mutation tests |
| Content checks on every header match | Line 92 of the README: other projects rename and reorder columns | generalization fixture, 26/26 |
| Undesignated windows are Not Applicable; doubt about the room sits on the room finding | The README asks for a finding per EGRESS window plus one per room; raising Office 102's doubt once avoids double-counting | W4 / R102 |
| `answers.json`, not YAML | Standard library only | — |
| No model in the run | Graders likely have no key; content checks already decide what a classifier would | generalization fixture |

## How I used AI, and how I checked it

Three models worked as a team: Opus (me) as lead and builder, Fable and Sonnet as independent reviewers and testers. Every plan revision went to both for review before building. During the build each had a job that couldn't see my code's answers:

- **Fable** wrote the test suite from the code text and README, not from the implementation.
- **Sonnet** built a second project, with renamed and reordered columns, new room names and new OCR errors. It wrote the expected verdicts before seeing any output.

On top of that, every verdict on the README fixtures was audited by hand against the drawing images.

**AI catches** (where an assistant got it wrong, and what caught it):

1. **Plan, Office 102.** The plan gave it a verdict that isn't one of the four ("Flagged") alongside a Could Not Evaluate reason code. *Caught by Sonnet's review.*
2. **Plan, W12's area.** Two plan revisions missed that the best-case area (½ × 12 sf = 6.0 sf) also sits close to the 5.7 sf minimum. *Caught by Fable's review.*
3. **Plan, footnote markers.** A shortened plan dropped the rule that splits `<sup>` from labels; `R<sup>h</sup>` would have read as `Rh` and missed row R. *Caught by Fable's review.*
4. **Build, generalization.** The first build scored 3/26 on Sonnet's second project. *Caught by the generalization fixture.* Six bugs:
   - A schedule with no number column lost every window ID.
   - `HD HT.` and `BLDG. HEIGHT` weren't recognized.
   - A rough-opening pattern matched the letters "RO" inside `CLROPNG`.
   - Net-clear columns holding bare inch numbers were rejected, and net-clear data wasn't used even when present.
   - `NURS ERY`, split across a line, became a non-sleeping room. That's a silent miss in the dangerous direction.
   - `DEN lO2` lost its room number.
5. **Build, Pass with net clear.** Net clear width and height don't give the height of the opening's bottom edge. My first version would have passed the sill on the unit's sill height alone. Now the worst-case opening position is used: all the vertical frame loss below the opening, or for a hung window, everything below a sash at least as tall as the opening. *Caught while checking Sonnet's expected Pass for window D1.*
6. **Build, Fable's independent tests.** Fable wrote 135 tests from the code text; 130 passed and 5 failed on real bugs, all now fixed:
   - A `NET CLEAR / WIDTH` header also matched *height*, because "WIDTH" ends in H.
   - README-style symbols like `W-A` weren't accepted as window IDs.
   - With no width or operation column, a sill over 44" in every case wasn't called Fail.
   - A room that passed on a supplied fact didn't say so.
   *Caught by the test suite.*
7. **Report, read as a plan checker.** Sonnet reviewed REPORT.md as the person who'd issue it. It found no wrong verdicts, but it did find problems with what would be sent:
   - A draft comment repeated the OCR typo `BEDRROM`.
   - The fixed window W13 cited 1030.1.1 (keys and tools) when the rule is 1030.2.1 (normal operation).
   - The tool ignored the code analysis's grade plane (EL 100.0') and first-floor level (EL 101.0'). Using them shows W7 is probably not a grade-floor opening; this changes wording only, because the grade plane is an average. Verdicts still use 5.0 sf on floor 1.
   - Comment 1 didn't say which sprinkler upgrade would give 60 ft.
   - Exception 2 and the per-window assumptions were repeated many times; each now appears once.
   *Caught by Sonnet's report review.*
8. **Plan vs. build, two rules.** The plan listed undesignated windows in doubtful rooms (W4, W21) as Could Not Evaluate. The build makes them Not Applicable and raises the doubt once, on the room. Fable's tests and Sonnet's fixture expectations initially disagreed with each other here, which is how it surfaced. Both are recorded with the reason in `tests/fixtures/generalization/EXPECTED.md`.

**Hand audit.** Every verdict on the README fixtures was re-derived by hand and checked against `window-schedule.png`, `code-analysis.png` and `table-504-3.png`:
- The R row of Table 504.3 matches the parsed slice in the report, cell for cell.
- W13's Y is in the EGRESS column, not shifted.
- `3' - O"` and `BEDRROM` are printed that way on the drawing itself.

**Results:** `eval/score.py` gives 25/25 on the README fixtures and 26/26 on the generalization fixture. `python -m unittest` runs 135 tests, all passing.

## What I couldn't verify, and what would settle it

| Item | Why | Settled by |
|---|---|---|
| Net clear opening of every window | The schedule gives nominal sizes | Manufacturer data per window type |
| Head-height datum (W7 hinges on it) | The schedule doesn't say what HEAD HEIGHT measures to | A note on the schedule, or a window detail |
| Grade-floor status of first-floor windows (5.0 sf) | Finished grade at each window isn't given; the grade plane gives only an estimate | Site plan / elevations |
| Exception 2: a bedroom door straight to the outside | No floor plans | Floor plans |
| Opens to a public way, yard or court | No site plan | Site plan |
| 1030.5 screens releasable from inside | No hardware data | Window details |
| Whether Office 102 is a sleeping room | Naming only | Floor plan / the architect |
| Building height of 41'-6" | The architect's figure; the grade-plane calculation is on a civil sheet | Civil sheet C1.0 |
| Symbols 9 and 15–19 | Missing from the schedule | The full window schedule sheet |

## Another day

- **A review UI instead of a JSON answers file**, and a shared ruleset built from answers. It would be scoped by jurisdiction and code edition, need a second reviewer, expire, and be replayed against past findings before merging.
- **A model classifier for unfamiliar headers and room names** (e.g. Jev on Vercel's AI Gateway). It would be opt-in and used only for items the rules couldn't match. Its label would be checked against the column contents. It could add a room to the checks but never remove one, and it would never touch numbers, Table 504.3 or verdicts.
- **Cross-checking OCR text against the drawing image**, for example the `3' - O"` cell.
- **At 200 sheets and 40 checks**, what scales is this split: deterministic extraction with provenance, rules as small tested functions per code section, and "Could Not Evaluate with a reason" as the default.
  - The hard part becomes finding the right table on the right sheet, and linking facts across sheets (a door on the floor plan settling Exception 2).
  - That needs a document index with provenance and per-check fixtures like the two here.
  - Speed and cost stay low because the model work is retrieval and labelling, checked by rules, not judgement.
