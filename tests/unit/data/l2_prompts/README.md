# Golden judge prompts

The exact prompt the matrix L2 judge sent for each rubric before the rubric
material moved out of `harness/skill_evals.py` into `harness/l2_rubrics.py`
(change `add-dev-runner-judge`, design D6). They pin the move as a pure
refactor: `tests/unit/test_l2_rubrics.py` compares `l2_rubrics.judge_prompt`
with them byte for byte, and `tests/unit/test_eval_wiring.py` asserts that
`skill_evals.judge()` hands exactly these bytes to the judge model.

| file | rubric |
| --- | --- |
| `rq_quality.txt` | `harness/rubrics/rq_quality.txt` |
| `density.txt` | `harness/rubrics/density.txt` |
| `citation_practice.txt` | `harness/rubrics/citation_practice.txt` |
| `review_quality.txt` | `harness/rubrics/review_quality.txt` |
| `title_alarm.txt` | `harness/rubrics/title_alarm.txt` |
| `socratic.txt` | `harness/rubrics/socratic.txt` |
| `readiness.txt` | `harness/rubrics/readiness.txt` — new in `proportionate-readiness-review`, recorded 2026-10-13 from `l2_rubrics.judge_prompt` with the same inputs; nothing shipped before it |

- **Inputs:** `inputs.json` holds the synthetic `question`, `answer` and
  `criterion`; `instructions` was `skill_evals.JUDGE_INSTRUCTIONS`. The values
  are synthetic and the personal data obviously fake. The answer carries the
  marker `l2-prompts-7f3a` and the criterion a non-ASCII tail, so a lost
  substitution or a changed encoding shows.
- **Formatting code:** `template.format(question=…, answer=…, criterion=…,
  instructions=skill_evals.JUDGE_INSTRUCTIONS)`, the body of `skill_evals.judge()`
  at the time, run once from a throwaway script that was never committed.
- **Recorded:** 2026-10-05, against commit `138bf62`.

A rubric template or `JUDGE_INSTRUCTIONS` edit changes what the matrix judge
sends, and therefore shipped verdicts. Such an edit re-records these files in the
same change, so the diff shows the new prompt under review; never re-record them
to make a test pass.
