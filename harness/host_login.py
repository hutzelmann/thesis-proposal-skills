"""The operator's stored host login, as an isolated configuration links it.

An isolated CLAUDE_CONFIG_DIR (the routing rig's, the dev runner's
`--isolated`) holds a symlink to the stored `.credentials.json`. When the host
refreshes an expired access token it writes a new file by atomic rename, which
replaces the symlink and rotates the refresh token: recorded 2026-10-04 on host
2.1.284, the temp directory took the only valid refresh token with it, and
every later run failed with "OAuth session expired and could not be
refreshed". Nothing else refreshes the stored file on a machine whose sessions
run in the desktop app, so this recurred after every token lifetime.

`keep_login` closes that: it writes a refresh back to the stored login and
restores the link, and it serializes refreshes across concurrent isolated runs,
whose host-side refresh locks live in their separate config directories.
Credential values are copied byte for byte and never printed; only
`expiresAt` is ever read out of them.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from pathlib import Path

CREDENTIALS = ".credentials.json"
LONG_LIVED_TOKEN = "CLAUDE_CODE_OAUTH_TOKEN"
CLAIM_NAME = ".devrun-refresh.claim"
RELOGIN = "run `claude` and enter `/login`"

# Judgment, not host constants (the host's own refresh margin is not
# documented). A run whose stored token expires within the margin is about to
# refresh. The host refreshes on its first request, seconds after start, so a
# holder that has not written back after CLAIM_HOLD_S is not going to; a claim
# twice that old was left by a run that died; waiters outlast one hold.
POLL_S = 0.5
CLAIM_POLL_S = 1.0
REFRESH_MARGIN_S = 300
CLAIM_HOLD_S = 60
CLAIM_STALE_S = 120
CLAIM_WAIT_S = 90


def expires_at(path: Path) -> int | None:
    """The access token's expiry in epoch milliseconds; None when absent or unreadable."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))["claudeAiOauth"]["expiresAt"]
    except (OSError, ValueError, KeyError, TypeError):
        return None
    return value if isinstance(value, int) else None


def needs_refresh(source: Path) -> bool:
    expiry = expires_at(source)
    return expiry is not None and expiry < (time.time() + REFRESH_MARGIN_S) * 1000


def _write_private(path: Path, data: bytes) -> None:
    """Atomic replace through an owner-only temporary file beside `path`
    (`mkstemp` creates it exclusively with mode 0600)."""
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=f"{path.name}.", suffix=".tmp")
    tmp = Path(name)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)


def _relink(link: Path, target: Path) -> None:
    tmp = link.with_name(f"{link.name}.relink")
    tmp.unlink(missing_ok=True)
    tmp.symlink_to(target)
    tmp.replace(link)


def settle(link: Path, target: Path) -> bool:
    """If the host replaced `link`, write a newer login back to `target` and
    restore the link. True when something was written back.

    A replacement that does not expire later is discarded rather than written —
    the stored login may have been renewed meanwhile. When either side is
    unreadable both are left for the next look: the host may not be done with
    its file, and a stored login that vanished was logged out on purpose.
    """
    if link.is_symlink() or not link.exists():
        return False
    fresh, stored = expires_at(link), expires_at(target)
    if fresh is None or stored is None:
        return False
    written = fresh > stored
    if written:
        _write_private(target.resolve(), link.read_bytes())
    _relink(link, target)
    return written


def take_claim(claim: Path, mark: str) -> bool:
    """Create the claim exclusively; an abandoned one is removed for the next try."""
    try:
        with claim.open("x", encoding="utf-8") as fh:
            fh.write(mark)
    except FileExistsError:
        with suppress(FileNotFoundError):
            if time.time() - claim.stat().st_mtime > CLAIM_STALE_S:
                claim.unlink()
        return False
    return True


def release_claim(claim: Path, mark: str) -> None:
    """Remove the claim only while it still carries this run's mark."""
    with suppress(OSError):
        if claim.read_text(encoding="utf-8") == mark:
            claim.unlink()


def acquire_claim(source: Path, mark: str) -> Path | None:
    """The refresh claim when this run is about to refresh the stored login,
    None when no refresh is due. Waits a bounded time on another run's claim
    and refuses when that run's refresh never arrives."""
    claim = source.parent / CLAIM_NAME
    deadline = time.monotonic() + CLAIM_WAIT_S
    while needs_refresh(source):
        if take_claim(claim, mark):
            return claim
        if time.monotonic() > deadline:
            sys.exit(
                f"the stored login at {source} has expired and another isolated run "
                f"holds the refresh ({claim}); no refreshed login arrived within "
                f"{CLAIM_WAIT_S}s. Rerun once that run has started; if it keeps "
                f"happening, {RELOGIN}, then rerun."
            )
        time.sleep(CLAIM_POLL_S)
    return None


class _Keeper(threading.Thread):
    """Polls the link while the configuration is in use; releases the claim once
    the refresh is written back or the hold has passed."""

    def __init__(self, link: Path, target: Path, claim: Path | None, mark: str):
        super().__init__(name="keep-login", daemon=True)
        self.link, self.target, self.claim, self.mark = link, target, claim, mark
        self.stopped = threading.Event()
        self.release_at = time.monotonic() + CLAIM_HOLD_S

    def run(self) -> None:
        while not self.stopped.wait(POLL_S):
            try:
                written = settle(self.link, self.target)
            except OSError:
                written = False  # the next look, or the exit check, retries
            if self.claim and (written or time.monotonic() > self.release_at):
                release_claim(self.claim, self.mark)
                self.claim = None


@contextmanager
def keep_login(link: Path) -> Iterator[None]:
    """Keep the stored login behind `link` current while the configuration is
    in use. A configuration without a link (a long-lived token, a prepared
    directory) has nothing to keep."""
    if not link.is_symlink():
        yield
        return
    target = link.readlink()
    if not target.is_absolute():
        target = link.parent / target
    mark = f"{os.getpid()}-{uuid.uuid4().hex}"
    keeper = _Keeper(link, target, acquire_claim(target.resolve(), mark), mark)
    keeper.start()
    try:
        yield
    finally:
        keeper.stopped.set()
        keeper.join()
        try:
            settle(link, target)
        except OSError as exc:
            print(f"could not write the refreshed login back to {target}: "
                  f"{exc.strerror}; if the next run cannot authenticate, {RELOGIN}",
                  file=sys.stderr)
        if keeper.claim:
            release_claim(keeper.claim, mark)
