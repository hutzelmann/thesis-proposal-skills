"""Shared pytest fixtures for the L0 suite.

This file exists because the alternative was twelve test files each re-deriving
the same paths and the same `sys.path` preamble — and the next test file being
written by copying the last one. Import roots live in
`[tool.pytest.ini_options] pythonpath`; nothing here or in any test may touch
`sys.path` (`tests/unit/test_repo_conventions.py` enforces it).

Only fixtures belong here — things that need `tmp_path` or another pytest
facility. Ordinary callables live in `tests/helpers.py`. A fixture earns its
place at the third caller; anything used by one file stays in that file, so
this does not grow into a second test framework.
"""

from __future__ import annotations

from pathlib import Path

import common
import copilot_cli
import host_login
import model_currency
import openspec_currency
import pytest
import validate_specs
from helpers import (
    COPILOT_TOKEN,
    FIXTURES,
    MODEL_CATALOG,
    REPO,
    failing_fetch,
    fixture_proposal,
)


class RealCopilotStarted(AssertionError):
    """Raised by the Copilot binary seam in every L0 test that did not patch it."""


def _no_real_copilot() -> str:
    raise RealCopilotStarted("L0 never starts the real copilot: patch copilot_cli.binary "
                             "with a fake script")


@pytest.fixture(scope="session")
def _absent_state_root(tmp_path_factory) -> Path:
    return tmp_path_factory.mktemp("harness-state") / "absent"


@pytest.fixture(autouse=True)
def _harness_login_offline(monkeypatch, _absent_state_root):
    """L0 never touches a real login: every test sees a harness state root
    with no login home in it, so an isolated configuration prepared without a
    test's own setup is refused by the preflight before any client could start
    (a missing home starts none), and the operator's opt-in, a long-lived
    token exported for token mode and the removed override in the
    developer's shell cannot reach a test. Tests that need a home point
    `THESIS_PROPOSAL_DEV_STATE` at their own `tmp_path`; tests that need a
    token set one."""
    monkeypatch.setenv(host_login.STATE_VAR, str(_absent_state_root))
    for name in (host_login.OPT_IN_VAR, host_login.LONG_LIVED_TOKEN, "ROUTING_CONFIG_DIR"):
        monkeypatch.delenv(name, raising=False)


# stands in for the system's temporary directories in L0 (see `_copilot_offline`)
L0_TEMP_STANDIN = "/nonexistent-l0-system-tmp"


@pytest.fixture(autouse=True)
def _copilot_offline(monkeypatch):
    """No test can start the real `copilot` (add-copilot-dev-runner design
    Decision 14): the binary seam raises unless a test points it at a fake
    script, before any `Popen`. The full suite also reruns after a real token
    exists in the default state root, so a test that missed a seam would
    otherwise spend credits without a go; `_harness_login_offline` above
    keeps every test's state root in a temporary directory as well.

    The Copilot work directory (Decision 7, D-b) never lies in a temporary
    directory, but every test's `tmp_path` does: so `host_login.temp_dirs`
    names a stand-in that holds no test directory, and the per-user runtime
    directory is never found, so no test writes under the real
    `/run/user/<uid>`; a Copilot workspace then lies under the test's state
    root. The kernel's Yama ptrace scope reads as the minimum the preflight
    accepts, so no test reads the real sysctl and the suite passes on a host
    without Yama. Tests of those seams set them themselves."""
    monkeypatch.setattr(copilot_cli, "binary", _no_real_copilot)
    monkeypatch.setattr(host_login, "temp_dirs", lambda: (L0_TEMP_STANDIN,))
    monkeypatch.setattr(copilot_cli, "runtime_dir", lambda _uid=None: None)
    monkeypatch.setattr(copilot_cli, "ptrace_scope",
                        lambda _path=None: copilot_cli.MIN_PTRACE_SCOPE)


@pytest.fixture
def copilot_account(tmp_path, monkeypatch) -> Path:
    """An account home of the test's own for the Copilot host: the deny list,
    the workspace scan and the probe read `host_login.account_home`, never the
    operator's."""
    account = tmp_path / "account"
    account.mkdir()
    monkeypatch.setattr(host_login, "account_home", lambda _uid=None: account)
    return account


@pytest.fixture
def copilot_home(tmp_path, monkeypatch, copilot_account) -> Path:
    """A seeded Copilot harness home under a state root in `tmp_path`, beside an
    account home of the test's own (`copilot_account`), with the synthetic
    token in the token file beside it (owner-only), and the operator's go
    with its canary passed (add-copilot-dev-runner design Decision 9), so a
    skill run's go check passes; tests of the go or of the canary set the go
    themselves."""
    monkeypatch.setenv(host_login.STATE_VAR, str(tmp_path / "state"))
    path = host_login.home(host_login.COPILOT)
    assert not path.is_relative_to(copilot_account)
    host_login.seed(host_login.COPILOT, path)
    host_login.token_path(path).write_text(COPILOT_TOKEN + "\n", encoding="utf-8")
    host_login.token_path(path).chmod(0o600)
    copilot_cli.clear_stop(path)  # the go
    copilot_cli.record_canary_pass(path, "00000000-0000-4000-8000-000000000000")
    return path


@pytest.fixture(autouse=True)
def _model_catalog_offline(monkeypatch):
    """L0 is offline by construction: the currency checker's one network call
    raises for every test, so a test that reaches the matrix cost gate without a
    substitute (the gate tests in this change, and those other changes add)
    prints "model currency unknown" instead of making a live request. Raising
    the error the gate already handles keeps such tests free of any knowledge
    of the catalog."""
    monkeypatch.setattr(model_currency, "fetch_json", failing_fetch("network disabled in L0 tests"))


class RealOpenSpecStarted(AssertionError):
    """Raised by the OpenSpec gate's CLI runner in every L0 test that did not replace it."""


def _no_real_openspec(*_args: object) -> object:
    raise RealOpenSpecStarted("L0 never starts the OpenSpec CLI through npx: replace "
                              "validate_specs.run_cli with a replay of recorded output")


@pytest.fixture(autouse=True)
def _openspec_offline(monkeypatch):
    """L0 is offline by construction for the OpenSpec gate and its currency
    check too (bump-openspec): the gate's CLI runner raises loudly, since npx
    would download the pinned package, and the registry fetch fails the way
    an unreachable registry does, which the check already reads as unknown.
    The two test files that exercise them replace both with recordings."""
    monkeypatch.setattr(validate_specs, "run_cli", _no_real_openspec)
    monkeypatch.setattr(openspec_currency, "fetch_json",
                        failing_fetch("network disabled in L0 tests"))


@pytest.fixture(autouse=True)
def _lit_keys_offline(monkeypatch, tmp_path_factory, _absent_state_root):
    """L0 never reads the developer's own literature-search keys
    (classify-arxiv-answers design D11). `common` computes its user-global key
    file from the real home at import, consults `api-keys.env` wherever pytest
    runs, and `user_agent()` looks up CONTACT_EMAIL on every request; a real
    key there would turn a keyless test into a live, keyed one. So the global
    file lies in a temporary directory, the key variables a developer's shell
    may export are dropped, and the key-file reader opens nothing outside
    pytest's temporary root: tests that need a key file write it under
    `tmp_path` and point the working directory or THESIS_PROPOSAL_KEYS at it.
    `import common` is the lit-search source for every test, so the vendored
    `validate_refs.py` callers are covered too."""
    root = tmp_path_factory.getbasetemp().resolve()
    read = common._read_key

    def read_test_files_only(path: Path, name: str) -> str | None:
        return read(path, name) if Path(path).resolve().is_relative_to(root) else None

    monkeypatch.setattr(common, "_read_key", read_test_files_only)
    monkeypatch.setattr(common, "GLOBAL_KEY_FILE", _absent_state_root / common.KEY_FILE)
    for name in (common.KEY_FILE_ENV, "OPENALEX_API_KEY", "CONTACT_EMAIL", "OPENCITATIONS_TOKEN"):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def catalog_snapshot(monkeypatch):
    """Serve the recorded 2026-10-04 catalog (tests/unit/data/model_catalog/)
    for every currency read in the test."""
    replay = model_currency.replay_fetch(MODEL_CATALOG / "models.json", MODEL_CATALOG / "endpoints")
    monkeypatch.setattr(model_currency, "fetch_json", replay)
    return replay


@pytest.fixture
def no_role_overrides(monkeypatch):
    """Clear the role overrides a developer's shell may carry: `matrix.main`
    resolves the judge, persona and smoke model from the environment, and an
    override left over from a re-grade would change what a gate test prices."""
    for name in ("JUDGE_MODEL", "PERSONA_MODEL", "SMOKE_MODEL"):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def inspect_markers(monkeypatch):
    """Inspect's own OpenRouter cache-marker function, put back after the test.
    The `marker` mechanism's `openrouter_cache.install()` replaces it for the
    whole process, and `matrix.build_model` installs it for a marker routing, so
    any test that may install it takes this fixture."""
    import importlib

    import openrouter_cache

    module = importlib.import_module(openrouter_cache.INSPECT_MODULE)
    original = getattr(module, openrouter_cache.INSPECT_FUNCTION)
    original = getattr(original, "__wrapped__", original)  # never restore a wrapper
    monkeypatch.setattr(module, openrouter_cache.INSPECT_FUNCTION, original)
    return original


@pytest.fixture
def routable_openrouter(monkeypatch, inspect_markers):
    """What a test needs to build an OpenRouter Model offline: a placeholder key
    (Inspect's provider refuses to construct without one; nothing is sent) and
    Inspect's marker function put back afterwards. Any test that builds a routed
    model needs the key, so taking both together keeps a `marker` build from
    leaving the wrapper installed for the rest of the process."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "placeholder-not-a-credential")
    return inspect_markers


@pytest.fixture(scope="session")
def repo() -> Path:
    return REPO


@pytest.fixture(scope="session")
def fixtures() -> Path:
    return FIXTURES


@pytest.fixture
def proposal_file(tmp_path):
    """Copy a fixture's proposal into `tmp_path`, optionally substituting text.

    The copy-and-mutate block this replaces appears dozens of times across the
    check tests. `replace` takes (old, new) pairs applied in order; `name`
    renames the copy where a test asserts on the filename.
    """
    def make(fixture: str, *, replace: list[tuple[str, str]] | None = None,
             name: str | None = None) -> Path:
        source = fixture_proposal(fixture)
        text = source.read_text(encoding="utf-8")
        for old, new in replace or []:
            text = text.replace(old, new)
        target = tmp_path / (name or source.name)
        target.write_text(text, encoding="utf-8")
        return target

    return make
