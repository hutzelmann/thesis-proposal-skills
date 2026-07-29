#!/usr/bin/env python3
"""Print a storyboard shot from transcript.jsonl into the terminal.

Usage: python3 docs/demo/replay.py --shot 1|2|3
Screenshot the terminal to regenerate the README images (stdlib only).
"""

import argparse
import json
import textwrap
from pathlib import Path

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
CYAN = "\033[36m"

# Scenes are the clear-delimited sections of the transcript, 0-indexed.
SHOTS = {1: [0], 2: [2], 3: [4, 5]}


def scenes() -> list[list[dict]]:
    transcript = Path(__file__).parent / "transcript.jsonl"
    result: list[list[dict]] = [[]]
    for line in transcript.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        if event.get("clear") and result[-1]:
            result.append([])
        result[-1].append(event)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shot", type=int, choices=sorted(SHOTS), required=True)
    args = parser.parse_args()

    print("\033[2J\033[H", end="")
    for index in SHOTS[args.shot]:
        for event in scenes()[index]:
            text = event["text"]
            if event["role"] == "user":
                wrapped = textwrap.fill(text, width=76, subsequent_indent="  ")
                print(f"{BOLD}{GREEN}❯ {RESET}{BOLD}{wrapped}{RESET}\n")
            elif event["role"] == "agent":
                print(f"{text}\n")
            elif event["role"] == "tool":
                print(f"{DIM}{CYAN}  ⚙ {text}{RESET}\n")


if __name__ == "__main__":
    main()
