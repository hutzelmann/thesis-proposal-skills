"""`.githooks/pre-push`: a push needs a person at a terminal.

main is the release channel, so the hook refuses any push from a shell without
a controlling terminal (an agent's) and asks once at the maintainer's terminal.
"""

import json
import os
import subprocess

import pytest

if os.name == "posix":
    import fcntl
    import termios
from helpers import REPO

HOOK = REPO / ".githooks" / "pre-push"
REFS = "refs/heads/main 1111111 refs/heads/main 0000000\n"

pytestmark = pytest.mark.skipif(os.name != "posix", reason="the hook's terminal check is POSIX")


def run_hook(stdin: str, *, terminal: str | None = None) -> subprocess.CompletedProcess:
    """Run the hook in a new session, so it has no controlling terminal unless
    `terminal` is given: then a pseudo-terminal becomes the controlling one and
    receives `terminal` as the typed answer."""
    argv = ["sh", str(HOOK), "origin", "git@example.invalid:x.git"]
    if terminal is None:
        return subprocess.run(argv, input=stdin, capture_output=True, text=True,
                              encoding="utf-8", start_new_session=True, timeout=30)
    master, slave = os.openpty()

    def take_terminal() -> None:  # runs in the child, after setsid made it a session leader
        fcntl.ioctl(slave, termios.TIOCSCTTY, 0)

    try:
        os.write(master, terminal.encode())
        return subprocess.run(argv, input=stdin, capture_output=True, text=True,
                              encoding="utf-8", start_new_session=True, pass_fds=(slave,),
                              preexec_fn=take_terminal, timeout=30)
    finally:
        os.close(master)
        os.close(slave)


def test_hook_is_executable():
    assert os.access(HOOK, os.X_OK)


def test_a_push_without_a_terminal_is_refused():
    run = run_hook(REFS)
    assert run.returncode == 1
    assert "refused: no terminal" in run.stderr


def test_nothing_to_push_passes_without_asking():
    assert run_hook("").returncode == 0


def test_the_maintainer_confirms_at_the_terminal():
    assert run_hook(REFS, terminal="y\n").returncode == 0


@pytest.mark.parametrize("answer", ["\n", "n\n", "no\n"])
def test_anything_but_yes_cancels(answer):
    run = run_hook(REFS, terminal=answer)
    assert run.returncode == 1
    assert "push cancelled" in run.stderr


def test_settings_deny_every_push_form():
    deny = json.loads((REPO / ".claude" / "settings.json").read_text(encoding="utf-8"))
    rules = set(deny["permissions"]["deny"])
    for form in ("git push", "rtk git push", "/usr/bin/git push"):
        assert f"Bash({form})" in rules, form
        assert f"Bash({form} *)" in rules, form
