"""The workspace after a sandboxed run, before the harness reads or writes in it.

A host's sandbox lets the model's shell write the run's workspace, and making a
link never touches its target, so a run whose every shell call was confined can
still leave a link, a FIFO, a socket, a device or a hard link there — or the
workspace itself replaced — which the harness, not sandboxed, would then follow:
into the verdicts and the judge's prompt, into the event file it writes, into a
scrub. `breach` checks the workspace right after the child, before any of that,
and removes each such entry without following it: the link goes, its target
stays untouched. Shared by the Copilot host (`copilot_cli.workspace_breach`,
which also scrubs the token from its message; add-copilot-dev-runner design
Decision 13) and the Codex host (`codex_cli`; add-codex-dev-runner design
Decision 16, the user's decision D-d). Stdlib only; imports nothing of the
harness.
"""

from __future__ import annotations

import os
import stat
from collections.abc import Iterator
from contextlib import suppress
from pathlib import Path

WORKSPACE_REPLACED = ("the workspace itself was replaced (by a link or another directory), so "
                      "the harness read nothing in it")
SHOWN_ENTRIES = 5


def unsafe_entry(mode: int, links: int) -> str | None:
    """Why the harness must not follow, read or write a workspace entry: a
    link (it would act on the link's target), a FIFO, socket or device, or a
    regular file with another name elsewhere (a hard link, whose content is
    another file's). A directory or a singly linked regular file is safe."""
    if stat.S_ISDIR(mode):
        return None
    if stat.S_ISLNK(mode):
        return "a link"
    if not stat.S_ISREG(mode):
        return "not a regular file"
    return "a hard link" if links > 1 else None


def workspace_entries(root: Path) -> Iterator[tuple[Path, os.stat_result]]:
    """Every entry under `root`, by `lstat`, without following a link: a link
    to a directory is listed, never descended into."""
    for top, dirs, files in os.walk(root, followlinks=False):
        for name in sorted((*dirs, *files)):
            path = Path(top, name)
            with suppress(OSError):
                yield path, os.lstat(path)


def unsafe_entries(root: Path) -> list[tuple[Path, str]]:
    """The entries under `root` the harness must not follow (`unsafe_entry`),
    each with why; nothing is read."""
    found = []
    for path, info in workspace_entries(root):
        why = unsafe_entry(info.st_mode, info.st_nlink)
        if why:
            found.append((path, why))
    return found


def workspace_identity(ws: Path) -> tuple[int, int]:
    """The workspace directory's device and inode, taken before any host child
    starts in it."""
    info = os.lstat(ws)
    return info.st_dev, info.st_ino


def replaced(ws: Path, identity: tuple[int, int] | None) -> bool:
    """Whether `ws` is no longer the directory the run started in; a link left
    in its place is removed, never followed."""
    try:
        info = os.lstat(ws)
    except OSError:
        return True
    if stat.S_ISDIR(info.st_mode) and (info.st_dev, info.st_ino) == identity:
        return False
    if stat.S_ISLNK(info.st_mode):
        with suppress(OSError):
            ws.unlink()  # the link itself, never its target
    return True


def breach(ws: Path, identity: tuple[int, int] | None) -> str | None:
    """Why the workspace cannot be read after the run, or None: the workspace
    replaced (`replaced`), or entries `unsafe_entry` names, each unlinked
    without being followed. Names at most SHOWN_ENTRIES entries and never
    reads one; a caller with a secret to keep out scrubs the message."""
    if replaced(ws, identity):
        return WORKSPACE_REPLACED
    found = unsafe_entries(ws)
    for path, _why in found:
        with suppress(OSError):
            path.unlink()  # the entry itself, never a link's target
    if not found:
        return None
    named = ", ".join(f"{path.relative_to(ws).as_posix()} ({why})"
                      for path, why in found[:SHOWN_ENTRIES])
    more = f" and {len(found) - SHOWN_ENTRIES} more" if len(found) > SHOWN_ENTRIES else ""
    return (f"the workspace held entries the harness must not follow, removed unread: "
            f"{named}{more}")
