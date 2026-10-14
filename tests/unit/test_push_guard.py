"""`.githooks/pre-push`: a push needs a person at a terminal.

Every push is the maintainer's, so the hook refuses any push from a shell
without a controlling terminal (an agent's) and asks once at the maintainer's
terminal. The question says what the push reaches: a push that moves the
remote's `main`, the release channel, releases to every user; any other push
(`develop`, another branch, a tag) reaches no installer.
"""

import json
import os
import select
import subprocess
from dataclasses import dataclass

import pytest

if os.name == "posix":
    import fcntl
    import termios
from helpers import REPO

HOOK = REPO / ".githooks" / "pre-push"
# git's pre-push stdin: <local ref> <local sha> <remote ref> <remote sha>
MAIN = "refs/heads/main 1111111 refs/heads/main 0000000\n"
DEVELOP = "refs/heads/develop 2222222 refs/heads/develop 0000000\n"
DEVELOP_AS_MAIN = "refs/heads/develop 2222222 refs/heads/main 0000000\n"
TAG = "refs/tags/v0.9.0 3333333 refs/tags/v0.9.0 0000000\n"
RELEASES = "This releases to every user."
NO_INSTALLER = "This reaches no installer."

pytestmark = pytest.mark.skipif(os.name != "posix", reason="the hook's terminal check is POSIX")


@dataclass(frozen=True)
class HookRun:
    returncode: int
    stderr: str
    terminal: str  # what the hook wrote to its controlling terminal ("" without one)


def _drain(fd: int) -> str:
    """Everything waiting on the master side of a pseudo-terminal."""
    out = b""
    while select.select([fd], [], [], 0.2)[0]:
        try:
            chunk = os.read(fd, 4096)
        except OSError:  # EIO: nothing left on a closed slave side
            break
        if not chunk:
            break
        out += chunk
    return out.decode("utf-8", errors="replace")


def run_hook(stdin: str, *, terminal: str | None = None) -> HookRun:
    """Run the hook in a new session, so it has no controlling terminal unless
    `terminal` is given: then a pseudo-terminal becomes the controlling one,
    receives `terminal` as the typed answer, and its output is returned."""
    argv = ["sh", str(HOOK), "origin", "git@example.invalid:x.git"]
    if terminal is None:
        run = subprocess.run(argv, input=stdin, capture_output=True, text=True,
                             encoding="utf-8", start_new_session=True, timeout=30)
        return HookRun(run.returncode, run.stderr, "")
    master, slave = os.openpty()

    def take_terminal() -> None:  # runs in the child, after setsid made it a session leader
        fcntl.ioctl(slave, termios.TIOCSCTTY, 0)

    try:
        os.write(master, terminal.encode())
        run = subprocess.run(argv, input=stdin, capture_output=True, text=True,
                             encoding="utf-8", start_new_session=True, pass_fds=(slave,),
                             preexec_fn=take_terminal, timeout=30)
        return HookRun(run.returncode, run.stderr, _drain(master))
    finally:
        os.close(master)
        os.close(slave)


def test_hook_is_executable():
    assert os.access(HOOK, os.X_OK)


@pytest.mark.parametrize("refs", [MAIN, DEVELOP, TAG], ids=["main", "develop", "tag"])
def test_a_push_without_a_terminal_is_refused(refs):
    run = run_hook(refs)
    assert run.returncode == 1
    assert "refused: no terminal" in run.stderr


def test_nothing_to_push_passes_without_asking():
    assert run_hook("").returncode == 0


def test_the_maintainer_confirms_at_the_terminal():
    assert run_hook(MAIN, terminal="y\n").returncode == 0


@pytest.mark.parametrize("refs", [MAIN, DEVELOP], ids=["main", "develop"])
@pytest.mark.parametrize("answer", ["\n", "n\n", "no\n"])
def test_anything_but_yes_cancels(refs, answer):
    run = run_hook(refs, terminal=answer)
    assert run.returncode == 1
    assert "push cancelled" in run.stderr


# git sends one line per refspec in command-line order, so a line after main's
# must not reset the wording; the release push is what scripts/changelog.py prints
@pytest.mark.parametrize("refs", [MAIN, DEVELOP + MAIN, DEVELOP_AS_MAIN, TAG + MAIN,
                                  MAIN + DEVELOP, DEVELOP + MAIN + TAG],
                         ids=["main", "develop-and-main", "develop-as-main", "tag-and-main",
                              "main-first", "release-push"])
def test_a_push_that_moves_main_says_it_releases(refs):
    run = run_hook(refs, terminal="y\n")
    assert run.returncode == 0
    assert RELEASES in run.terminal
    assert NO_INSTALLER not in run.terminal


@pytest.mark.parametrize("refs", [DEVELOP, TAG, DEVELOP + TAG],
                         ids=["develop", "tag", "develop-and-tag"])
def test_a_push_that_leaves_main_says_it_reaches_no_installer(refs):
    run = run_hook(refs, terminal="y\n")
    assert run.returncode == 0
    assert NO_INSTALLER in run.terminal
    assert "releases" not in run.terminal


def test_the_question_names_the_refs_and_the_remote():
    run = run_hook(DEVELOP + TAG, terminal="n\n")
    assert f"Push develop refs/tags/v0.9.0 to origin? {NO_INSTALLER} [y/N]" in run.terminal


def test_settings_deny_every_push_form():
    deny = json.loads((REPO / ".claude" / "settings.json").read_text(encoding="utf-8"))
    rules = set(deny["permissions"]["deny"])
    for form in ("git push", "rtk git push", "/usr/bin/git push"):
        assert f"Bash({form})" in rules, form
        assert f"Bash({form} *)" in rules, form
