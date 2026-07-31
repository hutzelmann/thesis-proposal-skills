"""Pure L1 verdict functions shared by the Inspect scorers and the dev runner.

Every function takes plain strings/paths and returns (passed, explanation).
No sandbox, no model calls — unit-testable and runner-agnostic.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

DRAFT_ALLOWED_ERRORS = ("references — at least",)


def disallowed_errors(check_output: str, allowed: tuple[str, ...] = ()) -> list[str]:
    lines = [l for l in check_output.splitlines() if l.startswith("- ERROR:")]
    return [l for l in lines if not any(a in l for a in allowed)]


def is_enumerated_review(text: str) -> bool:
    return bool(re.search(r"^\s*(1[.)]|#+\s*1)", text, re.MULTILINE)) or bool(
        re.search(r"^\d+[.)]\s", text, re.MULTILINE)
    )


def parse_grade(completion: str) -> bool:
    matches = re.findall(r"GRADE:\s*([CI])", completion)
    return bool(matches) and matches[-1] == "C"


def verdict_draft(proposal_text: str | None, check_output: str) -> tuple[bool, str]:
    """write_from_seed: draft survives and check is clean apart from tolerated errors."""
    if not proposal_text:
        return False, "seed proposal file gone"
    bad = disallowed_errors(check_output, DRAFT_ALLOWED_ERRORS)
    if bad:
        return False, "check errors: " + "; ".join(bad)
    return True, "draft mechanically sound"


def verdict_review(original: str, current: str | None, review: str | None,
                   review_name: str) -> tuple[bool, str]:
    """review_fixture: review file exists, enumerated, proposal untouched."""
    if current != original:
        detail = "file missing" if current is None else (
            f"len {len(original)} -> {len(current)}, first diff at "
            f"{next((i for i, (a, b) in enumerate(zip(original, current, strict=False)) if a != b), min(len(original), len(current)))}"
        )
        return False, f"review modified the proposal ({detail})"
    if not review:
        return False, f"{review_name} not written"
    if not is_enumerated_review(review):
        return False, "review not enumerated"
    return True, "review file present, proposal untouched"


def verdict_check_report(oracle_path: Path, original: str, current: str | None,
                         chat_text: str) -> tuple[bool, str]:
    """check_report: >=3 oracle errors relayed in chat AND proposal byte-identical."""
    oracle = json.loads(oracle_path.read_text(encoding="utf-8"))
    if current != original:
        return False, "check modified the proposal — advisory skill must only report"
    needles = oracle["check"]["errors_contain"]
    # case-insensitive: the skill relays findings as prose, so a finding that
    # opens a sentence arrives capitalised ("Duplicate reference id …"). Case is
    # a property of the sentence, not of the finding.
    lowered = chat_text.lower()
    hits = sum(1 for n in needles if n.split("`")[0].strip().lower() in lowered)
    if hits >= 3:
        return True, f"{hits}/{len(needles)} oracle errors surfaced, file untouched"
    return False, f"only {hits}/{len(needles)} oracle errors surfaced"


IMPORT_ALLOWED_ERRORS = ("references — at least",)

IMPORT_LEAKS = (
    "00000000", "erika@example.org", "prof@example.org", "Prof. Example",
    "CONFIDENTIAL", "INTERNAL USE ONLY",
)


def verdict_import(proposal_text: str | None, check_output: str = "",
                   filename: str = "") -> tuple[bool, str]:
    """import_messy: mechanically sound, nothing leaked, citations converted.

    Format is established by the check script, not by looking for characteristic
    substrings — an unclosed metadata block and a mapping-shaped reference list
    both contain "---" and "references" while being unusable. Only the
    reference-count shortfall is tolerated: the source carries what it carries
    and import must not invent sources.

    The leak and typed-name assertions stay here because the check cannot make
    them: it does not know this source's personal data, and a name carried over
    from a rendered citation is legal markdown.
    """
    if not proposal_text:
        return False, "no proposal file produced"
    problems = [
        l.removeprefix("- ERROR:").strip()
        for l in disallowed_errors(check_output, IMPORT_ALLOWED_ERRORS)
    ]
    for leak in IMPORT_LEAKS:
        if leak in proposal_text:
            problems.append(f"personal/confidential data leaked: {leak}")
    # a TODO marker as a bare line in the trailing block has no key, so pandoc
    # rejects the whole block and the file cannot build. Verified: only this
    # shape breaks — `title: [TODO: …]` and `title: "[TODO: …]"` both parse.
    # check.py cannot see it, extracting narrowly rather than parsing YAML.
    lines = proposal_text.rstrip("\n").split("\n")
    delims = [i for i, l in enumerate(lines) if l.strip() == "---"]
    if len(delims) >= 2 and any(
        l.strip().startswith("[TODO:") for l in lines[delims[-2]:]
    ):
        problems.append("[TODO: …] as a bare line in the metadata block — the YAML does not parse")
    body = proposal_text.rsplit("\n---", 1)[0]
    for pattern in (r"et al\.\s*\[@", r"\b(?:Rivera|Tanaka)\b[^.\[\]]*\[@"):
        if m := re.search(pattern, body):
            problems.append(f"author name typed before a bracketed citation: {m.group(0)!r}")
            break
    if problems:
        return False, "; ".join(problems[:4])
    return True, f"standard file {filename or ''}, stripped clean".replace("  ", " ")


def verdict_seed(seed_text: str | None, filename: str = "") -> tuple[bool, str]:
    """ideate: seeded file structurally complete."""
    if not seed_text:
        return False, "no seeded proposal file"
    problems = []
    if "\n---" not in seed_text:
        problems.append("no metadata block")
    if "[TODO:" not in seed_text:
        problems.append("no TODO markers")
    if "references" not in seed_text:
        problems.append("no references key")
    if problems:
        return False, "; ".join(problems) + (f" in {filename}" if filename else "")
    return True, f"seed file {filename or ''} structurally complete".strip()
