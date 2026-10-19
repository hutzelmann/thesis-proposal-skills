"""Dev runner: exercise a skill with a real host CLI on the operator's subscription.

Stages a fixture into a temp workspace, installs the skill under test into the
host's skill directory (real skill discovery, closer to production than the
Inspect agent loop), runs the host headless with the user request, then
applies the same L1 verdicts as the authoritative evals (harness/l1_checks.py).

Three hosts sit behind one runner (`HOSTS`, harness/hosts.py; testing-harness
spec: Dev-runner host adapters):

- **Claude Code** (`--host claude`, the default): headless `claude -p` on the
  Max subscription, skills under `<ws>/.claude/skills/`. Described below.
- **Codex** (`--host codex --model <name>`): `codex exec --json` in the
  harness's own Codex login home on the operator's ChatGPT plan quota
  (harness/codex_cli.py), skills under `<ws>/.agents/skills/`. It needs a model
  named on the command line (passed on unchanged, never provider-qualified),
  refuses `--max-budget-usd` (Codex offers no cap) and the install-prompt
  scenarios, and always runs isolated. Its plan billing guard reads the plan
  quota before each run, under a run lock its child also holds, and the session
  record after it; every refusal is untested. Codex reports no cost: the
  summary carries the quota windows before and after instead.
- **GitHub Copilot** (`--host copilot --model <id> --max-ai-credits <N>`):
  `copilot -p --output-format json` in the harness's own Copilot home on the
  operator's included AI credits (harness/copilot_cli.py), skills under
  `<ws>/.agents/skills/`, its shell in the OS sandbox. It needs a model named on
  the command line (never `auto`, never provider-qualified) and a credit cap of
  at least 30 (a soft cap), refuses `--max-budget-usd`, the install-prompt
  scenarios and Windows, and always runs isolated, with the fine-grained token
  of the token file beside the home. Before each run, under the run lock, the
  headless status read checks the raw quota snapshot (any possible or drawn
  overage, legacy billing or low quota refuses), the rosters and the
  confinement probe; after it, a second read, the session's consumption and
  the sandbox reports may record a billing or isolation stop, and every login
  records an approval stop, each refusing later runs until the operator runs
  `uv run poe host-login copilot --clear-stop`, which is the operator's go: it
  covers one canary and, only once that canary passed, one skill run, whose
  start records the approval stop again. `--preflight-only` prints every
  check before the run and starts no prompt-mode child. Copilot reports AI
  credits, not money: the summary's cost is absent, the credits, the cap and
  the overage and remaining values before and after are reported. Its
  workspaces lie in the Copilot work directory, never in the system
  temporary directory, which its sandbox denies. The pseudo-scenario `canary`
  (Copilot only, exactly `--max-ai-credits 30`) is the first model call after
  the operator's go: the shell alone, the confinement probe's commands in one
  script the harness writes into the workspace and one fixed command that
  runs it as the whole prompt, passing only when the client reports every
  shell call sandboxed, that command ran to its end, every row is answered
  and reads as the probe requires, its network namespace is its own and
  nothing else ran; it is no eval scenario,
  and a canary that does not pass leaves the skill run refused (and, after
  its child, records a stop).

Dev loop only — not the source of record. Every summary carries its host and
the label "dev-runner (<host>), not comparable to matrix", and a
`--summary-log` inside `logs/evals` (where the support report reads) is a usage
error. `--judge` adds dev-runner L2: the scenarios with a rubric twin are
graded by the subscription judge (`[roles].dev_judge` in harness/models.toml,
at its pinned effort) against the same rubric templates and criteria as the
matrix (harness/l2_rubrics.py), on every host: a Codex run is graded in a fresh
isolated Claude configuration of the judge's own, prepared after the Codex
child has exited. Its grades are labelled "dev-runner L2, not comparable to
matrix", are never written where the support report reads, and never stand in
for a matrix cell.

Usage:
  uv run python harness/claude_runner.py check_report [--model haiku]
  uv run python harness/claude_runner.py review_fixture --model sonnet
  uv run python harness/claude_runner.py write_from_seed
  uv run python harness/claude_runner.py import_messy
  uv run python harness/claude_runner.py customize_override
  uv run python harness/claude_runner.py ideate_scoped --model sonnet
  uv run python harness/claude_runner.py ideate_scoped_adjacent --model sonnet
  uv run python harness/claude_runner.py write_offtopic_reference --model sonnet
  uv run python harness/claude_runner.py install_prompt --model sonnet
  uv run python harness/claude_runner.py install_prompt_answered --model sonnet
  uv run python harness/claude_runner.py install_prompt_versioned_python --model sonnet
  uv run python harness/claude_runner.py ideate_from_scratch --isolated --model sonnet
  uv run python harness/claude_runner.py publish_figures_latex --preflight-only --isolated
  uv run python harness/claude_runner.py review_fixture --isolated --max-budget-usd 2
  uv run python harness/claude_runner.py write_from_seed --isolated --judge --keep
  uv run python harness/claude_runner.py write_from_seed --rejudge /tmp/devrun-write_from_seed-x
  uv run python harness/claude_runner.py write_rich_seed --isolated --judge --max-notional 1
  uv run python harness/claude_runner.py check_report --host codex --model <name> --keep
  uv run python harness/claude_runner.py write_from_seed --host codex --model <name> --judge
  uv run python harness/claude_runner.py write_from_seed --host codex --rejudge /tmp/devrun-x
  uv run python harness/claude_runner.py check_report --host copilot --model <id> \
      --max-ai-credits 30 --preflight-only
  uv run python harness/claude_runner.py check_report --host copilot --model <id> \
      --max-ai-credits 30 --keep
  uv run python harness/claude_runner.py canary --host copilot --model <id> \
      --max-ai-credits 30 [--preflight-only | --keep]
  uv run python harness/claude_runner.py --summarize logs/devrun/smoke.jsonl \
      --expect write_from_seed import_messy customize_override

Every run reads the host's stream-json events and prints, beside the L1
verdict, the run's cost, turns, duration, token counts, any helper-agent
tool calls (Agent/Task/Workflow) and an advisory single-context verdict —
the probe for the fan-out class of failure, which no other harness path can
see — plus the model the host served and its CLI version. `--isolated` runs
against a fresh host configuration (the routing rig's `isolated_config`, which
links the harness's own login after its preflight — `uv run poe host-login
claude` sets it up once — or the `CLAUDE_REAL_CONFIG_DIR` opt-in, or nothing
under a long-lived token, keeps that login current, and holds only the
claude.ai opt-out settings and an empty Anthropic profile directory) and the
allowlisted environment `host_login.allowlisted_env` builds for every isolated
Claude child, the judge's included, so a run measures the default host rather
than the operator's session mode. The summary says which (`config`), which
login a run linked (`login`) and that login's directory (`login_dir`), the one
place a refresh is written back. A login that no longer serves is named with
that login's one remedy (`host_login.login_remedy`).

The host's stream is read as it arrives (`routing.follow_stream`), and the host
is stopped at the first event that shows a claude.ai account surface — in an
isolated run any MCP server, foreign plugin or synced skill, in an ambient run
a claude.ai connector. A host that announces it before the model's first turn,
as 2.1.284 does, therefore never leaves a publishing connector live for turns
that skip permission prompts. Such a run, and an isolated run whose
configuration holds synced content afterwards, is untested
(`account_surfaces`).

Billing stays on the subscription: every `ANTHROPIC_*` variable and every
`CLAUDE_CODE_USE_*` switch is stripped from the model run's environment (an
isolated run's allowlist admits none of them in the first place; its one
`ANTHROPIC_` name is the empty profile directory the harness sets), the
claude.ai connector switch is off in both modes, and a run whose stream shows
an API-key source, overage, a refused rate-limit status or no rate-limit
report at all is untested, never passed; its summary line carries the reason
as `billing`. A run given `--summary-log` starts no host once an earlier line
in that log carries `billing`: detection after a run is the only billing check
a Claude run has, so `poe smoke` stops there, and `--summarize` clears the log.
A host still running at its time limit is asked to terminate and killed only
after a grace (`host_login.stop_child`). `--rejudge` re-grades kept
workspaces without running the model again; `--max-notional` caps the judge
calls' cumulative notional cost (plan quota, not money).

Exit status: 0 every computed verdict passed, 1 a verdict failed (L1 or a
graded L2 criterion), 2 usage error, 3 untested (the subscription could not
serve the run or the judge — on Codex or Copilot, the plan billing guard
refused it, a Copilot billing stop included —, a claude.ai account surface or,
on Codex or Copilot, a foreign skill, an MCP call, a broken confinement or a
leaked token reached it, or a Codex or Copilot precondition did not hold: the
run lock, the CLI version, the feature allowlist, the sandbox tools, the
model listing, the served model or effort, the Copilot approval stop), or a
scenario's hidden or required tools did not hold (a hidden tool a login shell
still finds, a required one missing, a build on another tier), 4 other runner
failure (a Copilot session without a shutdown record is one, with a billing
stop; so is a scenario that hides tools off Linux).

Note: runs claude with --dangerously-skip-permissions inside the temp
workspace so file edits and script calls work headlessly; Codex runs in its
`workspace-write` sandbox, with network only for the scenarios that need it;
Copilot approves its allowlisted tools without prompting and runs its shell in
the OS sandbox, with URL approvals only for the scenarios that need them.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import traceback
import zipfile
from collections.abc import Iterable, Mapping
from contextlib import ExitStack, suppress
from dataclasses import asdict, dataclass
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path, PurePosixPath

import anyio
import claude_cli
import codex_cli
import copilot_cli
import host_login
import support
from account_surfaces import (
    SurfaceLeak,
    ambient_env,
    config_surfaces,
    stream_surfaces,
    surface_reason,
)
from claude_cli import Criterion, Grade, JudgeRun, parse_events
from fixture_paths import fixture_dir, fixture_proposal, oracle_path, staged_tree
from host_login import LOGIN_FAILURE, LoginSource, login_remedy, refusal
from hosts import Host, JudgeBackend, RunView
from l1_checks import (
    FEEDBACK_ROLE,
    HELPER_TOOLS,
    LATEX_ENGINES,
    NOTES_ROLE,
    PROPOSAL_ROLE,
    REVIEW_FILE,
    REVIEW_ROLE,
    SWAP_PAIR_TOOL,
    assistant_text,
    built_tiers,
    family_members_at,
    feedback_body_words,
    load_closing_note,
    renamed_proposal,
    select_draft,
    tool_result_text,
    verdict_check_report,
    verdict_cited_draft,
    verdict_customize_override,
    verdict_draft,
    verdict_earlier_round_rewritten,
    verdict_family_only,
    verdict_family_renamed,
    verdict_figures_embedded,
    verdict_handoff,
    verdict_handoff_after_revision,
    verdict_handoff_ready,
    verdict_handoff_review_feedback,
    verdict_handoff_superseded,
    verdict_handoff_untouched,
    verdict_hollow_review,
    verdict_ideate_from_scratch,
    verdict_ideate_scoped,
    verdict_import,
    verdict_import_figures,
    verdict_install_prompt_asks_scope,
    verdict_install_prompt_found_python,
    verdict_install_prompt_installed,
    verdict_kept_on_request,
    verdict_l2_grades,
    verdict_litsearch_expanded,
    verdict_no_orphans,
    verdict_offtopic_reference,
    verdict_paper_foundation,
    verdict_repaired_draft,
    verdict_review,
    verdict_review_converged,
    verdict_review_dependency,
    verdict_review_ready,
    verdict_review_records_questions,
    verdict_review_swap_anchored,
    verdict_review_swap_decorative,
    verdict_scoping_containment,
    verdict_seed,
    verdict_single_context,
    verdict_sources_untouched,
    verdict_supervise_feedback_contract,
    verdict_supervise_pass_listed,
    verdict_supervise_point_kept,
    verdict_supervise_ready_block,
    verdict_supervise_review_sections,
    verdict_supervise_scope_options,
    verdict_supervise_swap_missed,
    verdict_supervise_swap_question,
    verdict_supervise_swap_quiet,
    verdict_supervise_verification_declared,
    verdict_supervise_verifier,
)
from l2_rubrics import CRITERIA, DEV_RUBRICS, JUDGE_SYSTEM, judge_prompt, question_for
from routing import (
    OUTWARD_TOOLS,
    error_result_reason,
    follow_stream,
    host_cli_version,
    isolated_config,
    result_event,
    served_model,
    tool_calls,
)
from sources import MESSY_REQUEST

HARNESS = Path(__file__).resolve().parent
REPO = HARNESS.parent
SKILLS = REPO / "skills"
CHECK = SKILLS / "proposal-check" / "scripts" / "check.py"
REGISTRY = HARNESS / "models.toml"

# exit statuses (design D7): only a failed verdict reads as a failure of the skill
EXIT_PASS, EXIT_FAIL, EXIT_USAGE, EXIT_UNTESTED, EXIT_RUNNER = 0, 1, 2, 3, 4
OUTCOMES = {EXIT_PASS: "PASS", EXIT_FAIL: "FAIL", EXIT_UNTESTED: "UNTESTED",
            EXIT_RUNNER: "RUNNER FAILURE"}
JUDGE_LABEL = "dev-runner L2, not comparable to matrix"
DEFAULT_MAX_NOTIONAL = 5.00


def all_but(skill: str) -> tuple[str, ...]:
    """Every other shipped skill: a handoff scenario installs the full set, so
    the host routes an approval or a follow-up as a student's install would."""
    return tuple(sorted(d.name for d in SKILLS.iterdir()
                        if d.is_dir() and d.name.startswith("proposal-") and d.name != skill))


# the incident's own words, after a review (testing-harness spec: handoff coverage)
WHAT_NOW = "What do we do now with that feedback?"
# One request per side across the readiness controls and the swap-test pair, so
# a verdict difference between them can only come from the fixture's text.
# Every proposal fixture is a workspace root holding the proposal's folder
# (adopt-proposal-folders, design D10), so a scenario's `proposal` and its
# request name `<slug>/<slug>.md`, relative to the root the run starts in.
F28 = "ci-repair-agent-configurations/ci-repair-agent-configurations.md"
READINESS_REVIEW_REQUEST = (f"Please review my proposal {F28} — "
                            "is it ready for my supervisor?")
# A professor saves a student's file wherever they like, here at the workspace
# root: staged through `sources` as a source document, never as a proposal in
# its folder (design D22, D24)
SUBMITTED_AT_ROOT = {"ci-repair-agent-configurations.md": F28}
SUPERVISE_REQUEST_TAIL = (
    "If the verdict turns out borderline, do not ask "
    "me — take the needs-revision path. Do not make any network "
    "lookups — no claim checks and no literature — and I cannot answer "
    "any further question.")
READINESS_SUPERVISE_REQUEST = (
    "A student sent me this thesis proposal — I saved it as "
    "ci-repair-agent-configurations.md. Prepare my feedback: the draft "
    "I can send back. " + SUPERVISE_REQUEST_TAIL)
# the two earlier-round shapes of the reported run (testing-harness spec:
# claim-scope swap coverage): a resubmission after earlier feedback, and a redo
# the professor asks for over an earlier run's files
RESUBMISSION_SUPERVISE_REQUEST = (
    "A student revised their thesis proposal after my earlier feedback and sent it "
    "again — I saved it as ci-repair-agent-configurations.md. Prepare my feedback: "
    "the draft I can send back. " + SUPERVISE_REQUEST_TAIL)
REDO_SUPERVISE_REQUEST = (
    "Redo my feedback on the student's thesis proposal, which I saved as "
    "ci-repair-agent-configurations.md: replace the earlier draft in its folder "
    "with a new one I can send back. " + SUPERVISE_REQUEST_TAIL)
# the figure fixture's proposal, which the publish scenarios build
F16 = "sensor-anomaly-triage/sensor-anomaly-triage.md"
# the tools a run may extract a PDF's figures with (skill-import: Figures
# marked, not embedded); one of them must be on the run's PATH
EXTRACTION_TOOLS = ("pdfimages", "mutool")
# where tools are hidden, the request rules out installing them instead
INSTALL_NOTHING = "Install nothing: use only what is on this machine."

SCENARIOS = {
    "check_report": {
        "fixture": "f15-format-broken",
        "skill": "proposal-check",
        "proposal": "broken-format/broken-format.md",
        "request": "Please check my proposal broken-format/broken-format.md.",
    },
    "review_fixture": {
        "fixture": "f05-slr-interviews",
        "skill": "proposal-review",
        "proposal": "microservice-technical-debt/microservice-technical-debt.md",
        "request": "Please review my proposal "
                   "microservice-technical-debt/microservice-technical-debt.md — "
                   "is it ready for my supervisor?",
    },
    # check-clean but hollow: the run passes only on the no-viable-core verdict,
    # judged by the pure L1 function alone — no model-graded scorer on this path
    "review_hollow": {
        "fixture": "f22-hollow-generic",
        "skill": "proposal-review",
        "proposal": "software-quality-ml/software-quality-ml.md",
        "request": "Please review my proposal software-quality-ml/software-quality-ml.md — "
                   "is it ready for my supervisor?",
    },
    # readiness, both directions (testing-harness spec: readiness coverage). f28
    # is viable with bounded execution decisions open, so any blocker is
    # overblocking; f29 differs in one paragraph that makes RQ3 depend on
    # partner access still to be negotiated, so ready is underblocking; w09 is
    # f28's text beside an earlier review whose blockers it resolves
    "review_ready": {
        "fixture": "f28-open-decisions",
        "skill": "proposal-review",
        "proposal": F28,
        "request": READINESS_REVIEW_REQUEST,
    },
    "review_dependency": {
        "fixture": "f29-doubtful-dependency",
        "skill": "proposal-review",
        "proposal": F28,
        "request": READINESS_REVIEW_REQUEST,
    },
    # the swap test's check of named choices, both directions (testing-harness
    # spec: swap-test anchor coverage). f31 names Mendwright in its title and
    # RQs while the contribution claims configuration effects in general, so a
    # swap-test blocker on it is expected; f32 differs only in the contribution
    # close, which makes Mendwright's own configurations the object, so any
    # swap-test finding is overblocking. f28 (review_ready) is the no-name control
    "review_swap_decorative": {
        "fixture": "f31-decorative-tool",
        "skill": "proposal-review",
        "proposal": F28,
        "request": READINESS_REVIEW_REQUEST,
    },
    "review_swap_anchored": {
        "fixture": "f32-tool-as-object",
        "skill": "proposal-review",
        "proposal": F28,
        "request": READINESS_REVIEW_REQUEST,
    },
    # the claim-scope pair at Bachelor's level (testing-harness spec: claim-scope
    # swap coverage): f33 states the gap for agent configurations in general beside
    # a close scoped to Mendwright and no reason why, so the scope is undecided and
    # a swap-test blocker is expected; f34 lacks only those two sentences, so every
    # claim is Mendwright's and any swap-test finding is overblocking
    "review_swap_scope": {
        "fixture": "f33-mixed-scope",
        "skill": "proposal-review",
        "proposal": F28,
        "request": READINESS_REVIEW_REQUEST,
    },
    "review_swap_setting": {
        "fixture": "f34-named-setting",
        "skill": "proposal-review",
        "proposal": F28,
        "request": READINESS_REVIEW_REQUEST,
    },
    "review_converge": {
        "fixture": "w09-revised-round",
        "skill": "proposal-review",
        "proposal": F28,
        "request": f"I revised {F28} after your last review — "
                   "please review it again. Is it ready for my supervisor now?",
    },
    # the review's closing record of the research questions it judged
    # (testing-harness spec: review-currency coverage): review_ready's inputs,
    # judged on the record alone, through check.py's own extractor
    "review_record": {
        "fixture": "f28-open-decisions",
        "skill": "proposal-review",
        "proposal": F28,
        "request": READINESS_REVIEW_REQUEST,
    },
    # supervisor side of the overblocking control: a standard-format proposal
    # saved at the workspace root, copied into `<slug>/<slug>.md` (`proposal`)
    # with the original left as it is, so the feedback's tier, points and
    # clarify-early block are what is measured
    "supervise_ready": {
        "fixture": "f28-open-decisions",
        "skill": "proposal-supervise",
        "proposal": F28,
        "sources": SUBMITTED_AT_ROOT,
        "feedback": True,
        "ready": True,
        "helpers": 1,
        "request": READINESS_SUPERVISE_REQUEST,
    },
    # supervisor side of the swap-test pair: the decorative name reaches the
    # student as a question without the test's name; the anchored one raises
    # nothing, so the feedback opens ready with no numbered point. Saved at the
    # root, as `supervise_ready`, whose request they share
    "supervise_swap_decorative": {
        "fixture": "f31-decorative-tool",
        "skill": "proposal-supervise",
        "proposal": F28,
        "sources": SUBMITTED_AT_ROOT,
        "feedback": True,
        "swap": "decorative",
        "helpers": 1,
        "request": READINESS_SUPERVISE_REQUEST,
    },
    "supervise_swap_anchored": {
        "fixture": "f32-tool-as-object",
        "skill": "proposal-supervise",
        "proposal": F28,
        "sources": SUBMITTED_AT_ROOT,
        "feedback": True,
        "swap": "anchored",
        "pass_listed": True,
        "helpers": 1,
        "request": READINESS_SUPERVISE_REQUEST,
    },
    # supervisor side of the claim-scope pair, and the two earlier-round shapes
    # of the reported run on f33's text: a resubmission whose earlier review
    # called Mendwright the object of study (w17), and a redo over an earlier
    # run that had raised it as a point (w18). `tree` stages the fixture's
    # earlier round beside the root copy; the verdict refuses to grade it
    "supervise_swap_scope": {
        "fixture": "f33-mixed-scope",
        "skill": "proposal-supervise",
        "proposal": F28,
        "sources": SUBMITTED_AT_ROOT,
        "feedback": True,
        "swap": "decorative",
        "helpers": 1,
        "request": READINESS_SUPERVISE_REQUEST,
    },
    "supervise_swap_setting": {
        "fixture": "f34-named-setting",
        "skill": "proposal-supervise",
        "proposal": F28,
        "sources": SUBMITTED_AT_ROOT,
        "feedback": True,
        "swap": "anchored",
        "pass_listed": True,
        "helpers": 1,
        "request": READINESS_SUPERVISE_REQUEST,
    },
    "supervise_swap_earlier_remark": {
        "fixture": "w17-earlier-object-remark",
        "skill": "proposal-supervise",
        "proposal": F28,
        "sources": SUBMITTED_AT_ROOT,
        "tree": True,
        "feedback": True,
        "earlier": "remark",
        "helpers": 1,
        "request": RESUBMISSION_SUPERVISE_REQUEST,
    },
    "supervise_swap_earlier_point": {
        "fixture": "w18-earlier-swap-point",
        "skill": "proposal-supervise",
        "proposal": F28,
        "sources": SUBMITTED_AT_ROOT,
        "tree": True,
        "feedback": True,
        "earlier": "point",
        "helpers": 1,
        "request": REDO_SUPERVISE_REQUEST,
    },
    "write_from_seed": {
        "fixture": "w01-ideate-seed",
        "skill": "proposal-write",
        "proposal": "data-drift-detection/data-drift-detection.md",
        "request": "Please turn my idea notes in data-drift-detection/data-drift-detection.md "
                   "into a full proposal draft. Keep my idea, mark anything missing as TODO. "
                   "I cannot answer any questions — decide and tell me what you did.",
    },
    # no fixture: the source arrives pasted in the request and the skill
    # creates the proposal, choosing its own content-derived filename
    "import_messy": {
        "skill": "proposal-import",
        "request": MESSY_REQUEST,
        "produces": True,
    },
    # the core set's third task: the Inspect request verbatim; the verdict reads
    # the untouched proposal and the guidelines.md the skill writes at the
    # workspace root
    "customize_override": {
        "fixture": "f00-clean-en",
        "skill": "proposal-customize",
        "proposal": "ml-code-review/ml-code-review.md",
        "request": "My supervisor requires a detailed work plan with milestones in the "
                   "proposal, not just a one-line timeline, and at least 8 references. "
                   "Please adjust the rules for this workspace.",
    },
    # supervisor-side: raw email fixture (.txt) to paste-ready feedback; import
    # is installed as a sibling, matching a professor's whole-set install
    "supervise_feedback": {
        "fixture": "s01-raw-email",
        "skill": "proposal-supervise",
        "siblings": ("proposal-import",),
        "feedback": True,
        # the skill's one fresh verifier of the finished feedback; the probe
        # flags anything beyond it (skill-supervise spec: single-context execution)
        "helpers": 1,
        # the closing sentences pre-answer both interactive stops — the
        # borderline deferral and the lookup approval (claim checks and
        # literature alike): a headless single-turn run has no professor to
        # ask, so it exercises the needs-revision default and the offline
        # path instead of stalling
        "request": "A student emailed me this thesis idea — I saved it as "
                   "submission-email.txt. Prepare my feedback: the draft "
                   "I can send back. If the verdict turns out "
                   "borderline, do not ask me — take the needs-revision path. "
                   "Do not make any network lookups — no claim checks and no "
                   "literature — and I cannot answer any further question.",
    },
    # the network path of the same scenario: lit-search staged as a sibling and
    # the approval granted in the request, so the run asks nothing and — the
    # fixture's bibliography being two blog posts — has a finding to ground.
    # Live scholarly APIs: expect variance, read the woven papers by hand.
    "supervise_literature": {
        "fixture": "s01-raw-email",
        "skill": "proposal-supervise",
        "siblings": ("proposal-import", "proposal-lit-search"),
        "feedback": True,
        "helpers": 1,
        "request": "A student emailed me this thesis idea — I saved it as "
                   "submission-email.txt. Prepare my feedback: the draft "
                   "I can send back. If the verdict turns out "
                   "borderline, do not ask me — take the needs-revision path. "
                   "Yes, you may look up literature: read-only queries through "
                   "proposal-lit-search are fine, and I cannot answer any "
                   "further question.",
    },
    # the proposal family (testing-harness spec: Proposal-family coverage), here
    # and in `write_rename_family` and `ideate_seed_rename` below: L1 only, with
    # no Inspect twin, so family-only is part of each one's verdict; `family`
    # names the check and `old` the slug a rename must leave behind. No request
    # asks to keep anything, so a kept file is licensed only as a rename. Live
    # scholarly APIs: expect variance in the expansion, not in the family
    # verdict, which reads the workspace alone. w03 has one resolvable seed DOI.
    "litsearch_snowball": {
        "fixture": "w03-snowball-seed",
        "skill": "proposal-lit-search",
        "proposal": "serverless-energy-scheduling/serverless-energy-scheduling.md",
        "family": "expand",
        "request": "Please snowball from the references in "
                   "serverless-energy-scheduling/serverless-energy-scheduling.md and merge "
                   "what fits into it. I cannot answer any questions — decide and tell me "
                   "what you did.",
    },
    # the over-scoped export: chained packages, an uncounted catalogue, a phase
    # table and chapter outline as format bait, a wrong regulation claim and a
    # paper cited against its own abstract. The lookups are granted so the claim
    # checks can run; whether the planted claims were caught is read by hand.
    "supervise_scope": {
        "fixture": "s02-overscoped-export",
        "skill": "proposal-supervise",
        "siblings": ("proposal-import", "proposal-lit-search"),
        "feedback": True,
        "scope": True,
        "helpers": 1,
        "forbidden": ("Musterfrau", "00000000", "erika.musterfrau@example.org",
                      "Musterstraße", "Mustermann"),
        "request": "A student uploaded this revised exposé for a Bachelor's thesis — I "
                   "saved it as submission-export.txt. Prepare my feedback: the draft "
                   "I can send back. If the verdict turns out borderline, do not ask "
                   "me — take the needs-revision path. Yes, you may run read-only "
                   "lookups to check claims and find literature, and I cannot answer "
                   "any further question.",
    },
    # nothing staged: the group page and a canned DBLP-shaped publication list
    # are served over localhost ({url}/{dblp} filled at runtime) and the
    # single-turn request pre-answers the whole administrative preamble,
    # declining the guidelines.md note so the run needs no second turn
    "ideate_scoped": {
        "skill": "proposal-ideate",
        "serve": "g01-research-group",
        "produces": True,
        # the closing sentences are the session-termination cue: without them
        # the model ends turn one mid-Socratic-dialogue and never seeds (the
        # skill seeds at convergence or on "enough", and a one-shot run has no
        # second turn to converge in)
        "request": (
            "I want to develop a thesis idea. To answer your usual questions up "
            "front: I'm in the M.Sc. Embedded Systems Engineering program at "
            "Musterstadt University, it's a Master's thesis, the proposal should "
            "be in English, I have about five months (April 2027 to September "
            "2027), and yes, you may look things up online. The research group I "
            "hope will supervise me has its page at {url} — please take a look "
            "at what they do; a saved export of their recent publication list is "
            "at {dblp}. My rough idea: energy-efficient scheduling of "
            "containerized workloads on edge devices. This message is our whole "
            "session — I cannot reply again, so develop the idea as far as you "
            "can without asking me anything, then treat this as me saying "
            "'enough' and create the seed proposal file now. Don't keep any "
            "scoping notes for later sessions."
        ),
    },
    # the containment pair. `ideate_scoped` above shares its fixture but cannot
    # measure containment: its student idea restates the group's first research
    # area, so a profile term in the seed is indistinguishable from the student's
    # own words. These two put daylight between the idea and the profile — fully
    # in `_adjacent`, all but one area in `_partial` — so a term that arrived
    # through the lookup is attributable.
    "ideate_scoped_adjacent": {
        "skill": "proposal-ideate",
        "serve": "g01-research-group",
        "produces": True,
        "request": (
            "I want to develop a thesis idea. To answer your usual questions up "
            "front: I'm in the M.Sc. Embedded Systems Engineering program at "
            "Musterstadt University, it's a Master's thesis, the proposal should "
            "be in English, I have about five months (April 2027 to September "
            "2027), and yes, you may look things up online. The research group I "
            "hope will supervise me has its page at {url} — please take a look "
            "at what they do; a saved export of their recent publication list is "
            "at {dblp}. My rough idea: whether code review comments on embedded "
            "firmware predict where field defects later show up. This message is "
            "our whole session — I cannot reply again, so develop the idea as far "
            "as you can without asking me anything, then treat this as me saying "
            "'enough' and create the seed proposal file now. Don't keep any "
            "scoping notes for later sessions."
        ),
    },
    "ideate_scoped_partial": {
        "skill": "proposal-ideate",
        "serve": "g01-research-group",
        "produces": True,
        "request": (
            "I want to develop a thesis idea. To answer your usual questions up "
            "front: I'm in the M.Sc. Embedded Systems Engineering program at "
            "Musterstadt University, it's a Master's thesis, the proposal should "
            "be in English, I have about five months (April 2027 to September "
            "2027), and yes, you may look things up online. The research group I "
            "hope will supervise me has its page at {url} — please take a look "
            "at what they do; a saved export of their recent publication list is "
            "at {dblp}. My rough idea: how much an eBPF tracing probe changes the "
            "latency of the code it observes. This message is our whole session — "
            "I cannot reply again, so develop the idea as far as you can without "
            "asking me anything, then treat this as me saying 'enough' and create "
            "the seed proposal file now. Don't keep any scoping notes for later "
            "sessions."
        ),
    },
    # proposal family (see `litsearch_snowball`). w15's notes carry converged
    # state and the preamble facts; the request repeats them, declines lookups
    # and the guidelines.md note, and states a title whose slug differs from the
    # provisional folder `flaky-ci-triage/`
    "ideate_seed_rename": {
        "fixture": "w15-provisional-notes",
        "skill": "proposal-ideate",
        "family": "seed",
        "old": "flaky-ci-triage",
        "request": (
            "I'd like to continue my thesis idea from my notes in flaky-ci-triage/notes.md. "
            "To answer your usual questions up front: I'm in the M.Sc. Computer Science "
            "program, I hope the department's software engineering group will supervise me, "
            "it's a Master's thesis, the proposal should be in English, I have about six "
            "months (April 2027 to September 2027), and no, please don't look anything up "
            "online in this session. My working title is settled: \"Separating Flaky "
            "Failures from Regressions in Continuous Integration\". This message is our "
            "whole session — I cannot reply again, so treat this as me saying 'enough' and "
            "create the seed proposal file now. Don't write anything into a guidelines.md."
        ),
    },
    # the fixture carries two uncited entries with opposite right answers, and
    # the request deliberately does not say which is which: the judgment is the
    # thing under test, and naming the off-topic entry would hand it over.
    "write_offtopic_reference": {
        "skill": "proposal-write",
        "fixture": "f26-offtopic-reference",
        "proposal": "onboarding-documentation-formats/onboarding-documentation-formats.md",
        "request": (
            "Please do a writing pass over "
            "onboarding-documentation-formats/onboarding-documentation-formats.md and "
            "resolve whatever the check reports. I cannot answer any questions — "
            "decide and tell me what you did."
        ),
    },
    # citation practice: neither request mentions citations. The rule has to
    # reach the draft through the skill's own guidance, which is what a student
    # asking for a draft or a polish gets.
    "write_rich_seed": {
        "skill": "proposal-write",
        "fixture": "w08-rich-seed",
        "proposal": "flaky-test-prediction/flaky-test-prediction.md",
        "citations": "draft",
        "request": (
            "Please turn my idea notes in flaky-test-prediction/flaky-test-prediction.md "
            "into a full proposal draft. Keep my idea, mark anything missing as TODO. I "
            "cannot answer any questions — decide and tell me what you did."
        ),
    },
    "write_repair_citations": {
        "skill": "proposal-write",
        "fixture": "f27-citation-runs",
        "proposal": "dependency-update-breakage/dependency-update-breakage.md",
        "citations": "repair",
        # the routing case `write-polish-collision` repeats this request word for
        # word, and the routing rig stages the folder it names
        "request": (
            "Please do a writing pass over "
            "dependency-update-breakage/dependency-update-breakage.md so it is ready "
            "for my supervisor. I cannot answer any questions — decide and tell me what "
            "you did."
        ),
    },
    # proposal family (see `litsearch_snowball`): a requested rename of w14's
    # proposal folder
    "write_rename_family": {
        "fixture": "w14-family-rename",
        "skill": "proposal-write",
        "proposal": F28,
        "family": "rename",
        "old": "ci-repair-agent-configurations",
        "request": "My supervisor and I settled the title: \"Context and Architecture Effects "
                   f"on CI Repair Agents\". Please put it into {F28} and rename my files to "
                   "match it. I cannot answer any questions — decide and tell me what you did.",
    },
    # The folder layout's own flows (testing-harness spec: Folder-layout dev
    # scenarios; adopt-proposal-folders, design D12). Ideation from scratch:
    # nothing staged, three turns on one session — the preamble without a
    # topic, a topic phrase, then a working title whose slug differs from the
    # provisional one — judged on the recorded moves and the end state
    "ideate_from_scratch": {
        "skill": "proposal-ideate",
        "family": "scratch",
        "request": (
            "I need to find a thesis topic. To answer your usual questions up front: I'm in "
            "the M.Sc. Computer Science program, I don't have a supervisor or research group "
            "yet, it's a Master's thesis, the proposal should be in English, I have about six "
            "months (April 2027 to September 2027), and no, please don't look anything up "
            "online in this session. I have no topic yet. Don't write anything into a "
            "guidelines.md."
        ),
        "followups": (
            "My rough topic: how teams decide which flaky tests to quarantine in continuous "
            "integration, and what quarantining costs them later.",
            "My working title is settled: \"Quarantine Decisions for Flaky Tests in Continuous "
            "Integration\". That's enough for today — I cannot reply again, so please create "
            "the seed proposal file now.",
        ),
    },
    # f16's source PDF alone at the workspace root, under a name with no slug
    # (design D24); untested where no extraction tool is on the run's PATH
    "import_figures": {
        "fixture": "f16-figures-import",
        "skill": "proposal-import",
        "sources": {"submission.pdf": "submission.pdf"},
        "extract": True,
        "requires": (EXTRACTION_TOOLS,),
        "request": "My thesis proposal is saved as submission.pdf — please import it into the "
                   "standard proposal format. It has two figures: extract them into the "
                   "proposal's folder and link them, rather than leaving placeholders. I cannot "
                   "answer any questions — decide and tell me what you did.",
    },
    # publish with figures, one scenario per tier (design D12, Q7): typst with
    # nothing hidden; LaTeX with typst hidden; the word processor with typst and
    # every LaTeX engine hidden, each request saying to install nothing. A run
    # whose login shell still finds a hidden tool is untested before it starts
    "publish_figures_typst": {
        "fixture": "f16-figures-import",
        "skill": "proposal-publish",
        "proposal": F16,
        "tier": "typst",
        "requires": (("pandoc",), ("typst",)),
        "request": f"Please build a PDF of my proposal {F16}.",
    },
    "publish_figures_latex": {
        "fixture": "f16-figures-import",
        "skill": "proposal-publish",
        "proposal": F16,
        "tier": "latex",
        "hide": ("typst",),
        "requires": (("pandoc",), LATEX_ENGINES),
        "request": f"Please build a PDF of my proposal {F16}. {INSTALL_NOTHING}",
    },
    "publish_figures_docx": {
        "fixture": "f16-figures-import",
        "skill": "proposal-publish",
        "proposal": F16,
        "tier": "docx",
        "hide": ("typst", *LATEX_ENGINES),
        "requires": (("pandoc",),),
        "request": f"Please build my proposal {F16} into a document I can send to my "
                   f"supervisor. {INSTALL_NOTHING}",
    },
    # a kept file on request: the snowball of `litsearch_snowball`, asked to
    # keep its candidate list; judged by verdict_kept_on_request, family-only
    # with keeping licensed
    "litsearch_keep": {
        "fixture": "w03-snowball-seed",
        "skill": "proposal-lit-search",
        "proposal": "serverless-energy-scheduling/serverless-energy-scheduling.md",
        "family": "keep",
        "request": "Please snowball from the references in "
                   "serverless-energy-scheduling/serverless-energy-scheduling.md and merge "
                   "what fits into it. Please also keep the candidate list you worked from as "
                   "a file in my proposal's folder, so I can look through it later. I cannot "
                   "answer any questions — decide and tell me what you did.",
    },
    # the install prompt, unanswered and with the scope answer given up front
    # (run_install_probe; nothing is staged)
    "install_prompt": {"install": True},
    "install_prompt_answered": {"install": True, "answered": True},
    # optional, Linux only, on the maintainer's go-ahead: pre-answered, with a
    # PATH on which only a versioned python3.N answers (versioned_python_path)
    "install_prompt_versioned_python": {"install": True, "answered": True,
                                        "versioned_python": True},
    # the paper-foundation path's first turn: preamble pre-answered with lookups
    # declined, and no axis named, so the right turn reads the paper's framing
    # slice, says which sections it read and asks what would change. Unlike
    # `ideate_scoped` the request carries no "seed now" cue: the first turn is
    # what is measured, and a seed there is itself a failure. Judged by
    # verdict_paper_foundation over the chat, the tool results and the workspace.
    "ideate_paper_foundation": {
        "skill": "proposal-ideate",
        "fixture": "p01-published-paper",
        "paper": True,
        "request": (
            "I came across a paper I really like and I'd like to write my thesis on "
            "something similar. It's saved here as quieter-pagers.txt. To answer your "
            "usual questions up front: I'm in the M.Sc. Computer Science program. I don't "
            "have a supervisor or research group yet. It's a Master's thesis, the "
            "proposal should be in English, I have about five months, and no, please "
            "don't look anything up online in this session."
        ),
    },
    # the stage handoff (testing-harness spec: handoff coverage). Each installs every
    # skill, so the host routes the request — and the follow-up — itself; `skill`
    # names the one expected to answer. The verdicts read the final turn and the
    # workspace; the rubric reads the whole transcript against `semantic`, or the
    # fixture's own list where the scenario carries none.
    "handoff_review_feedback": {
        "fixture": "f05-slr-interviews",
        "skill": "proposal-review",
        "siblings": all_but("proposal-review"),
        "proposal": "microservice-technical-debt/microservice-technical-debt.md",
        "handoff": "review_feedback",
        "request": "Please review my proposal "
                   "microservice-technical-debt/microservice-technical-debt.md — is it ready "
                   "for my supervisor?",
        "followups": (WHAT_NOW,),
        "semantic": [
            "the first turn is a review whose verdict and blockers are its own; what is graded "
            "is how the second reply turns that review into a path, not which blockers it found",
            "asked what to do with the feedback, the reply states the remaining path in a few "
            "sentences — one revision of the blockers, one fresh review, then the final check "
            "and the hand-in — and adds no further work",
            "the reply recommends one step: revising the blockers, or, where a blocker needs "
            "the student's choice such as which of the two methods the thesis keeps, an "
            "anchored choice that quotes the proposal, says what the choice changes and offers "
            "options from the student's own material plus a way out — never a bare open question",
            "the proposal is not edited before the student approves, and no skill is named in "
            "the handoff",
        ],
    },
    "handoff_superseded": {
        "fixture": "w10-narrowed-scope",
        "skill": "proposal-check",
        "siblings": all_but("proposal-check"),
        "proposal": F28,
        "handoff": "superseded",
        "request": "I narrowed the scope of my proposal after the review. Where does it stand "
                   "now, and what should I do next?",
    },
    # the handoff's own flow: a status answer recommends revising the blocker,
    # the student approves with the decision it needs, and the revision must run
    # under the writing skill — a direct request ("apply the blocker …") was
    # carried out as a bare edit by sonnet and haiku alike in rounds 1 and 2
    "handoff_after_revision": {
        "fixture": "w11-blocker-revision",
        "skill": "proposal-write",
        "siblings": all_but("proposal-write"),
        "proposal": F28,
        "handoff": "after_revision",
        "request": f"Where does my proposal {F28} stand, and what should I do next?",
        "followups": (
            "Yes, go ahead with the revision. My decision: RQ3 is answered from my own "
            "audit of a random sample of accepted patches against the published "
            "patch-quality rubric of Chen26Repair, which is already in my references, "
            "with the sample size fixed after a pilot of twenty patches; ratings by the "
            "partner's engineers become optional.",),
    },
    # the cold direct request rounds 1 and 2 carried out as a bare edit: kept
    # as its own measurement of whether the writing skill loads without a handoff
    # having led there (the description names "apply review findings or blockers")
    "handoff_direct_revision": {
        "fixture": "w11-blocker-revision",
        "skill": "proposal-write",
        "siblings": all_but("proposal-write"),
        "proposal": F28,
        "handoff": "direct_revision",
        "request": f"Please apply the blocker from the review to {F28}. My decision: RQ3 is "
                   "answered from my own audit of a random sample of accepted patches against "
                   "the published "
                   "patch-quality rubric of Chen26Repair, which is already in my references, "
                   "with the sample size fixed after a pilot of twenty patches; ratings by the "
                   "partner's engineers become optional.",
        "semantic": [
            "the request applies the review's one blocker with the decision that resolves "
            "it, so the revision runs under the writing skill's instructions",
            "the pass rewrites the RQ3 passage the blocker cites and leaves the review file "
            "as it is; because that passage changed, the review on file describes an earlier "
            "text and the right step is a fresh review, recommended rather than run",
            "no skill is named in the handoff",
        ],
    },
    "handoff_ready": {
        "fixture": "w12-ready-current",
        "skill": "proposal-check",
        "siblings": all_but("proposal-check"),
        "proposal": F28,
        "handoff": "ready",
        "request": "My review says the proposal is ready. What should I do next?",
    },
    "handoff_todos": {
        "fixture": "f30-open-markers",
        "skill": "proposal-check",
        "siblings": all_but("proposal-check"),
        "proposal": F28,
        "handoff": "todos",
        "request": f"Where does my proposal {F28} stand, and what should I do next?",
    },
}

# Scenarios whose verdict is scoping containment rather than the default.
CONTAINMENT_SCENARIOS = ("ideate_scoped_adjacent", "ideate_scoped_partial")
# Scenarios with hidden or required tools, checked before any model call
PRECONDITIONED = tuple(name for name, scenario in SCENARIOS.items()
                       if scenario.get("hide") or scenario.get("requires"))
# Scenarios judged on the produced draft; `citations` adds the citation verdicts.
DRAFT_SCENARIOS = ("write_from_seed", "write_rich_seed", "write_repair_citations")
# Scenarios judged from `<slug>/review.md`: same inputs, different bar.
REVIEW_VERDICTS = {
    "review_fixture": verdict_review,
    "review_hollow": verdict_hollow_review,
    "review_ready": verdict_review_ready,
    "review_dependency": verdict_review_dependency,
    "review_converge": verdict_review_converged,
    "review_record": verdict_review_records_questions,
    "review_swap_decorative": partial(verdict_review_swap_decorative, tool=SWAP_PAIR_TOOL),
    "review_swap_anchored": partial(verdict_review_swap_anchored, tool=SWAP_PAIR_TOOL),
    "review_swap_scope": partial(verdict_review_swap_decorative, tool=SWAP_PAIR_TOOL),
    "review_swap_setting": partial(verdict_review_swap_anchored, tool=SWAP_PAIR_TOOL),
}


# ---------- install prompt probe (installation spec) -------------------------
#
# Not a skill scenario: nothing is staged, and the agent installs the skills
# itself by carrying out the shared install prompt. The default branch is
# replaced by a local server holding install.py and a zip of the working tree,
# so the probe measures this tree and reaches no public service, and the run
# gets its own HOME so the installer can never touch the operator's skills.

INSTALL_PROMPT = REPO / "shared" / "blocks" / "install-prompt.md"
INSTALLER = REPO / "install.py"
RAW_INSTALLER_URL = (
    "https://raw.githubusercontent.com/hutzelmann/thesis-proposal-skills/main/install.py")
DEFAULT_ARCHIVE_URL = (
    "https://codeload.github.com/hutzelmann/thesis-proposal-skills/zip/refs/heads/main")
PROBE_REVISION = "0" * 39 + "1"  # stands in for the commit id a GitHub archive carries
INSTALL_TARGETS = (".agents/skills", ".claude/skills")
ANSWER = "(My answer to your question in step 2, in advance: install for all my projects.)"


def working_tree_skills() -> dict[str, dict[str, bytes]]:
    return {
        skill.name: {p.relative_to(skill).as_posix(): p.read_bytes()
                     for p in sorted(skill.rglob("*"))
                     if p.is_file() and "__pycache__" not in p.parts}
        for skill in sorted(SKILLS.iterdir())
        if skill.is_dir() and skill.name.startswith("proposal-")
    }


def stage_install_source(root: Path, base_url: str) -> None:
    """install.py, its default archive pointed at a zip of the working tree.
    A drifted installer is a runner failure: the probe cannot redirect it."""
    text = INSTALLER.read_text(encoding="utf-8")
    if text.count(DEFAULT_ARCHIVE_URL) != 1:
        raise RunnerFailure("install.py no longer names the default archive the probe "
                            "redirects")
    with zipfile.ZipFile(root / "main.zip", "w") as archive:
        for name, files in working_tree_skills().items():
            for rel, payload in files.items():
                archive.writestr(f"thesis-proposal-skills-main/skills/{name}/{rel}", payload)
        archive.comment = PROBE_REVISION.encode()
    (root / "install.py").write_text(text.replace(DEFAULT_ARCHIVE_URL, f"{base_url}/main.zip"),
                                     encoding="utf-8")


def install_request(base_url: str, answered: bool) -> str:
    """The shared prompt pointed at the local installer; a drifted prompt is a
    runner failure, as a drifted installer is."""
    prompt = INSTALL_PROMPT.read_text(encoding="utf-8")
    if prompt.count(RAW_INSTALLER_URL) != 1:
        raise RunnerFailure("the install prompt no longer names the installer the probe "
                            "redirects")
    request = prompt.replace(RAW_INSTALLER_URL, f"{base_url}/install.py")
    return f"{request.rstrip()}\n\n{ANSWER}" if answered else request


def skill_copies(*roots: Path) -> list[Path]:
    """Every `proposal-*` folder holding a SKILL.md under the given roots."""
    return sorted({p.parent for root in roots for p in root.rglob("SKILL.md")
                   if p.parent.name.startswith("proposal-")})


def install_probe_verdict(answered: bool, home: Path, ws: Path, chat: str) -> tuple[bool, str]:
    copies = skill_copies(home, ws)
    if not answered:
        return verdict_install_prompt_asks_scope(chat, [str(c) for c in copies])
    targets = {rel: home / rel for rel in INSTALL_TARGETS}
    found = {rel: {c.name: {p.relative_to(c).as_posix(): p.read_bytes()
                            for p in sorted(c.rglob("*")) if p.is_file()}
                   for c in copies if c.parent == root}
             for rel, root in targets.items()}
    records = {}
    for rel, root in targets.items():
        try:
            records[rel] = json.loads((root / ".thesis-proposal-install.json")
                                      .read_text(encoding="utf-8"))
        except (OSError, ValueError):
            records[rel] = None
    strays = [str(c) for c in copies if c.parent not in targets.values()]
    return verdict_install_prompt_installed(working_tree_skills(), found, records, strays)


# every name under which a Python (or something that reports one) answers, so
# the versioned-interpreter variant can leave exactly one: python, python3,
# python3.13, python3.13-config, pythonw, pip3, pydoc3, py, uv, uvx
HIDDEN_PYTHON_RE = re.compile(r"^(?:python[0-9.]*(?:-config)?w?|pip[0-9.]*|pydoc[0-9.]*|py|"
                              r"uvx?)(?:\.exe)?$")


def versioned_python_path(root: Path, search_path: str, interpreter: Path,
                          version: tuple[int, int]) -> str:
    """A PATH of one folder: links to every executable on `search_path` (the
    first of each name wins, as a shell would pick it) except the Python names
    and uv, plus `python3.<minor>` linked to `interpreter`. The three usual names
    and uv then fail, and only a lookup for versioned names finds Python
    (design D10 of desktop-first-install)."""
    root.mkdir(parents=True, exist_ok=True)
    for folder in search_path.split(os.pathsep):
        directory = Path(folder) if folder else None
        if directory is None or not directory.is_dir():
            continue
        for entry in sorted(directory.iterdir()):
            link = root / entry.name
            if HIDDEN_PYTHON_RE.match(entry.name) or link.is_symlink() or link.exists():
                continue
            if entry.is_file() and os.access(entry, os.X_OK):
                link.symlink_to(entry.resolve())
    (root / f"python{version[0]}.{version[1]}").symlink_to(interpreter.resolve())
    return str(root)


def probe_search_path(scenario: dict, base: Path) -> str | None:
    """The host's PATH for the versioned-interpreter variant; None (the
    inherited PATH) for the others."""
    if not scenario.get("versioned_python"):
        return None
    if not sys.platform.startswith("linux"):
        raise RunnerFailure("install_prompt_versioned_python runs on Linux only")
    return versioned_python_path(base / "bin", os.environ.get("PATH", ""),
                                 Path(sys.executable), sys.version_info[:2])


def probe_verdict(scenario: dict, home: Path, ws: Path, chat: str) -> tuple[bool, str]:
    verdict = install_probe_verdict(scenario.get("answered", False), home, ws, chat)
    if scenario.get("versioned_python"):
        return verdict_install_prompt_found_python(verdict, chat)
    return verdict


# ---------- preconditions: hidden and required tools (adopt-proposal-folders, D12) ---
#
# A scenario's `hide` names tools the run's PATH leaves out (Linux only), and
# its `requires` names groups of tools of which one must be on that PATH. Both
# are checked after staging and before any model call; a run that could not
# measure what it is meant to is untested. The host starts its shell from the
# user's profile, and a login shell reads the system profile, which may put
# `/usr/bin` back, so a login shell under the run's environment is asked
# whether it still finds a hidden tool.

# what the check's shell prints for a hidden tool it found; nothing else it
# prints is read, so profile output cannot be taken for a finding
HIDDEN_MARK = "devrun-hidden:"
LOGIN_SHELL_TIMEOUT = 30


def hidden_tool_path(root: Path, search_path: str, hidden: Iterable[str]) -> str:
    """A PATH of one folder: links to every executable on `search_path` (the
    first of each name wins, as a shell would pick it) except the `hidden`
    names. Built like `versioned_python_path`, which stays the install probe's
    own."""
    hidden = set(hidden)
    root.mkdir(parents=True, exist_ok=True)
    for folder in search_path.split(os.pathsep):
        directory = Path(folder) if folder else None
        if directory is None or not directory.is_dir():
            continue
        for entry in sorted(directory.iterdir()):
            link = root / entry.name
            if entry.name in hidden or link.is_symlink() or link.exists():
                continue
            if entry.is_file() and os.access(entry, os.X_OK):
                link.symlink_to(entry.resolve())
    return str(root)


def login_shell_finds(env: Mapping[str, str], tools: Iterable[str],
                      timeout: float = LOGIN_SHELL_TIMEOUT) -> list[str]:
    """The `tools` a shell under `env` still finds: the user's shell (`SHELL`)
    as a login shell, interactive so it also reads the rc files a host's shell
    snapshot reads. One that does not finish, or cannot start, leaves the run
    untested."""
    tools = list(tools)
    shell = env.get("SHELL") or "/bin/sh"
    script = "\n".join(f"command -v {shlex.quote(tool)} >/dev/null 2>&1 && "
                       f"echo {shlex.quote(HIDDEN_MARK + tool)}" for tool in tools)
    try:
        done = subprocess.run([shell, "-l", "-i", "-c", script], env=dict(env),
                              capture_output=True, encoding="utf-8", errors="replace",
                              stdin=subprocess.DEVNULL, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise RunnerFailure(f"untested: the hidden-tool check's login shell ({shell}) did not "
                            f"finish within {timeout:g} s", untested=True) from None
    except OSError as exc:
        raise RunnerFailure(f"untested: the hidden-tool check could not start a login shell "
                            f"({shell}): {exc}", untested=True) from None
    found = {line.strip().removeprefix(HIDDEN_MARK) for line in done.stdout.splitlines()
             if line.strip().startswith(HIDDEN_MARK)}
    return [tool for tool in tools if tool in found]


def precondition_problems(scenario: dict, env: Mapping[str, str]) -> list[str]:
    """Why a run under `env` cannot measure what the scenario is meant to: a
    required tool missing from its PATH, or a hidden tool a login shell under
    it still finds. Nothing when every precondition holds."""
    path = env.get("PATH") or os.defpath
    problems = [f"no {' or '.join(group)} on the run's search path"
                for group in scenario.get("requires", ())
                if not any(shutil.which(tool, path=path) for tool in group)]
    hidden = scenario.get("hide", ())
    found = login_shell_finds(env, hidden) if hidden else []
    if found:
        problems.append(f"a login shell under the run's environment still finds "
                        f"{', '.join(found)}, which the scenario hides")
    return problems


def search_path_for(name: str, scenario: dict, stack: ExitStack) -> str | None:
    """The run's PATH: None (the inherited one) unless the scenario hides
    tools, in a temporary folder outside the workspace that `stack` removes.
    Hiding runs on Linux only; anywhere else it is a runner failure."""
    hidden = scenario.get("hide")
    if not hidden:
        return None
    if not sys.platform.startswith("linux"):
        raise RunnerFailure(f"{name} hides {', '.join(hidden)} from the run's search path, "
                            "which the dev runner does on Linux only")
    root = Path(stack.enter_context(tempfile.TemporaryDirectory(prefix="devrun-path-")))
    return hidden_tool_path(root / "bin", os.environ.get("PATH", ""), hidden)


def check_env(host: str, config: Path | None, path: str | None) -> dict[str, str]:
    """The environment the preconditions are checked under: the Claude run's
    own (`model_env`), or the inherited one for another host, with the run's
    PATH."""
    env = model_env(os.environ, config) if host == "claude" else dict(os.environ)
    if path is not None:
        env["PATH"] = path
    return env


def checked_search_path(args: argparse.Namespace, scenario: dict, stack: ExitStack,
                        config: Path | None) -> str | None:
    """The run's PATH once every precondition holds; a run that cannot
    measure what it is meant to raises untested before any model call."""
    path = search_path_for(args.scenario, scenario, stack)
    problems = precondition_problems(scenario, check_env(host_for(args).name, config, path))
    if problems:
        raise RunnerFailure("untested: " + "; ".join(problems), untested=True)
    return path


def with_search_path(args: argparse.Namespace, path: str | None) -> argparse.Namespace:
    """The run's arguments carrying its PATH, which the Claude host passes to
    every turn; the caller's own are left as they were."""
    return argparse.Namespace(**{**vars(args), "search_path": path}) if path else args


def search_path_kwargs(args: argparse.Namespace) -> dict:
    path = getattr(args, "search_path", None)
    return {"path": path} if path else {}


def run_install_probe(args: argparse.Namespace, scenario: dict) -> int:
    """Two temp homes' worth of isolation, always: the host's config is the
    routing rig's isolated one (logged in without the real home: the harness
    login, kept current, or a long-lived token), and HOME is empty, so
    whatever the installer writes lands where the verdict looks. Exit
    statuses as for a dev run."""
    base = Path(tempfile.mkdtemp(prefix=f"devrun-{args.scenario}-"))
    ws, home, served = base / "proposals", base / "home", base / "served"
    for d in (ws, home, served):
        d.mkdir()
    answered = scenario.get("answered", False)
    stack = ExitStack()
    config, chat = None, ""
    try:
        try:
            config = enter_isolation(stack, "devrun-config-")
            server = HTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(served)))
            stack.callback(server.server_close)  # after the shutdown below (last in, first out)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            stack.callback(server.shutdown)
            url = f"http://127.0.0.1:{server.server_port}"
            stage_install_source(served, url)
            events = run_claude(ws, install_request(url, answered), args.model, args.timeout,
                                budget=args.max_budget_usd, config=config, home=home,
                                path=probe_search_path(scenario, base))
            save_events(events, base)
            chat = final_text(events)
            passed, why = probe_verdict(scenario, home, ws, chat)
            out = summary(args, passed, why, events, config)
            status = EXIT_PASS if passed else EXIT_FAIL
            out["outcome"], out["exit_status"] = OUTCOMES[status], status
        except RunnerFailure as failure:
            if failure.events:
                save_events(failure.events, base)
            out, status = failure_summary(args, failure, config), failure.status
        except Exception as exc:  # a crash still leaves its line in the summary log
            traceback.print_exc()
            failure = RunnerFailure(f"runner crashed: {exc!r}")
            out, status = failure_summary(args, failure, config), failure.status
        # the probe never runs ambient, so a refused isolation names the
        # login it would have linked
        out["config"] = "isolated"
        out.update(login_label(config, isolated=True))
        emit(out, args.summary_log)
        if chat:
            print("\n--- chat tail ---\n" + chat[-1200:])
        return status
    finally:
        stack.close()
        if args.keep:
            print(f"\nprobe directory kept: {base}")
        else:
            shutil.rmtree(base, ignore_errors=True)


class QuietHandler(SimpleHTTPRequestHandler):
    """Serve the fixture page without request logging on stderr."""

    def log_message(self, *_args) -> None:
        pass


def staging_plan(scenario: dict) -> dict[str, Path]:
    """What `stage()` copies, by workspace-relative path: the scenario's
    `sources` alone where it maps workspace names to fixture-relative files
    (design D24) — with the fixture's tree beside them where `tree` asks for an
    earlier round to be staged too — else the fixture's tree, which is the
    workspace root, its oracle and import source left behind; nothing without a
    fixture."""
    if not scenario.get("fixture"):
        return {}
    if scenario.get("sources"):
        fixture = fixture_dir(scenario["fixture"])
        sources = {name: fixture / rel for name, rel in scenario["sources"].items()}
        return {**staged_tree(scenario["fixture"]), **sources} if scenario.get("tree") else sources
    return staged_tree(scenario["fixture"])


def stage(scenario: dict, ws: Path, install_skill: bool = True,
          skill_dir: tuple[str, str] | None = None) -> None:
    """Copy the scenario's fixture into the workspace and install the skill
    under test and its siblings into the host's skill directory —
    `.claude/skills` for Claude, `.agents/skills` for Codex — without `evals/`."""
    skills = ws.joinpath(*(skill_dir or HOSTS["claude"].skill_dir))
    plan = staging_plan(scenario)
    for rel, source in plan.items():
        (ws / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, ws / rel)
    _STAGED[ws.resolve()] = {rel: (ws / rel).read_bytes() for rel in plan}
    if not install_skill:  # baseline arm: same workspace, no skill discovered
        return
    # evals/ stays out: a model that can read its own eval assertions is not
    # being measured (testing-harness spec: Measured environments carry no
    # eval definitions). User installs legitimately carry it; measured ones not.
    no_evals = shutil.ignore_patterns("evals")
    shutil.copytree(SKILLS / scenario["skill"], skills / scenario["skill"], ignore=no_evals)
    # Sibling skills the scenario relies on (e.g. ideate's lit-search fallback).
    for sibling in scenario.get("siblings", ()):
        shutil.copytree(SKILLS / sibling, skills / sibling, ignore=no_evals)


def host_command(request: str, model: str, budget: float | None = None,
                 resume: str | None = None) -> list[str]:
    """The headless invocation: stream-json emits events only with --verbose,
    the outward-facing tools are denied because permission prompts are skipped,
    the budget cap is added only when one was given, and a follow-up turn
    resumes the session its first turn opened."""
    command = [
        "claude", "-p", request, "--model", model, "--dangerously-skip-permissions",
        "--output-format", "stream-json", "--verbose",
        "--disallowed-tools", *OUTWARD_TOOLS,
    ]
    if budget is not None:
        command += ["--max-budget-usd", str(budget)]
    if resume is not None:
        command += ["--resume", resume]
    return command


def host_failure(events: list[dict], returncode: int, stderr: str,
                 source: LoginSource) -> str | None:
    """Why the run is a runner failure, or None — with the one remedy for the
    login the run used (`source`) when the reason is that login, which no
    rerun repairs."""
    message = host_failure_reason(events, returncode, stderr)
    return login_remedy(message, source) if message else None


def host_failure_reason(events: list[dict], returncode: int, stderr: str) -> str | None:
    """Checked in this order: an error result event (a budget overrun is one —
    it exits non-zero with nothing on stderr in stream mode, and carries the
    subtype, errors and cost so far), a non-zero exit without one (the stderr
    tail), and a zero exit with no result event at all, which the host allows
    and which would otherwise judge the L1 over partial narration with empty
    telemetry. The first is composed by `routing.error_result_reason`, which
    the routing rig reads the same way."""
    reason = error_result_reason(events)
    if reason:
        return reason
    if returncode != 0:
        return f"claude failed: {stderr.strip()[-800:] or 'no stderr'}"
    if not result_event(events):
        return "claude emitted no result event"
    return None


class RunnerFailure(Exception):
    """The run ended without a verdict. `untested` when the subscription could
    not serve it (exit status 3), else another runner failure (4); `events`
    is whatever stream the host produced, saved into a kept workspace;
    `billing` the billing reason when that is why the run is untested."""

    def __init__(self, message: str, untested: bool = False,
                 events: list[dict] | None = None, billing: str | None = None):
        super().__init__(message)
        self.message = message
        self.untested = untested
        self.events = events or []
        self.billing = billing

    @property
    def status(self) -> int:
        return EXIT_UNTESTED if self.untested else EXIT_RUNNER


def model_env(environ: Mapping[str, str], config: Path | None) -> dict[str, str]:
    """The model-under-test child's environment; `environ` is not modified.

    Ambient: `account_surfaces.ambient_env` — the inherited one minus every
    variable that can move its billing off the subscription login, with the
    claude.ai connector switch off. Effort and session settings stay — they
    are part of what an ambient run measures. Isolated: the one allowlisted
    environment of every isolated Claude child (`host_login.allowlisted_env`),
    which admits no billing variable and nothing of the launching session,
    effort included, so the run measures the default host (testing-harness
    spec: Isolated child environment)."""
    if config is not None:
        return host_login.allowlisted_env(host_login.CLAUDE, config, environ)
    return ambient_env(environ)


def surface_failure(leaks: list[SurfaceLeak], events: list[dict],
                    host_reason: str | None = None, *, isolated: bool) -> RunnerFailure:
    """An untested run that a claude.ai account surface reached. The surface
    leads: a polluted run's other failures say nothing about the skill. Every
    explicit billing reason the stream carries is named beside it, so a
    surface never hides overage, and so is the host's own failure or its
    timeout, if any. `isolated` picks which opt-outs the message says failed."""
    message = surface_reason(leaks, isolated=isolated)
    signals = claude_cli.billing_signals(events)
    for signal in signals:
        message += f" Also not a subscription result: {signal}."
    if host_reason:
        message += f" The host also failed: {host_reason}"
    return RunnerFailure(message, untested=True, events=events,
                         billing=signals[0] if signals else None)


def run_claude(ws: Path, request: str, model: str, timeout: int,
               budget: float | None = None, config: Path | None = None,
               home: Path | None = None, resume: str | None = None,
               path: str | None = None) -> list[dict]:
    """Run the host headless and return its stream-json events.

    The stream, not the plain text, is what a run is judged on: the final
    `result` event carries the chat text plus cost, turns and token usage, and
    the assistant events carry every tool call — including a helper-agent
    spawn, which plain text output never shows. It is read as it arrives
    (`routing.follow_stream`), and the host is stopped at the first event that
    shows a claude.ai account surface — any in an isolated run, a claude.ai
    connector in an ambient one. A host that announces it before the model's
    first turn, as 2.1.284 does, therefore never leaves a publishing connector
    live for turns that run with permissions skipped. Such a run, and an
    isolated one whose configuration holds synced content afterwards (finished
    or timed out), is untested.

    A run the host failed raises `RunnerFailure` — untested when the login was
    refused or the stream shows an explicit billing signal: an API-key source,
    a foreign provider, overage or a refused rate-limit status (a run stopped
    at the plan limit ends with an error result), else a runner
    failure; so does a finished run whose stream shows billing other than the
    subscription.
    """
    env = model_env(os.environ, config)
    if home is not None:
        # the install probe's scratch home, layered on top of the child's
        # environment so the installer can never touch the operator's skills
        env.update(HOME=str(home), USERPROFILE=str(home))
    if path is not None:  # the versioned-interpreter probe's scratch PATH
        env["PATH"] = path
    isolated = config is not None
    source = host_login.login_source(config, os.environ)
    seen = follow_stream(host_command(request, model, budget, resume), cwd=ws, env=env,
                         timeout=timeout,
                         stop=lambda events: bool(stream_surfaces(events[-1:], isolated)))
    events = seen.events
    if seen.stopped:
        raise surface_failure(stream_surfaces(events, isolated), events, isolated=isolated)
    late = f"claude did not finish within {timeout}s" if seen.timed_out else None
    failure = late or host_failure(events, seen.returncode, seen.stderr, source)
    synced = config_surfaces(config) if config is not None else []
    if synced:  # checked before the configuration is removed, a timed-out run included
        raise surface_failure(synced, events, failure, isolated=True)
    if late:
        raise RunnerFailure(late, events=events)
    if failure:
        # only an explicit signal counts here — an API-key source, a foreign
        # provider, overage or a refused status: a budget overrun on the
        # subscription stays a runner failure, and so does a stream with no report
        signals = claude_cli.billing_signals(events)
        billing = signals[0] if signals else None
        message = f"{failure} (not a subscription result: {billing})" if billing else failure
        raise RunnerFailure(message, untested=bool(billing or LOGIN_FAILURE.search(failure)),
                            events=events, billing=billing)
    billing = claude_cli.billing_problem(events)
    if billing:
        raise RunnerFailure(f"not a subscription result: {billing}", untested=True,
                            events=events, billing=billing)
    return events


# inside the workspace so a kept run carries its own transcript; the leading
# dot keeps it out of every `*.md` glob a verdict reads
EVENTS_FILE = ".devrun-events.jsonl"


def save_events(events: list[dict], ws: Path) -> Path:
    """Write the host's event stream into the workspace, one object per line —
    the only record of why a run did or skipped something. The file is always
    created afresh, never opened through what the run left at its name: an
    entry there is unlinked first (a link goes, its target stays untouched),
    and the new file is created exclusively without following a link. A
    workspace that is no longer a real directory, or a name that cannot be
    freed, gets no file, and stderr says so (add-copilot-dev-runner Decision
    13, the workspace after the run)."""
    path = ws / EVENTS_FILE
    text = "".join(json.dumps(e, ensure_ascii=False) + "\n" for e in events)
    if ws.is_symlink() or not ws.is_dir():
        print(f"events not saved: the workspace {ws} is not a directory", file=sys.stderr)
        return path
    with suppress(FileNotFoundError, IsADirectoryError, PermissionError):
        path.unlink()
    try:
        handle = path.open("x", encoding="utf-8")  # O_CREAT|O_EXCL: a link there fails, unfollowed
    except OSError:
        print(f"events not saved: {path} is taken by an entry the run left", file=sys.stderr)
        return path
    with handle:
        handle.write(text)
    return path


def final_text(events: list[dict]) -> str:
    """The chat the verdicts read: the result event's final text — what the
    plain output mode printed — and nothing else."""
    text = result_event(events).get("result")
    return text if isinstance(text, str) else ""


def turn_texts(events: list[dict]) -> list[str]:
    """Every turn's final text, in order — one per `result` event, so a
    scenario with follow-up turns yields one entry per user turn."""
    return [e["result"] for e in events
            if e.get("type") == "result" and isinstance(e.get("result"), str)]


def session_id(events: list[dict]) -> str | None:
    """The session the latest turn ran in, from its `init` event."""
    return next((e.get("session_id") for e in reversed(events)
                 if e.get("type") == "system" and e.get("subtype") == "init"), None)


def transcript(scenario: dict, events: list[dict]) -> str:
    """The conversation a handoff rubric grades: each user turn beside the
    final text the host answered it with."""
    asked = [scenario["request"], *scenario.get("followups", ())]
    return "\n\n".join(f"USER: {question}\n\nASSISTANT: {answer}"
                       for question, answer in zip(asked, turn_texts(events), strict=False))


def follow_up(args: argparse.Namespace, scenario: dict, ws: Path, events: list[dict],
              config: Path | None) -> list[dict]:
    """Send the scenario's follow-up turns to the session the first turn opened
    (testing-harness spec: handoff coverage), each under the same budget cap
    and the same billing and surface checks; the events of every turn, in
    order. A stream without a session id cannot be resumed, and a turn that
    reports another session than the one it resumed did not continue the
    conversation: both are runner failures, never a multi-turn pass. The budget
    cap applies to the session's running total, which the host reports.

    Only the Claude host resumes a session here: on any other host a scenario
    with follow-up turns is untested, never a first turn graded as the whole
    conversation and never a follow-up sent to `claude`."""
    followups = scenario.get("followups", ())
    host = host_for(args).name
    if followups and host != "claude":
        raise RunnerFailure(f"untested: {args.scenario} sends follow-up turns, which the dev "
                            f"runner resumes on the Claude host only, not on --host {host}",
                            untested=True, events=events)
    for text in followups:
        session = session_id(events)
        if not session:
            raise RunnerFailure("the first turn's stream carries no session id, which a "
                                "follow-up turn needs", events=events)
        try:
            turn = run_claude(ws, text, args.model, args.timeout,
                              budget=args.max_budget_usd, config=config, resume=session,
                              **search_path_kwargs(args))
        except RunnerFailure as failure:
            failure.events = events + failure.events
            raise
        events = events + turn
        if session_id(turn) != session:
            raise RunnerFailure(f"the follow-up turn ran in session {session_id(turn)!r}, "
                                f"not the resumed {session!r}", events=events)
    return events


def _result_figures(result: dict) -> dict:
    usage = result.get("usage") or {}
    return {
        "cost_usd": result.get("total_cost_usd"),
        "num_turns": result.get("num_turns"),
        "duration_ms": result.get("duration_ms"),
        "tokens_in": usage.get("input_tokens"),
        "tokens_out": usage.get("output_tokens"),
        "tokens_cache_read": usage.get("cache_read_input_tokens"),
        "tokens_cache_write": usage.get("cache_creation_input_tokens"),
    }


def telemetry(events: list[dict]) -> dict:
    """Cost, turns, duration and tokens from the result event; None where absent.
    A run with follow-up turns has one result event per turn. Turns, duration
    and tokens are per turn there and are summed; `total_cost_usd` is the
    session's running total (recorded 2026-10-13: 0.191 after the first turn,
    0.202 after a one-turn follow-up), so the last one is the cost.
    `conversation_turns` counts the turns.

    `tokens_in` is the uncached input only; the bulk of a run's input is the
    cache pair, and the 2026-09-02 fan-out was a cache-write story (~45K per
    helper), so both cache counts travel too.
    """
    results = [e for e in events if e.get("type") == "result"]
    if len(results) < 2:
        return _result_figures(result_event(events))
    figures = [_result_figures(r) for r in results]
    summed = {key: sum(f[key] for f in figures if f[key] is not None)
              if any(f[key] is not None for f in figures) else None
              for key in figures[0]}
    return {**summed, "cost_usd": figures[-1]["cost_usd"], "conversation_turns": len(results)}


def claude_read(events: list[dict], args: argparse.Namespace | None) -> RunView:
    """The Claude host's readers: the result event's text, the served full ID
    (checked against the per-model usage) and the CLI version — read by
    `routing.served_model` and `routing.host_cli_version`, the readers the
    routing rig shares — and the telemetry. Codex and Copilot keep readers of
    their own (`codex_cli.codex_read`, `copilot_cli.copilot_read`)."""
    model, note = served_model(events)
    return RunView(final_text(events), getattr(args, "model", None), model,
                   host_cli_version(events), telemetry(events), note)


def _identity(args: argparse.Namespace, view: RunView) -> dict:
    record = {"scenario": args.scenario, "model_requested": args.model, "model": view.model,
              "cli_version": view.cli_version}
    if view.model_check:
        record["model_check"] = view.model_check
    return record


def identity(args: argparse.Namespace, events: list[dict]) -> dict:
    """What ran: the requested name beside the served model and CLI version,
    read by the run's host."""
    return _identity(args, host_for(args).read(events, args))


def summary(args: argparse.Namespace, passed: bool, why: str, events: list[dict],
            config: Path | None, allowed: int = 0, extra: dict | None = None) -> dict:
    """The run's L1 verdict plus the probe: telemetry and the advisory
    single-context verdict against the scenario's helper allowance, which never
    changes the exit status. `extra` carries scenario-specific information —
    a supervise run's feedback length — that is reported, never judged. Every
    summary names its host and carries the host's not-comparable label."""
    host = host_for(args)
    view = host.read(events, args)
    names = [name for name, _ in tool_calls(events)]
    single, single_why = verdict_single_context(names, allowed)
    handed, handed_why = verdict_handoff(view.final_text)
    return {
        **_identity(args, view),
        "host": host.name, "label": host.run_label,
        "arm": "baseline" if args.no_skill else "with-skill",
        "l1": "PASS" if passed else "FAIL", "why": why,
        "billing": None,
        "config": "isolated" if config else "ambient",
        "config_dir": str(config) if config else None,
        **host.label(config, config is not None),
        **view.telemetry,
        "helper_calls": [name for name in names if name in HELPER_TOOLS],
        "single_context": f"{'PASS' if single else 'FAIL'}: {single_why}",
        # advisory like single_context: the stage-handoff format of the final
        # chat, reported on every run and never part of the exit status
        "handoff": f"{'PASS' if handed else 'FAIL'}: {handed_why}",
        **(extra or {}),
    }


def failure_summary(args: argparse.Namespace, failure: RunnerFailure,
                    config: Path | None) -> dict:
    """A run that ended without a verdict, in the same shape: no `l1` key, the
    outcome and the host's own message instead. The label follows the request:
    a run whose isolated config could not be prepared was still not ambient,
    and a host without an ambient mode is always isolated."""
    host = host_for(args)
    view = host.read(failure.events, args)
    isolated = bool(getattr(args, "isolated", False)) or host.always_isolated
    return {
        **_identity(args, view),
        "host": host.name, "label": host.run_label,
        "arm": "baseline" if args.no_skill else "with-skill",
        "outcome": OUTCOMES[failure.status], "exit_status": failure.status,
        "why": failure.message,
        "billing": failure.billing,
        "config": "isolated" if isolated else "ambient",
        "config_dir": str(config) if config else None,
        **host.label(config, isolated),
        **view.telemetry,
    }


def login_label(config: Path | None, *, isolated: bool) -> dict:
    """Which login the run linked, and that login's directory — the one place
    a refresh is written back (`host_login.login_dir`). An isolated run whose
    configuration could not be prepared names the login it would have linked."""
    if config is None and isolated:
        source, directory = host_login.planned_source(os.environ), None
    else:
        source = host_login.login_source(config, os.environ)
        directory = host_login.login_dir(config, os.environ)
    return {"login": source.value, "login_dir": str(directory) if directory else None}


def exit_status(*, runner_failure: bool, failed: bool, untested: bool) -> int:
    """Precedence: a runner failure, then a failed verdict — a real FAIL
    outranks an ungraded criterion — then untested, then pass."""
    if runner_failure:
        return EXIT_RUNNER
    if failed:
        return EXIT_FAIL
    if untested:
        return EXIT_UNTESTED
    return EXIT_PASS


def aggregate_status(statuses: list[int]) -> int:
    """Several outcomes as one exit status, by the same precedence; nothing
    recorded at all is a runner failure, never a pass, and so is any status
    that is not a verdict's (a usage error, or a value a log should not hold)."""
    if not statuses:
        return EXIT_RUNNER
    verdicts = (EXIT_PASS, EXIT_FAIL, EXIT_UNTESTED)
    return exit_status(runner_failure=any(s not in verdicts for s in statuses),
                       failed=EXIT_FAIL in statuses, untested=EXIT_UNTESTED in statuses)


def run_check(ws: Path, proposal: str) -> str:
    """The check's report over `proposal`, a path relative to the workspace,
    run from the workspace root as a user's agent runs it (testing-harness:
    Check run from the staged workspace's root)."""
    result = subprocess.run(
        [sys.executable, str(CHECK), proposal], capture_output=True, encoding="utf-8", cwd=ws
    )
    return result.stdout


def read(path: Path) -> str | None:
    return path.read_text(encoding="utf-8") if path.exists() else None


def workspace_markdown(ws: Path) -> dict[str, str]:
    """Every markdown file the run can leave, by workspace-relative path: the
    listing walks the proposal folders (testing-harness: Check run from the
    staged workspace's root) and leaves out what `present_files` does."""
    return {rel: (ws / rel).read_text(encoding="utf-8") for rel in present_files(ws)
            if rel.endswith(".md")}


def review_of(proposal: str) -> str:
    """The review beside a proposal, `<slug>/review.md`, as a workspace path."""
    return str(PurePosixPath(proposal).with_name(REVIEW_FILE))


S01_FORBIDDEN = ("Musterfrau", "00000000", "erika.musterfrau@example.org", "Musterstraße")
# the fixture email is written in English, so the feedback — and its closing
# note — must be too
S01_LANGUAGE = "English"
INSTALLED_SKILLS = tuple(sorted(
    d.name for d in SKILLS.iterdir() if d.is_dir() and d.name.startswith("proposal-")
))


def text_reader(ws: Path):
    """A workspace path's text, as the verdicts ask for it; None when the file
    is not there."""
    return lambda rel: read(ws / rel)


def role_files(ws: Path, *roles: str) -> dict[str, str]:
    """The files of a proposal folder that take one of `roles`, by
    workspace-relative path, at any depth the listing walks: classified by
    check.py's own listing classifier, so a role-named file outside a proposal
    folder is no companion (testing-harness: Supervise feedback coverage)."""
    members = family_members_at(present_files(ws), text_reader(ws))
    return {rel: (ws / rel).read_text(encoding="utf-8")
            for rel, member in members.items() if member and member[1] in roles}


def first_role_text(ws: Path, role: str) -> str | None:
    found = role_files(ws, role)
    return found[min(found)] if found else None


def feedback_files(ws: Path) -> dict[str, str]:
    """The feedback draft(s) plus the notes file the literature verdict reads,
    by workspace-relative path: the role-named files of a proposal folder."""
    return role_files(ws, FEEDBACK_ROLE, NOTES_ROLE)


def normalized_proposal(ws: Path) -> str | None:
    """The normalized `<slug>/<slug>.md` a supervise run wrote — the locator
    verdict compares the feedback's standards against it — or None."""
    return first_role_text(ws, PROPOSAL_ROLE)


def staged_earlier_round(scenario: dict, ws: Path) -> dict[str, str]:
    """The earlier round's review and feedback a `tree` scenario staged in the
    proposal's folder, by file name, from what `stage()` wrote."""
    folder = PurePosixPath(scenario["proposal"]).parent
    staged = staged_files(scenario, ws)
    return {name: staged[f"{folder}/{name}"].decode("utf-8")
            for name in (REVIEW_FILE, "feedback.md") if f"{folder}/{name}" in staged}


def swap_verdicts(scenario: dict, ws: Path, review: str | None,
                  feedback: str | None) -> list[tuple[bool, str]]:
    """The swap-test verdicts a supervise scenario asks for: the decorative or
    anchored feedback, the pass listed in the review's verification section, and
    an earlier round re-examined — the latter only once the run is shown to have
    rewritten the staged earlier files, so they are never graded as its output."""
    closing = load_closing_note(SKILLS)
    results: list[tuple[bool, str]] = []
    if scenario.get("swap") == "decorative":
        results.append(verdict_supervise_swap_question(feedback, SWAP_PAIR_TOOL, closing))
    elif scenario.get("swap") == "anchored":
        results.append(verdict_supervise_swap_quiet(feedback, SWAP_PAIR_TOOL))
    if scenario.get("pass_listed"):
        results.append(verdict_supervise_pass_listed(review, normalized_proposal(ws),
                                                     SWAP_PAIR_TOOL))
    if scenario.get("tree"):
        rewritten = verdict_earlier_round_rewritten(
            role_files(ws, REVIEW_ROLE, FEEDBACK_ROLE), staged_earlier_round(scenario, ws),
            sorted(role_files(ws, PROPOSAL_ROLE)))
        results.append(rewritten)
        if not rewritten[0]:
            return results
    if scenario.get("earlier") == "remark":
        results.append(verdict_supervise_swap_missed(review, feedback, SWAP_PAIR_TOOL, closing))
    elif scenario.get("earlier") == "point":
        results.append(verdict_supervise_point_kept(review, feedback, SWAP_PAIR_TOOL, closing))
    return results


def supervise_verdict(scenario: dict, ws: Path,
                      events: list[dict] | None = None) -> tuple[bool, str]:
    """The feedback contract over the scenario's fixture identity; the verifier
    — started with its brief, and declared in the review — wherever the
    scenario allows the helper; and, for the over-scoped fixture, the lettered
    cut options in the feedback and the workload and verification sections."""
    passed, why = verdict_supervise_feedback_contract(
        feedback_files(ws), scenario.get("forbidden", S01_FORBIDDEN), INSTALLED_SKILLS,
        load_closing_note(SKILLS), S01_LANGUAGE, proposal=normalized_proposal(ws))
    results = [(passed, why)]
    review, feedback = first_role_text(ws, REVIEW_ROLE), first_role_text(ws, FEEDBACK_ROLE)
    if scenario.get("sources"):  # the saved submission is a source, never moved (D22)
        results.append(verdict_sources_untouched(workspace_changes(scenario, ws)[0],
                                                 scenario["sources"]))
    if scenario.get("helpers"):
        results += [verdict_supervise_verifier(tool_calls(events or [])),
                    verdict_supervise_verification_declared(review)]
    if scenario.get("scope"):
        results += [verdict_supervise_scope_options(feedback, load_closing_note(SKILLS)),
                    verdict_supervise_review_sections(review)]
    if scenario.get("ready"):
        results.append(verdict_supervise_ready_block(feedback, load_closing_note(SKILLS)))
    results += swap_verdicts(scenario, ws, review, feedback)
    failed = [reason for ok, reason in results if not ok]
    if failed:
        return False, "; ".join(failed)
    return True, "; ".join(reason for _, reason in results)


def supervise_extra(scenario: dict, ws: Path) -> dict:
    """What a supervise run reports beside its verdict without being judged on it."""
    if not scenario.get("feedback"):
        return {}
    feedback = first_role_text(ws, FEEDBACK_ROLE)
    return {"feedback_words": feedback_body_words(feedback, load_closing_note(SKILLS))
            if feedback else None}


def containment_inputs(request: str, chat: str,
                       events: list[dict]) -> tuple[str, str]:
    """A two-turn transcript and the run's issued queries.

    The dev runner's scenarios are one-shot, so the student's only turn is the
    request itself — which is the right attribution anyway: it is the whole of
    what the student said. Queries are read from the tool-call inputs, where a
    search term reaches whether the run used the shipped script, a fetch tool, or
    a shell command.
    """
    transcript = f"STUDENT: {request}\n\nASSISTANT: {chat}"
    queries = " ".join(json.dumps(inp, ensure_ascii=False) for _, inp in tool_calls(events))
    return transcript, queries


def containment_verdict(ws: Path, request: str, chat: str,
                        events: list[dict]) -> tuple[bool, str]:
    """Seed structurally complete, and no scoping vocabulary the student never
    voiced in the files or the queries."""
    files = workspace_markdown(ws)
    produced, where = select_draft(files)
    if not produced:
        return False, where
    seeded, why = verdict_seed(files.get(produced), produced)
    if not seeded:
        return False, why
    transcript, queries = containment_inputs(request, chat, events)
    contained, detail = verdict_scoping_containment(transcript, files, queries)
    return contained, f"{why}; {detail} ({where})"


def draft_verdict(scenario: dict, ws: Path, original: str) -> tuple[bool, str]:
    """The draft is mechanically sound. The citation scenarios add that no
    source is cited on consecutive sentences — and, over the over-citing
    fixture, that no source was dropped to get there."""
    # the skill may draft into a fresh <slug>.md instead of the seed
    chosen, where = select_draft(workspace_markdown(ws), scenario["proposal"], original)
    if not chosen:
        return False, where
    text = read(ws / chosen)
    check = run_check(ws, chosen)
    citations = scenario.get("citations")
    if citations == "repair":
        passed, why = verdict_repaired_draft(original, text, check)
    elif citations == "draft":
        passed, why = verdict_cited_draft(text, check)
    else:
        passed, why = verdict_draft(text, check)
    return passed, f"{why} ({where})"


def ideate_verdict(ws: Path, chat: str) -> tuple[bool, str]:
    files = workspace_markdown(ws)
    produced, where = select_draft(files)
    if not produced:
        return False, where
    # the request explicitly declines the scoping note, so a guidelines.md
    # existing at all fails the run
    passed, why = verdict_ideate_scoped(files, produced, chat, note_declined=True)
    return passed, f"{why} ({where})"


def import_verdict(ws: Path) -> tuple[bool, str]:
    produced, _ = select_draft(workspace_markdown(ws))
    if not produced:
        return verdict_import(None)
    return verdict_import(read(ws / produced), run_check(ws, produced), produced)


def figures_verdict(scenario: dict, ws: Path, events: list[dict]) -> tuple[bool, str]:
    """A publish-with-figures scenario: the figures embedded on the scenario's
    tier, with that tier's evidence. A build line naming another tier means a
    hidden tool was reached another way, so the run measured nothing: untested,
    never the skill's failure (design D12)."""
    tier, seen = scenario["tier"], tool_result_text(events)
    others = [other for other in built_tiers(seen) if other != tier]
    if others and tier not in built_tiers(seen):
        raise RunnerFailure(f"untested: the build ran on the {', '.join(others)} tier, not the "
                            f"{tier} tier the scenario measures: a tool it hides was reached "
                            "another way", untested=True, events=events)
    after = {rel: (ws / rel).read_bytes() for rel in present_files(ws)}
    return verdict_figures_embedded(tier, scenario["proposal"], staged_files(scenario, ws), after,
                                    seen)


# What `stage()` wrote into each workspace, by its resolved path. The verdicts
# compare against these bytes rather than the fixture as it reads when the run
# ends, so a fixture edited while a run is in flight cannot move a verdict (a
# 2026-10-19 redo run read its untouched submission as changed that way).
_STAGED: dict[Path, dict[str, bytes]] = {}


def staged_files(scenario: dict, ws: Path | None = None) -> dict[str, bytes]:
    """What `stage()` copied from the scenario's fixture, by workspace-relative
    path — the snapshot taken when `ws` was staged, else the fixture as it
    reads now; nothing for a scenario without one."""
    if ws is not None and ws.resolve() in _STAGED:
        return _STAGED[ws.resolve()]
    return {rel: source.read_bytes() for rel, source in staging_plan(scenario).items()}


def present_files(ws: Path) -> list[str]:
    """Every file in the workspace but the harness's and the interpreter's:
    hidden paths — the installed skills under `.claude/`, the saved event
    stream — and bytecode caches."""
    return sorted(rel for rel in (p.relative_to(ws).as_posix() for p in ws.rglob("*")
                                  if p.is_file())
                  if not any(part.startswith(".") or part == "__pycache__"
                             for part in rel.split("/")))


def workspace_changes(scenario: dict, ws: Path) -> tuple[list[str], list[str]]:
    """Which staged files a run changed and which files it added, by path
    relative to the workspace. A scenario without a fixture staged nothing,
    so every file it leaves counts as added."""
    staged = staged_files(scenario, ws)
    changed = sorted(name for name, data in staged.items()
                     if not (ws / name).is_file() or (ws / name).read_bytes() != data)
    new = [rel for rel in present_files(ws) if rel not in staged]
    return changed, new


def family_only(scenario: dict, ws: Path, seed: str = "") -> tuple[bool, str]:
    """verdict_family_only over the run's workspace; no request asks to keep.
    Its metadata-block test reads the workspace, and a staged file the run
    removed from what was staged."""
    staged = staged_files(scenario, ws)
    _, added = workspace_changes(scenario, ws)

    def read(rel: str) -> str:
        path = ws / rel
        data = path.read_bytes() if path.is_file() else staged[rel]
        return data.decode("utf-8", errors="replace")

    return verdict_family_only(added, present_files(ws), sorted(staged), seed=seed, read=read)


def run_check_json(ws: Path, proposal: str) -> list[dict]:
    """The check's findings over `proposal`, run as `run_check` runs it."""
    result = subprocess.run(
        [sys.executable, str(CHECK), proposal, "--json"],
        capture_output=True, encoding="utf-8", cwd=ws,
    )
    try:
        return json.loads(result.stdout)["findings"]
    except (json.JSONDecodeError, KeyError):
        return [{"rule": "check-failed", "message": result.stderr[-300:]}]


def calls_by_turn(events: list[dict]) -> list[tuple[int, str, dict]]:
    """Every tool call of the run as (turn, tool, input), in order: the turn
    is counted from zero and ends with its `result` event, so a call can be
    placed in the turn that made it."""
    calls, turn = [], 0
    for event in events:
        if event.get("type") == "result":
            turn += 1
        else:
            calls += [(turn, name, args) for name, args in tool_calls([event])]
    return calls


def kept_verdict(scenario: dict, ws: Path) -> tuple[bool, str]:
    """litsearch_keep: the candidate list kept in the proposal's folder, and
    family-only with keeping licensed."""
    staged = staged_files(scenario, ws)
    _, added = workspace_changes(scenario, ws)
    return verdict_kept_on_request(added, present_files(ws), sorted(staged),
                                   scenario["proposal"].partition("/")[0], read=text_reader(ws))


def family_verdict(scenario: dict, ws: Path, events: list[dict] | None = None) -> tuple[bool, str]:
    """The proposal-family scenarios: the scenario's own verdict, a rename's,
    and family-only, all of which must pass; ideation from scratch and the
    kept candidate list, whose verdicts carry family-only themselves."""
    kind = scenario["family"]
    if kind == "scratch":
        return verdict_ideate_from_scratch(calls_by_turn(events or []), present_files(ws),
                                           text_reader(ws))
    if kind == "keep":
        return kept_verdict(scenario, ws)
    after = {rel: (ws / rel).read_bytes() for rel in present_files(ws)}
    results = []
    if kind == "expand":
        results.append(verdict_litsearch_expanded(read(ws / scenario["proposal"])))
    else:
        staged = staged_files(scenario, ws)
        results.append(verdict_family_renamed(staged, after, scenario["old"]))
        proposal, _ = renamed_proposal(staged, after, scenario["old"])
        if kind == "seed":
            results.append(verdict_seed(read(ws / proposal) if proposal else None,
                                        proposal or ""))
        elif proposal:
            results.append(verdict_no_orphans(run_check_json(ws, proposal)))
    results.append(family_only(scenario, ws))
    failed = [why for ok, why in results if not ok]
    return (False, "; ".join(failed)) if failed else (True, "; ".join(w for _, w in results))


def family_extra(name: str, scenario: dict, ws: Path) -> dict:
    """The advisory family observation every other run reports (Q4): it never
    changes the pass flag. A draft scenario's staged proposal is the seed."""
    if scenario.get("family"):
        return {}
    seed = scenario["proposal"] if name in DRAFT_SCENARIOS else ""
    passed, why = family_only(scenario, ws, seed=seed)
    return {"family": f"{'PASS' if passed else 'FAIL'}: {why}"}


def skills_invoked(events: list[dict], after_turns: int = 0) -> list[str]:
    """The skills the run loaded through the Skill tool, skipping the first
    `after_turns` turns — so an approval turn shows whether the step it
    approved ran under its own skill's instructions."""
    seen, turn = [], 0
    for event in events:
        if event.get("type") == "result":
            turn += 1
        elif turn >= after_turns:
            seen += [str(args["skill"]) for name, args in tool_calls([event])
                     if name == "Skill" and isinstance(args, dict) and args.get("skill")]
    return seen


EDIT_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")


def first_turn_edits(events: list[dict]) -> list[str]:
    """The files the first turn wrote with an edit tool, by name — a status
    answer that edits anything has acted before any approval."""
    first = events[:next((i for i, e in enumerate(events) if e.get("type") == "result"),
                         len(events))]
    return sorted({Path(str(args.get("file_path", ""))).name
                   for name, args in tool_calls(first)
                   if name in EDIT_TOOLS and isinstance(args, dict)})


def handoff_verdict(scenario: dict, ws: Path, chat: str,
                    events: list[dict]) -> tuple[bool, str]:
    """The scenario's handoff verdict over the final turn and the workspace."""
    changed, new = workspace_changes(scenario, ws)
    proposal = scenario["proposal"]
    review = review_of(proposal)
    kind = scenario["handoff"]
    if kind == "review_feedback":
        return verdict_handoff_review_feedback(changed, new, chat, proposal, review)
    if kind == "superseded":
        return verdict_handoff_superseded(changed, new, chat)
    if kind in ("after_revision", "direct_revision"):
        # a direct request has no status turn whose edits would come unasked
        edits = first_turn_edits(events) if kind == "after_revision" else []
        return verdict_handoff_after_revision(changed, new, chat, run_check(ws, proposal),
                                              proposal, review, skills_invoked(events), edits)
    if kind == "ready":
        return verdict_handoff_ready(changed, new, chat)
    return verdict_handoff_untouched(changed, new, chat)


def verdict(name: str, scenario: dict, ws: Path, chat: str,
            request: str = "", events: list[dict] | None = None) -> tuple[bool, str]:
    if scenario.get("handoff"):
        return handoff_verdict(scenario, ws, chat, events or [])
    if name in CONTAINMENT_SCENARIOS:
        return containment_verdict(ws, request, chat, events or [])
    if scenario.get("paper"):
        return verdict_paper_foundation(assistant_text(events or []) or chat,
                                        tool_result_text(events or []), workspace_markdown(ws))
    if scenario.get("feedback"):
        return supervise_verdict(scenario, ws, events)
    if scenario.get("family"):
        return family_verdict(scenario, ws, events)
    if scenario.get("tier"):
        return figures_verdict(scenario, ws, events or [])
    if scenario.get("extract"):
        return verdict_import_figures(present_files(ws), text_reader(ws))
    if name == "ideate_scoped":
        return ideate_verdict(ws, chat)
    if scenario.get("produces"):
        return import_verdict(ws)
    return staged_proposal_verdict(name, scenario, ws, chat)


def staged_original(scenario: dict, ws: Path) -> str:
    """The proposal the run was given: the snapshot `stage()` took, so a
    fixture edited while the run is in flight moves no verdict, else the
    fixture's file as it reads now (a kept workspace graded later)."""
    staged = _STAGED.get(ws.resolve(), {})
    if scenario["proposal"] in staged:
        return staged[scenario["proposal"]].decode("utf-8")
    return fixture_proposal(scenario["fixture"]).read_text(encoding="utf-8")


def staged_proposal_verdict(name: str, scenario: dict, ws: Path,
                            chat: str) -> tuple[bool, str]:
    """The scenarios judged against the fixture's own proposal file."""
    original = staged_original(scenario, ws)
    current = read(ws / scenario["proposal"])
    if name == "check_report":
        return verdict_check_report(oracle_path(scenario["fixture"]), original, current, chat)
    if name == "customize_override":
        return verdict_customize_override(original, current, read(ws / "guidelines.md"))
    if name == "write_offtopic_reference":
        # the reason may land in the notes file or in chat; the verdict accepts
        # either, so both are handed over as one blob
        notes = "".join(text for _, text in sorted(role_files(ws, NOTES_ROLE).items()))
        return verdict_offtopic_reference(current, notes + chat)
    if name in REVIEW_VERDICTS:
        review_name = review_of(scenario["proposal"])
        return REVIEW_VERDICTS[name](original, current, read(ws / review_name), review_name)
    if name in DRAFT_SCENARIOS:
        return draft_verdict(scenario, ws, original)
    raise ValueError(name)


# ---------- dev-runner L2: the subscription judge -------------------------------


@dataclass(frozen=True)
class Judge:
    """The dev judge of one invocation, validated before anything is staged."""

    model: str
    effort: str
    cap: float


def resolve_judge(args: argparse.Namespace, parser: argparse.ArgumentParser) -> Judge | None:
    """None without judging. Otherwise the registry's dev-judge role at its
    pinned effort — refused with a usage error, before any staging or call,
    when it could not judge: no isolation, no rubric twin, or an ID the
    subscription does not serve (an alias, or a metered provider's ID)."""
    if not (args.judge or args.rejudge):
        return None
    if args.judge and args.rejudge:
        parser.error("--judge grades a fresh run and --rejudge kept workspaces: pass one")
    if args.judge and not args.isolated and not host_for(args).always_isolated:
        parser.error("--judge requires --isolated: the judge reuses the run's isolated "
                     "configuration and never reads the ambient one")
    if args.scenario not in DEV_RUBRICS:
        parser.error(f"{args.scenario} has no rubric twin; dev-runner L2 grades only "
                     f"{', '.join(DEV_RUBRICS)}")
    roles = support.parse_registry(REGISTRY.read_text(encoding="utf-8")).roles
    model = support.role_model(roles, "dev_judge", os.environ)
    if not support.is_subscription_model(model):
        source = " (set by DEV_JUDGE_MODEL)" if os.environ.get("DEV_JUDGE_MODEL") else ""
        parser.error(f"[roles].dev_judge resolves to {model!r}{source}, which is not a full "
                     "model ID the subscription serves (claude-…, no provider prefix, not an "
                     "alias); a metered ID never grades dev runs")
    return Judge(model, roles.dev_judge_effort, args.max_notional)


def l2_artifact(name: str, scenario: dict, ws: Path) -> str | None:
    """What the judge grades, selected as the scenario's L1 verdict selects it:
    the review file, or the produced draft (which may be a fresh `<slug>.md`) —
    or, for a handoff scenario, the conversation saved with the run."""
    if scenario.get("handoff"):
        return transcript(scenario, load_events(ws)) or None
    if name in REVIEW_VERDICTS:
        return read(ws / review_of(scenario["proposal"])) or None
    original = staged_original(scenario, ws)
    chosen, _ = select_draft(workspace_markdown(ws), scenario["proposal"], original)
    return (read(ws / chosen) or None) if chosen else None


def fixture_oracle(scenario: dict) -> dict:
    """The fixture's oracle — or the scenario's own `semantic` list, where the
    fixture's describes something else (f05's lists the review's defects, not
    what a reply to "what now?" should say)."""
    if scenario.get("semantic"):
        return {"semantic": list(scenario["semantic"])}
    path = oracle_path(scenario["fixture"])
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def judge_criteria(name: str, scenario: dict, ws: Path,
                   request: str) -> tuple[list[Criterion], dict[str, str]]:
    """One prompt per rubric criterion of the scenario, from the same templates
    and criteria the matrix judge reads; the question is the visible request
    (the oracle list for the review scenarios). Nothing to grade costs no call:
    those criteria are reported "not judged"."""
    artifact = l2_artifact(name, scenario, ws)
    if artifact is None:
        return [], {entry.name: "not judged: no artifact" for entry in DEV_RUBRICS[name]}
    facts = fixture_oracle(scenario)
    return [
        Criterion(entry.name, judge_prompt(entry.rubric, question_for(entry, request, facts),
                                           artifact, CRITERIA[entry.key]))
        for entry in DEV_RUBRICS[name]
    ], {}


def run_judge(judge: Judge, criteria: list[Criterion], config: Path,
              projection: bool = False) -> JudgeRun:
    """Every judge call of the invocation under one event loop, in the
    isolated configuration `config`: the login preflight, the warm-up alone,
    then the bounded fan-out."""
    if not criteria:
        return JudgeRun((), 0.0)
    return anyio.run(partial(
        claude_cli.judge_all, criteria, model=judge.model, effort=judge.effort,
        system_prompt=JUDGE_SYSTEM, config=config,
        source=host_login.login_source(config, os.environ), cap=judge.cap,
        projection=projection))


GRADE_NAMES = {True: "PASS", False: "FAIL", None: "UNTESTED"}


def l2_report(judge: Judge, grades: tuple[Grade, ...] | list[Grade],
              not_judged: dict[str, str], served: str | None) -> tuple[dict, int]:
    """The summary's L2 part under its label, and the L2 status: a graded
    failure fails, an ungraded criterion is untested, never a failing grade."""
    calls = [g.call for g in grades if g.call is not None]
    criteria = {name: {"grade": "UNTESTED", "why": why} for name, why in not_judged.items()}
    criteria.update({g.name: {"grade": GRADE_NAMES[g.passed], "why": g.reason} for g in grades})
    graded = {g.name: bool(g.passed) for g in grades if g.passed is not None}
    passed, why = verdict_l2_grades(graded) if graded else (True, "nothing graded")
    untested = bool(not_judged) or len(graded) < len(grades)
    status = exit_status(runner_failure=False, failed=not passed, untested=untested)
    block = {
        "criteria": criteria,
        "judge_model": judge.model,
        "judge_served": calls[0].model if calls else None,
        "effort": judge.effort,
        "cli_version": calls[0].cli_version if calls else None,
        "thinking_tokens": sum(c.thinking_tokens for c in calls),
        "notional_usd": round(sum(c.notional_usd for c in calls), 6),
        "rate_limit": asdict(calls[-1].rate_limit) if calls else None,
    }
    return {"l2": block, "l2_label": JUDGE_LABEL, "l2_verdict": why,
            "self_graded": served is not None and served == judge.model}, status


# ---------- one dev run ---------------------------------------------------------


def enter_isolation(stack: ExitStack, prefix: str) -> Path:
    """The isolated configuration, a sibling temp directory outside the
    workspace (staging and the verdicts' `*.md` glob never see it). Preparing
    it exits with a message when the harness login fails its preflight, the
    opted-in login is missing, or another run's refresh never arrives: the
    subscription cannot serve the run — untested."""
    try:
        return stack.enter_context(isolated_config(prefix))
    except SystemExit as exc:
        if isinstance(exc.code, str):
            raise RunnerFailure(exc.code, untested=True) from None
        raise


def served_request(scenario: dict, stack: ExitStack) -> str:
    """The scenario's request; a `serve` scenario's fixture is served over
    localhost for the run's duration and its URLs are filled in."""
    request = scenario["request"]
    if not scenario.get("serve"):
        return request
    handler = partial(QuietHandler, directory=str(fixture_dir(scenario["serve"])))
    server = HTTPServer(("127.0.0.1", 0), handler)
    stack.callback(server.server_close)  # after the shutdown below (last in, first out)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    stack.callback(server.shutdown)
    base = f"http://127.0.0.1:{server.server_port}"
    return request.format(url=f"{base}/group.html", dblp=f"{base}/dblp.json")


# ---------- the hosts (harness/hosts.py; testing-harness spec: Dev-runner host adapters) --


def codex_rates(model: str | None, registry_text: str | None = None) -> codex_cli.Rates | None:
    """The roster row pricing `model` under OpenAI's provider
    (`openrouter/openai/<model>`), for a Codex run's notional figure; None —
    an unpriced run — otherwise. No Codex model is named anywhere in code."""
    if not model:
        return None
    registry = support.parse_registry(
        REGISTRY.read_text(encoding="utf-8") if registry_text is None else registry_text)
    row = next((m for m in registry.models if m.id == f"openrouter/openai/{model}"), None)
    return codex_cli.Rates(row.input_price, row.cache_read_price, row.output_price) if row else None


def codex_isolation(stack: ExitStack, args: argparse.Namespace) -> Path:
    """The Codex harness home after its preflight; a refusal is untested."""
    try:
        return codex_cli.isolated_home(stack, args)
    except codex_cli.CodexRefused as refused:
        raise RunnerFailure(refused.message, untested=True) from None


def run_codex(ws: Path, request: str, args: argparse.Namespace, home: Path) -> list[dict]:
    """A Codex run (`codex_cli.run_codex`) and its after-run checks, as the
    runner's outcomes: a held run lock, a billing guard refusal, a feature
    outside the allowlist, an effort not served, a login Codex rejected and a
    broken isolation are untested (exit 3); a failed turn, a missing turn and
    the time limit are runner failures — unless that run's session record also
    shows an explicit billing signal or a broken isolation, which makes it
    untested too."""
    skill_root = ws.joinpath(*HOSTS["codex"].skill_dir)
    try:
        events = codex_cli.run_codex(ws, request, model=args.model, effort=args.effort,
                                     timeout=args.timeout, home=home,
                                     scenario=SCENARIOS[args.scenario])
    except host_login.RunLockRefused as busy:
        raise RunnerFailure(refusal(busy.problem), untested=True) from None
    except codex_cli.CodexRefused as refused:
        raise RunnerFailure(refused.message, untested=True, events=refused.events,
                            billing=refused.billing) from None
    except codex_cli.CodexRunFailed as failed:
        late = codex_cli.timeout_problem(failed, skill_root=skill_root)
        raise RunnerFailure(late.message, untested=late.untested, events=failed.events,
                            billing=late.billing) from None
    problem = codex_cli.run_problem(events, skill_root=skill_root, effort=args.effort)
    if problem:
        raise RunnerFailure(problem.message, untested=problem.untested, events=events,
                            billing=problem.billing)
    return events


def codex_label(home: Path | None) -> dict:
    """Every Codex run is isolated in the Codex harness home, on the harness login."""
    return {"login": LoginSource.HARNESS.value,
            "login_dir": str(home or host_login.home(host_login.CODEX))}


def copilot_isolation(stack: ExitStack, args: argparse.Namespace) -> Path:
    """The Copilot harness home after the checks before the lock; a refusal
    (a recorded stop among them) is untested."""
    try:
        return copilot_cli.isolated_home(stack, args)
    except copilot_cli.CopilotRefused as refused:
        raise RunnerFailure(refused.message, untested=True, billing=refused.billing) from None


def _copilot_failure(problem: copilot_cli.RunProblem, events: list[dict]) -> RunnerFailure:
    return RunnerFailure(problem.message, untested=problem.untested, events=events,
                         billing=problem.billing)


def run_copilot(ws: Path, request: str, args: argparse.Namespace, home: Path) -> list[dict]:
    """A Copilot run (`copilot_cli.run_copilot`) and its after-run checks, as
    the runner's outcomes (design Decision 11): a held run lock, a preflight
    or billing-guard refusal, a broken confinement, an isolation finding, a
    rejected token, a limit reached, a served model or effort other than the
    requested one and an unknown tool are untested (exit 3); a session error,
    a missing result line and the time limit are runner failures, unless the
    run's events also show an untested cause; a session without a shutdown
    record stays a runner failure (exit 4) and records a billing stop. Every
    message was scrubbed of the token before it reaches here."""
    canary = args.scenario == CANARY
    scenario = {} if canary else SCENARIOS[args.scenario]
    try:
        events = copilot_cli.run_copilot(ws, request, model=args.model, effort=args.effort,
                                         cap=args.max_ai_credits, timeout=args.timeout,
                                         home=home, scenario=scenario, canary=canary)
    except host_login.RunLockRefused as busy:
        raise RunnerFailure(refusal(busy.problem), untested=True) from None
    except copilot_cli.CopilotRefused as refused:
        raise RunnerFailure(refused.message, untested=True, events=refused.events,
                            billing=refused.billing) from None
    except copilot_cli.CopilotRunFailed as failed:
        raise _copilot_failure(copilot_cli.timeout_problem(failed), failed.events) from None
    problem = copilot_cli.run_problem(events)
    if problem:
        raise _copilot_failure(problem, events)
    return events


# The Copilot canary (add-copilot-dev-runner, the user's decision D-c): a
# pseudo-scenario the positional accepts, absent from SCENARIOS, so no eval,
# verdict, judge or support report ever reads it
CANARY = copilot_cli.CANARY_SCENARIO
CANARY_LABEL = "dev-runner (copilot) canary, not an eval"


def copilot_work_root() -> Path:
    """The Copilot work directory the run's workspace is made in
    (`copilot_cli.work_root`, never the system temporary directory, which the
    Copilot sandbox denies); a refusal is untested."""
    try:
        return copilot_cli.work_root()
    except copilot_cli.CopilotRefused as refused:
        raise RunnerFailure(refused.message, untested=True) from None


def new_workspace(host: Host, scenario_name: str) -> Path:
    """A run's temporary workspace, owner-only: in the host's own work
    directory where it names one (`Host.workspace_root`), otherwise in the
    system temporary directory. Raises `RunnerFailure` (untested) when the
    host's directory cannot be had."""
    root = host.workspace_root() if host.workspace_root else None
    return Path(tempfile.mkdtemp(prefix=f"devrun-{scenario_name}-", dir=root))


def copilot_label(home: Path | None) -> dict:
    """Every Copilot run is isolated in the Copilot harness home, on the
    harness login (the token file beside it)."""
    return {"login": LoginSource.HARNESS.value,
            "login_dir": str(home or host_login.home(host_login.COPILOT))}


# Built here, where the Claude callables live, as lambdas over the module
# attributes, so every monkeypatch of run_claude, isolated_config and
# follow_stream keeps working (design Decision 2).
HOSTS: dict[str, Host] = {
    "claude": Host(
        name="claude", skill_dir=(".claude", "skills"),
        run=lambda ws, request, args, config: run_claude(
            ws, request, args.model, args.timeout, budget=args.max_budget_usd, config=config,
            **search_path_kwargs(args)),
        read=lambda events, args: claude_read(events, args),
        isolation=lambda stack, args: (enter_isolation(stack, "devrun-config-")
                                       if args.isolated else None),
        login=host_login.CLAUDE,
        label=lambda config, isolated: login_label(config, isolated=isolated)),
    "codex": Host(
        name="codex", skill_dir=(".agents", "skills"),
        run=lambda ws, request, args, home: run_codex(ws, request, args, home),
        read=lambda events, args: codex_cli.codex_read(
            events, args, codex_rates(getattr(args, "model", None))),
        isolation=lambda stack, args: codex_isolation(stack, args),
        login=host_login.CODEX,
        label=lambda home, _isolated: codex_label(home),
        always_isolated=True),
    "copilot": Host(
        name="copilot", skill_dir=(".agents", "skills"),
        run=lambda ws, request, args, home: run_copilot(ws, request, args, home),
        read=lambda events, args: copilot_cli.copilot_read(events, args),
        isolation=lambda stack, args: copilot_isolation(stack, args),
        login=host_login.COPILOT,
        label=lambda home, _isolated: copilot_label(home),
        always_isolated=True,
        workspace_root=lambda: copilot_work_root()),
}
# D3(a): the Claude dev judge grades every host's runs, in its own isolation
JUDGE = JudgeBackend(
    host="claude",
    isolation=lambda stack: enter_isolation(stack, "devjudge-config-"))
# where the support report reads its logs (report.py): no dev run writes there
SUPPORT_LOGS = REPO / "logs" / "evals"


def host_for(args: argparse.Namespace | None) -> Host:
    """The run's host; a namespace without one (the tests' ARGS) is Claude."""
    return HOSTS[getattr(args, "host", None) or "claude"]


def _inside_support_logs(path: Path) -> bool:
    return path.resolve().is_relative_to(SUPPORT_LOGS.resolve())


EFFORTS = {"codex": codex_cli.EFFORTS, "copilot": copilot_cli.EFFORTS}


def _host_rules(args: argparse.Namespace, host: str, scenario: dict,
                model: str) -> tuple[tuple[bool, str], ...]:
    """The usage rules a non-Claude host shares (Codex, Copilot): the install
    scenarios, a model required and passed on verbatim, a dollar cap refused
    on Codex, an effort from the host's own levels."""
    title, other = host.capitalize(), host != "claude"
    efforts = EFFORTS.get(host, ())
    return (
        (other and bool(scenario.get("install")),
         f"{args.scenario} is an install-prompt scenario, which runs on the Claude host only"),
        (other and bool(scenario.get("hide")),
         f"{args.scenario} hides tools from the run's search path, which the dev runner does "
         "on the Claude host only"),
        # the tier evidence is read from Claude's stream-json tool results
        # (tool_result_text); another host's tool output would read as no build
        (other and bool(scenario.get("tier")),
         f"{args.scenario} is judged on the build line in the run's tool results, which the "
         "dev runner reads on the Claude host only"),
        (other and not args.rejudge and not model,
         f"--host {host} requires --model: {title} has no default model here"),
        (other and "/" in model, f"--model {model!r} is provider-qualified; --host {host} takes "
         f"the name {title} serves and passes it on unchanged"),
        (host == "codex" and args.max_budget_usd is not None,
         "--max-budget-usd is refused on --host codex: Codex offers no hard budget cap, and "
         "the runner never ignores one"),
        (other and args.effort is not None and args.effort not in efforts,
         f"--effort {args.effort} is not a {title} effort ({', '.join(efforts)})"),
    )


def _canary_rules(args: argparse.Namespace, host: str) -> tuple[tuple[bool, str], ...]:
    """The canary's own usage rules (add-copilot-dev-runner, D-c): Copilot
    only, exactly the minimum credit cap, and nothing that would grade it or
    change what it stages."""
    canary = args.scenario == CANARY
    return (
        (canary and host != "copilot", f"{CANARY} runs on --host copilot only: it confirms the "
         "sandbox Copilot's prompt mode applies"),
        (canary and args.max_ai_credits is not None
         and args.max_ai_credits != copilot_cli.MIN_AI_CREDITS,
         f"{CANARY} takes exactly --max-ai-credits {copilot_cli.MIN_AI_CREDITS}, the smallest cap "
         "the runner allows"),
        *((canary and bool(getattr(args, option)),
           f"{CANARY} takes no --{option.replace('_', '-')}: it is no eval scenario, stages no "
           "skill and is never graded") for option in ("judge", "rejudge", "no_skill")),
    )


def _copilot_rules(args: argparse.Namespace, host: str,
                   model: str) -> tuple[tuple[bool, str], ...]:
    """Copilot's own usage rules (testing-harness spec: Dev-runner host adapters;
    Copilot plan billing guard)."""
    copilot = host == "copilot"
    live = copilot and not args.rejudge
    cap = args.max_ai_credits
    return (
        (copilot and model == "auto",
         "--model auto is refused on --host copilot: the served model could never equal the "
         "request, so every run would be untested"),
        (copilot and args.max_budget_usd is not None,
         "--max-budget-usd is refused on --host copilot: Copilot's only cap is the AI-credit "
         "cap, --max-ai-credits"),
        (live and cap is None, f"--host copilot requires --max-ai-credits N, N >= "
         f"{copilot_cli.MIN_AI_CREDITS}: the credit cap is soft, and the runner never runs "
         "without one"),
        (live and cap is not None and cap < copilot_cli.MIN_AI_CREDITS,
         f"--max-ai-credits {cap} is below the minimum {copilot_cli.MIN_AI_CREDITS}"),
        (not copilot and cap is not None, "--max-ai-credits applies to --host copilot only"),
        (host not in ("copilot", "claude") and args.preflight_only,
         "--preflight-only applies to --host copilot, and on --host claude to a scenario with "
         "hidden or required tools"),
        # it runs the checks before a run and nothing else: an option it would
        # ignore is refused, never dropped (--rejudge would make a judge call)
        *((args.preflight_only and bool(getattr(args, option)),
           f"--preflight-only takes no --{option}: it runs the checks before a run, makes no "
           "model call and keeps no workspace") for option in ("rejudge", "judge", "keep")),
    )


def usage_problem(args: argparse.Namespace) -> str | None:
    """The first reason the invocation is a usage error (design Decision 3),
    checked before anything is staged or started."""
    host = host_for(args).name
    scenario = SCENARIOS.get(args.scenario or "", {})
    model = args.model or ""
    rules = (
        (args.summary_log is not None and _inside_support_logs(args.summary_log),
         f"--summary-log {args.summary_log} lies inside logs/evals, where the support report "
         "reads its logs; a dev-runner summary is never written there"),
        (host == "claude" and args.effort is not None,
         "--effort applies to --host codex or --host copilot only"),
        *_canary_rules(args, host),
        (host == "claude" and args.preflight_only
         and not (scenario.get("hide") or scenario.get("requires")),
         f"--preflight-only on --host claude checks a scenario's hidden or required tools, and "
         f"{args.scenario} has none ({', '.join(PRECONDITIONED)} do)"),
        *_host_rules(args, host, scenario, model),
        *_copilot_rules(args, host, model),
        # last, so every other usage error reads the same on every platform; a
        # re-grade takes no lock and starts no Codex or Copilot process
        (host == "copilot" and not args.rejudge and sys.platform == "win32",
         "--host copilot is refused on Windows: the Copilot sandbox cannot enforce its deny "
         "list there"),
        (host != "claude" and not args.rejudge and host_login.fcntl is None,
         f"--host {host} needs POSIX file locks (fcntl), which this platform lacks"),
    )
    return next((message for refused, message in rules if refused), None)


def judged(args: argparse.Namespace, judge: Judge, criteria: list[Criterion],
           config: Path | None) -> JudgeRun:
    """Grade in the judge's own isolation (design Decision 13): a Claude run's
    isolated configuration is reused; any other host's run is graded in a fresh
    isolated Claude configuration, prepared after the model run has ended —
    never in another host's login home. One that cannot be prepared leaves
    every criterion untested, as for a re-grade."""
    if not criteria:
        return JudgeRun((), 0.0)
    if host_for(args).name == JUDGE.host and config is not None:
        return run_judge(judge, criteria, config)
    with ExitStack() as stack:
        try:
            judge_config = JUDGE.isolation(stack)
        except RunnerFailure as failure:
            return JudgeRun(tuple(Grade(c.name, None, failure.message) for c in criteria), 0.0)
        return run_judge(judge, criteria, judge_config)


def completed_run(args: argparse.Namespace, judge: Judge | None, scenario: dict, ws: Path,
                  request: str, events: list[dict], config: Path | None) -> tuple[dict, int]:
    """The verdicts of a run the host finished: L1, then the judge in its own
    isolation, with the precedence of `exit_status`."""
    chat = host_for(args).read(events, args).final_text
    passed, why = verdict(args.scenario, scenario, ws, chat, request, events)
    out = summary(args, passed, why, events, config, allowed=scenario.get("helpers", 0),
                  extra={**supervise_extra(scenario, ws),
                         **family_extra(args.scenario, scenario, ws)})
    status = EXIT_PASS if passed else EXIT_FAIL
    if judge:
        criteria, not_judged = judge_criteria(args.scenario, scenario, ws, request)
        judged_run = judged(args, judge, criteria, config)
        l2, l2_status = l2_report(judge, judged_run.grades, not_judged, out["model"])
        out.update(l2, billing=judged_run.billing)
        status = aggregate_status([status, l2_status])
    out["outcome"], out["exit_status"] = OUTCOMES[status], status
    return out, status


def emit(out: dict, log: Path | None) -> None:
    """Print the summary; with a summary log, also append it as one JSON line."""
    print(json.dumps(out, indent=2, ensure_ascii=False))
    if log is not None:
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(out, ensure_ascii=False) + "\n")


def dev_run(args: argparse.Namespace, judge: Judge | None) -> int:
    host = host_for(args)
    scenario = SCENARIOS[args.scenario]
    try:
        ws = new_workspace(host, args.scenario)
    except RunnerFailure as failure:  # no Copilot work directory: nothing was made
        emit(failure_summary(args, failure, None), args.summary_log)
        return failure.status
    # the isolated config's linked credentials are as reachable for the child as
    # ~/.claude is in ambient mode, and a refresh the child performs is written
    # back to them; a Claude judge reuses the same config, after L1. A Codex run
    # executes in the Codex harness home, and its judge gets a Claude config of
    # its own once the Codex child has exited (`judged`)
    stack = ExitStack()
    config, chat = None, ""
    try:
        try:
            config = host.isolation(stack, args)
            stage(scenario, ws, install_skill=not args.no_skill, skill_dir=host.skill_dir)
            run_args = with_search_path(args, checked_search_path(args, scenario, stack, config))
            request = served_request(scenario, stack)
            events = host.run(ws, request, run_args, config)
            events = follow_up(run_args, scenario, ws, events, config)
            save_events(events, ws)
            chat = host.read(events, args).final_text
            out, status = completed_run(args, judge, scenario, ws, request, events, config)
        except RunnerFailure as failure:
            if failure.events:
                save_events(failure.events, ws)
            out, status = failure_summary(args, failure, config), failure.status
        except Exception as exc:  # a crash still leaves its line in the summary log
            traceback.print_exc()
            failure = RunnerFailure(f"runner crashed: {exc!r}")
            out, status = failure_summary(args, failure, config), failure.status
        emit(out, args.summary_log)
        if chat:
            print("\n--- chat tail ---\n" + chat[-1200:])
        return status
    finally:
        stack.close()
        if args.keep:
            print(f"\nworkspace kept: {ws}")
        else:
            shutil.rmtree(ws, ignore_errors=True)


def copilot_preflight_only(args: argparse.Namespace) -> int:
    """`--preflight-only` on Copilot: stage the scenario, run and print every
    check before the run (`copilot_cli.preflight_report`), delete the
    workspace. A recorded stop and the operator's go (read for the canary or
    a skill run) are printed and do not decide the outcome.
    Exit 0 when every other check passes, 3 otherwise (a held run lock and a
    refused child environment included); no prompt-mode child. The
    workspace is made in the Copilot work directory, as a run's is; the
    canary's holds only its placeholder skill, as its run's does
    (`copilot_cli.stage_canary_skill`)."""
    scenario = SCENARIOS.get(args.scenario, {})
    try:
        ws = new_workspace(HOSTS["copilot"], args.scenario)
    except RunnerFailure as failure:
        print(failure.message, file=sys.stderr)
        return EXIT_UNTESTED
    try:
        if args.scenario != CANARY:
            stage(scenario, ws, install_skill=not args.no_skill,
                  skill_dir=HOSTS["copilot"].skill_dir)
        try:
            checks, ready = copilot_cli.preflight_report(ws, scenario, model=args.model,
                                                         effort=args.effort,
                                                         canary=args.scenario == CANARY)
        except host_login.RunLockRefused as busy:
            print(refusal(busy.problem), file=sys.stderr)
            return EXIT_UNTESTED
        except copilot_cli.CopilotRefused as refused:
            print(refused.message, file=sys.stderr)
            return EXIT_UNTESTED
        for check in checks:
            verdict = "ok" if check.problem is None else (
                "recorded" if check.name in copilot_cli.NOT_DECIDING else "REFUSED")
            print(f"{check.name}: {verdict} — {check.detail}")
            if check.problem is not None:
                print(f"  {refusal(check.problem)}")
        print(f"preflight: {'ready' if ready else 'not ready'}")
        return EXIT_PASS if ready else EXIT_UNTESTED
    finally:
        shutil.rmtree(ws, ignore_errors=True)


def claude_preflight_only(args: argparse.Namespace) -> int:
    """`--preflight-only` on Claude, for a scenario with hidden or required
    tools: build the run's PATH and check every precondition under the
    environment the run would get (the isolated allowlist with `--isolated`,
    else the ambient one), print each finding, and start no host. Exit 0 when
    every precondition holds, 3 when one does not, 4 where hiding cannot run."""
    scenario = SCENARIOS[args.scenario]
    # never created: the isolated allowlist names a configuration directory,
    # which no shell the check starts reads
    config = Path(tempfile.gettempdir()) / "devrun-preflight-config" if args.isolated else None
    with ExitStack() as stack:
        try:
            path = search_path_for(args.scenario, scenario, stack)
            problems = precondition_problems(scenario, check_env("claude", config, path))
        except RunnerFailure as failure:
            print(failure.message, file=sys.stderr)
            return failure.status
    hidden = ", ".join(scenario.get("hide", ())) or "nothing"
    required = "; ".join(" or ".join(group) for group in scenario.get("requires", ())) or "nothing"
    print(f"hidden from the run's PATH: {hidden}")
    print(f"required on it: {required}")
    for problem in problems:
        print(f"REFUSED — {problem}")
    print(f"preflight: {'not ready' if problems else 'ready'}")
    return EXIT_UNTESTED if problems else EXIT_PASS


def preflight_only(args: argparse.Namespace) -> int:
    """`--preflight-only` on the run's host: Claude's preconditions or
    Copilot's checks before a run; no model call either way."""
    if host_for(args).name == "claude":
        return claude_preflight_only(args)
    return copilot_preflight_only(args)


def canary_summary(args: argparse.Namespace, events: list[dict],
                   failure: RunnerFailure | None, ws: Path) -> dict:
    """The canary's summary: the run's identity and telemetry (K5's
    `events_seen` among it), the outcome, every row with its word and sandbox
    report, the unanswered rows, the state of the canary's one call and the
    extra shell calls."""
    host = HOSTS["copilot"]
    view = host.read(events, args)
    status = failure.status if failure else EXIT_PASS
    return {**_identity(args, view), "host": host.name, "label": CANARY_LABEL,
            "outcome": OUTCOMES[status], "exit_status": status,
            "why": failure.message if failure else copilot_cli.CANARY_PASSED,
            "billing": failure.billing if failure else None, "config": "isolated",
            **host.label(None, True), **view.telemetry, **copilot_cli.canary_report(events),
            "workspace": str(ws) if args.keep else None}


def copilot_canary(args: argparse.Namespace) -> int:
    """`poe dev canary --host copilot --model <id> --max-ai-credits 30` (D-c):
    a workspace in the Copilot work directory, the checks before the lock,
    then `copilot_cli.run_copilot(…, canary=True)`, which writes the
    confinement probe's commands into the workspace's script, prompts the one
    command that runs it, and passes only on confirmed confinement. Exit 0
    when it passed, 3 untested (a stop is then recorded), 4 a runner failure.
    The summary prints whatever ended it."""
    try:
        ws = new_workspace(HOSTS["copilot"], CANARY)
    except RunnerFailure as failure:
        emit(failure_summary(args, failure, None), args.summary_log)
        return failure.status
    stack = ExitStack()
    events: list[dict] = []
    failure: RunnerFailure | None = None
    try:
        try:
            home = HOSTS["copilot"].isolation(stack, args)
            events = run_copilot(ws, "", args, home)
        except RunnerFailure as caught:
            failure, events = caught, caught.events
        except Exception as exc:  # a crash still leaves its line in the summary log
            traceback.print_exc()
            failure = RunnerFailure(f"runner crashed: {exc!r}")
        if events:
            save_events(events, ws)
        out = canary_summary(args, events, failure, ws)
        emit(out, args.summary_log)
        return out["exit_status"]
    finally:
        stack.close()
        if args.keep:
            print(f"\nworkspace kept: {ws}")
        else:
            shutil.rmtree(ws, ignore_errors=True)


# ---------- re-grade kept workspaces ----------------------------------------------


def load_events(ws: Path) -> list[dict]:
    path = ws / EVENTS_FILE
    return parse_events(path.read_text(encoding="utf-8")) if path.exists() else []


def kept_identity(ws: Path, args: argparse.Namespace | None = None) -> dict:
    """What served a kept run: the served model and the CLI version from the
    stream saved in its workspace, read by the host that produced it (`--host`;
    Claude without one), each as that host's reader reports a stream that does
    not say (None on Claude). A stream that cannot be read says nothing, so a
    crashed re-grade's lines still carry both fields."""
    try:
        kept = load_events(ws)
    except (OSError, UnicodeDecodeError):
        kept = []
    view = host_for(args).read(kept, args)
    return {"model": view.model, "cli_version": view.cli_version}


def rejudge_lines(args: argparse.Namespace, judge: Judge,
                  workspaces: list[Path]) -> list[dict]:
    """One summary per kept workspace. One invocation: one isolated config,
    one warm-up, and the batch projection before the fan-out; a config that
    cannot be prepared leaves every criterion untested. No model under test
    runs, on any host.

    Each line names the kept run's served model and CLI version, read from
    the stream saved in its workspace by the host that produced it (`--host`;
    `kept_identity`), beside the judge's own inside `l2`. It names no
    requested alias: the workspace does not record one, and `--model`
    defaults to `haiku`, so a re-grade of a sonnet run would be labelled haiku."""
    scenario = SCENARIOS[args.scenario]
    host = host_for(args)
    plans = [(ws, *judge_criteria(args.scenario, scenario, ws, scenario["request"]))
             for ws in workspaces]
    flat = [c for _, criteria, _ in plans for c in criteria]
    with ExitStack() as stack:
        try:
            run = run_judge(judge, flat, JUDGE.isolation(stack), projection=True)
        except RunnerFailure as failure:
            run = JudgeRun(tuple(Grade(c.name, None, failure.message) for c in flat), 0.0)
    grades = iter(run.grades)
    lines = []
    for ws, criteria, not_judged in plans:
        kept = kept_identity(ws, args)
        l2, status = l2_report(judge, [next(grades) for _ in criteria], not_judged,
                               kept["model"])
        lines.append({"scenario": args.scenario, "mode": "rejudge", "workspace": str(ws),
                      "host": host.name, "label": host.run_label, **kept, **l2,
                      "outcome": OUTCOMES[status], "exit_status": status})
    return lines


def rejudge(args: argparse.Namespace, judge: Judge) -> int:
    """Re-grade kept workspaces of the scenario with the current rubric and
    request text, never running the model under test. A crash is a runner
    failure with one summary line per workspace, as a dev run's is."""
    workspaces = list(args.rejudge)
    missing = [str(ws) for ws in workspaces if not ws.is_dir()]
    if missing:
        print(f"--rejudge: not a kept workspace: {', '.join(missing)}", file=sys.stderr)
        return EXIT_USAGE
    try:
        lines = rejudge_lines(args, judge, workspaces)
    except Exception as exc:  # a crash still leaves its lines in the summary log
        traceback.print_exc()
        failure = RunnerFailure(f"runner crashed: {exc!r}")
        lines = [{"scenario": args.scenario, "mode": "rejudge", "workspace": str(ws),
                  **kept_identity(ws, args), "outcome": OUTCOMES[failure.status],
                  "exit_status": failure.status, "why": failure.message} for ws in workspaces]
    for line in lines:
        emit(line, args.summary_log)
    return aggregate_status([line["exit_status"] for line in lines])


# ---------- the closing summary of a sequence of runs -------------------------------


NO_LINE = ("no summary line: the step ended before recording one (a usage error, a "
           "crash outside the run, or a kill)")


def earlier_billing(log: Path | None) -> tuple[str, str] | None:
    """The scenario and reason of the first line in a summary log that carries
    `billing`, or None."""
    if log is None or not log.is_file():
        return None
    for line in parse_events(log.read_text(encoding="utf-8")):
        if line.get("billing"):
            return str(line.get("scenario")), str(line["billing"])
    return None


def billing_gate(args: argparse.Namespace) -> int | None:
    """Start no host after an earlier step of the same sequence reported
    billing other than the subscription (testing-harness spec: Smoke stops
    after a billing signal): record this step as not run, untested, and return
    its status. None when the run may proceed. A log left behind by a sequence
    that died before `--summarize` keeps refusing — fail-closed — and the
    message says how to clear it."""
    earlier = earlier_billing(args.summary_log)
    if earlier is None:
        return None
    scenario, reason = earlier
    failure = RunnerFailure(
        f"not run: {scenario} reported {reason} earlier in {args.summary_log}, and no later "
        "step starts a host after a billing signal (a log a dead sequence left behind is "
        f"cleared with --summarize {args.summary_log})", untested=True)
    emit(failure_summary(args, failure, None), args.summary_log)
    return failure.status


def summary_rows(lines: list[dict], expected: tuple[str, ...] | list[str] = ()) -> list[dict]:
    """One row per scenario — per workspace for a re-grade — from its latest
    line, in the order the scenarios first appeared; then a runner-failure row
    for each expected scenario that recorded no line at all."""
    latest: dict[tuple, dict] = {}
    for line in lines:
        why = "; ".join(part for part in (line.get("why"), line.get("l2_verdict")) if part)
        latest[(line.get("scenario"), line.get("workspace"))] = {
            "scenario": line.get("scenario"), "workspace": line.get("workspace"),
            "outcome": line.get("outcome", OUTCOMES[EXIT_RUNNER]),
            "exit_status": int(line.get("exit_status", EXIT_RUNNER)), "why": why,
        }
    rows = list(latest.values())
    seen = {row["scenario"] for row in rows}
    rows += [{"scenario": name, "workspace": None, "outcome": OUTCOMES[EXIT_RUNNER],
              "exit_status": EXIT_RUNNER, "why": NO_LINE}
             for name in dict.fromkeys(expected) if name not in seen]
    return rows


def summarize(path: Path, expected: tuple[str, ...] | list[str] = ()) -> int:
    """Print the rows of a summary log, remove it, and exit with the combined
    status: zero only when every row passed. With `expected`, a scenario that
    left no line is a runner failure — a step can exit before it records one —
    and an absent log with nothing expected means nothing ran."""
    lines = parse_events(path.read_text(encoding="utf-8")) if path.exists() else []
    rows = summary_rows(lines, expected)
    if not rows:
        print(f"no runs recorded in {path}: nothing ran")
        return EXIT_RUNNER
    print(f"\n=== {len(rows)} run(s) ===")
    for row in rows:
        where = f" [{row['workspace']}]" if row["workspace"] else ""
        print(f"  {row['outcome']:<15} {row['scenario']}{where}: {row['why'][:160]}")
    path.unlink(missing_ok=True)
    status = aggregate_status([row["exit_status"] for row in rows])
    print(f"=== {OUTCOMES[status]} ===")
    return status


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("scenario", nargs="?", choices=sorted([*SCENARIOS, CANARY]),
                        help=f"the scenario to run; `{CANARY}` (--host copilot only) is the "
                             "Copilot canary: the confinement probe's commands in one script, "
                             "run by one fixed command that is the whole prompt, no skill, the "
                             "shell alone, the minimum credit cap")
    parser.add_argument("--host", choices=sorted(HOSTS), default="claude",
                        help="the host CLI that runs the model under test (default claude); "
                             "codex runs in the Codex harness home on the ChatGPT plan quota, "
                             "copilot in the Copilot harness home on the included AI credits")
    parser.add_argument("--model", default=None,
                        help="the model under test: an alias or full ID on Claude (default "
                             "haiku); required on Codex and Copilot, passed on unchanged")
    parser.add_argument("--effort", default=None,
                        choices=list(dict.fromkeys([*copilot_cli.EFFORTS, *codex_cli.EFFORTS])),
                        help="codex or copilot only: the reasoning effort to request, from the "
                             "host's own levels; Codex's served one is checked after the run, "
                             "Copilot's must be one its model listing reports")
    parser.add_argument("--max-ai-credits", type=int, default=None, metavar="N",
                        help="copilot only, required: the client's soft AI-credit cap for the "
                             f"run, at least {copilot_cli.MIN_AI_CREDITS}")
    parser.add_argument("--preflight-only", action="store_true",
                        help="copilot: run and print every check before the run, the rosters "
                             "and the confinement probe included, and start no prompt-mode "
                             "child; claude, for a scenario with hidden or required tools: "
                             "check them, the login-shell check included, and start no host "
                             "(no model call either way)")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--keep", action="store_true", help="keep the temp workspace")
    parser.add_argument("--no-skill", action="store_true",
                        help="baseline arm: same staging and request, skill not installed")
    parser.add_argument("--max-budget-usd", type=float, default=None,
                        help="hard cost cap passed through to the host")
    parser.add_argument("--isolated", action="store_true",
                        help="run against a fresh host configuration (claude.ai opt-outs "
                             "set, credentials linked) instead of the operator's ambient one")
    parser.add_argument("--judge", action="store_true",
                        help="grade the scenario's rubric criteria with the subscription dev "
                             "judge ([roles].dev_judge); needs --isolated. Dev-runner L2, not "
                             "comparable to matrix")
    parser.add_argument("--rejudge", nargs="+", type=Path, metavar="DIR",
                        help="re-grade kept workspaces of the scenario with the dev judge, "
                             "without running the model under test")
    parser.add_argument("--max-notional", type=float, default=DEFAULT_MAX_NOTIONAL,
                        metavar="USD",
                        help="cap on the judge calls' cumulative notional cost — plan quota, "
                             "not money (default %(default).2f)")
    parser.add_argument("--summary-log", type=Path, metavar="PATH",
                        help="append the run's summary to PATH as one JSON line, failures "
                             "included (a usage error records none)")
    parser.add_argument("--summarize", type=Path, metavar="PATH",
                        help="print one row per scenario from a summary log, exit non-zero "
                             "unless every row passed, and remove the log")
    parser.add_argument("--expect", nargs="+", choices=sorted(SCENARIOS), metavar="SCENARIO",
                        help="with --summarize: the scenarios the sequence ran; one that left "
                             "no line in the log is a runner failure")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.expect and not args.summarize:
        parser.error("--expect lists the scenarios a --summarize PATH should hold")
    if not (args.summarize or args.scenario):
        parser.error("a scenario is required (or --summarize PATH)")
    problem = None if args.summarize else usage_problem(args)
    if problem:
        parser.error(problem)
    if args.model is None and not host_for(args).always_isolated:
        args.model = "haiku"  # Claude's default; an explicit model stays distinguishable
    try:
        if args.summarize:
            return summarize(args.summarize, args.expect or ())
        judge = resolve_judge(args, parser)
        stopped = billing_gate(args)
        if stopped is not None:
            return stopped
        if args.rejudge:
            return rejudge(args, judge)
        if args.preflight_only:
            return preflight_only(args)
        if args.scenario == CANARY:
            return copilot_canary(args)
        scenario = SCENARIOS[args.scenario]
        if scenario.get("install"):  # no rubric twin, so no judge reaches here
            return run_install_probe(args, scenario)
        return dev_run(args, judge)
    except Exception:  # whatever escaped the run's own handling never reads as FAIL (1)
        traceback.print_exc()
        return EXIT_RUNNER


if __name__ == "__main__":
    sys.exit(main())
