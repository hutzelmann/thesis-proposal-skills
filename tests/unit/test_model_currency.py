"""L0 coverage for harness/model_currency.py over the recorded catalog snapshot.

Every catalog read here is a replay of `tests/unit/data/model_catalog/` (recorded
2026-10-04): the fetch is injected, and the autouse fixture in `conftest.py`
makes any read that slips through raise instead of connecting. The model IDs in
this file are facts of that snapshot, not examples, which is why
`test_model_ids.py` exempts it.
"""

from __future__ import annotations

import ast
import http.client
import json
import subprocess
import sys
from dataclasses import fields
from datetime import date

import model_currency as mc
import pytest
import support
from helpers import MODEL_CATALOG as DATA
from helpers import REPO, failing_fetch

PRE_BUMP = (DATA / "registry-pre-bump.toml").read_text(encoding="utf-8")
AS_OF = "2026-10-04"

# a synthetic registry over the `lab/` snapshot entries: a held judge whose
# roster row has a successor, a pin about to expire, a pin without a vendor
# endpoint, and a subscription judge one Sonnet behind
LAB_TOML = """\
# header comment the write mode must keep
prices_as_of = 2026-08-06   # copied from the catalog
lines_reviewed_as_of = 2026-08-06

[roles]
judge = "openrouter/lab/judge-1"   # held
smoke = "openrouter/lab/judge-1"
dev_judge = "claude-sonnet-5"
dev_judge_effort = "medium"

[[models]]
id = "openrouter/lab/judge-1"
family = "lab"
tier = "cheap"
input_price = 1.0
output_price = 5.0
cache_read_price = 0.1
enabled = true

[[models]]
id = "openrouter/lab/fading-3"
family = "lab"
tier = "mid"
input_price = 2.0
output_price = 8.0
cache_read_price = 0.5
enabled = true
# a comment inside the block the write mode must keep
note = "a note the write mode must keep"

[[models]]
id = "openrouter/lab/thirdparty-1"
family = "lab"
tier = "frontier"
input_price = 0.5
output_price = 2.0
enabled = true

[tasks]
matrix = ["alpha"]
core = ["alpha"]
heavy = []
excluded_l1 = []
excluded = []

[tasks.priors]
default = { input = 100000, output = 10000 }

[tasks.judge]
input = 40000
output = 3000

[tasks.skills]
alpha = "proposal-alpha"
"""


@pytest.fixture
def catalog() -> dict[str, mc.CatalogEntry]:
    return mc.parse_catalog(json.loads((DATA / "models.json").read_text(encoding="utf-8")))


@pytest.fixture
def replay(catalog_snapshot):
    """The conftest snapshot replay, under the name the checks here pass it by."""
    return catalog_snapshot


def check(text: str, replay, catalog) -> mc.Result:
    return mc.check(support.parse_registry(text), catalog, fetch=replay)


def findings(result: mc.Result, subject: str) -> dict[str, mc.Finding]:
    return {f.kind: f for f in result.findings if f.subject == subject}


def substituted(text: str, *pairs: tuple[str, str]) -> str:
    for old, new in pairs:
        assert text.count(old) == 1, f"fixture drifted: {old!r} is not unique"
        text = text.replace(old, new)
    return text


def run_main(tmp_path, text: str, *args: str) -> tuple[int, str]:
    """main() over a tmp registry copy and the replayed snapshot."""
    registry = tmp_path / "models.toml"
    registry.write_text(text, encoding="utf-8")
    code = mc.main([
        "--registry", str(registry), "--catalog", str(DATA / "models.json"),
        "--endpoints", str(DATA / "endpoints"), "--as-of", AS_OF, *args,
    ])
    return code, registry.read_text(encoding="utf-8")


# ---------- identifiers and version lines -------------------------------------


@pytest.mark.parametrize(("model_id", "line"), [
    ("openrouter/anthropic/claude-haiku-4.5", "anthropic/claude-haiku-*"),
    ("openrouter/anthropic/claude-sonnet-5", "anthropic/claude-sonnet-*"),
    ("openrouter/anthropic/claude-sonnet-5.5", "anthropic/claude-sonnet-*"),
    ("openrouter/anthropic/claude-opus-5", "anthropic/claude-opus-*"),
    ("openrouter/anthropic/claude-opus-5.5", "anthropic/claude-opus-*"),
    ("openrouter/openai/gpt-5.6-luna", "openai/gpt-*-luna"),
    ("openrouter/openai/gpt-6-luna", "openai/gpt-*-luna"),
    ("openrouter/openai/gpt-5.6-terra", "openai/gpt-*-terra"),
    ("openrouter/openai/gpt-5.6-sol", "openai/gpt-*-sol"),
    ("openrouter/openai/gpt-6.1-sol", "openai/gpt-*-sol"),
    ("openrouter/deepseek/deepseek-v4-pro", "deepseek/deepseek-v*-pro"),
    ("openrouter/deepseek/deepseek-v4-pro-0813", "deepseek/deepseek-v*-pro"),
    ("openrouter/qwen/qwen3.8-max", "qwen/qwen*-max"),
    ("openrouter/qwen/qwen3.8-max-0902", "qwen/qwen*-max"),
    ("openrouter/moonshotai/kimi-k3", "moonshotai/kimi-k*"),
    ("claude-sonnet-5-5", "anthropic/claude-sonnet-*"),
    ("claude-haiku-4-5-20251001", "anthropic/claude-haiku-*"),
])
def test_line_derivation(model_id, line):
    assert mc.derive_line(mc.catalog_id(model_id)) == line


def test_subscription_ids_map_to_catalog_ids_and_back():
    assert mc.catalog_id("claude-haiku-4-5-20251001") == "anthropic/claude-haiku-4.5"
    assert mc.catalog_id("claude-sonnet-5-5") == "anthropic/claude-sonnet-5.5"
    assert mc.catalog_id("openrouter/openai/gpt-6.1-sol") == "openai/gpt-6.1-sol"
    assert mc.subscription_id("anthropic/claude-sonnet-5.5") == "claude-sonnet-5-5"
    assert mc.subscription_id("anthropic/claude-haiku-4.5-20251001") == "claude-haiku-4-5-20251001"


def test_snapshot_tokens_and_digitless_ids():
    assert mc.split_snapshot("deepseek-v4-pro-0813") == ("deepseek-v4-pro", "0813")
    assert mc.split_snapshot("claude-haiku-4.5-20251001") == ("claude-haiku-4.5", "20251001")
    assert mc.split_snapshot("qwen3.5-flash-02-23") == ("qwen3.5-flash", "02-23")
    assert mc.split_snapshot("kimi-k3") == ("kimi-k3", "")
    assert mc.derive_line("openai/gpt-audio") is None


# ---------- successors ---------------------------------------------------------


def test_successors_on_the_snapshot(replay, catalog):
    result = check(PRE_BUMP, replay, catalog)
    expected = {
        "openrouter/anthropic/claude-sonnet-5": ("newer", "anthropic/claude-sonnet-5.5"),
        "openrouter/anthropic/claude-opus-5": ("newer", "anthropic/claude-opus-5.5"),
        "openrouter/openai/gpt-5.6-luna": ("newer", "openai/gpt-6-luna"),
        "openrouter/openai/gpt-5.6-sol": ("newer", "openai/gpt-6.1-sol"),
        "openrouter/deepseek/deepseek-v4-pro": ("newer", "deepseek/deepseek-v4-pro-0813"),
        "openrouter/qwen/qwen3.8-max": ("missing", "qwen/qwen3.8-max-0902"),
    }
    for pin, (kind, proposed) in expected.items():
        found = findings(result, f"roster:{pin}")
        assert kind in found, f"{pin}: {sorted(found)}"
        assert found[kind].proposed == proposed
        assert found[kind].writable
    for current in ("anthropic/claude-haiku-4.5", "openai/gpt-5.6-terra", "moonshotai/kimi-k3"):
        found = findings(result, f"roster:openrouter/{current}")
        assert not {"newer", "missing", "expiring"} & set(found), f"{current}: {sorted(found)}"


def test_sol_proposes_the_highest_version_not_the_first_successor(catalog):
    assert mc.newest_in_line("openai/gpt-*-sol", catalog).id == "openai/gpt-6.1-sol"


def test_dated_snapshot_of_the_same_version_is_newer_by_created(catalog):
    kind, newest = mc.assess("deepseek/deepseek-v4-pro", "deepseek/deepseek-v*-pro", catalog)
    assert (kind, newest.id) == ("newer", "deepseek/deepseek-v4-pro-0813")


@pytest.mark.parametrize(("line", "excluded"), [
    ("openai/gpt-*-sol", ("openai/gpt-6.1-sol:batch", "openai/gpt-6.1-sol-pro")),
    ("qwen/qwen*-max", ("qwen/qwen3.8-max-prime",)),
    ("anthropic/claude-sonnet-*",
     ("~anthropic/claude-sonnet-latest", "anthropic/claude-sonnet-5.5:batch")),
    ("moonshotai/kimi-k*", ("moonshotai/kimi-k2.7-code", "moonshotai/kimi-k3:batch")),
])
def test_variants_siblings_and_aliases_are_not_members(catalog, line, excluded):
    members = {e.id for e in mc.line_members(line, catalog)}
    assert members, f"{line} has no member"
    assert not members & set(excluded)


def test_track_glob_overrides_the_derived_line(replay, catalog):
    text = substituted(PRE_BUMP, (
        'id = "openrouter/openai/gpt-5.6-luna"',
        'id = "openrouter/openai/gpt-5.6-luna"\ntrack = "openai/gpt-*-luna-pro"',
    ))

    def unrecorded_endpoints_are_empty(url, timeout):
        try:
            return replay(url, timeout)
        except OSError:
            return {"data": {"endpoints": []}}

    result = check(text, unrecorded_endpoints_are_empty, catalog)
    found = findings(result, "roster:openrouter/openai/gpt-5.6-luna")
    assert found["newer"].proposed == "openai/gpt-6-luna-pro"


def test_track_false_reports_untracked_and_proposes_nothing(replay, catalog):
    text = substituted(PRE_BUMP, (
        'id = "openrouter/deepseek/deepseek-v4-pro"',
        'id = "openrouter/deepseek/deepseek-v4-pro"\ntrack = false',
    ))
    found = findings(check(text, replay, catalog), "roster:openrouter/deepseek/deepseek-v4-pro")
    assert "untracked" in found
    assert "newer" not in found
    assert not found["untracked"].writable


# ---------- prices -------------------------------------------------------------


def test_terra_price_drift_against_the_openai_endpoint(replay, catalog):
    found = findings(check(PRE_BUMP, replay, catalog), "roster:openrouter/openai/gpt-5.6-terra")
    drift = found["price_drift"]
    assert drift.writable
    assert "1/6/0.1" in drift.detail
    assert "2/12/0.2" in drift.detail


def test_no_drift_within_half_a_percent(replay, catalog):
    text = substituted(
        PRE_BUMP,
        ("input_price = 1.0\noutput_price = 6.0\ncache_read_price = 0.1",
         "input_price = 2.005\noutput_price = 12.0\ncache_read_price = 0.2"),
    )
    found = findings(check(text, replay, catalog), "roster:openrouter/openai/gpt-5.6-terra")
    assert "price_drift" not in found


def test_successor_is_priced_at_its_vendor_endpoint(replay, catalog):
    result = check(PRE_BUMP, replay, catalog)
    quotes = {e.target: e.quote for e in result.edits if e.kind == "roster"}
    expected = {
        "openrouter/anthropic/claude-sonnet-5": (2.0, 10.0, 0.2, "anthropic"),
        "openrouter/anthropic/claude-opus-5": (4.0, 20.0, 0.2, "anthropic"),
        "openrouter/openai/gpt-5.6-luna": (0.1, 0.5, 0.01, "openai"),
        "openrouter/openai/gpt-5.6-sol": (2.0, 10.0, 0.1, "openai"),
        "openrouter/deepseek/deepseek-v4-pro": (0.66, 1.98, 0.022, "deepseek"),
        "openrouter/qwen/qwen3.8-max": (2.0, 6.0, 0.25, "alibaba"),
        "openrouter/openai/gpt-5.6-terra": (2.0, 12.0, 0.2, "openai"),
    }
    assert set(quotes) == set(expected), "haiku and kimi-k3 are current at their price"
    for target, (inp, out, cache, endpoint) in expected.items():
        q = quotes[target]
        assert (q.input_price, q.output_price, q.cache_read_price, q.endpoint) == (
            pytest.approx(inp), pytest.approx(out), pytest.approx(cache), endpoint), target


def test_qwen_without_price_endpoint_has_no_vendor_endpoint(replay, catalog):
    text = substituted(PRE_BUMP, (
        'price_endpoint = "alibaba"   # Qwen is served by Alibaba\'s provider slug\n', ""))
    found = findings(check(text, replay, catalog), "roster:openrouter/qwen/qwen3.8-max")
    assert "no_vendor_endpoint" in found
    assert found["missing"].writable, "the ID still moves; only the price stays"


def test_old_deepseek_pin_has_no_vendor_endpoint(replay, catalog):
    text = substituted(PRE_BUMP, (
        'id = "openrouter/deepseek/deepseek-v4-pro"',
        'id = "openrouter/deepseek/deepseek-v4-pro"\ntrack = false',
    ))
    found = findings(check(text, replay, catalog), "roster:openrouter/deepseek/deepseek-v4-pro")
    assert "no_vendor_endpoint" in found
    assert "price_drift" not in found


def test_no_drift_reported_on_outgoing_pins(replay, catalog):
    result = check(PRE_BUMP, replay, catalog)
    for pin in ("anthropic/claude-opus-5", "openai/gpt-5.6-sol", "deepseek/deepseek-v4-pro"):
        found = findings(result, f"roster:openrouter/{pin}")
        assert not {"price_drift", "no_vendor_endpoint"} & set(found), pin


def test_vendor_endpoint_selection():
    raw = {"data": {"endpoints": [
        {"tag": "openai/flex", "pricing": {"prompt": "0.000001", "completion": "0.000006"}},
        {"tag": "openai/fast", "pricing": {"prompt": "0.000004", "completion": "0.000024"}},
        {"tag": "openai", "pricing": {"prompt": "0.000002", "completion": "0.000012"}},
    ]}}
    q = mc.vendor_quote(raw, "openai")
    assert (q.input_price, q.output_price, q.cache_read_price, q.endpoint) == (
        2.0, 12.0, None, "openai")
    quantized = {"data": {"endpoints": [
        {"tag": "moonshotai/mxfp4", "pricing": {"prompt": "0.000003", "completion": "0.000015"}},
        {"tag": "together", "pricing": {"prompt": "0.0000027", "completion": "0.0000135"}},
    ]}}
    assert mc.vendor_quote(quantized, "moonshotai").endpoint == "moonshotai/mxfp4"
    only_tiers = {"data": {"endpoints": [
        {"tag": "lab/fast", "pricing": {"prompt": "0.000001", "completion": "0.000004"}},
    ]}}
    assert mc.vendor_quote(only_tiers, "lab") is None


def test_omitted_cache_read_price_is_dropped_on_write(tmp_path):
    code, written = run_main(tmp_path, LAB_TOML, "--write")
    assert code == 1
    block = written.split('id = "openrouter/lab/fading-3"', 1)[1].split("[[models]]", 1)[0]
    assert "cache_read_price" not in block, "the endpoint has none: the parser defaults it"
    fading = next(
        m for m in support.parse_registry(written).models if m.id == "openrouter/lab/fading-3")
    assert fading.cache_read_price == fading.input_price == 2.0


# ---------- alerts and held roles ---------------------------------------------


def test_expiring_pin_without_successor_is_an_alert(replay, catalog):
    result = check(LAB_TOML, replay, catalog)
    found = findings(result, "roster:openrouter/lab/fading-3")
    assert "2026-10-31" in found["expiring"].detail
    assert not found["expiring"].writable
    assert "roster:openrouter/lab/fading-3" in result.alerts
    assert result.exit_code == 1


def test_missing_pin_is_never_written_back_to_an_older_version(tmp_path, replay, catalog):
    """With lab/thirdparty-2 withdrawn, only lab/thirdparty-1 is left in its
    line: proposing it would downgrade the roster and silence the alert."""
    text = substituted(LAB_TOML, (
        'id = "openrouter/lab/thirdparty-1"', 'id = "openrouter/lab/thirdparty-2"'))
    result = check(text, replay, catalog)
    missing = findings(result, "roster:openrouter/lab/thirdparty-2")["missing"]
    assert (missing.writable, missing.proposed) == (False, "")
    assert "lab/thirdparty-1" in missing.detail
    assert "roster:openrouter/lab/thirdparty-2" in result.alerts
    assert not [e for e in result.edits if e.target == "openrouter/lab/thirdparty-2"]
    code, written = run_main(tmp_path, text, "--write")
    assert code == 1
    assert 'id = "openrouter/lab/thirdparty-2"' in written


def test_missing_dev_judge_is_never_moved_to_an_older_version(replay, catalog):
    text = substituted(LAB_TOML, ('dev_judge = "claude-sonnet-5"', 'dev_judge = "claude-sonnet-6"'))
    result = check(text, replay, catalog)
    assert not findings(result, "role:dev_judge")["missing"].writable
    assert "role:dev_judge" in result.alerts
    assert not [e for e in result.edits if e.target == "dev_judge"]


def test_dated_subscription_bump_settles(replay, catalog):
    """A dated anthropic snapshot listed beside the undated ID: next week the
    bumped dev_judge compares as that snapshot, not as its undated sibling,
    which the snapshot would outrank forever."""
    sonnet = catalog["anthropic/claude-sonnet-5.5"]
    dated = "anthropic/claude-sonnet-5.5-20260928"
    catalog = {**catalog, dated: mc.CatalogEntry(dated, sonnet.created + 86_400)}
    first = check(LAB_TOML, replay, catalog)
    assert findings(first, "role:dev_judge")["newer"].proposed == "claude-sonnet-5-5-20260928"
    bumped = mc.apply_edits(LAB_TOML, first.edits, date.fromisoformat(AS_OF))
    second = check(bumped, replay, catalog)
    assert not findings(second, "role:dev_judge")
    assert not [e for e in second.edits if e.target == "dev_judge"]


def test_judge_and_persona_are_held_never_written(replay, catalog):
    result = check(LAB_TOML, replay, catalog)
    for role in ("judge", "persona"):
        held = findings(result, f"role:{role}")["held"]
        assert held.proposed == "lab/judge-2"
        assert not held.writable
    assert not [e for e in result.edits if e.kind == "role" and e.target in ("judge", "persona")]


def test_held_role_kinds_are_informational():
    assert {"held", "untracked", "new_line"} == mc.INFORMATIONAL


# ---------- new lines ----------------------------------------------------------

NEW_LINES_2026_10_04 = {
    "line:anthropic/claude-fable-*",
    "line:deepseek/deepseek-v*-flash",
    "line:deepseek/deepseek-v*-flash-vision-exp",
    "line:openai/gpt-*-astra",
    "line:openai/gpt-*-astra-pro",
    "line:openai/gpt-*-luna-pro",
    "line:openai/gpt-*-sol-pro",
    "line:qwen/qwen*-flash",
    "line:qwen/qwen*-omni-flash",
    "line:qwen/qwen*-27b",
    "line:qwen/qwen*-2.4t-a95b",
    "line:qwen/qwen*-max-prime",
}


def new_lines(result: mc.Result) -> dict[str, mc.Finding]:
    return {f.subject: f for f in result.findings if f.kind == "new_line"}


def test_new_lines_on_the_snapshot(replay, catalog):
    reported = new_lines(check(PRE_BUMP, replay, catalog))
    assert set(reported) == NEW_LINES_2026_10_04
    fable = reported["line:anthropic/claude-fable-*"]
    assert fable.proposed == "anthropic/claude-fable-5.1"
    assert not fable.writable


def test_new_lines_ignore_old_digitless_and_known_lines(replay, catalog):
    text = substituted(PRE_BUMP, (
        'id = "openrouter/deepseek/deepseek-v4-pro"',
        'id = "openrouter/deepseek/deepseek-v4-pro"\ntrack = false',
    ))
    reported = set(new_lines(check(text, replay, catalog)))
    assert "line:openai/gpt-oss-*b" not in reported, "every member predates the review date"
    assert not [s for s in reported if "audio" in s or "chat" in s], "no digit run, no line"
    assert "line:deepseek/deepseek-v*-pro" not in reported, "an opted-out entry still knows it"
    assert "line:anthropic/claude-sonnet-*" not in reported


def test_moving_the_review_date_clears_a_reported_line(replay, catalog):
    text = substituted(PRE_BUMP, (
        "lines_reviewed_as_of = 2026-08-06", "lines_reviewed_as_of = 2026-09-01"))
    reported = set(new_lines(check(text, replay, catalog)))
    assert "line:anthropic/claude-fable-*" not in reported
    assert "line:openai/gpt-*-astra" in reported, "created after the new date, still open"


def test_new_lines_leave_the_exit_status_alone(tmp_path):
    _, bumped = run_main(tmp_path, PRE_BUMP, "--write")
    code, _ = run_main(tmp_path, bumped, "--json")
    assert code == 0, "only informational findings remain after the bump"


# ---------- write mode ---------------------------------------------------------


def test_write_bumps_the_roster_and_reprices(tmp_path):
    code, written = run_main(tmp_path, PRE_BUMP, "--write")
    assert code == 1
    reg = support.parse_registry(written)
    ids = [m.id.removeprefix("openrouter/") for m in reg.models]
    assert ids == [
        "anthropic/claude-haiku-4.5", "anthropic/claude-sonnet-5.5",
        "anthropic/claude-opus-5.5", "openai/gpt-6-luna", "openai/gpt-5.6-terra",
        "openai/gpt-6.1-sol", "deepseek/deepseek-v4-pro-0813", "qwen/qwen3.8-max-0902",
        "moonshotai/kimi-k3",
    ]
    terra = next(m for m in reg.models if m.id.endswith("gpt-5.6-terra"))
    assert (terra.input_price, terra.output_price, terra.cache_read_price) == (2.0, 12.0, 0.2)
    assert reg.roles.judge == reg.roles.smoke == "openrouter/anthropic/claude-haiku-4.5"
    assert reg.roles.dev_judge == "claude-sonnet-5-5"
    assert reg.role_prices == {}, "the haiku row did not move"
    assert reg.prices_as_of.isoformat() == AS_OF
    assert reg.lines_reviewed_as_of.isoformat() == "2026-08-06", "moved by hand only"


def test_write_preserves_comments_and_notes(tmp_path):
    _, written = run_main(tmp_path, PRE_BUMP, "--write")
    for kept in (
        "# Price basis:", "the eval harness cannot drive this model",
        "# The account's data policy pins luna to Azure",
        'price_endpoint = "alibaba"   # Qwen is served by Alibaba\'s provider slug',
        "# matrix L2 judge (held)",
    ):
        assert kept in written, kept


def test_write_is_idempotent(tmp_path):
    _, once = run_main(tmp_path, PRE_BUMP, "--write")
    _, twice = run_main(tmp_path, once, "--write")
    assert twice == once


def test_write_moves_smoke_and_dev_judge_but_holds_the_judge(tmp_path):
    code, written = run_main(tmp_path, LAB_TOML, "--write")
    assert code == 1
    reg = support.parse_registry(written)
    assert reg.models[0].id == "openrouter/lab/judge-2"
    assert reg.roles.smoke == "openrouter/lab/judge-2"
    assert reg.roles.dev_judge == "claude-sonnet-5-5"
    assert reg.roles.judge == reg.roles.persona == "openrouter/lab/judge-1"
    for kept in (
        "# held", "# header comment the write mode must keep",
        "a note the write mode must keep", "# a comment inside the block the write mode must keep",
    ):
        assert kept in written, kept


def test_held_judge_leaving_the_roster_gets_a_role_price(tmp_path):
    _, written = run_main(tmp_path, LAB_TOML, "--write")
    reg = support.parse_registry(written)
    entry = reg.role_prices["openrouter/lab/judge-1"]
    assert (entry.input_price, entry.output_price, entry.cache_read_price) == (1.0, 5.0, 0.1)
    row = next(m for m in reg.models if m.id == "openrouter/lab/judge-2")
    assert (row.input_price, row.output_price) == (1.2, 6.0), "the new row: judge-2's endpoint"
    est = support.estimate_cost([row], ["alpha"], reg)
    assert est.unknown_models == ()
    # 3 * (0.1M * $1.2 + 0.01M * $6) + judge 3 * (0.04M * $1 + 0.003M * $5)
    assert est.lines[0].usd == pytest.approx(3 * 0.18 + 3 * 0.055, abs=0.01)
    _, again = run_main(tmp_path, written, "--write")
    assert again == written


@pytest.mark.parametrize("header", [
    '[role_prices."openrouter/lab/judge-1"]',            # as --write spells it
    "[ role_prices . 'openrouter/lab/judge-1' ]",        # the same table, hand-written
])
def test_role_price_drift_is_reported_and_refreshed(tmp_path, replay, catalog, header):
    _, written = run_main(tmp_path, LAB_TOML, "--write")
    written = written.replace('[role_prices."openrouter/lab/judge-1"]', header)
    reg = support.parse_registry(written)

    def repriced(url, timeout):
        raw = replay(url, timeout)
        if url == mc.ENDPOINTS_URL.format(model_id="lab/judge-1"):
            raw = json.loads(json.dumps(raw))
            raw["data"]["endpoints"][0]["pricing"]["prompt"] = "0.0000015"
        return raw

    result = mc.check(reg, catalog, fetch=repriced)
    drift = findings(result, "role_price:openrouter/lab/judge-1")["price_drift"]
    assert drift.writable
    refreshed = mc.apply_edits(written, result.edits, date.fromisoformat(AS_OF))
    assert refreshed.count("role_prices") == 1, "refreshed in place, never a second table"
    entry = support.parse_registry(refreshed).role_prices["openrouter/lab/judge-1"]
    assert entry.input_price == 1.5
    assert support.parse_registry(refreshed).roles.judge == "openrouter/lab/judge-1"


def test_write_finds_a_row_whatever_string_quoting_spells_its_id(tmp_path):
    text = substituted(PRE_BUMP, (
        'id = "openrouter/openai/gpt-5.6-sol"', "id = 'openrouter/openai/gpt-5.6-sol'"))
    code, written = run_main(tmp_path, text, "--write")
    assert code == 1
    assert "openrouter/openai/gpt-6.1-sol" in [m.id for m in support.parse_registry(written).models]


def test_a_write_the_registry_cannot_take_exits_3_without_a_report(tmp_path, monkeypatch, capsys):
    def unappliable(*_args):
        raise ValueError("no [roles] table")

    monkeypatch.setattr(mc, "apply_edits", unappliable)
    code, written = run_main(tmp_path, PRE_BUMP, "--write", "--json")
    assert (code, written) == (3, PRE_BUMP)
    captured = capsys.readouterr()
    assert captured.out == "", "no JSON report: the workflow tells a failure from findings by it"
    assert "write failed" in captured.err


# ---------- interface ----------------------------------------------------------


def test_json_output_matches_the_schema(tmp_path, capsys):
    code, _ = run_main(tmp_path, LAB_TOML, "--json")
    assert code == 1
    out = json.loads(capsys.readouterr().out)
    assert set(out) == {"source", "fetched_at", "findings", "alerts"}
    assert out["findings"], "the lab registry has findings"
    expected = {f.name for f in fields(mc.Finding)}
    assert expected == {"subject", "kind", "pinned", "proposed", "detail", "writable"}
    for finding in out["findings"]:
        assert set(finding) == expected
        assert finding["kind"] in mc.KINDS
    assert out["alerts"] == ["roster:openrouter/lab/fading-3"]


def test_default_output_is_human_readable(tmp_path, capsys):
    run_main(tmp_path, PRE_BUMP)
    out = capsys.readouterr().out
    for shown in ("newer", "openai/gpt-6.1-sol", "new_line", "claude-fable-5.1"):
        assert shown in out, shown
    assert not out.lstrip().startswith("{")


def test_pr_body_carries_what_the_maintainer_needs(tmp_path):
    body_path = tmp_path / "body.md"
    run_main(tmp_path, LAB_TOML, "--write", "--pr-body", str(body_path))
    body = body_path.read_text(encoding="utf-8")
    for needed in (
        "lab/judge-2",                                   # a finding
        "held",                                          # the held roles
        '[role_prices."openrouter/lab/judge-1"]',        # the entry this run wrote
        "anthropic/claude-fable-*",                      # a new line
        "lines_reviewed_as_of",                          # ...and how to clear it
        "uv run poe report", "python3 scripts/sync_shared.py", "gitignored",
        "untested",                                      # until a gated run
        "claude -p --model claude-sonnet-5-5",           # subscription resolved-ID check
        "close and reopen",                              # dispatched-CI fallback
    ):
        assert needed in body, needed


def test_pr_body_lists_files_still_naming_an_outgoing_id():
    result = mc.Result(findings=(
        mc.Finding("roster:openrouter/lab/a-1", "newer", "openrouter/lab/a-1", "lab/a-2",
                   writable=True),
    ), edits=())
    body = mc.render_pr_body(result, date(2026, 10, 4), ["docs/example.md"])
    assert "`docs/example.md`" in body


def test_files_naming_finds_every_spelling_of_an_outgoing_id(tmp_path):
    files = {
        "pyproject.toml": 'cmd = "python harness/matrix.py --models claude-haiku-4.5 --core"\n',
        "docs/qualified.md": "pinned: anthropic/claude-haiku-4.5\n",
        "docs/subscription.md": "claude -p --model claude-haiku-4-5\n",
        "docs/other-versions.md": "claude-haiku-4.5-20251001, claude-haiku-4.50\n",
        "openspec/record.md": "claude-haiku-4.5\n",
    }
    for name, body in files.items():
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_text(body, encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
    assert mc.files_naming(["anthropic/claude-haiku-4.5"], tmp_path) == [
        "docs/qualified.md", "docs/subscription.md", "pyproject.toml"]
    assert mc.spellings("openai/gpt-6-luna") == ["openai/gpt-6-luna", "gpt-6-luna"]


@pytest.mark.parametrize("catalog_text", [None, '{"data": [{"id": 5}]}', "not json"])
def test_unknown_currency_exits_2_and_writes_nothing(tmp_path, catalog_text):
    registry = tmp_path / "models.toml"
    registry.write_text(PRE_BUMP, encoding="utf-8")
    args = ["--registry", str(registry), "--write", "--as-of", AS_OF]
    if catalog_text is not None:  # None: the live fetch, which the L0 fixture refuses
        broken = tmp_path / "catalog.json"
        broken.write_text(catalog_text, encoding="utf-8")
        args += ["--catalog", str(broken), "--endpoints", str(DATA / "endpoints")]
    assert mc.main(args) == 2
    assert registry.read_text(encoding="utf-8") == PRE_BUMP


def test_truncated_catalog_body_is_currency_unknown(tmp_path, monkeypatch):
    """IncompleteRead is an http.client.HTTPException, neither an OSError nor a
    ValueError, and must still end as exit 2 rather than a traceback (exit 1)."""
    def truncated(*_request):
        raise http.client.IncompleteRead(b"partial")

    monkeypatch.setattr(mc, "fetch_json", truncated)
    registry = tmp_path / "models.toml"
    registry.write_text(PRE_BUMP, encoding="utf-8")
    assert mc.main(["--registry", str(registry), "--write", "--as-of", AS_OF]) == 2
    assert registry.read_text(encoding="utf-8") == PRE_BUMP


def test_fetch_json_is_refused_inside_l0():
    with pytest.raises(OSError, match="network disabled in L0 tests"):
        mc.fetch_json(mc.CATALOG_URL, 1.0)


# ---------- the cost-gate warning (matrix.main) --------------------------------

PRE_BUMP_PATH = DATA / "registry-pre-bump.toml"


def _estimate_block(out: str) -> str:
    return "\n".join(line for line in out.splitlines() if not line.startswith("model currency"))


@pytest.mark.usefixtures("catalog_snapshot")
def test_gate_prints_stale_pins_after_the_estimate(monkeypatch, capsys):
    import matrix

    monkeypatch.setitem(sys.modules, "inspect_ai", object())
    monkeypatch.setattr(matrix, "REGISTRY", PRE_BUMP_PATH)
    assert matrix.main(["--estimate-only"]) == 0
    warned = capsys.readouterr().out
    assert "is stale — newer in its line: openai/gpt-6.1-sol" in warned
    assert "is missing from the catalog (newest in its line: qwen/qwen3.8-max-0902)" in warned
    assert warned.index("TOTAL") < warned.index("model currency:"), "warnings follow the estimate"

    monkeypatch.setattr(mc, "fetch_json", failing_fetch("catalog down"))
    assert matrix.main(["--estimate-only"]) == 0
    offline = capsys.readouterr().out
    assert "model currency unknown (catalog unreachable: catalog down)" in offline
    assert _estimate_block(warned) == _estimate_block(offline), "the estimate is unchanged"


@pytest.mark.usefixtures("catalog_snapshot")
def test_gate_declined_with_warnings_still_makes_no_metered_call(monkeypatch, capsys):
    import matrix

    monkeypatch.setattr("builtins.input", lambda _: "n")
    monkeypatch.setitem(sys.modules, "inspect_ai", object())
    monkeypatch.setattr(matrix, "REGISTRY", PRE_BUMP_PATH)
    assert matrix.main(["--tier", "frontier"]) == 1
    out = capsys.readouterr().out
    assert "is stale" in out
    assert "aborted before any metered call" in out


@pytest.mark.usefixtures("catalog_snapshot")
def test_gate_names_held_roles_and_current_pins():
    registry = support.parse_registry(PRE_BUMP)
    kimi = support.select_models(registry, ids=["kimi-k3"])
    lines = mc.gate_warnings(registry, kimi, environ={})
    assert lines == ["model currency: every selected pin is current in the OpenRouter catalog"]
    stale_judge = {"JUDGE_MODEL": "openrouter/anthropic/claude-sonnet-5"}
    lines = mc.gate_warnings(registry, kimi, environ=stale_judge)
    assert any("judge/persona role" not in line and "judge role" in line and "held" in line
               for line in lines), lines


# ---------- the "plain python3" property ---------------------------------------


@pytest.mark.parametrize("module", ["model_currency.py", "support.py"])
def test_checker_imports_only_the_standard_library(module):
    tree = ast.parse((REPO / "harness" / module).read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            imported.add(node.module.split(".")[0])
    allowed = set(sys.stdlib_module_names) | {"support", "model_currency"}
    assert imported <= allowed, f"{module}: non-stdlib imports {sorted(imported - allowed)}"
