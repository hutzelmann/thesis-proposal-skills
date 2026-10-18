# Design

## Context

See proposal.md — Why. Current state:

- Eight `SKILL.md` files run their scripts as `python3 ${CLAUDE_SKILL_DIR}/scripts/<name>.py …` (16 invocations). Below the commands, each has one fallback paragraph that opens "`${CLAUDE_SKILL_DIR}` is substituted by the host … on a host that leaves it unexpanded, the script really lives in `scripts/` next to this SKILL.md". It continues with per-skill text: where the command runs (the workspace root) and why, what `<location>` stands for, what to say when a script cannot be found, and the interpreter clause. `tests/unit/test_script_paths.py` finds that paragraph by the marker "leaves it unexpanded".
- Claude Code substitutes the variable everywhere in text it delivers from a skill, prose included. The paragraph that explains the variable therefore reaches a Claude Code model as "`/home/…/proposal-check` is substituted by the host with this skill's install directory". The same thing happened in the session that wrote this change: a skill argument that named the variable arrived with the variable replaced by the invoking skill's directory.
- What hosts tell the model when a skill loads (checked 2026-10-17):

  | Host | What the model receives |
  |---|---|
  | Claude Code | `Base directory for this skill: <dir>` above the body (local session transcripts) |
  | OpenCode, and OpenChamber on top of it | `Base directory for this skill: <dir>`, "Relative paths in this skill (e.g., scripts/, reference/) are relative to this base directory.", and an absolute list of the skill's files (`anomalyco/opencode` `packages/core/src/skill.ts:37-59`) |
  | Codex | Each skill's `SKILL.md` path, plus "When `SKILL.md` references relative paths (e.g., `scripts/foo.py`), resolve them relative to the directory containing that expanded `SKILL.md` first" (`openai/codex` `codex-rs/ext/skills/src/catalog_prompt.rs:29`) |
  | Agent Skills client guide | Hosts give the model each skill's `location`, or a "Skill directory:" line on activation, and resolve relative paths against it, using absolute paths in tool calls (agentskills.io, "How to add skills support to your agent") |

- The 2026-07-31 change `resolvable-script-paths` measured the bare form `python3 scripts/<name>.py`. Models ran it from the workspace, missed the script, and quietly fell back to manual inspection: `check_report` scored 1–2 of 5 oracle errors, against 5/5 for haiku and sonnet once the path resolved.
- The open change `desktop-first-install` modifies the same `skill-packaging` requirement (User-side script constraints). Its delta is not archived yet; its remaining tasks are the maintainer's manual app runs.

## Goals / Non-Goals

**Goals:**
- One command form that is correct on every host and carries no host's syntax.
- Keep each fallback paragraph's per-skill content: the workspace-root stake, `<location>`, the not-found rule, and the interpreter clause.
- A metered path that makes the model resolve the placeholder, as a real host does.

**Non-Goals:**
- No change to `references/…` paths in skill bodies. They are already relative to the skill folder, as the standard has them, and are read with a file tool rather than run from the workspace.
- No install-time rewriting of skill files.
- No new host runner. OpenCode stays unmeasured by the harness.

## Decisions

**D1 — `<skill-dir>/scripts/<name>.py`, a placeholder the model fills in.**
- *Over keeping the variable:* only Claude Code expands it, so every other host gets a wrong command first. Claude Code also expands it inside the prose that explains it (Context).
- *Over the standard's bare `scripts/<name>.py`:* a command runs from the working directory, so a bare relative path reads as relative to the workspace. That is the measured 2026-07-31 failure. In a workspace that has its own `scripts/` folder (a student's code repository, say), `scripts/search.py` or `scripts/publish.py` could run the student's file instead of the skill's.
- *Over install-time substitution:* `npx skills add` and plugin installs run none of our code. A rewritten file would also no longer match the git blob hashes that `proposal-troubleshoot`'s collector reports and `poe identify` resolves.
- The placeholder follows `<location>` and `<slug>`, which the same commands already carry and models already fill in. Left unfilled, it fails before anything runs. In POSIX shells and `cmd.exe`, `<skill-dir>` parses as an input redirection from a file that does not exist; in PowerShell, `<` is a reserved operator and the line does not parse. An unfilled placeholder can never run a different script.

**D2 — One defining sentence leads the existing paragraph.** The sentence replaces the variable half of each fallback paragraph, and the per-skill text after the dash stays as it is:

> `<skill-dir>` stands for this skill's own folder, the one holding this SKILL.md, which the host names when it loads the skill (as its base directory, or as the path of this SKILL.md); replace it with that folder's path — but keep running the command from the workspace root, the working directory: …

Skills whose paragraph today starts "Either way, run …" are reworded so the sentence reads on, with the same per-skill content. The opening clause is fixed and identical in all eight files. It is the marker the guard test finds the paragraph by, replacing "leaves it unexpanded". It is not materialized from `shared/blocks/`, because the rest of the paragraph is worded per skill, like the interpreter clause the test already pins.

**D3 — The guard forbids the variable outright.** `test_script_paths.py`:
- No shipped `SKILL.md` contains `${CLAUDE_SKILL_DIR}`, nor any `${…}` or `$VAR/scripts/` reference.
- Every `python3 …scripts/…` invocation starts with `<skill-dir>/scripts/`.
- Each script-bearing skill has exactly one paragraph holding the definition marker, and that paragraph carries the interpreter clause, the workspace-root stake and, where `<location>` appears, its meaning.

The existing test that the fallback never sends the agent to work from the skill directory stays as it is.

**D4 — The metered path emulates a host instead of substituting.** `skill_prompt` stops replacing anything in the body. Its intro gives the skill's base directory in the words hosts use ("Base directory for this skill: `.claude/skills/<skill>/` … relative paths in this skill resolve against it"). It does not say what `<skill-dir>` means; the skill's own definition does that, as on a real host. Matrix logs for the script-running tasks are therefore not comparable cell by cell across this change, and `harness/README.md` says so where it describes the sandbox layout. The dev runner needs no code change: no host substitutes anything any more, so its runs measure resolution as users get it.

**D5 — The divergence is listed.** The README divergence table gains a row: script commands write `<skill-dir>/scripts/…` instead of the standard's bare `scripts/…`, because commands run from the workspace. The placeholder states the step the standard's client guide asks hosts to take — resolve against the skill directory and use an absolute path in the tool call — so a host that skips it still leads the agent there. AGENTS.md's sentence on script paths says the same, and keeps the 2026-07-31 lesson.

**D6 — Archive after `desktop-first-install`.**
- This change's `skill-packaging` delta is the whole requirement block as `desktop-first-install` leaves it, edited.
- Archiving this change first would let the later archive of `desktop-first-install` overwrite it with that change's older text. So this change archives second.
- If `desktop-first-install`'s delta for the requirement changes before then, this delta is redone on top of it.
- `openspec/long-requirements.json` gets entries under `changes/host-neutral-script-paths` for the two MODIFIED requirements, at their measured lengths. Neither is longer than its predecessor: `desktop-first-install`'s version for `skill-packaging`, the main spec for `skill-import`.

**D7 — Verification.**
- L0 (`uv run poe test`) and the spec gate (`uv run poe specs`).
- Dev runner on the Claude subscription: `check_report` on haiku and on sonnet, the scenario that measured the 2026-07-31 failure. Pass means the script ran (oracle errors found, file untouched).
- `import_messy` on sonnet, whose scripts depend on the working directory. Pass means the output lands in the workspace and the checks ran from there.
- One Codex `check_report` run only after the maintainer's explicit go, since it draws on the ChatGPT plan quota.
- Copilot needs the maintainer's `--clear-stop` go and is left to them.
- `desktop-first-install`'s pending manual app runs exercise the new form, if this change lands first.

## Risks / Trade-offs

- [A model fills `<skill-dir>` with the working directory (`.`)] → the definition names the folder holding the SKILL.md, and every host checked names it on load. A wrong fill fails with "file not found" unless the workspace holds a same-named script. That hazard is the bare form's, reached only by a misreading here. The dev runs check the common case.
- [A host gives neither the base directory nor the SKILL.md path] → no host checked does this. The agent then has to locate the skill folder, and the existing not-found rule makes it say the script did not run rather than fake a result. This is the same exposure as today's fallback.
- [Haiku fills placeholders less reliably] → measured directly by the haiku `check_report` run. A failure there sends the wording back for revision before archive.
- [Installed copies still carry the variable until they are updated] → they keep working as they do today. The change touches no workspace file.
- [Archive order slips] → D6, and the task list carries the order as an explicit gate.
