"""L0 coverage for harness/support.py — every matrix rule without a model call."""

import sys
from pathlib import Path

import pytest
import support

REPO = Path(__file__).resolve().parents[2]

REGISTRY_TOML = """
prices_as_of = 2026-08-06
lines_reviewed_as_of = 2026-08-06

[roles]
judge = "openrouter/lab/cheapo-1"
smoke = "openrouter/lab/cheapo-1"
dev_judge = "lab-sub-2-1"
dev_judge_effort = "medium"

[[models]]
id = "openrouter/lab/cheapo-1"
family = "lab"
tier = "cheap"
input_price = 1.0
output_price = 5.0
enabled = true

[[models]]
id = "openrouter/lab/big-9"
family = "lab"
tier = "frontier"
input_price = 5.0
output_price = 25.0
enabled = true

[[models]]
id = "openrouter/lab/off-2"
family = "lab"
tier = "mid"
input_price = 2.0
output_price = 10.0
enabled = false

[tasks]
matrix = ["alpha", "beta", "dialog"]
core = ["alpha"]
heavy = ["dialog"]
dialogue = ["dialog"]
excluded_l1 = ["beta"]
excluded = ["netty"]

[tasks.priors]
default = { input = 100000, output = 10000 }
dialog = { input = 500000, output = 20000 }

[tasks.judge]
input = 40000
output = 4000

[tasks.skills]
alpha = "proposal-alpha"
beta = "proposal-beta"
dialog = "proposal-dialog"
"""


@pytest.fixture
def registry():
    return support.parse_registry(REGISTRY_TOML)


def test_parse_registry(registry):
    assert [m.id for m in registry.models] == [
        "openrouter/lab/cheapo-1",
        "openrouter/lab/big-9",
        "openrouter/lab/off-2",
    ]
    assert registry.tasks.priors["dialog"] == (500000, 20000)
    assert registry.tasks.judge_tokens == (40000, 4000)


def test_parse_registry_rejects_bad_tier():
    bad = REGISTRY_TOML.replace('tier = "cheap"', 'tier = "budget"')
    with pytest.raises(ValueError, match="tier"):
        support.parse_registry(bad)


def test_parse_registry_requires_default_prior():
    bad = REGISTRY_TOML.replace("default = ", "off_default = ")
    with pytest.raises(ValueError, match="default"):
        support.parse_registry(bad)


def test_parse_registry_rejects_matrix_excluded_overlap():
    bad = REGISTRY_TOML.replace('excluded = ["netty"]', 'excluded = ["alpha"]')
    with pytest.raises(ValueError, match="alpha"):
        support.parse_registry(bad)


def test_select_models_skips_disabled_and_filters_tier(registry):
    assert [m.id for m in support.select_models(registry)] == [
        "openrouter/lab/cheapo-1",
        "openrouter/lab/big-9",
    ]
    assert [m.id for m in support.select_models(registry, tier="frontier")] == [
        "openrouter/lab/big-9"
    ]
    assert support.select_models(registry, tier="mid") == []


def test_select_models_by_id_suffix(registry):
    assert [m.id for m in support.select_models(registry, ids=["cheapo-1"])] == [
        "openrouter/lab/cheapo-1"
    ]
    with pytest.raises(ValueError, match="off-2"):
        support.select_models(registry, ids=["off-2"])  # disabled


def test_select_tasks(registry):
    assert support.select_tasks(registry) == ["alpha", "beta", "dialog"]
    assert support.select_tasks(registry, core_only=True) == ["alpha"]
    assert support.select_tasks(registry, names=["beta"]) == ["beta"]
    with pytest.raises(ValueError, match="excluded"):
        support.select_tasks(registry, names=["netty"])
    with pytest.raises(ValueError, match="scorable"):
        support.select_tasks(registry, names=["gamma"])


def test_epochs_for_reduces_heavy_on_frontier(registry):
    cfg = registry.tasks
    assert support.epochs_for("dialog", "frontier", cfg) == 1
    assert support.epochs_for("dialog", "cheap", cfg) == 3
    assert support.epochs_for("alpha", "frontier", cfg) == 3


def test_epochs_for_tier_policy_and_cli_cap():
    reg = support.parse_registry(
        REGISTRY_TOML + "\n[tasks.epochs]\ncheap = 3\nfrontier = 1\n"
    )
    cfg = reg.tasks
    assert support.epochs_for("alpha", "frontier", cfg) == 1
    assert support.epochs_for("alpha", "cheap", cfg) == 3
    assert support.epochs_for("alpha", "cheap", cfg, default=1) == 1  # CLI caps
    assert support.epochs_for("alpha", "mid", cfg) == 3  # unlisted tier -> default
    with pytest.raises(ValueError, match=r"tasks\.epochs"):
        support.parse_registry(REGISTRY_TOML + "\n[tasks.epochs]\nbudget = 2\n")


def test_epoch_pass_ignores_l1_on_excluded_l1_task(registry):
    cfg = registry.tasks
    scores = {"beta_l1": "I", "beta_l2_quality": "C"}
    assert support.epoch_pass(scores, "beta", cfg) is True
    assert support.epoch_pass(scores, "alpha", cfg) is False
    assert support.epoch_pass({"beta_l1": "I"}, "beta", cfg) is None


def test_classify_cell_bands():
    assert support.classify_cell([]) == "untested"
    assert support.classify_cell([True, True, True]) == "solid"
    assert support.classify_cell([True, False, True]) == "flaky"
    assert support.classify_cell([False, False]) == "fail"


def test_model_verdict_priorities():
    v = support.model_verdict({"a": "solid", "b": "flaky", "c": "fail"})
    assert v.status == "failing"
    assert v.failing_tasks == ("c",)
    assert v.flaky_tasks == ("b",)
    assert support.model_verdict({"a": "solid", "b": "flaky"}).status == "flaky"
    assert support.model_verdict({"a": "solid"}).status == "supported"
    assert support.model_verdict({"a": "untested"}).status == "untested"


def test_model_verdict_partial_never_supported_with_untested_cells():
    # Spec: "supported when all scorable cells are solid" — a smoke-only run
    # must not publish an unqualified "supported".
    v = support.model_verdict({"a": "solid", "b": "untested"})
    assert v.status == "partial"
    assert v.untested_tasks == ("b",)


def test_rollup_cells_lets_the_worst_measured_result_win():
    assert support.rollup_cells(["solid", "fail"]) == "fail"
    assert support.rollup_cells(["solid", "flaky"]) == "flaky"
    assert support.rollup_cells(["solid", "solid"]) == "solid"


def test_rollup_cells_never_lets_untested_mask_a_measured_result():
    """A skill covered by two tasks, one measured and one not, is as good as its
    measurement — reporting `untested` there would hide a real failure, and
    reporting a pass would invent one."""
    assert support.rollup_cells(["fail", "untested"]) == "fail"
    assert support.rollup_cells(["solid", "untested"]) == "solid"
    assert support.rollup_cells(["untested", "untested"]) == "untested"
    assert support.rollup_cells([]) == "untested"


def test_export_support_keys_by_skill_and_drops_the_routing_prefix(registry):
    models = support.select_models(registry, ids=["cheapo-1"])
    tasks = ["alpha", "beta"]
    cells = {
        (models[0].id, "alpha"): support.Cell("fail", passes=0, epochs=3),
        (models[0].id, "beta"): support.Cell("solid", passes=3, epochs=3),
    }
    verdicts = {models[0].id: support.model_verdict({"alpha": "fail", "beta": "solid"})}
    out = support.export_support(
        models, tasks, cells, verdicts, "2026-08-06",
        skills={"alpha": "proposal-write", "beta": "proposal-check"},
    )
    key = next(iter(out["models"]))
    assert not key.startswith("openrouter/"), "the routing prefix is not part of model identity"
    record = out["models"][key]
    assert record["verdict"] == "failing"
    assert record["skills"] == {"proposal-check": "solid", "proposal-write": "fail"}
    assert record["tasks"] == {"alpha": "fail", "beta": "solid"}


def test_export_support_marks_a_never_measured_cell_untested(registry):
    """A consumer reading a blank cell as a pass would clear a model nothing is
    known about, so absence has to be explicit in the data."""
    models = support.select_models(registry, ids=["cheapo-1"])
    out = support.export_support(
        models, ["alpha"], {}, {}, "2026-08-06", skills={"alpha": "proposal-write"}
    )
    record = next(iter(out["models"].values()))
    assert record["tasks"]["alpha"] == "untested"
    assert record["skills"]["proposal-write"] == "untested"
    assert record["verdict"] == "untested"
    assert "untested" in out["statuses"], "the export documents what its statuses mean"


def test_estimate_cost_arithmetic(registry):
    models = support.select_models(registry, ids=["cheapo-1"])
    est = support.estimate_cost(models, ["alpha"], registry)
    # 3 epochs * (0.1M * $1 + 0.01M * $5) = 3 * $0.15 = $0.45
    # judge: 3 * (0.04M * $1 + 0.004M * $5) = 3 * $0.06 = $0.18
    assert est.lines[0].usd == pytest.approx(0.63)
    assert est.unknown_models == ()


def test_estimate_cost_prefers_history(registry):
    models = support.select_models(registry, ids=["cheapo-1"])
    history = {"alpha": (200000, 20000)}
    est = support.estimate_cost(models, ["alpha"], registry, history=history)
    # 3 * (0.2M * $1 + 0.02M * $5) + judge 0.18 = 0.9 + 0.18
    assert est.lines[0].usd == pytest.approx(1.08)


def test_price_usage_flags_unknown_models(registry):
    report = support.price_usage(
        {"openrouter/lab/cheapo-1": (1_000_000, 100_000), "openrouter/x/y": (5, 5)},
        registry,
    )
    assert report.lines[0].usd == pytest.approx(1.5)
    assert report.unknown_models == ("openrouter/x/y",)
    assert report.total == pytest.approx(1.5)


def test_price_usage_bills_cache_reads_at_cache_price():
    reg = support.parse_registry(
        REGISTRY_TOML.replace(
            'output_price = 5.0\nenabled = true',
            'output_price = 5.0\ncache_read_price = 0.1\nenabled = true',
            1,
        )
    )
    report = support.price_usage(
        {"openrouter/lab/cheapo-1": (100_000, 10_000, 1_000_000)}, reg
    )
    # 0.1M*$1 + 0.01M*$5 + 1M*$0.1 = 0.1 + 0.05 + 0.1
    assert report.lines[0].usd == pytest.approx(0.25)


def test_cache_read_price_defaults_to_input_price(registry):
    m = registry.models[0]
    assert m.cache_read_price == m.input_price


def test_merge_history_keeps_max():
    merged = support.merge_history({"a": (10, 5)}, {"a": (8, 9), "b": (1, 1)})
    assert merged == {"a": (10, 9), "b": (1, 1)}


README = "intro\n<!-- model-support:start -->\nold\n<!-- model-support:end -->\ntail\n"


def test_splice_readme_idempotent():
    once = support.splice_readme(README, "| new |")
    twice = support.splice_readme(once, "| new |")
    assert once == twice
    assert "old" not in once
    assert "| new |" in once
    assert once.startswith("intro\n")
    assert once.endswith("tail\n")


def test_splice_readme_requires_markers():
    with pytest.raises(ValueError, match="marker"):
        support.splice_readme("no markers here", "x")
    with pytest.raises(ValueError, match="marker"):
        support.splice_readme(README + README, "x")


def test_render_summary_shows_untested_and_flaky(registry):
    models = support.select_models(registry)
    verdicts = {"openrouter/lab/cheapo-1": support.Verdict("flaky", flaky_tasks=("beta",))}
    text = support.render_summary(models, verdicts, "2026-08-06", registry.tasks.skills)
    assert "`lab/cheapo-1`" in text
    assert "flaky on: proposal-beta" in text
    assert ": beta" not in text  # skill names, not raw task ids (spec scenario)
    assert "`lab/big-9`" in text
    assert "❔ untested" in text
    assert "2026-08-06" in text


def test_render_summary_keeps_disabled_models_visible(registry):
    text = support.render_summary(list(registry.models), {}, "2026-08-06")
    assert "`lab/off-2`" in text
    assert "disabled in registry" in text


def test_render_summary_partial_discloses_untested(registry):
    verdicts = {
        "openrouter/lab/cheapo-1": support.Verdict("partial", untested_tasks=("dialog", "beta"))
    }
    text = support.render_summary(support.select_models(registry), verdicts, "x")
    assert "🟡 partial" in text
    assert "untested on 2 task(s)" in text


def test_failing_verdict_names_skills_once(registry):
    v = support.Verdict("failing", failing_tasks=("alpha", "dialog"), flaky_tasks=("beta",))
    label, notes = support._verdict_text(v, registry.tasks.skills)
    assert label == "❌ not recommended"
    assert notes == "fails: proposal-alpha, proposal-dialog; flaky on: proposal-beta"


# cheapo-1 with a registry note; the other models stay note-free
_NOTED_TOML = REGISTRY_TOML.replace(
    "output_price = 5.0\nenabled = true",
    'output_price = 5.0\nenabled = true\nnote = "harness cannot drive it"',
)


def test_parse_registry_reads_optional_note(registry):
    noted = support.parse_registry(_NOTED_TOML)
    assert noted.models[0].note == "harness cannot drive it"
    assert noted.models[1].note == ""
    assert registry.models[0].note == ""


def test_render_summary_note_alone_on_untested_row():
    noted = support.parse_registry(_NOTED_TOML)
    text = support.render_summary(support.select_models(noted), {}, "x")
    row = next(line for line in text.splitlines() if "cheapo-1" in line)
    assert "❔ untested" in row
    assert row.endswith("| harness cannot drive it |")


def test_render_summary_note_appended_after_verdict_notes():
    noted = support.parse_registry(_NOTED_TOML)
    verdicts = {"openrouter/lab/cheapo-1": support.Verdict("failing", failing_tasks=("alpha",))}
    text = support.render_summary(
        support.select_models(noted), verdicts, "x", noted.tasks.skills
    )
    row = next(line for line in text.splitlines() if "cheapo-1" in line)
    assert "fails: proposal-alpha; harness cannot drive it" in row


def test_parse_registry_requires_skill_mapping_for_matrix_tasks():
    bad = REGISTRY_TOML.replace('alpha = "proposal-alpha"\n', "")
    with pytest.raises(ValueError, match="skills mapping"):
        support.parse_registry(bad)


def test_render_grid_marks_reduced_and_untested(registry):
    models = support.select_models(registry)
    cells = {
        ("openrouter/lab/cheapo-1", "alpha"): support.Cell("solid", 3, 3),
        ("openrouter/lab/big-9", "dialog"): support.Cell("flaky", 1, 1, reduced=True),
    }
    text = support.render_grid(
        models, ["alpha", "dialog"], cells,
        {"openrouter/lab/cheapo-1": 1.5}, "2026-08-06",
    )
    assert "3/3" in text
    assert "1/1*" in text
    assert "—" in text
    assert "$1.50" in text


# --- roles table and role prices (testing-harness spec: Pinned model registry) -


def _registry_with(*pairs: tuple[str, str], extra: str = "") -> str:
    """REGISTRY_TOML with (old, new) substitutions applied once each, plus text
    appended at the end (after [tasks.skills], so new tables stay valid TOML)."""
    text = REGISTRY_TOML
    for old, new in pairs:
        assert old in text, f"fixture drifted: {old!r} not in REGISTRY_TOML"
        text = text.replace(old, new, 1)
    return text + extra


def _with_persona(persona: str) -> str:
    """REGISTRY_TOML with an explicit persona role (it defaults to the judge)."""
    anchor = 'dev_judge = "lab-sub-2-1"'
    return _registry_with((anchor, f'persona = "{persona}"\n{anchor}'))


def test_roles_parse_and_persona_defaults_to_judge(registry):
    roles = registry.roles
    assert roles.judge == "openrouter/lab/cheapo-1"
    assert roles.persona == roles.judge
    assert roles.smoke == "openrouter/lab/cheapo-1"
    assert roles.dev_judge == "lab-sub-2-1"
    assert roles.dev_judge_effort == "medium"


def test_explicit_persona_is_kept():
    reg = support.parse_registry(_with_persona("openrouter/lab/big-9"))
    assert reg.roles.persona == "openrouter/lab/big-9"
    assert reg.roles.judge == "openrouter/lab/cheapo-1"


def test_registry_dates_are_parsed(registry):
    assert registry.prices_as_of.isoformat() == "2026-08-06"
    assert registry.lines_reviewed_as_of.isoformat() == "2026-08-06"


def test_task_config_judge_model_comes_from_roles(registry):
    assert registry.tasks.judge_model == registry.roles.judge


def test_leftover_task_judge_model_points_to_roles():
    bad = _registry_with(("[tasks.judge]\n", '[tasks.judge]\nmodel = "openrouter/lab/cheapo-1"\n'))
    with pytest.raises(ValueError, match=r"\[roles\]\.judge"):
        support.parse_registry(bad)


@pytest.mark.parametrize("alias", ["sonnet", "~lab/x-latest", "lab/x-latest"])
def test_floating_alias_rejected_in_the_roster(alias):
    bad = _registry_with(('id = "openrouter/lab/off-2"', f'id = "{alias}"'))
    with pytest.raises(ValueError, match="floating alias") as err:
        support.parse_registry(bad)
    assert alias in str(err.value)


@pytest.mark.parametrize("role", ["judge", "persona", "smoke", "dev_judge"])
@pytest.mark.parametrize("alias", ["sonnet", "~lab/x-latest", "lab/x-latest"])
def test_floating_alias_rejected_in_roles(role, alias):
    if role == "persona":
        bad = _with_persona(alias)
    else:
        current = {"judge": "openrouter/lab/cheapo-1", "smoke": "openrouter/lab/cheapo-1",
                   "dev_judge": "lab-sub-2-1"}[role]
        bad = _registry_with((f'{role} = "{current}"', f'{role} = "{alias}"'))
    with pytest.raises(ValueError, match="floating alias") as err:
        support.parse_registry(bad)
    assert role in str(err.value)


@pytest.mark.parametrize("smoke", ["openrouter/lab/off-2", "openrouter/lab/nope-1"])
def test_smoke_must_name_an_enabled_roster_entry(smoke):
    bad = _registry_with(('smoke = "openrouter/lab/cheapo-1"', f'smoke = "{smoke}"'))
    with pytest.raises(ValueError, match="smoke"):
        support.parse_registry(bad)


def test_unknown_dev_judge_effort_rejected():
    bad = _registry_with(('dev_judge_effort = "medium"', 'dev_judge_effort = "turbo"'))
    with pytest.raises(ValueError, match="dev_judge_effort"):
        support.parse_registry(bad)


def test_track_and_price_endpoint_are_accepted():
    reg = support.parse_registry(_registry_with(
        ('id = "openrouter/lab/big-9"',
         'id = "openrouter/lab/big-9"\ntrack = "lab/big-*"\nprice_endpoint = "labcloud"'),
        ('id = "openrouter/lab/off-2"', 'id = "openrouter/lab/off-2"\ntrack = false'),
    ))
    by_id = {m.id: m for m in reg.models}
    assert by_id["openrouter/lab/big-9"].track == "lab/big-*"
    assert by_id["openrouter/lab/big-9"].price_endpoint == "labcloud"
    assert by_id["openrouter/lab/off-2"].track is False
    assert by_id["openrouter/lab/cheapo-1"].track is True  # derived line by default
    assert by_id["openrouter/lab/cheapo-1"].price_endpoint == ""


def test_track_glob_needs_exactly_one_wildcard():
    big = 'id = "openrouter/lab/big-9"'
    bad = _registry_with((big, f'{big}\ntrack = "lab/big"'))
    with pytest.raises(ValueError, match="track"):
        support.parse_registry(bad)


def test_role_model_override_applies_to_its_own_role_only(registry):
    env = {"JUDGE_MODEL": "openrouter/lab/other-3"}
    assert support.role_model(registry.roles, "judge", env) == "openrouter/lab/other-3"
    assert support.role_model(registry.roles, "persona", env) == registry.roles.persona
    persona_env = {"PERSONA_MODEL": "openrouter/lab/other-4"}
    assert support.role_model(registry.roles, "persona", persona_env) == "openrouter/lab/other-4"
    assert support.role_model(registry.roles, "judge", persona_env) == registry.roles.judge
    assert support.role_model(registry.roles, "judge", {"JUDGE_MODEL": ""}) == registry.roles.judge
    with pytest.raises(ValueError, match="role"):
        support.role_model(registry.roles, "critic", {})


# a judge whose roster row has moved on: priced by a role-price entry
_HELD_JUDGE = (
    ('judge = "openrouter/lab/cheapo-1"', 'judge = "openrouter/lab/cheapo-0"'),
)
_HELD_PRICE = """
[role_prices."openrouter/lab/cheapo-0"]
input_price = 2.0
output_price = 8.0
cache_read_price = 0.2
"""


def test_held_judge_priced_by_role_price_entry():
    reg = support.parse_registry(_registry_with(*_HELD_JUDGE, extra=_HELD_PRICE))
    price = support.model_price(reg, "openrouter/lab/cheapo-0")
    assert (price.input_price, price.output_price, price.cache_read_price) == (2.0, 8.0, 0.2)
    assert reg.tasks.judge_model == "openrouter/lab/cheapo-0"


def test_model_price_prefers_roster_rows_including_disabled(registry):
    cheap = support.model_price(registry, "openrouter/lab/cheapo-1")
    assert (cheap.input_price, cheap.output_price) == (1.0, 5.0)
    assert cheap.cache_read_price == 1.0  # parser default: the input price
    off = support.model_price(registry, "openrouter/lab/off-2")
    assert (off.input_price, off.output_price) == (2.0, 10.0)
    assert support.model_price(registry, "openrouter/lab/ghost-1") is None


def test_estimate_cost_prices_a_held_judge_from_role_prices():
    reg = support.parse_registry(_registry_with(*_HELD_JUDGE, extra=_HELD_PRICE))
    models = support.select_models(reg, ids=["cheapo-1"])
    est = support.estimate_cost(models, ["alpha"], reg)
    # model 3 * $0.15 = $0.45; judge 3 * (0.04M * $2 + 0.004M * $8) = 3 * $0.112
    assert est.lines[0].usd == pytest.approx(0.45 + 0.336, abs=0.01)
    assert est.unknown_models == ()


def test_price_usage_prices_a_held_judge_from_role_prices():
    reg = support.parse_registry(_registry_with(*_HELD_JUDGE, extra=_HELD_PRICE))
    report = support.price_usage({"openrouter/lab/cheapo-0": (1_000_000, 0, 1_000_000)}, reg)
    assert report.lines[0].usd == pytest.approx(2.2)
    assert report.unknown_models == ()


def test_unpriced_judge_rejected_naming_the_role():
    bad = _registry_with(*_HELD_JUDGE)
    with pytest.raises(ValueError, match="judge"):
        support.parse_registry(bad)


def test_unpriced_persona_rejected_naming_the_role():
    with pytest.raises(ValueError, match="persona"):
        support.parse_registry(_with_persona("openrouter/lab/ghost-1"))


def test_orphaned_role_price_rejected_naming_the_entry():
    orphan = '\n[role_prices."openrouter/lab/orphan-1"]\ninput_price = 1.0\noutput_price = 2.0\n'
    with pytest.raises(ValueError, match="orphan-1"):
        support.parse_registry(REGISTRY_TOML + orphan)


def test_role_price_duplicating_a_roster_row_rejected():
    dup = '\n[role_prices."openrouter/lab/cheapo-1"]\ninput_price = 1.0\noutput_price = 5.0\n'
    with pytest.raises(ValueError, match="cheapo-1"):
        support.parse_registry(REGISTRY_TOML + dup)


# --- shipped registry stays coherent with the real task set -------------------


def test_shipped_registry_parses_and_covers_all_eval_tasks():
    registry = support.parse_registry(
        (REPO / "harness" / "models.toml").read_text(encoding="utf-8"))
    evals_src = (REPO / "harness" / "skill_evals.py").read_text(encoding="utf-8")
    import re

    defined = set(re.findall(r"@task\ndef (\w+)\(", evals_src))
    accounted = (
        set(registry.tasks.matrix) | set(registry.tasks.extended) | set(registry.tasks.excluded)
    )
    assert defined == accounted, (
        f"tasks drifted: missing from models.toml {sorted(defined - accounted)}, "
        f"stale in models.toml {sorted(accounted - defined)}"
    )
    assert set(registry.tasks.core) <= set(registry.tasks.matrix)
    assert set(registry.tasks.heavy) <= set(registry.tasks.matrix)
    assert set(registry.tasks.excluded_l1) <= set(registry.tasks.matrix)
    assert not set(registry.tasks.extended) & set(registry.tasks.matrix)


REGENERATE = "uv run poe report` and `python3 scripts/sync_shared.py"


def shipped_roster_mismatch(
    registry_path: Path = REPO / "harness" / "models.toml",
    support_path: Path = REPO / "shared" / "model-support.json",
    readme_path: Path = REPO / "README.md",
) -> dict[str, set[str]]:
    """Per shipped artifact, the IDs it lists beyond the roster ("extra") and
    the roster IDs it lacks ("missing"), routing prefix dropped as the report
    drops it."""
    import json
    import re

    registry = support.parse_registry(registry_path.read_text(encoding="utf-8"))
    roster = {m.id.removeprefix("openrouter/") for m in registry.models}
    shipped = {
        "shared/model-support.json":
            set(json.loads(support_path.read_text(encoding="utf-8"))["models"]),
    }
    readme = readme_path.read_text(encoding="utf-8")
    region = readme.split(support.START_MARKER, 1)[1].split(support.END_MARKER, 1)[0]
    shipped["README.md summary"] = set(re.findall(r"^\| `([^`]+)` \|", region, re.MULTILINE))
    mismatch = {}
    for name, ids in shipped.items():
        mismatch[f"{name} extra"] = ids - roster
        mismatch[f"{name} missing"] = roster - ids
    return {k: v for k, v in mismatch.items() if v}


def test_shipped_verdicts_list_exactly_the_registry_roster():
    """A roster edit cannot reach main until the report is regenerated: a bump
    PR is red here until the maintainer regenerates the verdicts from the logs,
    which only their machine holds (`logs/` is gitignored)."""
    mismatch = shipped_roster_mismatch()
    assert not mismatch, (
        f"shipped verdicts list a different model set than harness/models.toml: {mismatch} — "
        f"outgoing IDs are extra, incoming ones missing. Regenerate on the machine that holds "
        f"logs/evals/: `{REGENERATE}`"
    )


def test_shipped_verdict_check_catches_an_unregenerated_bump(tmp_path):
    registry = (REPO / "harness" / "models.toml").read_text(encoding="utf-8")
    parsed = support.parse_registry(registry)
    named_by_roles = {parsed.roles.judge, parsed.roles.persona, parsed.roles.smoke}
    first = next(m.id for m in parsed.models if m.id not in named_by_roles)
    bumped = tmp_path / "models.toml"
    bumped.write_text(registry.replace(f'id = "{first}"', f'id = "{first}-next"'), encoding="utf-8")
    mismatch = shipped_roster_mismatch(registry_path=bumped)
    short = first.removeprefix("openrouter/")
    assert mismatch["shared/model-support.json extra"] == {short}
    assert mismatch["shared/model-support.json missing"] == {f"{short}-next"}
    assert mismatch["README.md summary extra"] == {short}


def test_select_tasks_allows_extended_by_name_only():
    reg = support.parse_registry(
        REGISTRY_TOML.replace('matrix = ["alpha", "beta", "dialog"]',
                              'matrix = ["alpha", "beta"]\nextended = ["dialog"]')
    )
    assert support.select_tasks(reg) == ["alpha", "beta"]
    assert support.select_tasks(reg, names=["dialog"]) == ["dialog"]


# --- cost gate (spec: estimate shown and declined -> no metered call) ---------


OFFLINE_GATE = "model currency unknown (catalog unreachable: network disabled in L0 tests)"


def test_matrix_gate_declined_makes_no_metered_call(monkeypatch, capsys):
    import matrix

    monkeypatch.setattr("builtins.input", lambda _: "n")
    monkeypatch.setitem(sys.modules, "inspect_ai", object())  # any import attempt breaks
    assert matrix.main([]) == 1
    out = capsys.readouterr().out
    assert "Estimated cost" in out
    assert "aborted before any metered call" in out
    assert OFFLINE_GATE in out, "the conftest fixture reaches the gate: no live request"


def test_matrix_estimate_only_exits_clean(monkeypatch, capsys):
    import matrix

    monkeypatch.setitem(sys.modules, "inspect_ai", object())
    assert matrix.main(["--estimate-only", "--tier", "cheap"]) == 0
    out = capsys.readouterr().out
    assert "TOTAL" in out
    assert OFFLINE_GATE in out


# The gate tests that assert stale pins replay the recorded catalog and live in
# test_model_currency.py, the one test file whose model IDs are snapshot facts.


def _refuse(*_request):
    raise OSError("catalog down")


def test_gate_offline_warns_and_keeps_the_exit_status(monkeypatch, capsys):
    import matrix

    monkeypatch.setitem(sys.modules, "inspect_ai", object())
    monkeypatch.setattr(matrix.model_currency, "fetch_json", _refuse)
    assert matrix.main(["--estimate-only", "--tier", "cheap"]) == 0
    assert "model currency unknown (catalog unreachable: catalog down)" in capsys.readouterr().out


# ---------- baseline arm (testing-harness spec: Baseline comparison arm) ------


def test_dialogue_tasks_parsed(registry):
    assert registry.tasks.dialogue == ("dialog",)


def test_select_baseline_tasks_drops_dialogue_from_a_default_selection(registry):
    assert support.select_baseline_tasks(registry, ["alpha", "beta", "dialog"]) == [
        "alpha", "beta",
    ]


def test_select_baseline_tasks_rejects_an_explicitly_named_dialogue_task(registry):
    with pytest.raises(ValueError, match="no baseline arm"):
        support.select_baseline_tasks(registry, ["alpha", "dialog"], explicit=True)


def _arm(passes, scorer_passes, tokens, duration=None):
    return support.ArmStats(
        passes=tuple(passes),
        scorer_passes={k: tuple(v) for k, v in scorer_passes.items()},
        tokens=tokens,
        duration_s=duration,
    )


def test_baseline_delta_shows_what_the_skill_buys_and_costs(registry):
    pairs = {
        ("openrouter/lab/cheapo-1", "alpha"): (
            _arm([True, True], {"alpha_l1": [True, True]}, 5000, 60.0),
            _arm([False, False], {"alpha_l1": [False, False]}, 2000, 30.0),
        )
    }
    text = support.render_baseline_delta(pairs, registry.tasks.skills)
    assert "1.00 / 0.00 / +1.00" in text
    assert "5000 / 2000 / +3000" in text
    assert "60 / 30" in text


def test_baseline_delta_flags_dead_and_too_hard_assertions(registry):
    pairs = {
        ("openrouter/lab/cheapo-1", "alpha"): (
            _arm([True], {"dead_l1": [True], "hard_l2": [False], "live_l1": [True]}, 1, 1.0),
            _arm([False], {"dead_l1": [True], "hard_l2": [False], "live_l1": [False]}, 1, 1.0),
        )
    }
    text = support.render_baseline_delta(pairs, registry.tasks.skills)
    assert "`dead_l1` passes in both arms" in text
    assert "`hard_l2` fails in both arms" in text
    assert "live_l1" not in text.split("Assertion flags")[1]


def test_baseline_delta_is_empty_without_pairs():
    assert support.render_baseline_delta({}) == ""


def test_duration_seconds_parses_iso_span():
    assert support.duration_seconds(
        "2026-08-24T10:00:00+00:00", "2026-08-24T10:02:30+00:00"
    ) == 150.0
    assert support.duration_seconds(None, "2026-08-24T10:00:00+00:00") is None
    assert support.duration_seconds("not-a-date", "also-not") is None


def test_render_grid_runtime_column_only_when_durations_given(registry):
    models = support.select_models(registry)
    cells = {("openrouter/lab/cheapo-1", "alpha"): support.Cell("solid", 3, 3)}
    without = support.render_grid(models, ["alpha"], cells, {}, "2026-08-24")
    with_timing = support.render_grid(
        models, ["alpha"], cells, {}, "2026-08-24",
        durations={"openrouter/lab/cheapo-1": 92.4},
    )
    assert "runtime" not in without
    assert "runtime" in with_timing
    assert "92s" in with_timing
