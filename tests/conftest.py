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

import pytest
from helpers import FIXTURES, REPO, fixture_proposal


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
