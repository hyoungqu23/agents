"""Workspace files: lock, journal, init intent and atomic file replacement."""

import errno
import os
import re
import shutil
import time
from contextlib import contextmanager
from pathlib import Path

from .contracts import StudyError, check, dumps_line, fail, loads

JOURNAL = "records/events.jsonl"
LOCK = "records/.lock"
INTENT = "records/.init.json"
TEMP_NAME = re.compile(
    r"^\.study-loop-(init|events)-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}(-\d+)?\.tmp$"
)
# Finder drops .DS_Store into any folder it shows; it is not user data.
IGNORED_NAMES = {".DS_Store"}
NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)


def _fsync_dir(path):
    if os.name == "nt":
        return  # ponytail: Windows cannot fsync a directory handle.
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _lock_fd(fd):
    if os.name == "nt":
        import msvcrt

        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
    else:
        import fcntl

        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)


def _unlock_fd(fd):
    if os.name == "nt":
        import msvcrt

        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
    else:
        import fcntl

        fcntl.flock(fd, fcntl.LOCK_UN)


class Store:
    def __init__(self, root):
        self.root = Path(root)
        self.records = self.root / "records"
        self.journal = self.root / JOURNAL

    # ---- paths ------------------------------------------------------------

    def inside(self, relative, area=None):
        """Resolve a workspace-relative path; refuse escapes and links that leave it."""
        if "\x00" in relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
            fail("PATH_OUTSIDE_WORKSPACE", f"{relative} is not a path inside the workspace")
        try:
            root = self.root.resolve()
            target = (self.root / relative).resolve()
            base = (self.root / area).resolve() if area else root
        except (OSError, RuntimeError) as error:
            fail("INVALID_REQUEST", f"{relative} is not a usable path: {error}")
        if base != root and root not in base.parents:
            fail("PATH_OUTSIDE_WORKSPACE", f"{area}/ itself resolves outside the workspace")
        if target != base and base not in target.parents:
            where = f"{area}/" if area else "the workspace"
            fail("PATH_OUTSIDE_WORKSPACE", f"{relative} resolves outside {where}")
        return target

    # ---- journal ----------------------------------------------------------

    def initialized(self):
        return self.journal.exists()

    def read_commits(self):
        try:
            data = self.journal.read_bytes()
        except OSError as error:
            fail("WRITE_FAILED", f"cannot read journal: {error}")
        if not data.endswith(b"\n"):
            fail("CORRUPT_JOURNAL", "journal does not end with a complete line")
        commits = []
        for number, line in enumerate(data[:-1].split(b"\n"), 1):
            try:
                commits.append(loads(line))
            except (ValueError, UnicodeDecodeError) as error:
                fail("CORRUPT_JOURNAL", f"journal line {number} is not valid JSON: {error}")
        return commits

    def _new_temp(self, directory, stem):
        """Create a fresh temp file; never reuse or overwrite an earlier one."""
        suffix = 0
        while True:
            name = f"{stem}.tmp" if suffix == 0 else f"{stem}-{suffix}.tmp"
            path = directory / name
            try:
                fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | NOFOLLOW, 0o644)
                return path, fd
            except FileExistsError:
                suffix += 1

    def append(self, commit, operation_id):
        """Copy the journal plus one new line into a temp file, then replace it."""
        try:
            temp, fd = self._new_temp(self.records, f".study-loop-events-{operation_id}")
            with os.fdopen(fd, "wb") as out:
                if self.journal.exists():
                    with open(self.journal, "rb") as source:
                        shutil.copyfileobj(source, out)
                out.write(dumps_line(commit) + b"\n")
                out.flush()
                os.fsync(out.fileno())
        except OSError as error:
            fail("WRITE_FAILED", f"journal was not changed: {error}")
        try:
            os.replace(temp, self.journal)
            _fsync_dir(self.records)
        except OSError as error:
            raise StudyError(
                "COMMIT_STATUS_UNKNOWN",
                f"journal replacement could not be confirmed: {error}",
                committed=None,
            )

    # ---- lock -------------------------------------------------------------

    @contextmanager
    def lock(self, timeout=2.0):
        try:
            self.records.mkdir(exist_ok=True)  # never creates a missing workspace
            fd = os.open(self.root / LOCK, os.O_RDWR | os.O_CREAT | NOFOLLOW, 0o644)
        except OSError as error:
            if error.errno == errno.ELOOP:
                fail("PATH_OUTSIDE_WORKSPACE", "records/.lock must not be a link")
            fail("WRITE_FAILED", f"cannot open lock file: {error}")
        try:
            deadline = time.monotonic() + timeout
            while True:
                try:
                    _lock_fd(fd)
                    break
                except OSError as error:
                    if error.errno not in (errno.EAGAIN, errno.EACCES, errno.EWOULDBLOCK, errno.EDEADLK):
                        fail("WRITE_FAILED", f"cannot lock workspace: {error}")
                    if time.monotonic() >= deadline:
                        fail("LOCK_BUSY", f"another process holds {LOCK}")
                    time.sleep(0.05)
            try:
                yield
            finally:
                _unlock_fd(fd)
        finally:
            os.close(fd)

    # ---- atomic files -----------------------------------------------------

    def write_atomic(self, relative, data):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        temp, fd = self._new_temp(path.parent, f".{path.name}")
        try:
            with os.fdopen(fd, "wb") as out:
                out.write(data)
                out.flush()
                os.fsync(out.fileno())
            os.replace(temp, path)
        except OSError:
            if temp.exists():
                temp.unlink()
            raise

    # ---- first initialization --------------------------------------------

    def check_uninitialized(self):
        """Allow only user inputs and this engine's own partial-init files."""
        if not self.root.exists():
            return
        if not self.root.is_dir() or self.root.is_symlink():
            fail("WORKSPACE_NOT_EMPTY", f"{self.root} is not a directory")
        for entry in self.root.iterdir():
            if entry.name in IGNORED_NAMES:
                continue
            if entry.name == "learner.md" and entry.is_file() and not entry.is_symlink():
                continue
            if entry.name == "materials" and entry.is_dir() and not entry.is_symlink():
                continue
            if entry.name == "records" and entry.is_dir() and not entry.is_symlink():
                continue
            fail("WORKSPACE_NOT_EMPTY", f"{entry.name} is not a study-loop or learner file")
        if not self.records.exists():
            return
        has_events_temp = False
        for entry in self.records.iterdir():
            if entry.is_symlink():
                fail("WORKSPACE_NOT_EMPTY", f"records/{entry.name} is a link")
            if entry.name == ".lock":
                head = entry.read_bytes()[:1]
                if head not in (b"", b"0"):
                    fail("WORKSPACE_NOT_EMPTY", "records/.lock is not an engine lock file")
            elif entry.name == ".init.json":
                continue
            elif TEMP_NAME.match(entry.name):
                has_events_temp = has_events_temp or entry.name.startswith(".study-loop-events-")
            else:
                fail("WORKSPACE_NOT_EMPTY", f"records/{entry.name} is not an engine file")
        if has_events_temp and self.read_intent() is None:
            fail("WORKSPACE_NOT_EMPTY", "a journal temp file exists without a valid init intent")

    def read_intent(self):
        path = self.root / INTENT
        if not path.exists():
            return None
        try:
            intent = loads(path.read_bytes())
        except (ValueError, UnicodeDecodeError):
            fail("WORKSPACE_NOT_EMPTY", "records/.init.json is not valid JSON")
        problem = check(intent, "InitIntent")
        if problem:
            fail("WORKSPACE_NOT_EMPTY", f"records/.init.json is not a valid init intent: {problem}")
        return intent

    def write_intent(self, intent):
        temp, fd = self._new_temp(self.records, f".study-loop-init-{intent['request']['operationId']}")
        try:
            with os.fdopen(fd, "wb") as out:
                out.write(dumps_line(intent) + b"\n")
                out.flush()
                os.fsync(out.fileno())
            os.replace(temp, self.root / INTENT)
            _fsync_dir(self.records)
        except OSError as error:
            fail("WRITE_FAILED", f"cannot record init intent: {error}")
