"""L0 coverage for harness/support.py — every matrix rule without a model call."""

import sys
from pathlib import Path

import pytest
import support

REPO = Path(__file__).resolve().parents[2]

REGISTRY_TOML = """
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
excluded_l1 = ["beta"]
excluded = ["netty"]

[tasks.priors]
default = { input = 100000, output = 10000 }
dialog = { input = 500000, output = 20000 }

[tasks.judge]
model = "openrouter/lab/cheapo-1"
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


# --- shipped registry stays coherent with the real task set -------------------


def test_shipped_registry_parses_and_covers_all_eval_tasks():
    registry = support.parse_registry((REPO / "harness" / "models.toml").read_text())
    evals_src = (REPO / "harness" / "skill_evals.py").read_text()
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


def test_select_tasks_allows_extended_by_name_only():
    reg = support.parse_registry(
        REGISTRY_TOML.replace('matrix = ["alpha", "beta", "dialog"]',
                              'matrix = ["alpha", "beta"]\nextended = ["dialog"]')
    )
    assert support.select_tasks(reg) == ["alpha", "beta"]
    assert support.select_tasks(reg, names=["dialog"]) == ["dialog"]


# --- cost gate (spec: estimate shown and declined -> no metered call) ---------


def test_matrix_gate_declined_makes_no_metered_call(monkeypatch, capsys):
    import matrix

    monkeypatch.setattr("builtins.input", lambda _: "n")
    monkeypatch.setitem(sys.modules, "inspect_ai", object())  # any import attempt breaks
    assert matrix.main([]) == 1
    out = capsys.readouterr().out
    assert "Estimated cost" in out
    assert "aborted before any metered call" in out


def test_matrix_estimate_only_exits_clean(monkeypatch, capsys):
    import matrix

    monkeypatch.setitem(sys.modules, "inspect_ai", object())
    assert matrix.main(["--estimate-only", "--tier", "cheap"]) == 0
    assert "TOTAL" in capsys.readouterr().out
