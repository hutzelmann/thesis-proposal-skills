"""L0: the typst CI build script must not drift from publish.py.

The pandoc/typst image has no Python, so the export matrix cannot run there and
scripts/ci_typst_build.sh restates the typst tier's pandoc invocation. A restated
command can silently stop matching the shipped one — the same class of blind spot
that let the LaTeX tier ship broken. Needs no toolchain, so it runs in the
ordinary CI job alongside the other drift guards.
"""

import itertools
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = (REPO / "scripts" / "ci_typst_build.sh").read_text(encoding="utf-8")
sys.path.insert(0, str(REPO / "skills" / "proposal-publish" / "scripts"))

import publish  # noqa: E402

COMMAND = publish.pandoc_command(Path("proposal.md"), "typst")


def template_assets(flag: str) -> set[str]:
    """Basenames passed to a given pandoc flag by the shipped command."""
    return {
        Path(value).name
        # pairwise scan: a flag's value is the token that follows it
        for option, value in itertools.pairwise(COMMAND)
        if option == flag
    }


def script_assets(flag: str) -> set[str]:
    return set(re.findall(rf"{re.escape(flag)}\s+\"[^\"]*/([\w.-]+)\"", SCRIPT))


def test_script_runs_the_same_filter_chain():
    assert template_assets("--lua-filter") == script_assets("--lua-filter"), (
        "scripts/ci_typst_build.sh and publish.py's pandoc_command() disagree on "
        "the lua filter chain — the CI typst build no longer matches what users run"
    )


def test_script_uses_the_same_template_and_style():
    assert template_assets("--template") == script_assets("--template")
    assert template_assets("--csl") == script_assets("--csl")


def test_script_keeps_citation_processing():
    assert "--citeproc" in COMMAND
    assert "--citeproc" in SCRIPT


def test_script_covers_the_same_fixture_corpus():
    # both sides must exclude the non-proposal markdown files
    assert "README.md" in SCRIPT
    assert "guidelines.md" in SCRIPT
