"""`scripts/validate_specs.py`: the OpenSpec gate and its long-requirement ratchet.

testing-harness spec, "OpenSpec version kept current". The CLI output under
`tests/unit/data/openspec_cli/` was printed by the real OpenSpec 1.14.1 over a
small synthetic `openspec/` tree (two long specs, one short spec, one open change
with a long ADDED requirement and two long MODIFIED ones), with the root path
trimmed out. `archived/` holds what the same version printed after archiving
that change, and `show-change-no-proposal.json` its answer to a `show` of a
change without a proposal. No test here starts `npx`: the CLI runner is replaced
by a replay of those recordings, and the tree check reads an empty-file copy of
the synthetic layout.

Recorded lengths, as OpenSpec measures them (JavaScript `String.length`):
`sample-gate` "Long rule" 612, `sample-unicode` "Long rule with a symbol" 541
(540 code points: it holds U+1D538), and the change's ADDED "Long addition" 541,
MODIFIED "Long rule" 709 and MODIFIED "Middle rule" 529 (101 in the spec). After
the archive, `sample-gate` holds those three at 709, 529 and 541.
"""

from __future__ import annotations

import copy
import json
import re
import shutil
import subprocess
import tomllib

import pytest
import validate_specs
from helpers import REPO, tracked_files

DATA = REPO / "tests" / "unit" / "data" / "openspec_cli"
LONG = "Requirement text is very long (>500 characters). Move examples and edge cases " \
       "into scenarios, or split it into separate requirements that each state one behavior."
RECORDED = {
    "specs": {
        "sample-gate": {"Long rule": 612},
        "sample-unicode": {"Long rule with a symbol": 541},
    },
    "changes": {"sample-change": {"sample-gate": {
        "Long addition": 541, "Long rule": 709, "Middle rule": 529}}},
}
ARCHIVED = {
    "specs": {
        "sample-gate": {"Long addition": 541, "Long rule": 709, "Middle rule": 529},
        "sample-unicode": {"Long rule with a symbol": 541},
    },
    "changes": {},
}
SPECS = ("sample-gate", "sample-short", "sample-unicode")
REAL_RUN_CLI = validate_specs.run_cli


def recorded(name: str) -> dict:
    return json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))


def completed(stdout: str, returncode: int = 0) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess([], returncode, stdout=stdout, stderr="")


def lay_out(root, specs=SPECS, changes=("sample-change",), archived=()) -> None:
    """The synthetic tree's layout, empty files only: what the tree check reads."""
    for spec in specs:
        (root / "openspec" / "specs" / spec).mkdir(parents=True, exist_ok=True)
        (root / "openspec" / "specs" / spec / "spec.md").touch()
    for change in changes:
        delta = root / "openspec" / "changes" / change / "specs" / "sample-gate"
        delta.mkdir(parents=True, exist_ok=True)
        (delta / "spec.md").touch()
    for change in archived:
        (root / "openspec" / "changes" / "archive" / change).mkdir(parents=True, exist_ok=True)


class ReplayCli:
    """Serves the recorded output for the commands the gate runs. `validate`
    exits as 1.14.1 does: 1 when an item is invalid, 0 otherwise, unless a
    test sets `code`; a `show` answering with a status error exits 1."""

    def __init__(self) -> None:
        self.validate = recorded("validate")
        self.shows = {
            ("spec", "sample-gate"): recorded("show-spec-sample-gate"),
            ("spec", "sample-unicode"): recorded("show-spec-sample-unicode"),
            ("change", "sample-change"): recorded("show-change-sample-change"),
        }
        self.calls: list[list[str]] = []
        self.raw: str | None = None
        self.code: int | None = None
        self.guard = None

    def archive(self) -> None:
        """What 1.14.1 printed after `openspec archive sample-change`."""
        self.validate = recorded("archived/validate")
        self.shows = {
            ("spec", "sample-gate"): recorded("archived/show-spec-sample-gate"),
            ("spec", "sample-unicode"): recorded("show-spec-sample-unicode"),
        }

    def __call__(self, args: list[str], _root) -> subprocess.CompletedProcess:
        self.calls.append(list(args))
        if args[0] == "validate":
            if self.raw is not None:
                return completed(self.raw, 1 if self.code is None else self.code)
            code = int(not all(i["valid"] for i in self.validate["items"]))
            return completed(json.dumps(self.validate), code if self.code is None else self.code)
        kind = args[args.index("--type") + 1]
        shown = self.shows[(kind, args[1])]
        return completed(json.dumps(shown), 1 if "status" in shown else 0)

    def item(self, item_id: str) -> dict:
        return next(i for i in self.validate["items"] if i["id"] == item_id)


@pytest.fixture(autouse=True)
def cli(monkeypatch, tmp_path) -> ReplayCli:
    """Every test replays the recordings over the synthetic layout; L0 never
    starts the OpenSpec CLI. The two tests of the runner itself put the real
    one back and stub what it starts."""
    replay = ReplayCli()
    replay.guard = validate_specs.run_cli  # tests/conftest.py's, checked below
    monkeypatch.setattr(validate_specs, "run_cli", replay)
    lay_out(tmp_path)
    return replay


@pytest.fixture
def archived(cli, tmp_path) -> ReplayCli:
    """The tree after `openspec archive sample-change`."""
    cli.archive()
    shutil.rmtree(tmp_path / "openspec" / "changes" / "sample-change")
    lay_out(tmp_path, specs=(), changes=(), archived=("2026-10-14-sample-change",))
    return cli


def write_baseline(tmp_path, baseline: dict | None):
    path = tmp_path / "long-requirements.json"
    if baseline is not None:
        path.write_text(json.dumps(baseline), encoding="utf-8")
    return path


def gate(tmp_path, baseline: dict | None, *extra: str) -> tuple[int, object]:
    path = write_baseline(tmp_path, baseline)
    code = validate_specs.main(["--root", str(tmp_path), "--baseline", str(path), *extra])
    return code, path


def without(baseline: dict, *keys: str) -> dict:
    trimmed = copy.deepcopy(baseline)
    *parents, last = keys
    node = trimmed
    for key in parents:
        node = node[key]
    del node[last]
    return trimmed


def lines_with(out: str, *words: str) -> list[str]:
    return [line for line in out.splitlines() if all(w in line for w in words)]


def written(path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if k != "about"}


# ---------- the ratchet ------------------------------------------------------------


def test_the_recorded_tree_passes_against_its_baseline(tmp_path, capsys):
    code, _ = gate(tmp_path, RECORDED)
    out = capsys.readouterr().out
    assert code == 0, out
    assert f"OpenSpec {validate_specs.OPENSPEC_VERSION}" in out
    assert "5 long requirements" in out
    assert not lines_with(out, "note")


def test_a_new_long_requirement_in_a_spec_fails(tmp_path, capsys):
    code, _ = gate(tmp_path, without(RECORDED, "specs", "sample-gate", "Long rule"))
    out = capsys.readouterr().out
    assert code == 1
    assert lines_with(out, "FAIL", "new", "specs sample-gate", '"Long rule"', "612")


def test_a_new_long_requirement_in_a_change_fails(tmp_path, capsys):
    code, _ = gate(tmp_path, without(RECORDED, "changes", "sample-change"))
    out = capsys.readouterr().out
    assert code == 1
    assert lines_with(out, "FAIL", "new", "changes/sample-change", "sample-gate", '"Long addition"')


def test_a_grown_requirement_fails_naming_both_lengths_and_both_ways_out(tmp_path, capsys):
    baseline = copy.deepcopy(RECORDED)
    baseline["specs"]["sample-gate"]["Long rule"] = 600
    code, _ = gate(tmp_path, baseline)
    out = capsys.readouterr().out
    assert code == 1
    grew, = lines_with(out, "FAIL", "grew", "specs sample-gate", '"Long rule"')
    assert all(word in grew for word in ("612", "600", "shorten",
                                         "openspec/long-requirements.json")), grew


def test_shorter_and_gone_entries_are_reported_and_pass(tmp_path, capsys):
    baseline = copy.deepcopy(RECORDED)
    baseline["specs"]["sample-gate"]["Long rule"] = 650
    baseline["specs"]["sample-short"] = {"Removed rule": 700}
    code, _ = gate(tmp_path, baseline)
    out = capsys.readouterr().out
    assert code == 0, out
    assert lines_with(out, "shorter", '"Long rule"', "612", "650")
    assert lines_with(out, "gone", "sample-short", '"Removed rule"')
    assert "--update-baseline" in out
    assert not lines_with(out, "FAIL")


def test_an_archived_requirement_keeps_its_entry(tmp_path, capsys):
    """The ADDED requirement left its change for the specs: matched by
    capability and name, reported as moved."""
    baseline = without(RECORDED, "specs", "sample-gate", "Long rule")
    baseline["changes"]["old-change"] = {"sample-gate": {"Long rule": 612}}
    code, _ = gate(tmp_path, baseline)
    out = capsys.readouterr().out
    assert code == 0, out
    assert lines_with(out, "moved", "specs sample-gate", '"Long rule"', "changes/old-change")


def test_a_moved_requirement_that_grew_still_fails(tmp_path, capsys):
    baseline = without(RECORDED, "specs", "sample-gate", "Long rule")
    baseline["changes"]["old-change"] = {"sample-gate": {"Long rule": 611}}
    code, _ = gate(tmp_path, baseline)
    assert code == 1
    assert lines_with(capsys.readouterr().out, "FAIL", "grew", '"Long rule"')


# ---------- MODIFIED text, judged before the archive writes it ------------------------


def test_a_modified_requirement_without_its_own_entry_answers_to_the_spec_entry(tmp_path, capsys):
    """MODIFIED text draws no warning from OpenSpec, but an archive writes it
    into the spec: a delta that lengthens a baselined requirement fails while
    it is written."""
    code, _ = gate(tmp_path, without(RECORDED, "changes", "sample-change", "sample-gate",
                                     "Long rule"))
    out = capsys.readouterr().out
    assert code == 1
    grew, = lines_with(out, "FAIL", "grew", '"Long rule"')
    assert all(word in grew for word in ("changes/sample-change", "709", "612")), grew


def test_a_modified_requirement_made_long_fails_as_new(tmp_path, capsys):
    code, _ = gate(tmp_path, without(RECORDED, "changes", "sample-change", "sample-gate",
                                     "Middle rule"))
    out = capsys.readouterr().out
    assert code == 1
    assert lines_with(out, "FAIL", "new", "changes/sample-change", '"Middle rule"', "529")


def test_a_modified_requirement_within_the_spec_entry_passes(tmp_path, capsys):
    baseline = without(RECORDED, "changes", "sample-change", "sample-gate", "Long rule")
    baseline["specs"]["sample-gate"]["Long rule"] = 720
    code, _ = gate(tmp_path, baseline)
    out = capsys.readouterr().out
    assert code == 0, out
    assert lines_with(out, "note", "changes/sample-change", '"Long rule"', "entry in specs")


def test_an_open_change_does_not_loosen_the_spec_it_modifies(tmp_path, capsys):
    """While sample-change is open, its 709 for "Long rule" is the delta's
    allowance, not the spec's: the spec still answers to its own entry."""
    baseline = copy.deepcopy(RECORDED)
    baseline["specs"]["sample-gate"]["Long rule"] = 600
    code, _ = gate(tmp_path, baseline)
    out = capsys.readouterr().out
    assert code == 1
    assert lines_with(out, "FAIL", "grew", "specs sample-gate", '"Long rule"', "612", "600")
    assert not lines_with(out, "FAIL", "changes/sample-change")


@pytest.mark.usefixtures("archived")
def test_archiving_the_change_keeps_the_gate_green(tmp_path, capsys):
    """The archive wrote 709 over the spec's 612: the requirement answers to its
    change's entry, the larger, and every change entry is reported as moved."""
    code, _ = gate(tmp_path, RECORDED)
    out = capsys.readouterr().out
    assert code == 0, out
    for name in ("Long addition", "Long rule", "Middle rule"):
        assert lines_with(out, "moved", "specs sample-gate", f'"{name}"',
                          "changes/sample-change"), name
    assert not lines_with(out, "gone")
    assert not lines_with(out, "FAIL")


@pytest.mark.usefixtures("archived")
def test_archiving_a_change_whose_text_grew_after_its_entry_fails(tmp_path, capsys):
    baseline = copy.deepcopy(RECORDED)
    baseline["changes"]["sample-change"]["sample-gate"]["Long rule"] = 700
    code, _ = gate(tmp_path, baseline)
    assert code == 1
    assert lines_with(capsys.readouterr().out, "FAIL", "grew", '"Long rule"', "709", "700")


@pytest.mark.usefixtures("archived")
def test_update_after_the_archive_relocates_every_entry(tmp_path):
    code, path = gate(tmp_path, RECORDED, "--update-baseline")
    assert code == 0
    assert written(path) == ARCHIVED


# ---------- other findings ---------------------------------------------------------


@pytest.mark.parametrize("issue", [
    {"level": "ERROR", "path": "file", "message": "Spec must have a Purpose section"},
    {"level": "WARNING", "path": "requirements[0].scenarios",
     "message": "Requirement must have at least one scenario"},
    {"level": "WARNING", "path": "overview", "message": "Purpose section is too brief"},
    {"level": "error", "path": "file", "message": "A level spelled in lower case"},
    {"level": "NOTICE", "path": "file", "message": "A level this gate has never seen"},
    {"path": "file", "message": "An issue without a level"},
])
def test_any_other_finding_fails_whatever_the_baseline_holds(cli, tmp_path, capsys, issue):
    cli.item("sample-short")["issues"].append(issue)
    code, _ = gate(tmp_path, RECORDED)
    out = capsys.readouterr().out
    assert code == 1
    assert lines_with(out, "FAIL", "sample-short", issue["message"])


def test_an_info_issue_is_shown_and_fails_nothing(cli, tmp_path, capsys):
    cli.item("sample-short")["issues"].append(
        {"level": "INFO", "path": "file", "message": "Consider adding more scenarios"})
    code, _ = gate(tmp_path, RECORDED)
    out = capsys.readouterr().out
    assert code == 0, out
    assert lines_with(out, "note", "sample-short", "Consider adding more scenarios")


@pytest.mark.parametrize("issues", [
    [],
    [{"level": "INFO", "path": "file", "message": "Consider adding more scenarios"}],
])
def test_an_item_invalid_without_an_error_or_warning_fails(cli, tmp_path, capsys, issues):
    cli.item("sample-short")["valid"] = False
    cli.item("sample-short")["issues"] = issues
    code, _ = gate(tmp_path, RECORDED)
    out = capsys.readouterr().out
    assert code == 1
    assert lines_with(out, "FAIL", "spec sample-short", "invalid")


@pytest.mark.parametrize(("item", "issue", "why"), [
    ("sample-gate", {"level": "WARNING", "path": "requirements[7]", "message": LONG},
     "no requirement 7"),
    ("sample-gate", {"level": "WARNING", "path": "requirements[0]", "message": LONG},
     "65 characters"),
    ("sample-change", {"level": "WARNING", "path": "sample-gate/spec.md",
                       "message": f'ADDED "Ghost rule": {LONG}'}, "no ADDED"),
    ("sample-change", {"level": "WARNING", "path": "elsewhere/spec.md",
                       "message": f'ADDED "Long addition": {LONG}'}, "no ADDED"),
    ("sample-change", {"level": "WARNING", "path": "sample-gate/spec.md",
                       "message": f'ADDED "Long rule": {LONG}'}, "no ADDED"),
    ("sample-gate", {"level": "WARNING", "path": "requirements",
                     "message": LONG}, "unrecognized"),
])
def test_a_length_warning_that_cannot_be_matched_fails(cli, tmp_path, capsys, item, issue, why):
    cli.item(item)["issues"].append(issue)
    code, _ = gate(tmp_path, RECORDED)
    out = capsys.readouterr().out
    assert code == 1
    assert lines_with(out, "FAIL", "unmatched", item, why), out


def test_the_limit_is_read_from_the_warning(cli, tmp_path, capsys):
    """A length the CLI flags against its own limit is the length that counts."""
    gate_item = cli.item("sample-gate")
    gate_item["issues"][0]["message"] = LONG.replace(">500", ">700")
    code, _ = gate(tmp_path, RECORDED)
    assert code == 1
    assert lines_with(capsys.readouterr().out, "unmatched", "612", "700")


# ---------- the measure -------------------------------------------------------------


def test_lengths_count_utf16_code_units_as_openspec_does():
    assert validate_specs.utf16_len("a\U0001d538b") == 4
    assert validate_specs.utf16_len("Ł—é") == 3


def test_the_unicode_requirement_measures_as_javascript_does(tmp_path):
    text = recorded("show-spec-sample-unicode")["requirements"][0]["text"]
    assert len(text) == 540
    _, path = gate(tmp_path, None, "--update-baseline")
    assert written(path)["specs"]["sample-unicode"] == {"Long rule with a symbol": 541}


def test_one_validate_then_one_show_per_long_spec_and_per_change_with_deltas(cli, tmp_path):
    gate(tmp_path, RECORDED)
    assert cli.calls[0] == ["validate", "--all", "--strict", "--json", "--no-interactive"]
    shows = sorted(tuple(call) for call in cli.calls[1:])
    assert shows == [
        ("show", "sample-change", "--type", "change", "--json", "--deltas-only"),
        ("show", "sample-gate", "--type", "spec", "--json"),
        ("show", "sample-unicode", "--type", "spec", "--json"),
    ]


def test_a_change_with_deltas_is_shown_without_a_warning(cli, tmp_path, capsys):
    """Its MODIFIED text draws no warning, so the change is shown anyway."""
    cli.item("sample-change")["issues"] = []
    cli.item("sample-change")["valid"] = True
    code, _ = gate(tmp_path, without(RECORDED, "changes", "sample-change", "sample-gate",
                                     "Long addition"))
    out = capsys.readouterr().out
    assert ["show", "sample-change", "--type", "change", "--json", "--deltas-only"] in cli.calls
    assert code == 0, out
    assert "4 long requirements" in out


def test_a_change_without_delta_specs_is_not_shown(cli, tmp_path, capsys):
    """A tooling change (`skip_specs: true`) validates and has nothing to measure."""
    (tmp_path / "openspec" / "changes" / "sample-tooling").mkdir()
    cli.validate["items"].append({"id": "sample-tooling", "type": "change", "valid": True,
                                  "issues": [], "durationMs": 0})
    code, _ = gate(tmp_path, RECORDED)
    assert code == 0, capsys.readouterr().out
    assert not [call for call in cli.calls if "sample-tooling" in call]


# ---------- the gate cannot run --------------------------------------------------------


def test_cli_output_that_is_not_json_exits_2(cli, tmp_path, capsys):
    cli.raw = "npm ERR! network unreachable\n"
    code, _ = gate(tmp_path, RECORDED)
    assert code == 2
    assert "no JSON" in capsys.readouterr().err


@pytest.mark.parametrize("report", [
    {"items": "none"},
    {"items": [{"id": "sample-short", "type": "spec", "issues": []}]},
    {"items": [{"id": "sample-short", "type": "module", "valid": True, "issues": []}]},
    {"items": [{"id": "sample-short", "type": "spec", "valid": True, "issues": ["text"]}]},
])
def test_a_validate_report_of_the_wrong_shape_exits_2(cli, tmp_path, capsys, report):
    cli.raw = json.dumps(report)
    code, _ = gate(tmp_path, RECORDED)
    assert code == 2
    assert "items" in capsys.readouterr().err


@pytest.mark.parametrize("update", [(), ("--update-baseline",)])
def test_a_report_that_validated_nothing_exits_2_and_writes_nothing(cli, tmp_path, capsys,
                                                                     update):
    """What 1.14.1 prints, with exit 0, when its discovery finds nothing."""
    cli.raw = json.dumps({"items": [], "summary": {"totals": {"items": 0, "passed": 0,
                                                              "failed": 0}},
                          "version": "1.0", "root": {"path": "/synthetic", "source": "nearest"}})
    cli.code = 0
    code, path = gate(tmp_path, RECORDED, *update)
    assert code == 2
    assert "validated nothing" in capsys.readouterr().err
    assert written(path) == RECORDED


def test_an_empty_tree_exits_2(cli, tmp_path, capsys):
    shutil.rmtree(tmp_path / "openspec")
    cli.raw, cli.code = json.dumps({"items": []}), 0
    code, _ = gate(tmp_path, RECORDED)
    assert code == 2
    assert "validated nothing" in capsys.readouterr().err


@pytest.mark.parametrize("update", [(), ("--update-baseline",)])
def test_a_report_missing_an_item_of_the_tree_exits_2(cli, tmp_path, capsys, update):
    cli.validate["items"] = [i for i in cli.validate["items"] if i["id"] != "sample-unicode"]
    code, path = gate(tmp_path, RECORDED, *update)
    err = capsys.readouterr().err
    assert code == 2
    assert "missing spec sample-unicode" in err
    assert written(path) == RECORDED


def test_a_report_naming_an_item_the_tree_lacks_exits_2(tmp_path, capsys):
    (tmp_path / "openspec" / "specs" / "sample-short" / "spec.md").unlink()
    code, _ = gate(tmp_path, RECORDED)
    err = capsys.readouterr().err
    assert code == 2
    assert "not in the tree: spec sample-short" in err


def test_the_tree_check_finds_specs_as_openspec_does(tmp_path):
    """Nested capability folders count, dot entries and a spec.md at the top do not,
    and a change is any directory but `archive` and dot directories."""
    specs = tmp_path / "openspec" / "specs"
    (specs / "area" / "nested").mkdir(parents=True)
    (specs / "area" / "nested" / "spec.md").touch()
    (specs / ".hidden").mkdir()
    (specs / ".hidden" / "spec.md").touch()
    (specs / "spec.md").touch()
    (specs / "no-spec").mkdir()
    changes = tmp_path / "openspec" / "changes"
    (changes / ".draft").mkdir()
    (changes / "stray.md").touch()
    lay_out(tmp_path, specs=(), changes=(), archived=("2026-01-01-old",))
    assert validate_specs.tree_items(tmp_path) == {
        ("spec", "area/nested"), *(("spec", s) for s in SPECS), ("change", "sample-change")}


@pytest.mark.parametrize(("code", "why"), [(0, "exited 0"), (3, "exited 3")])
def test_an_exit_status_the_report_contradicts_exits_2(cli, tmp_path, capsys, code, why):
    cli.code = code
    status, _ = gate(tmp_path, RECORDED)
    assert status == 2
    assert why in capsys.readouterr().err


def test_a_refused_change_show_exits_2_with_the_cli_message_and_the_reason(cli, tmp_path, capsys):
    """`validate` accepts a change without a proposal; `show` does not."""
    cli.shows[("change", "sample-change")] = recorded("show-change-no-proposal")
    code, _ = gate(tmp_path, RECORDED)
    err = capsys.readouterr().err
    assert code == 2
    assert 'Change "sample-change" has no proposal.md yet' in err
    assert "proposal.md with its ## Why and ## What Changes sections" in err


def test_a_refused_spec_show_exits_2_with_the_cli_message(cli, tmp_path, capsys):
    cli.shows[("spec", "sample-gate")] = {"status": [
        {"severity": "error", "code": "show_error", "message": "Spec 'sample-gate' not found"}]}
    code, _ = gate(tmp_path, RECORDED)
    err = capsys.readouterr().err
    assert code == 2
    assert "Spec 'sample-gate' not found" in err
    assert "proposal" not in err


def test_a_missing_baseline_exits_2_and_says_how_to_record_one(cli, tmp_path, capsys):
    code, _ = gate(tmp_path, None)
    assert code == 2
    assert "--update-baseline" in capsys.readouterr().err
    assert cli.calls == []


def test_a_malformed_baseline_exits_2(tmp_path, capsys):
    code, _ = gate(tmp_path, {"specs": {"sample-gate": {"Long rule": "612"}}, "changes": {}})
    assert code == 2
    assert "baseline" in capsys.readouterr().err


def test_missing_npx_exits_2(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(validate_specs, "run_cli", REAL_RUN_CLI)
    monkeypatch.setattr(validate_specs.shutil, "which", lambda _name: None)
    monkeypatch.setattr(validate_specs.subprocess, "run",
                        lambda *_a, **_k: pytest.fail("nothing may start without npx"))
    code, _ = gate(tmp_path, RECORDED)
    assert code == 2
    assert "npx" in capsys.readouterr().err


def test_the_gate_runs_the_pinned_cli_quietly(monkeypatch, tmp_path):
    """The pinned package, from the root, with telemetry and the update check off,
    so a run neither phones home nor writes the user's global OpenSpec config."""
    seen = []

    def run(argv, **kwargs):
        seen.append((argv, kwargs))
        return completed("{}")

    monkeypatch.setattr(validate_specs.shutil, "which", lambda _name: "/opt/node/bin/npx")
    monkeypatch.setattr(validate_specs.subprocess, "run", run)
    REAL_RUN_CLI(["validate", "--all"], tmp_path)
    (argv, kwargs), = seen
    assert argv == ["/opt/node/bin/npx", "-y",
                    f"@fission-ai/openspec@{validate_specs.OPENSPEC_VERSION}", "validate", "--all"]
    assert kwargs["cwd"] == tmp_path
    assert kwargs["encoding"] == "utf-8"
    assert kwargs["env"]["OPENSPEC_TELEMETRY"] == "0"
    assert kwargs["env"]["OPENSPEC_NO_UPDATE_CHECK"] == "1"


def test_the_cli_runner_is_refused_inside_l0(cli, tmp_path, monkeypatch):
    """What this file's replay replaced: the suite-wide guard, so a test
    elsewhere that reaches the gate fails loudly instead of starting npx."""
    monkeypatch.setattr(validate_specs.subprocess, "run",
                        lambda *_a, **_k: pytest.fail("the guard let a CLI run start"))
    with pytest.raises(AssertionError, match="L0 never starts the OpenSpec CLI"):
        cli.guard(["validate", "--all"], tmp_path)


# ---------- --update-baseline only tightens ----------------------------------------------


def test_update_records_shorter_lengths_and_drops_gone_entries(tmp_path):
    baseline = copy.deepcopy(RECORDED)
    baseline["specs"]["sample-gate"]["Long rule"] = 650
    baseline["specs"]["sample-short"] = {"Removed rule": 700}
    code, path = gate(tmp_path, baseline, "--update-baseline")
    assert code == 0
    assert written(path) == RECORDED


def test_update_relocates_a_moved_entry(tmp_path):
    baseline = without(RECORDED, "specs", "sample-gate", "Long rule")
    baseline["changes"]["old-change"] = {"sample-gate": {"Long rule": 612}}
    _, path = gate(tmp_path, baseline, "--update-baseline")
    assert written(path)["specs"]["sample-gate"]["Long rule"] == 612
    assert "old-change" not in written(path)["changes"]


def test_update_records_a_modified_requirement_under_its_change(tmp_path):
    baseline = without(RECORDED, "changes", "sample-change", "sample-gate", "Long rule")
    baseline["specs"]["sample-gate"]["Long rule"] = 720
    code, path = gate(tmp_path, baseline, "--update-baseline")
    assert code == 0
    assert written(path) == RECORDED


def test_update_never_adds_or_lengthens_an_entry(tmp_path, capsys):
    """Nothing for the new ADDED and MODIFIED requirements, and the grown spec
    requirement and the MODIFIED delta that answers to its entry leave that
    entry as it was."""
    baseline = without(RECORDED, "changes", "sample-change")
    baseline["specs"]["sample-gate"]["Long rule"] = 600
    code, path = gate(tmp_path, baseline, "--update-baseline")
    assert code == 1
    assert written(path)["specs"]["sample-gate"] == {"Long rule": 600}
    assert written(path)["changes"] == {}
    assert lines_with(capsys.readouterr().out, "FAIL", "grew")


def test_update_keeps_a_grown_requirement_entry_where_it_is(tmp_path):
    baseline = without(RECORDED, "specs", "sample-gate", "Long rule")
    baseline["changes"]["old-change"] = {"sample-gate": {"Long rule": 611}}
    code, path = gate(tmp_path, baseline, "--update-baseline")
    assert code == 1
    assert written(path)["changes"]["old-change"] == {"sample-gate": {"Long rule": 611}}
    assert "sample-gate" not in written(path)["specs"]


def test_update_refuses_while_another_finding_stands(cli, tmp_path, capsys):
    """A spec that fails to parse yields no length warnings; tightening then
    would drop every entry it holds."""
    cli.item("sample-unicode")["issues"] = [
        {"level": "ERROR", "path": "file", "message": "Spec must have a Requirements section"}]
    code, path = gate(tmp_path, RECORDED, "--update-baseline")
    assert code == 1
    assert json.loads(path.read_text(encoding="utf-8")) == RECORDED
    assert "nothing written" in capsys.readouterr().out


def test_update_bootstraps_an_absent_baseline(tmp_path):
    code, path = gate(tmp_path, None, "--update-baseline")
    assert code == 0
    assert written(path) == RECORDED
    assert "--update-baseline" in json.loads(path.read_text(encoding="utf-8"))["about"]


def test_update_is_idempotent_and_canonical(tmp_path):
    _, path = gate(tmp_path, None, "--update-baseline")
    first = path.read_bytes()
    validate_specs.main(["--root", str(tmp_path), "--baseline", str(path), "--update-baseline"])
    assert path.read_bytes() == first
    assert first.endswith(b"}\n")
    assert b"\r\n" not in first


# ---------- the pin and the repository's baseline ------------------------------------------


def test_the_pin_is_a_plain_version():
    assert re.fullmatch(r"\d+\.\d+\.\d+", validate_specs.OPENSPEC_VERSION)


def test_the_pin_lives_in_one_place():
    """The weekly bump rewrites one line. A version spelled anywhere else would
    stay behind: as an npx spelling, as a second constant, or in prose."""
    spelled = re.compile(r"openspec@\d|OPENSPEC_VERSION = ")
    offenders = []
    for rel in sorted({*tracked_files(), "scripts/validate_specs.py"}):
        if rel.startswith("openspec/changes/") or rel.startswith("tests/"):
            continue
        try:
            text = (REPO / rel).read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
            continue
        offenders += [rel] * len(spelled.findall(text))
    assert offenders == ["scripts/validate_specs.py"]


def test_the_specs_task_runs_the_gate():
    tasks = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["poe"]
    assert tasks["tasks"]["specs"] == "python3 scripts/validate_specs.py"


def test_the_repository_baseline_is_canonical_and_long():
    path = REPO / validate_specs.BASELINE
    entries = validate_specs.load_baseline(path)
    assert entries, "the baseline records no requirement"
    assert all(length > 500 for length in entries.values())
    assert validate_specs.render_baseline(entries) == path.read_text(encoding="utf-8")
