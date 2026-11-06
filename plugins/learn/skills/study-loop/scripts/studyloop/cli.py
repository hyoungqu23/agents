"""One JSON request in, one JSON response out. Owns the clock, lock and files."""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import reducer, views
from .contracts import (
    EVENT_TYPE, EXIT_CODES, PACKET_LIMIT, REQUEST_LIMIT, RETRYABLE, SOURCE_LIMIT, StudyError,
    canonical, check, check_request, entity_id, fail, loads, request_hash, sha256,
)
from .storage import Store

UUID_CHARS = set("0123456789abcdef-")


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Study Loop state engine: JSON request on stdin, JSON response on stdout.")
    parser.add_argument("--workspace", required=True, help="absolute path of the learning folder")
    args = parser.parse_args(argv)
    raw = sys.stdin.buffer.read(REQUEST_LIMIT + 1)
    response, code = run(raw, args.workspace)
    sys.stdout.buffer.write(json.dumps(response, ensure_ascii=False).encode("utf-8") + b"\n")
    return code


def run(raw, workspace, clock=utc_now, lock_timeout=2.0):
    engine = None
    request = None
    try:
        if sys.version_info < (3, 10):
            fail("RUNTIME_UNSUPPORTED", f"Python {sys.version.split()[0]} is older than 3.10")
        if len(raw) > REQUEST_LIMIT:
            fail("INVALID_REQUEST", "the request is larger than 1 MiB")
        try:
            request = loads(raw)
            canonical(request)  # lone surrogates parse but can be neither hashed nor stored
        except (ValueError, RecursionError) as error:
            fail("INVALID_REQUEST", f"request is not strict UTF-8 JSON: {error}")
        check_request(request)
        if not os.path.isabs(workspace):
            fail("INVALID_REQUEST", "--workspace must be an absolute path")
        engine = Engine(Store(os.path.realpath(workspace)), request, clock, lock_timeout)
        return engine.execute()
    except StudyError as error:
        return failure(request, engine.revision if engine else None, error)


def _id_or_none(value):
    return value if isinstance(value, str) and len(value) == 36 and set(value) <= UUID_CHARS else None


def failure(request, revision, error):
    request = request if isinstance(request, dict) else {}
    return {
        "protocolVersion": 1,
        "ok": False,
        "workspaceId": _id_or_none(request.get("workspaceId")),
        "operationId": _id_or_none(request.get("operationId")),
        "revision": revision,
        "committed": error.committed,
        "error": {
            "code": error.code,
            "message": error.message[:3000] or error.code,
            "retryable": error.code in RETRYABLE,
            "recovery": error.recovery[:3000],
        },
    }, EXIT_CODES[error.code]


class Engine:
    def __init__(self, store, request, clock, lock_timeout):
        self.store = store
        self.request = request
        self.clock = clock
        self.lock_timeout = lock_timeout
        self.state = None
        self.revision = None  # revision before this request; failures report it

    # ---- dispatch -----------------------------------------------------------

    def execute(self):
        command = self.request["command"]
        if command == "workspace.init":
            return self.init()
        if command in ("workspace.query", "workspace.validate"):
            self.load()
            if command == "workspace.query":
                result = views.query(self.state, self.request["payload"], self.learner_text())
            else:
                result = self.validate()
            return self.success(result, committed=False, replayed=False, operation_revision=None, views_status="not_applicable")
        if not self.store.initialized():
            # Checked before locking so a wrong path never gets records/.lock.
            fail("WORKSPACE_MISSING", f"{self.store.root} has no study-loop journal")
        with self.store.lock(self.lock_timeout):
            if command == "workspace.export":
                self.load()
                return self.success(self.export(), committed=False, replayed=False, operation_revision=None, views_status="not_applicable")
            if command == "workspace.rebuild":
                self.load()
                self.require_revision()
                packet = views.context_packet(self.state, self.learner_text())
                return self.success(packet, committed=False, replayed=False, operation_revision=None, views_status=self.refresh(packet))
            return self.write()

    def load(self):
        if not self.store.initialized():
            fail("WORKSPACE_MISSING", f"{self.store.root} has no study-loop journal")
        state = reducer.replay(self.store.read_commits())
        try:
            views.context_packet(state, "")
        except (KeyError, TypeError, IndexError, AttributeError) as error:
            fail("CORRUPT_JOURNAL", f"the journal replays into an inconsistent state: {error!r}")
        self.state = state
        self.revision = state.revision
        if state.workspace["workspaceId"] != self.request["workspaceId"]:
            fail("WORKSPACE_MISMATCH", f"this folder is workspace {state.workspace['workspaceId']}")
        return state

    def require_revision(self):
        if self.request["expectedRevision"] != self.state.revision:
            fail("REVISION_CONFLICT", f"현재 revision은 {self.state.revision}이다.")

    def learner_text(self):
        try:
            return self.store.owned("learner.md").read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError, StudyError):
            return ""

    # ---- writes -------------------------------------------------------------

    def write(self):
        request = self.request
        state = self.load()
        digest = request_hash(request)
        operation = state.ops.get(request["operationId"])
        if operation:
            return self.replayed(operation, digest)
        self.require_revision()
        now = self.clock()
        material = self.material() if request["command"] == "source.register" else None
        context = reducer.Context(now, self.read_source, material)
        session_id, data, entity_ids = reducer.DECIDE[request["command"]](state, request, context)
        return self.commit(state, digest, now, session_id, data, entity_ids, material)

    def commit(self, state, digest, now, session_id, data, entity_ids, material=None, actor=None, before_append=None):
        request = self.request
        commit = {
            "schemaVersion": 1,
            "workspaceId": request["workspaceId"],
            "operationId": request["operationId"],
            "revision": state.revision + 1,
            "recordedAt": now,
            "requestHash": digest,
            "actor": actor or request["actor"],
            "command": request["command"],
            "events": [{
                "eventId": entity_id(request["workspaceId"], request["operationId"], "event:0"),
                "type": EVENT_TYPE[request["command"]],
                "sessionId": session_id,
                "data": data,
            }],
            "entityIds": entity_ids,
        }
        problem = check(commit, "Commit")
        if problem:
            fail("INVALID_REQUEST", f"the resulting record breaks the contract: {problem}")
        reducer.apply(state, commit)
        # learner.md is created only after the first journal line; show its initial copy until then.
        initial = request["command"] == "workspace.init" and not (self.store.root / "learner.md").exists()
        packet = views.context_packet(state, state.initial_learner_text if initial else self.learner_text())
        if len(canonical(packet)) > PACKET_LIMIT:
            fail("CONTEXT_LIMIT", "the resulting context packet is larger than 256 KiB; nothing was saved")
        if before_append:
            before_append()
        if material:
            try:
                self.store.write_atomic(data["snapshotPath"], material["bytes"])
            except OSError as error:
                fail("WRITE_FAILED", f"source snapshot was not saved: {error}")
        self.store.append(commit, request["operationId"])
        if request["command"] == "workspace.init":
            self.ensure_learner_file(state)
        result = {"kind": "transition", "entityIds": entity_ids, "packet": packet}
        return self.success(result, committed=True, replayed=False, operation_revision=commit["revision"], views_status=self.refresh(packet))

    def replayed(self, operation, digest):
        if operation["requestHash"] != digest:
            fail("OPERATION_CONFLICT", f"operation {self.request['operationId']} was saved with a different request")
        if self.request["command"] == "workspace.init":
            self.ensure_learner_file(self.state)
        packet = views.context_packet(self.state, self.learner_text())
        result = {"kind": "transition", "entityIds": operation["entityIds"], "packet": packet}
        return self.success(result, committed=True, replayed=True, operation_revision=operation["revision"], views_status=self.refresh(packet))

    def init(self):
        store, request = self.store, self.request
        if store.initialized():
            with store.lock(self.lock_timeout):
                return self.write()
        store.check_uninitialized()
        payload = request["payload"]
        learner = store.root / "learner.md"
        existing = self.existing_learner(learner, payload["learnerText"])
        try:
            store.root.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            fail("WRITE_FAILED", f"cannot create {store.root}: {error}")
        with store.lock(self.lock_timeout):
            if store.initialized():
                return self.write()
            store.check_uninitialized()
            existing = self.existing_learner(learner, payload["learnerText"])
            digest = request_hash(request)
            intent = store.read_intent()
            if intent:
                earlier = intent["request"]
                if (
                    earlier["workspaceId"] != request["workspaceId"]
                    or earlier["operationId"] != request["operationId"]
                    or request_hash(earlier) != digest
                ):
                    fail("OPERATION_CONFLICT", "a different workspace.init is recorded in records/.init.json; retry that request")
            text = payload["learnerText"] if payload["learnerText"] is not None else (existing or "")
            if len(text) > views.LEARNER_TEXT_LIMIT:
                fail("INVALID_REQUEST", f"learner.md is longer than {views.LEARNER_TEXT_LIMIT} characters; shorten it first")
            # The intent is recorded only once the first commit has passed every check,
            # so a refused init leaves nothing that blocks a corrected retry.
            new_intent = None if intent else {"schemaVersion": 1, "createdAt": self.clock(), "request": request}
            first = intent or new_intent
            self.state = reducer.State()
            session_id, data, entity_ids = reducer.workspace_event(request, first["createdAt"], text)
            return self.commit(
                self.state, digest, self.clock(), session_id, data, entity_ids, actor=first["request"]["actor"],
                before_append=(lambda: store.write_intent(new_intent)) if new_intent else None,
            )

    @staticmethod
    def existing_learner(path, requested):
        if not path.exists():
            return None
        try:
            existing = path.read_bytes().decode("utf-8")  # no newline translation
        except (OSError, UnicodeDecodeError) as error:
            fail("WORKSPACE_NOT_EMPTY", f"learner.md is not readable UTF-8: {error}")
        if requested is not None and requested != existing:
            fail("FILE_EXISTS", "learner.md already exists with different text; send learnerText=null to keep it")
        return existing

    def ensure_learner_file(self, state):
        """Created only after the first journal line; never overwritten."""
        learner = self.store.root / "learner.md"
        try:
            if not learner.exists():
                self.store.write_atomic("learner.md", state.initial_learner_text.encode("utf-8"))
            (self.store.root / "materials").mkdir(exist_ok=True)
        except (OSError, StudyError):
            pass  # The journal holds the initial text; a later init retry recreates the file.

    def refresh(self, packet):
        try:
            for relative, data in views.projections(self.state, packet).items():
                self.store.write_atomic(relative, data)
            return "current"
        except OSError:
            return "stale"
        except StudyError as error:
            if error.code != "PATH_OUTSIDE_WORKSPACE":
                raise
            return "stale"  # The journal committed; a protected projection may be rebuilt later.

    # ---- sources ---------------------------------------------------------------

    def read_source(self, source_id):
        source = self.state.sources[source_id]
        try:
            data = self.store.owned(source["snapshotPath"], area="sources").read_bytes()
        except OSError as error:
            fail("CORRUPT_JOURNAL", f"source snapshot {source['snapshotPath']} is unreadable: {error}")
        if sha256(data) != source["contentHash"]:
            fail("CORRUPT_JOURNAL", f"source snapshot {source['snapshotPath']} is missing or changed")
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError:
            fail("CORRUPT_JOURNAL", f"source snapshot {source['snapshotPath']} is not UTF-8")

    def material(self):
        relative = self.request["payload"]["relativePath"]
        path = self.store.inside(relative, area="materials")
        try:
            if not path.is_file():
                fail("INVALID_REQUEST", f"{relative} is not a file under materials/")
            before = path.stat()
            data = path.read_bytes()
            after = path.stat()
        except OSError as error:
            fail("INVALID_REQUEST", f"cannot read {relative}: {error}")
        if (before.st_mtime_ns, before.st_size) != (after.st_mtime_ns, after.st_size) or len(data) != after.st_size:
            fail("SOURCE_CHANGED", f"{relative} changed while it was read")
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            fail("INVALID_REQUEST", f"{relative} is not UTF-8 text; convert it to Markdown or text first")
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        encoded = text.encode("utf-8")
        if len(encoded) > SOURCE_LIMIT:
            fail("INVALID_REQUEST", f"{relative} is larger than 5 MiB after normalization")
        lines = text.count("\n") + (0 if text == "" or text.endswith("\n") else 1)
        return {
            "relativePath": path.relative_to(self.store.root.resolve()).as_posix(),
            "bytes": encoded, "contentHash": sha256(encoded), "byteLength": len(encoded), "lineCount": lines,
        }

    def validate(self):
        for source_id in self.state.sources:
            self.read_source(source_id)
        issues = []
        try:
            recorded = loads((self.store.root / "state.json").read_bytes()).get("revision")
        except (OSError, ValueError, UnicodeDecodeError, AttributeError):
            recorded = None
        if recorded != self.state.revision:
            issues.append(f"state.json is not at revision {self.state.revision}; workspace.rebuild regenerates it")
        return {"kind": "validation", "valid": True, "checkedRevision": self.state.revision, "issues": issues}

    def export(self):
        payload = self.request["payload"]
        target = self.store.inside(payload["outputPath"], area="artifacts")
        relative = target.relative_to(self.store.root.resolve()).as_posix()
        data = views.export_bytes(self.state, payload["format"])
        changed = True
        try:  # a directory or over-long name surfaces here as OSError
            if target.exists():
                if target.read_bytes() == data:
                    changed = False
                elif not payload["overwrite"]:
                    fail("FILE_EXISTS", f"{relative} exists with different content")
        except OSError as error:
            fail("INVALID_REQUEST", f"cannot use {relative}: {error}")
        if changed:
            try:
                self.store.write_atomic(relative, data)
            except OSError as error:
                fail("WRITE_FAILED", f"cannot write {relative}: {error}")
        return {
            "kind": "artifact", "relativePath": relative, "contentHash": sha256(data),
            "sourceRevision": self.state.revision, "changed": changed,
        }

    def success(self, result, committed, replayed, operation_revision, views_status):
        request = self.request
        return {
            "protocolVersion": 1,
            "ok": True,
            "workspaceId": request["workspaceId"],
            "operationId": request["operationId"],
            "command": request["command"],
            "revision": self.state.revision,
            "operationRevision": operation_revision,
            "committed": committed,
            "replayed": replayed,
            "viewsStatus": views_status,
            "result": result,
        }, 0
