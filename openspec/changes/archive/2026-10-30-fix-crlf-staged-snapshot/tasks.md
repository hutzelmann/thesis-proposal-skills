# Tasks

## 1. The snapshot reads as the file reads

- [x] 1.1 Add `test_a_crlf_checkout_is_graded_against_the_proposal_it_was_given` and `test_a_crlf_earlier_round_reads_as_its_file` to `tests/unit/test_dev_runner_probe.py`: the staged file in CRLF on disk and in the snapshot; the staged original and the earlier round equal the file read back, and an untouched customize workspace passes. Verify: both fail on Linux before 1.2.
  - 2026-10-30: before 1.2 both failed on Linux, with the Windows symptom (`'…\r\n---\r\n' == '…\n---\n'`, a `\r` in the earlier review).
- [x] 1.2 `harness/claude_runner.py`: `staged_text` decodes staged bytes with universal newlines; `staged_original` and `staged_earlier_round` use it. `test_the_guard_compares_against_the_bytes_staged_for_the_run` writes its edited fixture with `write_bytes`. Verify: the two new tests pass. A tree with every fixture `.md`, `.bib` and `.toml` converted to CRLF, run on Linux through `test_dev_runner_probe.py`, `test_folder_scenarios.py` and `test_citation_practice.py`, fails the Windows set before the fix and passes after it.
  - 2026-10-30: in the CRLF tree, the snapshot before the fix (`git archive HEAD`, `17dd16e`) failed 8 tests, the same ones `l0-windows` failed in CI run 41063611665. The ninth, the `write_text` test, fails only on Windows, where `write_text` writes CRLF. After the fix: 194 passed.

## 2. Gate

- [x] 2.1 `uv run poe test` green; `openspec validate fix-crlf-staged-snapshot --strict`. The Windows proof is `l0-windows` after the maintainer's push.
