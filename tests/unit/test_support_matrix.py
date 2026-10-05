"""L0 coverage for harness/support.py — every matrix rule without a model call."""

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import support
from helpers import MODEL_CATALOG, failing_fetch, shipped_registry

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

[tasks.persona]
input = 50000
output = 2000

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
    assert est.unpriced_roles == ()
    assert [r.model_id for r in est.roles] == ["openrouter/lab/cheapo-1"]


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
    assert est.unpriced_roles == ()
    assert [r.model_id for r in est.roles] == ["openrouter/lab/cheapo-0"]


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


# --- cache-aware accounting (fix-openrouter-caching, group 2) -----------------

_BIG_WRITE_PRICE = (
    'id = "openrouter/lab/big-9"', 'id = "openrouter/lab/big-9"\ncache_write_price = 6.25')
_HELD_PRICE_WITH_WRITE = _HELD_PRICE + "cache_write_price = 2.5\n"


def _usage(tin: int, tout: int, cread: int = 0, cwrite: int = 0) -> SimpleNamespace:
    """A stand-in for Inspect's ModelUsage."""
    return SimpleNamespace(input_tokens=tin, output_tokens=tout,
                           input_tokens_cache_read=cread, input_tokens_cache_write=cwrite)


def _log(model: str, task: str, samples: list, usage: dict, status: str = "success"):
    """A stand-in for Inspect's EvalLog: what collect_usage and record_spend read."""
    return SimpleNamespace(eval=SimpleNamespace(model=model, task=task),
                           stats=SimpleNamespace(model_usage=usage),
                           samples=samples, status=status)


def test_cache_write_price_defaults_to_input_price_on_rows_and_entries():
    reg = support.parse_registry(_registry_with(*_HELD_JUDGE, _BIG_WRITE_PRICE, extra=_HELD_PRICE))
    rows = {m.id: m for m in reg.models}
    assert rows["openrouter/lab/big-9"].cache_write_price == 6.25
    assert rows["openrouter/lab/cheapo-1"].cache_write_price == 1.0  # its input price
    assert reg.role_prices["openrouter/lab/cheapo-0"].cache_write_price == 2.0
    assert support.model_price(reg, "openrouter/lab/big-9").cache_write_price == 6.25
    assert support.model_price(reg, "openrouter/lab/cheapo-0").cache_write_price == 2.0
    written = support.parse_registry(_registry_with(*_HELD_JUDGE, extra=_HELD_PRICE_WITH_WRITE))
    assert written.role_prices["openrouter/lab/cheapo-0"].cache_write_price == 2.5
    assert support.model_price(written, "openrouter/lab/cheapo-0").cache_write_price == 2.5


def test_price_usage_charges_cache_writes_at_their_own_price():
    reg = support.parse_registry(_registry_with(_BIG_WRITE_PRICE))
    report = support.price_usage({
        "openrouter/lab/big-9": (100_000, 10_000, 1_000_000, 200_000),
        "openrouter/lab/cheapo-1": (0, 0, 0, 1_000_000),
    }, reg)
    by_id = {line.model_id: line.usd for line in report.lines}
    # 0.1M*$5 + 0.01M*$25 + 1M*$5 (cache read defaults to input) + 0.2M*$6.25
    assert by_id["openrouter/lab/big-9"] == pytest.approx(0.5 + 0.25 + 5.0 + 1.25)
    # a row priced without the field: writes at its input price
    assert by_id["openrouter/lab/cheapo-1"] == pytest.approx(1.0)


def test_price_usage_prices_a_held_judges_cache_writes_from_role_prices():
    reg = support.parse_registry(_registry_with(*_HELD_JUDGE, extra=_HELD_PRICE_WITH_WRITE))
    report = support.price_usage(
        {"openrouter/lab/cheapo-0": (1_000_000, 0, 1_000_000, 1_000_000)}, reg)
    assert report.unknown_models == ()
    assert report.lines[0].usd == pytest.approx(2.0 + 0.2 + 2.5)


def test_collect_usage_counts_cache_writes_in_billing_and_in_demand():
    import matrix

    sample = SimpleNamespace(model_usage={"openrouter/lab/m-1": _usage(100, 10, 1000, 500)})
    log = _log("openrouter/lab/m-1", "alpha", [sample],
               {"openrouter/lab/m-1": _usage(100, 10, 1000, 500)})
    no_samples = _log("openrouter/lab/m-1", "beta", [],
                      {"openrouter/lab/m-1": _usage(100, 10, 1000, 500)})
    usage, observed = matrix.collect_usage([log, no_samples])
    assert usage["openrouter/lab/m-1"] == (200, 20, 2000, 1000)
    assert observed["alpha"] == (1600, 10), "demand = input + cache writes + cache reads"
    assert observed["beta"] == (1600, 10), "the aggregate fallback counts writes too"


def test_report_prices_cache_writes_exactly_as_the_matrix_does():
    """report.py's per-model run cost and the matrix's actual spend share one
    accumulation, so a log with cache writes costs the same in both."""
    import matrix
    import report

    reg = support.parse_registry(_registry_with(_BIG_WRITE_PRICE))
    judge = "openrouter/lab/cheapo-1"
    usage = {BIG: _usage(100_000, 10_000, 1_000_000, 200_000), judge: _usage(0, 0, 0, 1_000_000)}
    log = _log(BIG, "alpha", [], usage)
    costs = report.model_costs({(BIG, "alpha"): log}, reg)
    actual = support.price_usage(matrix.collect_usage([log])[0], reg)
    assert costs[BIG] == pytest.approx(actual.total)
    # big-9 0.5 + 0.25 + 5.0 + 0.2M writes * $6.25; the judge's 1M writes at its input $1
    assert costs[BIG] == pytest.approx(0.5 + 0.25 + 5.0 + 1.25 + 1.0)
    extended = _log(BIG, "not-a-matrix-task", [], usage)
    assert report.model_costs({(BIG, "x"): extended}, reg) == {}, "matrix tasks only"


def test_report_baseline_tokens_count_full_demand(registry):
    import report

    log = _log(BIG, "alpha", [], {BIG: _usage(100, 10, 1000, 500)})
    log.stats.started_at = log.stats.completed_at = None
    assert report.arm_stats(log, "alpha", registry).tokens == 100 + 1000 + 500 + 10


# --- role pricing in the estimate (group 3) ------------------------------------


def test_persona_budget_is_read_explicitly(registry):
    assert registry.tasks.persona_tokens == (50000, 2000)
    assert registry.tasks.judge_tokens == (40000, 4000)


def test_persona_budget_required_with_dialogue_tasks():
    bad = _registry_with(("[tasks.persona]\ninput = 50000\noutput = 2000\n", ""))
    with pytest.raises(ValueError, match=r"\[tasks\.persona\]"):
        support.parse_registry(bad)
    without_dialogue = support.parse_registry(_registry_with(
        ("[tasks.persona]\ninput = 50000\noutput = 2000\n", ""), ('dialogue = ["dialog"]\n', "")))
    assert without_dialogue.tasks.persona_tokens == (0, 0)


def test_persona_budget_carries_no_model():
    bad = _registry_with(("[tasks.persona]\n", '[tasks.persona]\nmodel = "openrouter/lab/big-9"\n'))
    with pytest.raises(ValueError, match=r"\[roles\]\.persona"):
        support.parse_registry(bad)


def test_estimate_prices_a_judge_override(registry):
    models = support.select_models(registry, ids=["cheapo-1"])
    default = support.estimate_cost(models, ["alpha"], registry)
    override = support.estimate_cost(models, ["alpha"], registry, judge="openrouter/lab/big-9")
    # model 3 * $0.15; judge 3 * (0.04M * $1 + 0.004M * $5) by default ...
    assert default.lines[0].usd == pytest.approx(0.45 + 0.18)
    # ... and 3 * (0.04M * $5 + 0.004M * $25) at the override's price
    assert override.lines[0].usd == pytest.approx(0.45 + 0.9)
    [judge] = override.roles
    assert (judge.role, judge.model_id, judge.cell_epochs, judge.usd) == (
        "judge", "openrouter/lab/big-9", 3, pytest.approx(0.9))
    assert override.unpriced_roles == ()


def test_estimate_prices_the_persona_on_dialogue_tasks_only(registry):
    models = support.select_models(registry, ids=["cheapo-1"])
    single = support.estimate_cost(models, ["alpha"], registry)
    assert [r.role for r in single.roles] == ["judge"], "no dialogue task, no persona call"
    mixed = support.estimate_cost(models, ["alpha", "dialog"], registry)
    roles = {r.role: r for r in mixed.roles}
    assert (roles["judge"].cell_epochs, roles["persona"].cell_epochs) == (6, 3)
    # persona 3 * (0.05M * $1 + 0.002M * $5) = 3 * $0.06, on the dialogue cell-epochs only
    assert roles["persona"].usd == pytest.approx(0.18)
    # alpha 3 * $0.15 + dialog 3 * (0.5M * $1 + 0.02M * $5) + judge 6 * $0.06 + persona $0.18
    assert mixed.lines[0].usd == pytest.approx(0.45 + 1.8 + 0.36 + 0.18)


def test_estimate_prices_a_held_judge_from_its_role_price_entry():
    reg = support.parse_registry(_registry_with(*_HELD_JUDGE, extra=_HELD_PRICE))
    est = support.estimate_cost(support.select_models(reg, ids=["cheapo-1"]), ["alpha"], reg)
    [judge] = est.roles
    assert judge.model_id == "openrouter/lab/cheapo-0"
    assert judge.usd == pytest.approx(3 * (0.04 * 2.0 + 0.004 * 8.0), abs=0.005)  # cents
    assert est.unpriced_roles == ()


def test_estimate_reports_an_unpriced_role(registry):
    models = support.select_models(registry, ids=["cheapo-1"])
    est = support.estimate_cost(models, ["alpha"], registry, judge="openrouter/lab/ghost-1",
                                persona="openrouter/lab/ghost-2")
    assert est.unpriced_roles == ("openrouter/lab/ghost-1",), "the persona is not called here"
    assert est.lines[0].usd == pytest.approx(0.45), "an unpriced role adds nothing"
    with_dialogue = support.estimate_cost(models, ["dialog"], registry,
                                          persona="openrouter/lab/ghost-2")
    assert with_dialogue.unpriced_roles == ("openrouter/lab/ghost-2",)


@pytest.fixture
def gated_matrix(request, monkeypatch, tmp_path):
    """matrix.py over a temporary registry, with no usage history and no Inspect."""
    import matrix

    request.getfixturevalue("no_role_overrides")
    monkeypatch.setitem(sys.modules, "inspect_ai", object())
    monkeypatch.setattr(matrix, "USAGE_HISTORY", tmp_path / "usage.json")

    def over(text: str):
        path = tmp_path / "models.toml"
        path.write_text(text, encoding="utf-8")
        monkeypatch.setattr(matrix, "REGISTRY", path)
        return matrix

    return over


def test_unpriced_role_override_stops_before_the_prompt_even_with_yes(
        gated_matrix, monkeypatch, capsys):
    matrix = gated_matrix(REGISTRY_TOML)
    monkeypatch.setenv("JUDGE_MODEL", "openrouter/lab/ghost-1")
    monkeypatch.setattr(matrix, "confirm_spend",
                        lambda _yes: pytest.fail("the confirmation was reached"))
    monkeypatch.setattr(matrix, "run_matrix", lambda *_args: pytest.fail("run_matrix ran"))
    assert matrix.main(["--yes", "--models", "cheapo-1", "--tasks", "alpha"]) == 2
    err = capsys.readouterr().err
    assert "openrouter/lab/ghost-1" in err
    assert "roster ID" in err
    assert "role's own ID" in err
    assert "role_prices" not in err, "an entry no role names is no remedy for an override"


def test_held_judge_priced_by_its_entry_reaches_the_run(gated_matrix, monkeypatch):
    matrix = gated_matrix(_registry_with(*_HELD_JUDGE, extra=_HELD_PRICE))
    ran = []
    monkeypatch.setattr(matrix, "run_matrix", lambda *args: ran.append(args) or [])
    monkeypatch.setattr(matrix, "record_spend", lambda *_args: None)
    assert matrix.main(["--yes", "--models", "cheapo-1", "--tasks", "alpha"]) == 0
    assert ran, "no unpriced-role stop for a judge priced by its [role_prices] entry"


def test_estimate_prints_the_role_lines(gated_matrix, monkeypatch, capsys):
    matrix = gated_matrix(REGISTRY_TOML)
    monkeypatch.setenv("JUDGE_MODEL", "openrouter/lab/big-9")
    assert matrix.main(["--estimate-only", "--models", "cheapo-1",
                        "--tasks", "alpha", "dialog"]) == 0
    lines = capsys.readouterr().out.splitlines()
    judge = next(line for line in lines if line.strip().startswith("judge "))
    persona = next(line for line in lines if line.strip().startswith("persona "))
    assert "openrouter/lab/big-9" in judge
    assert "40,000 in / 4,000 out per cell-epoch × 6" in judge
    assert "openrouter/lab/cheapo-1" in persona, "a judge override leaves the persona alone"
    assert "50,000 in / 2,000 out per dialogue cell-epoch × 3" in persona


# --- cache telemetry (group 4) ---------------------------------------------------

# big-9 as an Anthropic-family row: routed, pinned, warned
ANTHROPIC_TOML = _registry_with(
    ('family = "lab"\ntier = "frontier"', 'family = "anthropic"\ntier = "frontier"'))
BIG = "openrouter/lab/big-9"
PIN = {"provider": {"order": ["amazon-bedrock", "google-vertex"], "allow_fallbacks": False}}
PIN_REQUEST = {"extra_body": PIN}


def _event(model: str, request: dict | None = None, provider: str | None = None):
    """A stand-in for a ModelEvent; `request` None means the log kept no raw call."""
    call = None if request is None else SimpleNamespace(
        request=request, response={"provider": provider} if provider else {})
    return SimpleNamespace(event="model", model=model, call=call)


@pytest.fixture
def anthropic_registry():
    return support.parse_registry(ANTHROPIC_TOML)


def test_cache_hit_rate_and_zero_tokens():
    assert support.CacheStats(BIG, 600, 100, 300).hit_rate == pytest.approx(0.3)
    assert support.CacheStats(BIG, 0, 0, 0).hit_rate == 0.0


@pytest.mark.parametrize(("cache_read", "warned"), [(499, True), (500, False)])
def test_cache_warning_threshold(anthropic_registry, cache_read, warned):
    stats = support.CacheStats(BIG, 1000 - cache_read, 0, cache_read)
    found = support.cache_warnings([stats], anthropic_registry, "marker")
    assert [w.kind for w in found] == (["low_hit"] if warned else [])
    if warned:
        assert found[0].model_id == BIG
        assert f"warning: {BIG} cache-hit rate 49.9% is below 50%" in str(found[0])


def test_cache_warning_for_zero_prompt_tokens(anthropic_registry):
    [found] = support.cache_warnings([support.CacheStats(BIG, 0, 0, 0)], anthropic_registry,
                                     "marker")
    assert found.kind == "no_prompt"
    assert "recorded no prompt tokens" in str(found)


def test_cache_warning_for_a_call_served_off_the_pin(anthropic_registry):
    """Bedrock, and Vertex (recorded as `Google`) on failover, are both on the
    pin; first-party Anthropic, which the ZDR guardrail excludes, is not."""
    stats = support.CacheStats(BIG, 100, 100, 800, {"Amazon Bedrock": 5, "Google": 2,
                                                    "Anthropic": 1, support.UNRECORDED: 9})
    [found] = support.cache_warnings([stats], anthropic_registry, "marker")
    assert found.kind == "off_pin"
    assert found.detail == ("had calls served off its pin (amazon-bedrock, google-vertex): "
                            "Anthropic ×1")


def test_calls_served_by_any_pinned_provider_are_never_warned(anthropic_registry):
    stats = support.CacheStats(BIG, 100, 100, 800, {"Amazon Bedrock": 7, "Google": 2,
                                                    support.UNRECORDED: 9})
    assert support.cache_warnings([stats], anthropic_registry, "marker") == []


def test_routing_serves_names_each_pinned_provider_by_its_recorded_name(anthropic_registry):
    big = next(m for m in anthropic_registry.models if m.id == BIG)
    routing = support.routing_for(big, "marker")
    assert [routing.serves(n) for n in ("Amazon Bedrock", "google", "amazon-bedrock",
                                        "Anthropic", "Azure")] == [True, True, True, False, False]
    assert set(support.PROVIDER_NAMES) == set(support.PINNED_PROVIDERS)


def test_provider_names_match_the_recorded_endpoint_catalog():
    """The names `serves` accepts are the endpoints' `provider_name` for every
    endpoint of a pinned slug, regional ones included, in the recorded catalog."""
    seen: dict[str, set[str]] = {}
    for path in sorted((MODEL_CATALOG / "endpoints").glob("anthropic__*.json")):
        for e in json.loads(path.read_text(encoding="utf-8"))["data"]["endpoints"]:
            seen.setdefault(e["tag"].split("/")[0], set()).add(e["provider_name"])
    assert {slug: seen[slug] for slug in support.PINNED_PROVIDERS} == {
        slug: {name} for slug, name in support.PROVIDER_NAMES.items()}


def test_cache_warning_kinds_are_the_declared_ones(anthropic_registry):
    stats = [support.CacheStats(BIG, 0, 0, 0, {"Anthropic": 1})]
    kinds = {w.kind for w in support.cache_warnings(stats, anthropic_registry, "marker")}
    assert kinds == {"no_prompt", "off_pin"}
    assert kinds <= set(support.CACHE_WARNING_KINDS)


def test_non_anthropic_and_role_price_ids_are_never_warned(anthropic_registry):
    cheap = support.CacheStats("openrouter/lab/cheapo-1", 1000, 0, 0, {"Amazon Bedrock": 4})
    assert support.cache_warnings([cheap], anthropic_registry, "marker") == []
    held = support.parse_registry(_registry_with(*_HELD_JUDGE, extra=_HELD_PRICE))
    entry = support.CacheStats("openrouter/lab/cheapo-0", 1000, 0, 0, {"Amazon Bedrock": 4})
    assert support.cache_warnings([entry], held, "marker") == []


def test_marker_is_the_adopted_mechanism():
    """Probe 2 (2026-10-05) passed `marker` on haiku-4.5 and sonnet-5.5; the
    unprobed `auto` was deleted (fix-openrouter-caching, task 8.1)."""
    assert (support.CACHE_MECHANISM, support.MECHANISMS) == ("marker", ("marker",))


def test_no_adopted_mechanism_routes_and_warns_nothing(anthropic_registry):
    """The rollback: CACHE_MECHANISM None sends every row as before."""
    big = next(m for m in anthropic_registry.models if m.id == BIG)
    assert not support.routing_for(big, None), "no probed mechanism, no routing"
    stats = support.CacheStats(BIG, 1000, 0, 0, {"Amazon Bedrock": 4})
    assert support.cache_warnings([stats], anthropic_registry, None) == []


def test_format_providers():
    assert support.format_providers({"Anthropic": 3, support.UNRECORDED: 9}) == (
        "Anthropic ×3, unrecorded ×9")
    assert support.format_providers({}) == "none"


def test_serving_providers_counts_recorded_providers_and_unrecorded_calls():
    events = [
        _event(BIG, PIN_REQUEST, "Anthropic"), _event(BIG, PIN_REQUEST, "Anthropic"),
        _event(BIG, PIN_REQUEST, "Amazon Bedrock"), _event(BIG), _event(BIG, PIN_REQUEST),
    ]
    assert support.serving_providers(events) == {
        "Amazon Bedrock": 1, "Anthropic": 2, support.UNRECORDED: 2}


def test_routed_events_drop_same_id_calls_the_routing_did_not_issue():
    pinned, unrecorded = _event(BIG, PIN_REQUEST, "Anthropic"), _event(BIG)
    judge_call = _event(BIG, {"messages": []}, "Amazon Bedrock")  # the judge on the same ID
    other = _event("openrouter/lab/cheapo-1", PIN_REQUEST, "Anthropic")
    tool = SimpleNamespace(event="tool", model=BIG, call=None)
    events = [pinned, unrecorded, judge_call, other, tool]
    assert support.routed_events(events, BIG, routed=True) == [pinned, unrecorded]
    assert support.routed_events(events, BIG, routed=False) == [pinned, unrecorded, judge_call]


BUDGETS = {"judge": (40000, 4000), "persona": (50000, 2000)}


def test_role_observations_skip_a_role_that_is_the_model_under_test():
    sample = SimpleNamespace(model_usage={BIG: _usage(90000, 9000)})
    assert support.role_observations([sample], {"judge": BIG}, BIG, BUDGETS) == []


def test_role_observations_take_the_heaviest_cell_epoch_and_flag_the_budget():
    judge = "openrouter/lab/cheapo-1"
    samples = [SimpleNamespace(model_usage={judge: _usage(20000, 3000, 5000, 1000)}),
               SimpleNamespace(model_usage={judge: _usage(30000, 3500, 9000, 2000)}),
               SimpleNamespace(model_usage=None)]
    [seen] = support.role_observations(samples, {"judge": judge}, BIG, BUDGETS)
    assert (seen.role, seen.input, seen.output) == ("judge", 41000, 3500)
    assert seen.exceeded, "41k demand is over the 40k input budget"
    [shared] = support.role_observations(samples, {"judge": judge, "persona": judge}, BIG,
                                         BUDGETS)
    assert (shared.role, shared.budget) == ("judge/persona", (90000, 6000))
    assert not shared.exceeded


def test_record_spend_persists_cache_telemetry_and_warns(
        anthropic_registry, tmp_path, monkeypatch, capsys):
    import matrix

    monkeypatch.setattr(matrix, "USAGE_HISTORY", tmp_path / "usage.json")
    judge = "openrouter/lab/cheapo-1"
    events = [_event(BIG, PIN_REQUEST, "Anthropic"), _event(BIG, PIN_REQUEST, "Amazon Bedrock"),
              _event(BIG), _event(judge, {"messages": []}, "Amazon Bedrock")]
    usage = {BIG: _usage(600, 50, 300, 100), judge: _usage(60000, 12000)}
    log = _log(BIG, "alpha", [SimpleNamespace(model_usage=usage, events=events)], usage)
    models = support.select_models(anthropic_registry, ids=["big-9"])
    roles = {"judge": judge, "persona": judge}
    matrix.record_spend([log], models, ["alpha"], anthropic_registry, {}, str(tmp_path), roles)

    [path] = tmp_path.glob("matrix-cost-*.json")
    summary = json.loads(path.read_text(encoding="utf-8"))
    assert set(summary) == {"timestamp", "models", "tasks", "per_model", "total",
                            "per_model_cache", "cache_warnings", "cache_mechanism", "roles"}, (
        "the original keys stay as they were")
    assert summary["roles"] == roles
    assert summary["cache_mechanism"] == "marker", "model_args alone cannot show the mechanism"
    cache = summary["per_model_cache"][BIG]
    assert (cache["hit_rate"], cache["cache_write"], cache["cache_read"]) == (0.3, 100, 300)
    assert cache["providers"] == {"Amazon Bedrock": 1, "Anthropic": 1, support.UNRECORDED: 1}
    assert judge not in summary["per_model_cache"], "role usage is no model under test"
    assert [(w["model_id"], w["kind"]) for w in summary["cache_warnings"]] == [
        (BIG, "low_hit"), (BIG, "off_pin")]
    out = capsys.readouterr().out
    assert f"{BIG} cache-hit rate 30.0% is below 50%" in out
    assert "served off its pin (amazon-bedrock, google-vertex): Anthropic ×1" in out
    assert "uncached-equivalent" in out
    judge_line = next(line for line in out.splitlines() if line.strip().startswith("judge "))
    assert "in 60,000 / 40,000" in judge_line
    assert "EXCEEDS BUDGET" in judge_line


def test_record_spend_merges_a_routed_row_across_its_logs(
        anthropic_registry, tmp_path, monkeypatch, capsys):
    """A routed row under test in two task logs, one a dialogue task: its cache
    stats are summed, its providers counted together, and each role keeps one
    line at its heaviest cell-epoch across both logs."""
    import matrix

    monkeypatch.setattr(matrix, "USAGE_HISTORY", tmp_path / "usage.json")
    judge, persona = "openrouter/lab/cheapo-1", "openrouter/lab/off-2"
    alpha_usage = {BIG: _usage(600, 50, 300, 100), judge: _usage(20000, 3000)}
    alpha = _log(BIG, "alpha", [SimpleNamespace(
        model_usage=alpha_usage, events=[_event(BIG, PIN_REQUEST, "Amazon Bedrock")] * 2)],
        alpha_usage)
    dialog_usage = {BIG: _usage(100, 20, 900, 50), judge: _usage(30000, 3500, 9000, 2000),
                    persona: _usage(10000, 1000)}
    dialog = _log(BIG, "dialog", [SimpleNamespace(model_usage=dialog_usage, events=[
        _event(BIG, PIN_REQUEST, "Amazon Bedrock"), _event(BIG, PIN_REQUEST, "Google"),
        _event(BIG)])], dialog_usage)
    models = support.select_models(anthropic_registry, ids=["big-9"])
    roles = {"judge": judge, "persona": persona}
    matrix.record_spend([alpha, dialog], models, ["alpha", "dialog"], anthropic_registry, {},
                        str(tmp_path), roles)

    [path] = tmp_path.glob("matrix-cost-*.json")
    summary = json.loads(path.read_text(encoding="utf-8"))
    cache = summary["per_model_cache"][BIG]
    assert (cache["input"], cache["cache_write"], cache["cache_read"]) == (700, 150, 1200)
    assert cache["hit_rate"] == round(1200 / 2050, 4)
    assert cache["providers"] == {"Amazon Bedrock": 3, "Google": 1, support.UNRECORDED: 1}
    assert summary["cache_warnings"] == [], "Vertex (`Google`) is on the pin; 58.5% is above 50%"
    out = capsys.readouterr().out
    [judge_line] = [line for line in out.splitlines() if line.strip().startswith("judge ")]
    assert "in 41,000 / 40,000   out 3,500 / 4,000" in judge_line, "the dialog log's heavier epoch"
    [persona_line] = [line for line in out.splitlines() if line.strip().startswith("persona ")]
    assert "in 10,000 / 50,000" in persona_line, "the persona is observed on the dialogue task"


def test_record_spend_names_a_routed_row_whose_every_call_failed(
        anthropic_registry, tmp_path, monkeypatch, capsys):
    """Probe 1's log shape: status `success` (fail_on_error=False), no model
    usage, a sample error (the routing 404). The routed row must still appear,
    with a `no_prompt` warning, and the run must count the errored samples."""
    import matrix

    monkeypatch.setattr(matrix, "USAGE_HISTORY", tmp_path / "usage.json")
    cheap = "openrouter/lab/cheapo-1"
    failed = _log(BIG, "alpha", [SimpleNamespace(
        model_usage={}, events=[_event(BIG, PIN_REQUEST)],
        error=SimpleNamespace(message="Error code: 404 - No endpoints found"))], {})
    healthy_usage = {cheap: _usage(1000, 100)}
    healthy = _log(cheap, "alpha", [SimpleNamespace(model_usage=healthy_usage, events=[],
                                                    error=None)], healthy_usage)
    silent = _log("openrouter/lab/off-2", "alpha", [], {})  # unrouted, no usage: no line
    models = support.select_models(anthropic_registry, ids=["big-9", "cheapo-1"])
    matrix.record_spend([failed, healthy, silent], models, ["alpha"], anthropic_registry, {},
                        str(tmp_path), {"judge": cheap, "persona": cheap})

    [path] = tmp_path.glob("matrix-cost-*.json")
    summary = json.loads(path.read_text(encoding="utf-8"))
    assert summary["per_model_cache"][BIG]["providers"] == {support.UNRECORDED: 1}
    assert (summary["per_model_cache"][BIG]["hit_rate"],
            summary["per_model_cache"][BIG]["cache_read"]) == (0.0, 0)
    assert "openrouter/lab/off-2" not in summary["per_model_cache"]
    assert [(w["model_id"], w["kind"]) for w in summary["cache_warnings"]] == [(BIG, "no_prompt")]
    out = capsys.readouterr().out
    assert f"warning: {BIG} recorded no prompt tokens" in out
    assert "warning: 1 eval run(s) did not finish cleanly or had errored samples" in out


def test_cost_summary_without_telemetry_keeps_the_original_shape(registry):
    actual = support.CostReport((support.CostLine("openrouter/lab/cheapo-1", 1.5),))
    import matrix

    summary = matrix.cost_summary(list(registry.models[:1]), ["alpha"], actual, "stamp")
    assert set(summary) == {"timestamp", "models", "tasks", "per_model", "total"}


# --- routing (group 5) -------------------------------------------------------------


def test_routing_for_a_non_anthropic_row_is_empty(registry):
    for mechanism in support.MECHANISMS:
        routing = support.routing_for(registry.models[0], mechanism)
        assert not routing
        assert (routing.model_args, routing.pins,
                routing.conversation_breakpoint) == ({}, (), False)
    assert not support.routing_for(None, "marker"), "an ID without a roster row is not routed"


def test_routing_for_an_anthropic_row(anthropic_registry):
    """`marker` pins the ZDR-compliant global endpoints in order, with no
    fallback beyond them (probe 1: first-party `anthropic` cannot route), and
    asks for the conversation breakpoint."""
    big = next(m for m in anthropic_registry.models if m.id == BIG)
    marker = support.routing_for(big, "marker")
    assert (marker.model_args, marker.conversation_breakpoint) == (PIN, True)
    assert marker.pins == ("amazon-bedrock", "google-vertex")
    assert "anthropic" not in marker.pins
    marker.model_args["provider"]["order"].append("other")
    assert support.routing_for(big, "marker").model_args == PIN, "built fresh on every call"
    for deleted in ("auto", "magic"):
        with pytest.raises(ValueError, match="mechanism"):
            support.routing_for(big, deleted)


@pytest.mark.usefixtures("routable_openrouter")
def test_build_model_keeps_the_registry_id_and_carries_the_routing(anthropic_registry):
    import matrix

    big = next(m for m in anthropic_registry.models if m.id == BIG)
    marker = matrix.build_model(big, support.routing_for(big, "marker"))
    assert str(marker) == BIG, "report.py counts a log only under its registry ID"
    assert (marker.model_args, marker.config.extra_body) == (PIN, None)
    cheap = anthropic_registry.models[0]
    assert matrix.build_model(cheap, support.routing_for(cheap, "marker")) == cheap.id


@pytest.mark.usefixtures("routable_openrouter")
@pytest.mark.parametrize("rolled_back", [False, True], ids=["adopted", "rolled-back"])
def test_run_matrix_routes_anthropic_rows_only_under_an_adopted_mechanism(
        anthropic_registry, monkeypatch, tmp_path, rolled_back):
    """Under the adopted mechanism (`marker`, the shipped default) the Anthropic
    row becomes a routed Model under its registry ID; rolled back
    (support.CACHE_MECHANISM None), every row goes to Inspect as a bare ID,
    exactly as before. The log's metadata names the mechanism, since a `marker`
    routing's model_args show the pin only."""
    import inspect_ai
    import matrix

    if rolled_back:
        monkeypatch.setattr(support, "CACHE_MECHANISM", None)
    mechanism = support.CACHE_MECHANISM
    sent, metadata = [], []

    def fake_eval(_task, model, **kwargs):
        sent.append(model)
        metadata.append(kwargs["metadata"])
        return []

    monkeypatch.setattr(inspect_ai, "eval", fake_eval)
    models = support.select_models(anthropic_registry, ids=["big-9", "cheapo-1"])
    args = SimpleNamespace(epochs=1, log_dir=str(tmp_path), baseline=False)
    matrix.run_matrix(models, ["alpha"], anthropic_registry, args)
    [batch] = sent
    assert metadata == [{"cache_mechanism": mechanism}]
    by_id = {str(m): m for m in batch}
    assert set(by_id) == {BIG, "openrouter/lab/cheapo-1"}
    assert by_id["openrouter/lab/cheapo-1"] == "openrouter/lab/cheapo-1", "never routed"
    if mechanism is None:
        assert by_id[BIG] == BIG, "no adopted mechanism: the Anthropic row stays a bare ID"
    else:
        assert by_id[BIG].model_args == PIN
        assert by_id[BIG].config.extra_body is None, "`marker` lives in the wrapper"


# --- shipped registry stays coherent with the real task set -------------------


def test_shipped_registry_parses_and_covers_all_eval_tasks():
    registry = shipped_registry()
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


@pytest.mark.usefixtures("no_role_overrides")
def test_matrix_gate_declined_makes_no_metered_call(monkeypatch, capsys):
    import matrix

    monkeypatch.setattr("builtins.input", lambda _: "n")
    monkeypatch.setitem(sys.modules, "inspect_ai", object())  # any import attempt breaks
    assert matrix.main([]) == 1
    out = capsys.readouterr().out
    assert "Estimated cost" in out
    assert "aborted before any metered call" in out
    assert OFFLINE_GATE in out, "the conftest fixture reaches the gate: no live request"


@pytest.mark.usefixtures("no_role_overrides")
def test_matrix_estimate_only_exits_clean(monkeypatch, capsys):
    import matrix

    monkeypatch.setitem(sys.modules, "inspect_ai", object())
    assert matrix.main(["--estimate-only", "--tier", "cheap"]) == 0
    out = capsys.readouterr().out
    assert "TOTAL" in out
    assert OFFLINE_GATE in out


# The gate tests that assert stale pins replay the recorded catalog and live in
# test_model_currency.py, the one test file whose model IDs are snapshot facts.


@pytest.mark.usefixtures("no_role_overrides")
def test_gate_offline_warns_and_keeps_the_exit_status(monkeypatch, capsys):
    import matrix

    monkeypatch.setitem(sys.modules, "inspect_ai", object())
    monkeypatch.setattr(matrix.model_currency, "fetch_json", failing_fetch("catalog down"))
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


# ---------- subscription model IDs (add-dev-runner-judge, design D7) ----------

SHIPPED = shipped_registry()


@pytest.mark.parametrize("model_id", [
    "claude-fixture-1-0", "claude-fixture-1-0-20260101", SHIPPED.roles.dev_judge,
])
def test_full_subscription_ids_are_recognized(model_id):
    assert support.is_subscription_model(model_id)


@pytest.mark.parametrize("model_id", [
    "fixture", "claude-fixture", "openrouter/lab/claude-fixture-1-0",
    "anthropic/claude-fixture-1-0", SHIPPED.roles.judge,
])
def test_aliases_and_metered_ids_are_not_subscription_ids(model_id):
    assert not support.is_subscription_model(model_id)


def test_the_subscription_rule_adds_no_roster_row():
    assert not any(support.is_subscription_model(m.id) for m in SHIPPED.models)


# ---------- matrix.py --smoke: selection only, gate unchanged -----------------


@pytest.fixture
def smoke_matrix(request, monkeypatch):
    import matrix

    request.getfixturevalue("no_role_overrides")
    monkeypatch.setitem(sys.modules, "inspect_ai", object())
    return matrix


def test_matrix_smoke_selects_the_role_model_core_tasks_and_one_epoch(smoke_matrix, monkeypatch):
    seen = {}

    def run_matrix(models, tasks, _registry, args):
        seen.update(models=[m.id for m in models], tasks=tasks, epochs=args.epochs)
        return []

    monkeypatch.setattr(smoke_matrix, "run_matrix", run_matrix)
    monkeypatch.setattr(smoke_matrix, "record_spend", lambda *_args: None)
    assert smoke_matrix.main(["--smoke", "--yes"]) == 0
    assert seen == {"models": [SHIPPED.roles.smoke], "tasks": list(SHIPPED.tasks.core),
                    "epochs": 1}


def test_matrix_smoke_estimate_only_prints_the_selection(smoke_matrix, capsys):
    assert smoke_matrix.main(["--smoke", "--estimate-only"]) == 0
    out = capsys.readouterr().out
    assert f"models: {SHIPPED.roles.smoke}" in out
    assert "epochs: 1" in out
    assert "TOTAL" in out


@pytest.mark.parametrize("other", [
    ["--models", "cheapo-1"], ["--tier", "cheap"], ["--tasks", "write_from_seed"], ["--core"],
    ["--epochs", "1"], ["--epochs", "0"],
])
def test_matrix_smoke_refuses_another_selection(smoke_matrix, other, capsys):
    with pytest.raises(SystemExit) as exc:
        smoke_matrix.main(["--smoke", *other])
    assert exc.value.code == 2
    assert "--smoke" in capsys.readouterr().err


def test_matrix_smoke_declined_makes_no_metered_call(smoke_matrix, monkeypatch):
    monkeypatch.setattr(smoke_matrix, "confirm_spend", lambda _yes: False)
    monkeypatch.setattr(smoke_matrix, "run_matrix",
                        lambda *_args: pytest.fail("run_matrix ran after a declined gate"))
    assert smoke_matrix.main(["--smoke"]) == 1
