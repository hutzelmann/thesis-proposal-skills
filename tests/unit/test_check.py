"""L0: deterministic check script against blueprint fixtures (skill-check spec)."""

import pytest
from helpers import FIXTURES, run_check


def test_clean_fixture_passes():
    result = run_check(FIXTURES / "f00-clean-en" / "ml-code-review.md")
    assert result.returncode == 0, result.stdout
    assert "no errors" in result.stdout
    assert "WARNING" not in result.stdout


def test_digest_line_identifies_checked_content(tmp_path):
    """Read-only tripwire (skill-check spec): digest present, stable, content-bound."""
    import hashlib

    source = (FIXTURES / "f00-clean-en" / "ml-code-review.md").read_bytes()
    proposal = tmp_path / "ml-code-review.md"
    proposal.write_bytes(source)
    first = run_check(proposal).stdout
    expected = hashlib.sha256(source).hexdigest()
    assert f"digest: sha256:{expected}" in first
    # unchanged file -> identical digest line
    assert f"digest: sha256:{expected}" in run_check(proposal).stdout
    # changed file -> digest line differs
    proposal.write_bytes(source + b"\n<!-- drift -->\n")
    assert f"digest: sha256:{expected}" not in run_check(proposal).stdout


def test_broken_fixture_trips_guardrails():
    result = run_check(FIXTURES / "f15-format-broken" / "broken-format.md")
    assert result.returncode == 1
    out = result.stdout
    assert "no blank line before the trailing" in out
    assert "boolean literal" in out
    assert "duplicate reference id `Lee24Index`" in out
    assert "cited key `@Ghost99Missing` not defined" in out
    assert "only 2 references" in out
    assert out.count("open [TODO:") == 2
    assert "`author:` found — proposals are anonymous by default" in out


def test_override_workspace_changes_verdicts():
    result = run_check(FIXTURES / "w02-override-workspace" / "ml-code-review.md")
    out = result.stdout
    # timeline heading is un-forbidden by the workspace TOML override
    assert "forbidden section" not in out
    # raised minimum is enforced
    assert "at least 8 required" in out


def test_detailed_timeline_needs_the_override(tmp_path):
    """Same file, without the guidelines.md that selects the detailed mode:
    the phase table under `# Timeline` is then a size-guard error."""
    source = (FIXTURES / "w02-override-workspace" / "ml-code-review.md").read_text()
    victim = tmp_path / "ml-code-review.md"
    victim.write_text(source)  # no guidelines.md next to it -> timeline_detail defaults to simple
    result = run_check(victim)
    assert "table in `Timeline`" in result.stdout
    assert "forbidden section: `Timeline`" not in result.stdout  # it is a canonical title now


def test_detailed_mode_also_unforbids_work_plan_headings(tmp_path):
    source = (FIXTURES / "f00-clean-en" / "ml-code-review.md").read_text()
    victim = tmp_path / "ml-code-review.md"
    victim.write_text(source.replace("# Timeline", "# Timeline and Milestones"))
    (tmp_path / "guidelines.md").write_text('```toml\ntimeline_detail = "detailed"\n```\n')
    result = run_check(victim)
    assert "matches `milestones`" not in result.stdout


def test_work_plan_headings_stay_forbidden_by_default(tmp_path):
    source = (FIXTURES / "f00-clean-en" / "ml-code-review.md").read_text()
    victim = tmp_path / "ml-code-review.md"
    victim.write_text(source.replace("# Timeline", "# Timeline and Milestones"))
    result = run_check(victim)
    assert "matches `milestones`" in result.stdout


def test_unknown_timeline_detail_is_reported(tmp_path):
    source = (FIXTURES / "f00-clean-en" / "ml-code-review.md").read_text()
    victim = tmp_path / "ml-code-review.md"
    victim.write_text(source)
    (tmp_path / "guidelines.md").write_text('```toml\ntimeline_detail = "gantt"\n```\n')
    result = run_check(victim)
    assert "unknown timeline_detail `gantt`" in result.stdout
    assert result.returncode == 1


def test_level2_sections_still_checked(tmp_path):
    source = (FIXTURES / "f00-clean-en" / "ml-code-review.md").read_text()
    demoted = source.replace("\n# ", "\n## ").replace("\n## Previous", "\n### Previous").replace(
        "\n## Requirements", "\n### Requirements").replace("\n## Evaluation", "\n### Evaluation")
    demoted = demoted.replace("(RQ3)", "")  # break one cross-ref
    victim = tmp_path / "demoted.md"
    victim.write_text(demoted)
    result = run_check(victim)
    assert "(RQ3) never referenced" in result.stdout


def with_extra_research_questions(source: str, count: int) -> str:
    """Extend f00's three-question list to `count`, keeping every (RQn) cross-ref."""
    added = "".join(
        f"{n}. To what degree does review latency change under configuration {n}?\n"
        for n in range(4, count + 1)
    )
    body = source.replace(
        "3. How does model performance vary across different programming "
        "languages and project domains?\n",
        "3. How does model performance vary across different programming "
        "languages and project domains?\n" + added,
    )
    refs = "".join(f" This is answered by measuring latency (RQ{n}).\n"
                   for n in range(4, count + 1))
    return body.replace("\n# Timeline", refs + "\n# Timeline")


def test_too_many_research_questions_errors(tmp_path):
    """The count bounds scope, and scope is exactly what an over-long list has
    not decided. Six questions is a second thesis hiding in the first."""
    source = (FIXTURES / "f00-clean-en" / "ml-code-review.md").read_text()
    victim = tmp_path / "six-questions.md"
    victim.write_text(with_extra_research_questions(source, 6))
    result = run_check(victim)
    assert result.returncode == 1
    assert "6 research questions — at most 5 allowed" in result.stdout


def test_research_questions_at_the_bound_pass(tmp_path):
    """Five is allowed: the rule is an upper bound, not a target of three."""
    source = (FIXTURES / "f00-clean-en" / "ml-code-review.md").read_text()
    victim = tmp_path / "five-questions.md"
    victim.write_text(with_extra_research_questions(source, 5))
    result = run_check(victim)
    assert "research questions — at most" not in result.stdout


def test_multiple_metadata_blocks_error(tmp_path):
    source = (FIXTURES / "f00-clean-en" / "ml-code-review.md").read_text()
    victim = tmp_path / "double.md"
    victim.write_text("---\ntitle: front\n---\n\n" + source)
    result = run_check(victim)
    assert "additional metadata block" in result.stdout


def with_nameless_references(source: str, sentence: str) -> str:
    """Append an authorless and an editor-only reference, and cite them."""
    lines = source.rstrip("\n").split("\n")
    extra = [
        "- id: NoName01Standard",
        "  type: webpage",
        "  title: Model monitoring practices",
        "  issued:",
        "    year: 2001",
        "- id: Ed02Collected",
        "  type: book",
        "  title: Collected works on drift",
        "  editor:",
        "  - family: Klein",
        "    given: Karl",
        "  issued:",
        "    year: 2002",
    ]
    body = "\n".join(lines[:-1] + extra + [lines[-1]]) + "\n"
    return body.replace("# Introduction to the Topic",
                        "# Introduction to the Topic\n\n" + sentence, 1)


def test_author_in_text_citation_of_authorless_reference_warns(tmp_path):
    source = (FIXTURES / "f00-clean-en" / "ml-code-review.md").read_text()
    victim = tmp_path / "nameless.md"
    victim.write_text(with_nameless_references(source, "@NoName01Standard states this."))
    result = run_check(victim)
    out = result.stdout
    assert "`@NoName01Standard` is cited author-in-text" in out
    assert "use `[@NoName01Standard]` instead" in out
    assert "WARNING" in out


def test_bracketed_citation_of_authorless_reference_is_silent(tmp_path):
    source = (FIXTURES / "f00-clean-en" / "ml-code-review.md").read_text()
    victim = tmp_path / "bracketed.md"
    victim.write_text(with_nameless_references(source, "Reported widely [@NoName01Standard]."))
    result = run_check(victim)
    assert "cited author-in-text" not in result.stdout


def test_author_in_text_citation_of_editor_only_reference_is_silent(tmp_path):
    source = (FIXTURES / "f00-clean-en" / "ml-code-review.md").read_text()
    victim = tmp_path / "editor.md"
    victim.write_text(with_nameless_references(source, "@Ed02Collected collects work."))
    result = run_check(victim)
    assert "cited author-in-text" not in result.stdout


def test_author_metadata_key_warns(tmp_path):
    """Proposals are anonymous; the key renders verbatim on the title page."""
    source = (FIXTURES / "f00-clean-en" / "ml-code-review.md").read_text()
    victim = tmp_path / "named.md"
    victim.write_text(source.replace("\ntitle:", "\nauthor: Erika Musterfrau\ntitle:", 1))
    result = run_check(victim)
    out = result.stdout
    assert "`author:` found — proposals are anonymous by default" in out
    assert "unless your program requires a named cover page" in out
    assert "WARNING" in out
    assert result.returncode == 0, "the author key is advisory, never a failure"


def test_author_placeholder_warns_too(tmp_path):
    """The reported defect: an unfilled placeholder reaching the title page."""
    source = (FIXTURES / "f00-clean-en" / "ml-code-review.md").read_text()
    victim = tmp_path / "todo-author.md"
    victim.write_text(source.replace("\ntitle:", "\nauthor: [TODO: add author]\ntitle:", 1))
    assert "`author:` found" in run_check(victim).stdout


def test_reference_author_fields_do_not_trip_the_key_warning():
    """f00 has `author:` inside every reference entry — indented, so not the key."""
    result = run_check(FIXTURES / "f00-clean-en" / "ml-code-review.md")
    assert "`author:` found" not in result.stdout


def with_sentence(source: str, sentence: str) -> str:
    return source.replace("# Introduction to the Topic",
                          "# Introduction to the Topic\n\n" + sentence, 1)


def check_sentence(tmp_path, sentence: str, name: str = "typed.md") -> str:
    """f00's first reference is Chen25Learning, authored by Chen and Novak."""
    source = (FIXTURES / "f00-clean-en" / "ml-code-review.md").read_text()
    victim = tmp_path / name
    victim.write_text(with_sentence(source, sentence))
    return run_check(victim).stdout


@pytest.mark.parametrize("sentence", [
    "Chen et al. [@Chen25Learning] propose a detector.",
    "The approach of Chen [@Chen25Learning] is broader.",
    "Chen and Novak [@Chen25Learning] argue otherwise.",
])
def test_typed_author_name_before_bracketed_citation_warns(tmp_path, sentence):
    out = check_sentence(tmp_path, sentence)
    assert "author name typed before `[@Chen25Learning]`" in out
    assert "write `@Chen25Learning` alone" in out


def test_typed_author_name_before_author_in_text_citation_warns(tmp_path):
    """This one renders the name twice — "Chen et al. Chen et al. [1]"."""
    out = check_sentence(tmp_path, "Chen et al. @Chen25Learning propose a detector.")
    assert "author name typed before `@Chen25Learning`" in out
    assert "renders twice" in out


@pytest.mark.parametrize("sentence", [
    "Deployments in Germany [@Chen25Learning] differ.",      # proper noun, not an author
    "@Chen25Learning propose a drift detector.",             # the correct form
    "the detector of @Chen25Learning is broader.",           # possessor, also correct
    "Degradation is widely reported [@Chen25Learning].",     # evidence form
    "Chen studied this. Later work is broader [@Miller23Review].",  # name is not adjacent
])
def test_no_false_positive_for_legitimate_sentences(tmp_path, sentence):
    assert "author name typed" not in check_sentence(tmp_path, sentence)


def test_typed_author_name_of_a_different_reference_is_not_flagged(tmp_path):
    """Anchoring is per-key: Chen is not an author of Miller23Review."""
    out = check_sentence(tmp_path, "Work by Chen is broader [@Miller23Review].")
    assert "author name typed" not in out


def test_typed_author_name_never_fails_the_run(tmp_path):
    source = (FIXTURES / "f00-clean-en" / "ml-code-review.md").read_text()
    victim = tmp_path / "advisory.md"
    victim.write_text(with_sentence(source, "Chen et al. [@Chen25Learning] propose a detector."))
    result = run_check(victim)
    assert "author name typed" in result.stdout
    assert result.returncode == 0, "the typed-name check is advisory, never a failure"


def test_first_person_capitalized_caught(tmp_path):
    source = (FIXTURES / "f00-clean-en" / "ml-code-review.md").read_text()
    victim = tmp_path / "fp.md"
    victim.write_text(source.replace(
        "Software quality assurance relies heavily",
        "We propose a novel approach. Our contribution relies heavily",
    ))
    result = run_check(victim)
    assert "first-person pronouns" in result.stdout


@pytest.mark.parametrize(("key", "reason"), [
    ("RiveraYearSurvey", "literal 'Year' where the year belongs — produced by a real import eval"),
    ("TanakaYearLoRA", "same shape, second key from that run"),
    ("SmithDeep", "no year at all"),
    ("2023Survey", "starts with the year"),
])
def test_malformed_reference_key_warns(tmp_path, key, reason):
    source = (FIXTURES / "f00-clean-en" / "ml-code-review.md").read_text()
    victim = tmp_path / "keys.md"
    victim.write_text(source.replace("- id: Chen25Learning", f"- id: {key}")
                            .replace("@Chen25Learning", f"@{key}"))
    result = run_check(victim)
    assert f"reference id `{key}` does not follow" in result.stdout, reason
    assert result.returncode == 0, "key shape is advisory, never a failure"


def test_overlong_reference_key_warns(tmp_path):
    source = (FIXTURES / "f00-clean-en" / "ml-code-review.md").read_text()
    long_key = "Bacchelli13Expectations"
    victim = tmp_path / "long.md"
    victim.write_text(source.replace("- id: Chen25Learning", f"- id: {long_key}")
                            .replace("@Chen25Learning", f"@{long_key}"))
    out = run_check(victim).stdout
    assert f"`{long_key}` is 23 characters" in out
    assert "does not follow" not in out, "well-formed but long: one complaint, not two"


@pytest.mark.parametrize("key", [
    "Smith26Deep",          # the documented example
    "ENISA24Threat",        # institutional author
    "vanDerAalst16Mining",  # particle-bearing name, 19 chars
])
def test_conforming_reference_keys_stay_silent(tmp_path, key):
    source = (FIXTURES / "f00-clean-en" / "ml-code-review.md").read_text()
    victim = tmp_path / "ok.md"
    victim.write_text(source.replace("- id: Chen25Learning", f"- id: {key}")
                            .replace("@Chen25Learning", f"@{key}"))
    out = run_check(victim).stdout
    assert "does not follow" not in out
    assert "characters — keep keys" not in out


def test_boolean_literal_key_is_not_also_shape_warned(tmp_path):
    """`on` is already an error; one complaint per key is enough."""
    source = (FIXTURES / "f15-format-broken" / "broken-format.md").read_text()
    victim = tmp_path / "bool.md"
    victim.write_text(source)
    out = run_check(victim).stdout
    assert "`on` is a YAML boolean literal" in out
    assert "reference id `on` does not follow" not in out


def inflate(source: str, words: int) -> str:
    """Insert one long single-sentence paragraph into the introduction section.

    One sentence with a unique start, so neither the repeated-sentence-start
    nor the first-person warning can fire on the padding.
    """
    filler = "Padding " + " ".join(f"w{i}" for i in range(words)) + "."
    heading = "# Introduction to the Topic\n"
    return source.replace(heading, heading + "\n" + filler + "\n", 1)


def test_length_estimate_warns_over_limit(tmp_path):
    """Default limit 5 pages at 500 words/page; the overrun is a warning, never
    an error (guidance-model spec: default page limit)."""
    source = (FIXTURES / "f00-clean-en" / "ml-code-review.md").read_text()
    victim = tmp_path / "long.md"
    victim.write_text(inflate(source, 2600))
    result = run_check(victim)
    assert result.returncode == 0, result.stdout
    assert "estimated length" in result.stdout
    assert "5-page limit" in result.stdout
    assert "estimate" in result.stdout


def test_length_estimate_stays_silent_within_limit():
    result = run_check(FIXTURES / "f00-clean-en" / "ml-code-review.md")
    assert "estimated length" not in result.stdout


def test_length_estimate_respects_override(tmp_path):
    """A workspace page_limit both relaxes and tightens the default."""
    source = (FIXTURES / "f00-clean-en" / "ml-code-review.md").read_text()
    victim = tmp_path / "long.md"
    victim.write_text(inflate(source, 2600))
    (tmp_path / "guidelines.md").write_text("```toml\npage_limit = 10\n```\n")
    assert "estimated length" not in run_check(victim).stdout

    tight = tmp_path / "tight"
    tight.mkdir()
    short = tight / "short.md"
    short.write_text(inflate(source, 600))
    (tight / "guidelines.md").write_text("```toml\npage_limit = 1\n```\n")
    out = run_check(short).stdout
    assert "estimated length" in out
    assert "1-page limit" in out


@pytest.mark.parametrize("value", ['"5"', "-1", "0", "nan", "true"])
def test_page_limit_override_must_be_a_positive_number(tmp_path, value):
    """A quoted, negative, zero, non-finite, or boolean value degrades to the
    default with an error — never a crash, never a silently disabled rule
    (skill-check spec: advisory reporting)."""
    source = (FIXTURES / "f00-clean-en" / "ml-code-review.md").read_text()
    victim = tmp_path / "typed.md"
    victim.write_text(source)
    (tmp_path / "guidelines.md").write_text(f"```toml\npage_limit = {value}\n```\n")
    result = run_check(victim)
    assert result.returncode == 1
    assert "page_limit must be a positive number" in result.stdout
    assert "digest: sha256:" in result.stdout


@pytest.mark.parametrize("value", ['"8"', "-5", "true"])
def test_min_references_override_must_be_a_non_negative_integer(tmp_path, value):
    """Same degradation for min_references: error plus the default minimum,
    which the clean fixture satisfies — so no shortfall error alongside."""
    source = (FIXTURES / "f00-clean-en" / "ml-code-review.md").read_text()
    victim = tmp_path / "typed.md"
    victim.write_text(source)
    (tmp_path / "guidelines.md").write_text(f"```toml\nmin_references = {value}\n```\n")
    result = run_check(victim)
    assert result.returncode == 1
    assert "min_references must be a non-negative integer" in result.stdout
    assert "references — at least" not in result.stdout


def test_footer_scopes_clean_verdict():
    """A clean result must say substance was not judged (skill-check spec:
    two-bucket honest reporting)."""
    out = run_check(FIXTURES / "f00-clean-en" / "ml-code-review.md").stdout
    assert "substance is not judged here" in out
    assert "review skill renders that verdict" in out
