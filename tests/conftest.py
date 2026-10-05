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

import model_currency
import pytest
from helpers import FIXTURES, MODEL_CATALOG, REPO, failing_fetch, fixture_proposal


@pytest.fixture(autouse=True)
def _model_catalog_offline(monkeypatch):
    """L0 is offline by construction: the currency checker's one network call
    raises for every test, so a test that reaches the matrix cost gate without a
    substitute (the gate tests in this change, and those other changes add)
    prints "model currency unknown" instead of making a live request. Raising
    the error the gate already handles keeps such tests free of any knowledge
    of the catalog."""
    monkeypatch.setattr(model_currency, "fetch_json", failing_fetch("network disabled in L0 tests"))


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
