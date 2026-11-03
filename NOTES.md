# Notes

## Run it

Python 3.12, standard library only. No install, no API keys.

```
python -m ichi instructions/fixtures/project/code-analysis.html instructions/fixtures/project/window-schedule.html -o REPORT.md
```

This writes `REPORT.md`, `findings.json` (every finding with its evidence) . Tests: `python -m unittest discover -s tests`. Scoring: `python eval/score.py`.

## How it works

`HTML → grid → column mapping → values → rules → REPORT.md`

1. **Grid** (`ichi/grid.py`) expands rowspan/colspan, including body cells, and keeps `<sup>` footnote markers apart from labels, so `R<sup>h</sup>` still matches row R.
2. **Column mapping** (`ichi/mapping.py`) matches headers by synonym, then checks each match against the column's contents. This is how the two `TYPE` columns are told apart, and it survives renamed or reordered columns. With no `EGRESS` column, the affected findings are Could Not Evaluate rather than guessed.
3. **Values** (`ichi/values.py`) parses feet-inches, sprinkler system → sub-row, room name → sleeping / unsure / other, and window operation. Every OCR repair is logged in the report (`3' - O"`, `BEDRROM`).
4. **Rules.** `rules/height.py` reads Table 504.3 at run time and returns the cell with its row, sub-row and column. `rules/egress.py` bounds each escape window.
5. **Report** (`ichi/report.py`) is a fixed template, so the same inputs give the same report.

**Verdict rule.** Fail only if it fails under the most favorable reading (no frame loss). Pass only with real net-clear data. Everything else is Could Not Evaluate, with the margin and the document that would settle it. The schedule gives nominal sizes only, so no window can Pass from it; the report says so up front.

**Confidence** is given as a margin, not a percentage, because inches can be checked. A window exactly at a limit in the best case is listed with the Fails as "likely Fail — confirm" rather than called Fail.

**Wrong-cell protection.** The report prints the whole parsed R row of Table 504.3 with the cell used in bold. The tests check lookups where neighbouring cells differ, because every NS sub-row is identical and would hide a wrong-row bug.

## Plain code vs. model calls

No model calls at run time. Every verdict is arithmetic a checker can retrace, and the Gemini screenshots in the README show why a table lookup shouldn't go to a model. A model would help with unfamiliar header and room names on other projects. I'd add it as an opt-in fallback that can add a room to the checks but never remove one, and never touches numbers or verdicts.

## How I used AI, and how I checked it

Claude (Opus) built it, and two other models reviewed it independently: Fable wrote the tests from the README and code text without seeing the implementation, and Sonnet built a second project with renamed columns and new OCR errors, writing its expected verdicts first. What that caught:

- **The first build scored 3/26 on Sonnet's project.** No ID column, unrecognized headers, `RO` matching inside `CLROPNG`, and `NURS ERY` (split by OCR) dropped as a non-sleeping room. Fixed; now 26/26.
- **Fable's tests found 5 real bugs**, e.g. a `NET CLEAR / WIDTH` header also matching *height* because "WIDTH" ends in H.
- **Plan reviews** caught a dropped footnote rule (`R<sup>h</sup>` → `Rh`, missing row R) and a borderline area I'd missed on W12.
- **Sonnet read the report as a plan checker** and found a draft comment repeating the OCR typo, a wrong code section on the fixed window, and the grade-plane elevation going unused.

I also checked every verdict by hand against the drawing images. `eval/score.py` gives 25/25 on the README fixtures and 26/26 on the second project, and all 115 tests pass.

## What I couldn't verify

| Item | Why | Settled by |
|---|---|---|
| Net clear opening of every window | The schedule gives nominal sizes | Manufacturer data per window type |
| What HEAD HEIGHT measures to (W7 hinges on it) | Not stated on the schedule | A schedule note or window detail |
| Grade-floor status of first-floor windows | The grade plane is an average; grade at each window isn't given | Site plan / elevations |
| Exception 2: a bedroom door straight outside | No floor plans | Floor plans |
| Whether Office 102 is a sleeping room | Name only | Floor plan / the architect |
| The 41'-6" building height | The architect's figure; the calculation is on civil sheet C1.0 | Sheet C1.0 |
| Window symbols 9 and 15–19 | Missing from the schedule | The full schedule sheet |

## Another day

- Let the checker supply facts, such as the net clear opening for a window type, and re-run the rules. Facts, not verdicts, so the tested rules still decide.
- Cross-check OCR text against the drawing image.
- **At 200 sheets and 40 checks**, the structure here holds: extraction that records its source, each code section as a small tested rule, and Could Not Evaluate as the default. The hard part becomes finding the right table on the right sheet and linking facts across sheets (a floor-plan door settling Exception 2). That's where a model earns its cost, for retrieval and labelling checked by rules, not for verdicts.

`extras/PLAN.md` has the plan and the decision log behind it.
