# Ichi plan-review take-home

Checks a building's height against IBC 2018 Table 504.3 and its bedroom escape windows against IBC 2018 Section 1030, from an OCR'd code analysis and window schedule, and writes a report for a plan checker.

- **[REPORT.md](REPORT.md)**: the report the tool generated from the fixtures, exactly as it came out (plus [findings.json](findings.json) and [answers.template.json](answers.template.json))
- **[NOTES.md](NOTES.md)**: how it works, code vs. model, how the AI was steered and checked, what couldn't be verified
- **[PLAN.md](PLAN.md)**: the plan and the decision log behind it
- The assignment is in [instructions/README.md](instructions/README.md)

```
python -m ichi instructions/fixtures/project/code-analysis.html instructions/fixtures/project/window-schedule.html -o REPORT.md
python -m unittest discover -s tests
python eval/score.py
```

Python 3.12, standard library only.
