## Context

Python picks the encoding of `sys.stdout` and `sys.stderr` when the interpreter starts. On a console it is the console's encoding. On a pipe, the Windows case whenever an agent captures a script's output, it is the ANSI code page: cp1252 on Western-European Windows, cp1250 in Central Europe, cp932 in Japan. Every file the user-side scripts read or write already names `encoding="utf-8"`. The two output streams are the only text these scripts encode with a platform default. One reader decodes with it too: `publish.py` captures the messages of pandoc and typst with `text=True`, which on Windows decodes them in the ANSI code page, while both tools write UTF-8 (D9). The scripts that produce non-ASCII output are the check report (file names, quoted titles, `—` in its headings), the literature search's CSL-YAML (author names, titles), the reference validator's report and completed entries, the publish and troubleshoot status lines (paths), and the installer's diagnostics.

Constraints from `AGENTS.md`: the user-side scripts are standard library only, Python ≥ 3.11, and cross-platform. A skill never imports from a sibling skill, so shared code reaches a second skill only as a generated copy. `install.py` must still parse on Python 3.7 so that an old interpreter can say which version it needs.

## Goals / Non-Goals

**Goals:**

- No user-side script can fail, or garble its output, because the platform's stream encoding cannot represent a character it prints, or because the platform's default encoding cannot decode a message a tool it starts writes.
- The fix is visible in each script's entry point and enforced offline. A new entry point without it fails the suite.
- The Windows pipe is reproduced in tests on every platform, not only on the Windows CI job.

**Non-Goals:**

- Changing any message's wording, any exit code, or file I/O.
- Reading input: stdin is untouched, since no script reads text from it.
- Instructing agents to set `PYTHONUTF8` or `-X utf8`. No `SKILL.md` changes.
- Host-side decoding. How an agent host decodes the pipe is the host's business; task 8.7 of `desktop-first-install` observes it on real Windows.

## Decisions

**D1 — Reconfigure the streams inside the script, at the start of `main()`.** `sys.stdout.reconfigure(encoding="utf-8", …)` changes the encoding of an already-open text stream, and has done so since Python 3.7. Alternatives considered:

- Documenting `PYTHONUTF8=1` or `python -X utf8` in every `SKILL.md` command. This depends on every agent copying the command exactly, would edit pinned prose in many skills, and the syntax for setting the variable differs between cmd, PowerShell and POSIX shells.
- `errors="replace"` on the platform encoding. This would not crash, but it writes `?` in place of the name into a CSL-YAML entry that is meant to go into the proposal verbatim.
- Writing bytes through `sys.stdout.buffer` at every print site. This is invasive, and the next print added would forget it.

The call goes in `main()`, not at module level, so that importing a script (as the tests and the harness do) never reconfigures the importing process. It is the first statement, before argument parsing, so usage errors and `--help` come out in UTF-8 as well.

**D2 — One helper per script family, named `utf8_output()`, kept identical by a pin.** The families are:

- `check.py`, which reaches five skills as generated copies;
- the lit-search `common.py`, which `search.py`, `snowball.py` and `validate_refs.py` import, and which reaches import and reverse as generated copies;
- `publish.py`;
- `collect.py`;
- `install.py`.

A single shared module would need a new generated file in every script-bearing skill and an import line in scripts that import nothing local today, all for a five-line function. The rule "extract at the third repetition" cannot cross a skill boundary here. So the copies are kept honest the other way: an AST test asserts that the five definitions are identical, and that every user-side `main()` calls its family's helper. The call is the bare name where the module defines the helper, and `common.utf8_output()` where it imports `common`.

**D3 — Keep each stream's error handler; pass nothing else.** `TextIOWrapper.reconfigure(encoding=...)` resets `errors` to `strict` when `errors` is not passed (documented). stderr is opened with `backslashreplace`. Under a POSIX C locale, stdout is opened with `surrogateescape`. The helper therefore passes `errors=stream.errors` explicitly. It passes no `newline`, `line_buffering` or `write_through`, and `reconfigure` keeps whatever it is not given, so line-ending translation and buffering are unchanged. A test asserts both.

**D4 — No-op for streams without `reconfigure`.** The helper looks the method up with `getattr` rather than testing `isinstance(..., io.TextIOWrapper)`. A test's `io.StringIO` (the `redirect_stdout` in `tests/helpers.py:run_check`) and the `None` a windowless interpreter gives both pass through untouched. pytest's capture streams subclass `TextIOWrapper`, are UTF-8 already, and keep their own error handler, so tests that use `capsys` are unaffected.

**D5 — The installer switches directly after its version gate.** `install.main()` keeps the version check as its first statement, so Python 3.7–3.10 reaches the sentence. The helper call follows. The helper uses only `getattr`, a `for` loop and a keyword call, all valid 3.7 syntax, and `test_the_installer_still_parses_on_an_old_interpreter` keeps guarding the module. The installer's stdout never carries user-supplied text, because `display()` makes every path home- or folder-relative so that no user name reaches the output. Its exposure is therefore stderr diagnostics that name the user's own argument, such as an unknown `--source` path. Before the fix, stderr's `backslashreplace` turns those into `Ł` escapes rather than crashing.

**D6 — In-repository consumers decode the output as UTF-8.** Tests and dev tooling that run these scripts as subprocesses with `text=True` decode with the locale's preferred encoding, which is cp1252 on the Windows CI runner. They would garble the new UTF-8 output, or fail outright on bytes cp1252 leaves undefined: `Ł` is `C5 81`, and `0x81` is undefined. These readers pass `encoding="utf-8"`:

- `tests/unit/test_fixture_oracles.py`;
- `tests/unit/test_install.py` (the installed-copy smoke);
- `tests/unit/test_lit_common.py` (the unknown-source run);
- `harness/claude_runner.py` (`run_check`);
- `scripts/install_check.py` (the installer arm and the smoke run).

On Linux and macOS, where the preferred encoding is already UTF-8, nothing changes.

**D7 — Three test layers, all synthetic, in `tests/unit/test_utf8_output.py`.**

- *In-process*: each entry point's `main(argv)` runs with `sys.stdout` and `sys.stderr` replaced by `io.TextIOWrapper(io.BytesIO(), encoding="cp1252")`. stdout gets `strict` and stderr gets `backslashreplace`, as on Windows. The run emits the synthetic name `Łucja Musterfrau-Kővári`, whose `Ł` and `ő` are both outside cp1252. The test asserts that the name's UTF-8 bytes reach the buffer. This layer covers all seven entry points (`check`, `search`, `snowball`, `validate_refs`, `publish`, `collect`, `install`), with sources and lookups stubbed in-process and no network.
- *Subprocess*: one test per family runs the real script file with `PYTHONIOENCODING=cp1252` in the child's environment. That is exactly what the ANSI code page does to a Windows pipe, so the bug reproduces on Linux. On the Windows CI job (`poe test-fast`, which includes these tests) it also runs against a real Windows pipe. Each run has a deterministic, offline path to a non-cp1252 character:
  - `check.py`: the clean fixture's text (`helpers.CLEAN_DRAFT`) is written under a file name carrying the name. The report's first line names the file. Expected exit 0.
  - `validate_refs.py`, for the `common.py` family: a reference whose id carries the name and which has neither DOI nor title. It is reported `UNVERIFIABLE` without a request. Expected exit 0.
  - `publish.py --handout`: the status line names the handout file. Expected exit 0.
  - `collect.py --dry-run --out <dir named after the name>`: the plan names the bundle path. Expected exit 0.
  - `install.py --source <missing path carrying the name>`: the diagnostic on stderr names it. Expected exit 2, see D5.

  `search.py` and `snowball.py` have no offline path to their output, so the in-process layer covers them; their family's subprocess representative is `validate_refs.py`.
- *Pin*: an AST scan of every `main()` under `skills/*/scripts/` and of `install.py`. It asserts the call position from D1/D5 and the identity of the helper definitions from D2. A second scan over the same files fails on any `subprocess` call in text mode without `encoding=` (D9).
- *Helper*: a parametrized unit test over the five helpers. It covers encoding switched, both handlers kept, `\r\n` newline translation kept, `StringIO` and `None` untouched. Both streams start with a non-default handler, stdout with `surrogateescape` as under a POSIX C locale and stderr with `backslashreplace`, because `reconfigure(encoding=...)` resets either to `strict`: a `strict` stdout would stay `strict` whether or not the helper kept it.
- *Captured messages*: `publish.run()` against a child that writes `Ł` and a lone `0xFF` to stderr, once exiting 0 and once exiting 1 (D9).

The fake home that the in-process cases of `collect.py` and `install.py` need is the third copy of the one in `test_install.py` and `test_troubleshoot_collect.py`, so it moves into `tests/helpers.py` as `fake_home()`, beside `fake_home_env()` for the subprocess layer's child environment.

No new proposal fixture is added, so no `expected.json` is needed.

**D8 — Archiving does not wait for a Windows machine.** The subprocess layer is the gate: it reproduces the failure on every platform and runs on the Windows CI job. `desktop-first-install` task 8.7 is a manual session on a clean Windows machine, but none of its steps prints a non-ASCII character, so it confirms this fix only if the operator adds one step. The manual note in `tasks.md` names that step, since this change may not edit `desktop-first-install`'s tasks. Its result is recorded as a note, not as a precondition, so this change can be archived as soon as its tasks and gates are done.

**D9 — `publish.py` decodes its tools' messages as UTF-8 and replaces what is not.** `run()` captured pandoc and typst with `text=True`, which decodes in the locale's preferred encoding: the ANSI code page on Windows. Pandoc writes UTF-8 on every platform, and typst, a Rust program, does too. Any UTF-8 sequence holding a byte cp1252 leaves undefined (0x81, 0x8D, 0x8F, 0x90, 0x9D) aborted the decode. Examples are `Ł` (C5 81), `Á` (C3 81), `č` (C4 8D), `Đ` (C4 90) and the hyphen U+2010 (E2 80 90). The decode runs whatever the exit code, so a citeproc warning about a key such as `Łukasz2020` turned a successful build into a traceback, and a failed one never reached `build failed: …`. `run()` therefore passes `encoding="utf-8", errors="replace"`. Replacing rather than raising is safe because this text only ever reaches a diagnostic. It is the only user-side subprocess call that decodes text: `install.py` captures curl's output as bytes and decodes it itself with `errors="replace"`, and `check.py` and `collect.py` start no processes. A Linux test cannot set the locale encoding a `text=True` child is decoded with to cp1252. The guard is therefore the source rule of D7's pin layer, and the behavioural test uses a lone `0xFF`, which no encoding the suite runs under decodes strictly. Both are red before the fix on every platform.

## Risks / Trade-offs

- [A host that decodes the pipe in a legacy code page now shows mojibake for non-ASCII characters] → Such a host already mismatched before this change: PowerShell, for example, decodes native output with the console's OEM code page, while Python wrote the ANSI one. Before the fix, a character outside the ANSI page aborted the script. Mojibake in a status line is recoverable; a traceback instead of a CSL-YAML block is not. Task 8.7 observes the real hosts.
- [A user who deliberately set `PYTHONIOENCODING` to another encoding is overridden] → The output contract is UTF-8. Nobody relies on another encoding for these scripts, and no documentation suggests one.
- [Five copies of one function] → The AST pin fails on the first divergence (D2). The two vendored families already ship as generated copies, which are drift-checked.
- [An in-process caller's own `TextIOWrapper` is switched to UTF-8] → Only when it calls `main()`. pytest's capture streams are UTF-8 already, and the dev harness runs the scripts as subprocesses.

## Migration Plan

None. The scripts change behaviour only where they used to crash or escape a character. Rollback is a revert of the implementing commit.
