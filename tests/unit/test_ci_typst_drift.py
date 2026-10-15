"""L0: the typst CI build script must not drift from publish.py.

The pandoc/typst image has no Python, so the export matrix cannot run there and
scripts/ci_typst_build.sh restates the typst tier's pandoc invocation. A restated
command can silently stop matching the shipped one — the same class of blind spot
that let the LaTeX tier ship broken. Needs no toolchain, so it runs in the
ordinary CI job alongside the other drift guards.
"""

import itertools
import re
from pathlib import Path

import publish

REPO = Path(__file__).resolve().parents[2]
SCRIPT = (REPO / "scripts" / "ci_typst_build.sh").read_text(encoding="utf-8")

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


def test_script_passes_every_option_the_shipped_command_does():
    """A flag added to the base list — `--resource-path` was one — must reach the
    CI build too, or the tier it guards is no longer the one users run."""
    options = {token.split("=")[0] for token in COMMAND if token.startswith("-")}
    missing = sorted(option for option in options if option not in SCRIPT)
    assert missing == [], f"scripts/ci_typst_build.sh does not pass {missing}"


def test_script_resolves_figures_against_the_proposal_folder():
    """The staged proposal's own folder, as publish.py passes it."""
    assert '--resource-path "$(dirname "$staged")"' in SCRIPT


def test_script_keeps_the_heading_shift():
    """Without the shift the leading H1 title and H2 sections render one level
    off — a silent layout break, not a build failure."""
    assert "--shift-heading-level-by=-1" in COMMAND
    assert "--shift-heading-level-by=-1" in SCRIPT


def test_script_reads_the_folder_layout_alone():
    """No flat fallback: a markdown file at a fixture's root is never built,
    as harness/fixture_paths.py never yields one (w13 keeps a flat proposal
    there for the check to report)."""
    assert '"$fixture"/*.md' not in SCRIPT
    assert '"$fixture"/proposals/*.md' not in SCRIPT
    assert "ends_in_block" not in SCRIPT


def test_script_walks_the_folder_layout():
    """`<fixture>/<slug>/<slug>.md`, or under the `proposals/` location a
    fixture configures, and a nested file only in the folder named by its stem
    (harness/fixture_paths.py walks the same way; test_fixture_paths.py holds
    the two lists equal)."""
    assert '"$fixture"/*/*.md "$fixture"/proposals/*/*.md' in SCRIPT
    assert '[ "$(basename "$(dirname "$proposal")").md" = "$(basename "$proposal")" ]' in SCRIPT


def test_script_fails_when_it_builds_fewer_than_the_oracles():
    """A walk that stops matching after a layout change must fail the job, not
    pass it with nothing built."""
    assert re.search(r'for oracle in "\$FIXTURES"/\*/expected\.json', SCRIPT)
    guard = re.search(r'if \[ "\$built" -eq 0 \] \|\| \[ "\$built" -lt "\$oracles" \]; then'
                      r'(.*?)\nfi', SCRIPT, re.DOTALL)
    assert guard, "no count guard against the oracles"
    message, *_ = guard.group(1).strip().splitlines()
    assert "$built" in message
    assert "$oracles" in message
    assert "exit 1" in guard.group(1)
