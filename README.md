# Ichi plan-review take-home

Checks building height against IBC 2018 Table 504.3 and bedroom escape windows against IBC 2018 Section 1030, then writes a report for a plan checker.

- **[REPORT.md](REPORT.md)**: generated from the fixtures, exactly as it came out (also [findings.json](findings.json))
- **[NOTES.md](NOTES.md)**: how to run it, how it works, how it was checked, what couldn't be verified
- The assignment is in [instructions/README.md](instructions/README.md); the plan and extras are in [extras/](extras/)

```
python -m ichi instructions/fixtures/project/code-analysis.html instructions/fixtures/project/window-schedule.html -o REPORT.md
```
