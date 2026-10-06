"""The workspace after a sandboxed run, before the harness reads or writes in it.

A host's sandbox lets the model's shell write the run's workspace, and making a
link never touches its target, so a run whose every shell call was confined can
still leave a link, a FIFO, a socket, a device or a hard link there — or the
workspace itself replaced — which the harness, not sandboxed, would then follow:
into the verdicts and the judge's prompt, into the event file it writes, into a
scrub. `breach` checks the workspace right after the child, before any of that,
and removes each such entry without following it: the link goes, its target
stays untouched. The check fails closed (revised 2026-10-07): a directory the
shell closed to its owner (mode 0300, say) would hide its links from a walk
while the harness could still open a fixed name in it, so the workspace and
every directory in it must stay owner-`rwx`, and a listing error or an entry
`lstat` cannot read is a breach too; such a directory is named, never chmodded
or reopened. Shared by the Copilot host (`copilot_cli.workspace_breach`,
which also scrubs the token from its message; add-copilot-dev-runner design
Decision 13) and the Codex host (`codex_cli`; add-codex-dev-runner design
Decision 16, the user's decision D-d). Stdlib only; imports nothing of the
harness.
"""

from __future__ import annotations

import os
import stat
from collections.abc import Callable, Iterator
from contextlib import suppress
from pathlib import Path

WORKSPACE_REPLACED = ("the workspace itself was replaced (by a link or another directory), so "
                      "the harness read nothing in it")
SHOWN_ENTRIES = 5
# what the harness needs of every directory it walks: read (to list), write
# (to unlink an entry) and search (to reach one)
OWNER_RWX = stat.S_IRWXU
CLOSED = "a directory closed to its owner"
UNREADABLE = "an entry the harness could not examine"


def closed_dir(mode: int) -> str | None:
    """Why a directory with this mode cannot be checked: it is not open to
    its owner for reading, writing and search (`OWNER_RWX`), so a walk would
    pass over what it holds. Pure."""
    if stat.S_IMODE(mode) & OWNER_RWX == OWNER_RWX:
        return None
    return f"{CLOSED} (mode {stat.S_IMODE(mode):04o})"


def unsafe_entry(mode: int, links: int) -> str | None:
    """Why the harness must not follow, read or write a workspace entry: a
    link (it would act on the link's target), a FIFO, socket or device, a
    regular file with another name elsewhere (a hard link, whose content is
    another file's), or a directory closed to its owner (`closed_dir`). An
    owner-`rwx` directory or a singly linked regular file is safe."""
    if stat.S_ISDIR(mode):
        return closed_dir(mode)
    if stat.S_ISLNK(mode):
        return "a link"
    if not stat.S_ISREG(mode):
        return "not a regular file"
    return "a hard link" if links > 1 else None


def workspace_entries(root: Path, failed: Callable[[Path], None] | None = None
                      ) -> Iterator[tuple[Path, os.stat_result]]:
    """Every entry under `root`, by `lstat`, without following a link: a link
    to a directory is listed, never descended into. A directory the walk
    cannot list, and an entry `lstat` cannot read, go to `failed` (passed
    over silently without one)."""
    report = failed or (lambda _path: None)
    for top, dirs, files in os.walk(root, followlinks=False,
                                    onerror=lambda error: report(Path(error.filename or root))):
        for name in sorted((*dirs, *files)):
            path = Path(top, name)
            try:
                info = os.lstat(path)
            except OSError:
                report(path)
                continue
            yield path, info


def unsafe_entries(root: Path) -> list[tuple[Path, str]]:
    """The entries under `root` the harness must not follow (`unsafe_entry`),
    each with why, and every directory the walk could not list or entry it
    could not examine, each once; nothing is read."""
    found: dict[Path, str] = {}
    unreadable: list[Path] = []
    for path, info in workspace_entries(root, unreadable.append):
        why = unsafe_entry(info.st_mode, info.st_nlink)
        if why:
            found[path] = why
    for path in unreadable:
        found.setdefault(path, UNREADABLE)
    return list(found.items())


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


def closed_root(ws: Path) -> str | None:
    """Why the workspace directory itself cannot be checked (`closed_dir`),
    read by `lstat` and never opened; None when it is open to its owner."""
    try:
        return closed_dir(os.lstat(ws).st_mode)
    except OSError:
        return UNREADABLE


def breach(ws: Path, identity: tuple[int, int] | None) -> str | None:
    """Why the workspace cannot be read after the run, or None: the workspace
    replaced (`replaced`) or itself closed to its owner (`closed_root`), so
    nothing in it is read; or entries `unsafe_entries` names, each link, FIFO,
    socket, device or hard link unlinked without being followed (a closed
    directory, or an entry that could not be examined, stays as it is, never
    chmodded or reopened). Names at most SHOWN_ENTRIES entries and never
    reads one; a caller with a secret to keep out scrubs the message."""
    if replaced(ws, identity):
        return WORKSPACE_REPLACED
    closed = closed_root(ws)
    if closed:
        return (f"the workspace itself is {closed}, so the harness checked and read nothing in "
                "it and must not follow what it may hold")
    found = unsafe_entries(ws)
    for path, why in found:
        if not why.startswith((CLOSED, UNREADABLE)):
            with suppress(OSError):
                path.unlink()  # the entry itself, never a link's target
    if not found:
        return None
    named = ", ".join(f"{path.relative_to(ws).as_posix()} ({why})"
                      for path, why in found[:SHOWN_ENTRIES])
    more = f" and {len(found) - SHOWN_ENTRIES} more" if len(found) > SHOWN_ENTRIES else ""
    kept = any(why.startswith((CLOSED, UNREADABLE)) for _path, why in found)
    note = ("removed unread, a directory or entry it could not check left as it is" if kept
            else "removed unread")
    return f"the workspace held entries the harness must not follow, {note}: {named}{more}"
