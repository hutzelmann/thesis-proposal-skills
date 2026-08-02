#!/usr/bin/env python3
"""Advisory LLM pre-flight for the Gen Agent Trust Hub audit categories.

ATH has no local runner; this approximates its per-skill judgement with one
headless `claude -p` call per skill (subscription-billed, like
claude_runner.py). Advisory only — it is NOT part of the default publish gate:
the real ruleset is unknown and model verdicts vary. Use it to spot obvious
category hits before publishing, never as proof of a pass.

Usage: uv run python harness/audit_llm_preflight.py [--model haiku] [--skill proposal-check]
Exit codes: 0 = no category flagged, 1 = at least one flagged, 2 = runner failure.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "skills"

CATEGORIES = [
    "COMMAND_EXECUTION",
    "PROMPT_INJECTION",
    "EXTERNAL_DOWNLOADS",
    "REMOTE_CODE_EXECUTION",
    "INSECURE_CREDENTIALS",
]

SCRIPT_CHAR_BUDGET = 30_000  # per skill; scripts beyond it are truncated with a marker

PROMPT = """You are a security auditor for AI agent skills, in the style of the \
Gen Agent Trust Hub. Audit ONLY the skill bundle below — its instructions \
(SKILL.md) and shipped scripts — as static content an agent will follow.

For each category, decide whether the bundle exhibits the pattern:
{categories}

Judge instructions the skill gives to an agent (e.g. commands to run, files to \
write, URLs to fetch, secrets to handle) and code the scripts execute. \
Legitimate, documented, read-only API access to public scholarly services is \
not automatically a finding; instructed shell mutation of user paths, \
execution of user-derived strings, or secret values passing through the agent \
are.

Respond with ONLY a JSON object, no prose before or after:
{{"categories": {{"<CATEGORY>": {{"flagged": true/false, "reason": "<one sentence>"}}}}}}

=== SKILL BUNDLE: {name} ===
{bundle}
=== END BUNDLE ==="""


def bundle_skill(skill_dir: Path) -> str:
    parts = [f"--- SKILL.md ---\n{(skill_dir / 'SKILL.md').read_text(encoding='utf-8')}"]
    remaining = SCRIPT_CHAR_BUDGET
    for script in sorted(skill_dir.glob("scripts/*.py")):
        text = script.read_text(encoding="utf-8")
        if len(text) > remaining:
            text = text[:remaining] + "\n# [truncated for the audit bundle]"
        remaining = max(0, remaining - len(text))
        parts.append(f"--- scripts/{script.name} ---\n{text}")
    return "\n\n".join(parts)


def parse_verdict(output: str) -> dict | None:
    """First JSON object in the model output; None when unparseable."""
    match = re.search(r"\{.*\}", output, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0)).get("categories")
    except json.JSONDecodeError:
        return None


def audit_skill(skill_dir: Path, model: str, timeout: int) -> tuple[list[str], dict]:
    prompt = PROMPT.format(
        categories="\n".join(f"- {c}" for c in CATEGORIES),
        name=skill_dir.name,
        bundle=bundle_skill(skill_dir),
    )
    result = subprocess.run(
        ["claude", "-p", prompt, "--model", model],
        stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=timeout,
    )
    if result.returncode != 0:
        sys.exit(f"claude failed on {skill_dir.name}: {result.stderr.strip()[-800:]}")
    verdicts = parse_verdict(result.stdout)
    if verdicts is None:
        sys.exit(f"unparseable verdict for {skill_dir.name}: {result.stdout[-800:]}")
    flagged = [c for c in CATEGORIES if (verdicts.get(c) or {}).get("flagged")]
    return flagged, verdicts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="haiku")
    parser.add_argument("--skill", help="audit one skill instead of all")
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()

    skill_dirs = (
        [SKILLS / args.skill] if args.skill
        else sorted(d for d in SKILLS.iterdir() if d.is_dir() and d.name.startswith("proposal-"))
    )
    any_flagged = False
    for skill_dir in skill_dirs:
        flagged, verdicts = audit_skill(skill_dir, args.model, args.timeout)
        any_flagged |= bool(flagged)
        status = ", ".join(flagged) if flagged else "clean"
        print(f"{skill_dir.name}: {status}")
        for category in flagged:
            print(f"  {category}: {verdicts[category].get('reason', '')[:200]}")
    print("\nadvisory result — not part of the publish gate; the authoritative "
          "ATH verdict only exists on skills.sh")
    return 1 if any_flagged else 0


if __name__ == "__main__":
    sys.exit(main())
