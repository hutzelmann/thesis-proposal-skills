"""Spike S1 dev runner: thin subprocess wrapper around `claude -p`.

Subscription-authed Claude Code runs live outside Inspect's provider layer
(the agent-bridge proxy breaks OAuth). This wrapper produces plain text that
the same judge path scores. Dev loop only — never the source of record.
"""

from __future__ import annotations

import subprocess


def run_claude(prompt: str, model: str = "haiku", timeout: int = 120) -> str:
    """Run a prompt through Claude Code headless on the subscription. Returns stdout text."""
    result = subprocess.run(
        ["claude", "-p", prompt, "--model", model],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=True,
    )
    return result.stdout.strip()


if __name__ == "__main__":
    import asyncio
    import sys

    from inspect_ai.model import get_model
    from rq_quality_task import GRADING_TEMPLATE, JUDGE_MODEL

    question = (
        "State exactly one research question for a Master's thesis about "
        "machine learning support for code review. Reply with only the research question."
    )
    answer = run_claude(question, model=sys.argv[1] if len(sys.argv) > 1 else "haiku")
    print(f"ANSWER: {answer}\n")

    judge_prompt = GRADING_TEMPLATE.format(
        question=question,
        answer=answer,
        criterion="Analytical research question, not an implementation goal, not yes/no.",
        instructions='End with exactly one line: "GRADE: C" (correct) or "GRADE: I" (incorrect).',
    )
    judgment = asyncio.run(get_model(JUDGE_MODEL).generate(judge_prompt))
    print(f"JUDGE: {judgment.completion[-200:]}")
