"""Request/response contracts: schema checks, hashing, IDs and errors.

The JSON Schema file is the structural contract. `check` interprets only the
keywords that schema uses, so the runtime keeps no third-party dependency.
"""

import functools
import hashlib
import json
import re
import unicodedata
import uuid
from datetime import datetime
from pathlib import Path

SCHEMA = json.loads(Path(__file__).with_name("contracts.schema.json").read_text(encoding="utf-8"))
DEFS = SCHEMA["$defs"]

REQUEST_LIMIT = 1024 * 1024
PACKET_LIMIT = 256 * 1024
SOURCE_LIMIT = 5 * 1024 * 1024
POLICY_VERSION = "1.0.0"

WRITE_COMMANDS = (
    "workspace.init", "session.start", "session.pause", "session.resume", "session.finish",
    "diagnosis.complete", "plan.propose", "plan.accept", "question.pose", "hint.record",
    "question.reveal", "question.skip", "answer.record", "assessment.record",
    "continuation.accept", "content.resolve", "source.register", "knowledge.commit",
)
# Commands that never change a session and are allowed in any session state.
WORKSPACE_COMMANDS = (
    "workspace.query", "workspace.validate", "workspace.rebuild", "workspace.export",
    "source.register", "knowledge.commit",
)
EVENT_TYPE = {
    "workspace.init": "workspace_initialized",
    "session.start": "session_started",
    "session.pause": "session_paused",
    "session.resume": "session_resumed",
    "session.finish": "session_finished",
    "diagnosis.complete": "diagnosis_completed",
    "plan.propose": "plan_proposed",
    "plan.accept": "plan_accepted",
    "question.pose": "question_posed",
    "hint.record": "hint_recorded",
    "question.reveal": "question_revealed",
    "question.skip": "question_skipped",
    "answer.record": "answer_recorded",
    "assessment.record": "assessment_recorded",
    "continuation.accept": "continuation_accepted",
    "content.resolve": "content_resolved",
    "source.register": "source_registered",
    "knowledge.commit": "knowledge_committed",
}

EXIT_CODES = {
    "INVALID_REQUEST": 2, "UNSUPPORTED_VERSION": 5, "WORKSPACE_MISSING": 2,
    "WORKSPACE_NOT_EMPTY": 2, "COMMIT_STATUS_UNKNOWN": 4, "WORKSPACE_MISMATCH": 2,
    "CORRUPT_JOURNAL": 4, "REVISION_CONFLICT": 3, "OPERATION_CONFLICT": 3, "LOCK_BUSY": 3,
    "WRITE_FAILED": 4, "INVALID_TRANSITION": 2, "PLAN_REQUIRED": 2, "INVALID_PLAN": 2,
    "NODE_REDEFINED": 2, "TARGET_NOT_ALLOWED": 2, "RUBRIC_MISMATCH": 2, "INVALID_ANSWER": 2,
    "HINT_LIMIT": 2, "ASSESSMENT_FINALIZED": 2, "CONTENT_REPAIR_REQUIRED": 2,
    "INVALID_REFERENCE": 2, "PATH_OUTSIDE_WORKSPACE": 2, "SOURCE_CHANGED": 2,
    "FILE_EXISTS": 3, "CONTEXT_LIMIT": 2, "RUNTIME_UNSUPPORTED": 5,
}
RETRYABLE = {"LOCK_BUSY", "COMMIT_STATUS_UNKNOWN", "WRITE_FAILED", "SOURCE_CHANGED"}
RECOVERY = {
    "INVALID_REQUEST": "필드를 고쳐 다시 요청한다. payload를 바꾸면 새 operationId를 쓴다.",
    "INVALID_ANSWER": "선택값·응답 종류를 고쳐 다시 요청한다. payload를 바꾸면 새 operationId를 쓴다.",
    "RUBRIC_MISMATCH": "질문의 criterion을 정확히 한 번씩 평가해 다시 요청한다.",
    "REVISION_CONFLICT": "workspace.query로 현재 상태를 읽고, 이전 작업의 저장 여부를 확인한 뒤 새 operationId로 재계획한다.",
    "OPERATION_CONFLICT": "workspace.query view=operation으로 기존 작업을 확인한다. 다른 작업이면 새 operationId를 쓴다.",
    "LOCK_BUSY": "다른 작업이 끝나기를 기다린 뒤 같은 요청을 다시 보낸다. 잠금 파일을 지우지 않는다.",
    "INVALID_TRANSITION": "workspace.query view=resume으로 현재 packet을 읽고 nextAction과 대기 중인 질문·평가·승인부터 처리한다.",
    "PLAN_REQUIRED": "계획을 제안하고 승인받은 뒤 다시 요청한다.",
    "INVALID_PLAN": "선행 관계·목표 노드·고유 ID·baseVersion을 고쳐 다시 제안한다.",
    "NODE_REDEFINED": "내용을 바꾼 노드는 새 nodeId로 제안한다.",
    "TARGET_NOT_ALLOWED": "packet의 session.requiredMove와 currentNodeId에 맞는 질문을 만든다.",
    "HINT_LIMIT": "답변·풀이 공개·건너뛰기 중 무엇을 원하는지 학습자에게 묻는다.",
    "CONTENT_REPAIR_REQUIRED": "content.resolve로 현재 repair를 먼저 해소한다.",
    "ASSESSMENT_FINALIZED": "과거 평가는 바꾸지 않는다. 새 세션의 확인 문제로 다시 검토한다.",
    "INVALID_REFERENCE": "실제 사본·인용 범위·이벤트를 query로 확인해 고친다.",
    "SOURCE_CHANGED": "자료가 바뀌지 않을 때 다시 등록한다.",
    "PATH_OUTSIDE_WORKSPACE": "워크스페이스 안의 허용된 경로(materials/, artifacts/)를 쓴다.",
    "FILE_EXISTS": "다른 경로를 쓰거나, 교체가 의도라면 overwrite=true로 요청한다.",
    "WORKSPACE_NOT_EMPTY": "빈 폴더 또는 learner.md·materials/만 있는 폴더를 지정한다.",
    "CONTEXT_LIMIT": "모델이 작성한 긴 설명·계획을 줄여 다시 요청한다. 학습자 원답을 요약해 대체하지 않는다.",
    "WORKSPACE_MISSING": "학습 폴더 경로를 확인한다. 새 학습이면 workspace.init을 쓴다.",
    "WORKSPACE_MISMATCH": "폴더와 workspaceId를 확인한다. 잘못된 폴더를 초기화하지 않는다.",
    "CORRUPT_JOURNAL": "쓰기를 멈추고 records/events.jsonl을 백업에서 복구한다.",
    "UNSUPPORTED_VERSION": "이 기록을 만든 새 버전의 study-loop로 연다.",
    "RUNTIME_UNSUPPORTED": "Python 3.10 이상으로 실행한다.",
    "WRITE_FAILED": "기존 기록이 그대로인지 query로 확인한 뒤 같은 요청을 다시 보낸다.",
    "COMMIT_STATUS_UNKNOWN": "새 operationId로 다시 실행하지 말고 view=operation으로 이 operationId의 저장 여부를 먼저 확인한다.",
}


class StudyError(Exception):
    def __init__(self, code, message, recovery=None, committed=False):
        super().__init__(message)
        self.code = code
        self.message = message
        self.recovery = recovery or RECOVERY.get(code, "현재 상태를 query로 확인한다.")
        self.committed = committed


def fail(code, message, recovery=None):
    raise StudyError(code, message, recovery)


# ---- JSON -----------------------------------------------------------------

def _no_duplicates(pairs):
    keys = [key for key, _ in pairs]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate key")
    return dict(pairs)


def _no_constant(name):
    raise ValueError(f"{name} is not allowed")


def loads(data):
    """Strict JSON: duplicate keys, NaN and Infinity are errors."""
    if isinstance(data, bytes):
        data = data.decode("utf-8")
    return json.loads(data, object_pairs_hook=_no_duplicates, parse_constant=_no_constant)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def dumps_line(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def request_hash(request):
    keys = ("protocolVersion", "workspaceId", "command", "payload")
    return sha256(canonical({key: request[key] for key in keys}))


def prompt_hash(prompt):
    text = unicodedata.normalize("NFKC", prompt).casefold()
    return sha256(re.sub(r"\s+", " ", text).strip().encode("utf-8"))


def entity_id(workspace_id, operation_id, role):
    return str(uuid.uuid5(uuid.UUID(workspace_id), f"{operation_id}:{role}"))


def named_id(workspace_id, name):
    return str(uuid.uuid5(uuid.UUID(workspace_id), name))


# ---- Schema subset --------------------------------------------------------

def _type_ok(value, kind):
    if kind == "object":
        return isinstance(value, dict)
    if kind == "array":
        return isinstance(value, list)
    if kind == "string":
        return isinstance(value, str)
    if kind == "integer":
        # ponytail: integers only; the contract never uses fractional numbers.
        return isinstance(value, int) and not isinstance(value, bool)
    if kind == "boolean":
        return isinstance(value, bool)
    if kind == "null":
        return value is None
    raise ValueError(f"unsupported schema type {kind}")


@functools.lru_cache(maxsize=None)
def _pattern(source):
    # JSON Schema uses ECMA regexes, where `$` ends the input; Python's `$` also
    # matches before a final newline, so "<uuid>\n" would pass. The contract
    # patterns contain no escaped `$`.
    return re.compile(source.replace("$", r"\Z"))


def _same(a, b):
    return canonical(a) == canonical(b)


def _timestamp_ok(text):
    try:
        datetime.fromisoformat(text.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def errors(value, schema, path="$"):
    """Return the first contract violation as text, or None."""
    if "$ref" in schema:
        return errors(value, DEFS[schema["$ref"].rsplit("/", 1)[1]], path)
    if "anyOf" in schema or "oneOf" in schema:
        branches = schema.get("anyOf") or schema["oneOf"]
        found = [errors(value, branch, path) for branch in branches]
        ok = [item for item in found if item is None]
        if "oneOf" in schema and len(ok) > 1:
            return f"{path}: matches several alternatives"
        if not ok:
            # Report the alternative that got furthest (deepest path).
            return max(found, key=lambda item: item.count(".") + item.count("["))
        return None
    if "const" in schema and not _same(value, schema["const"]):
        return f"{path}: must be {json.dumps(schema['const'], ensure_ascii=False)}"
    if "enum" in schema and not any(_same(value, item) for item in schema["enum"]):
        return f"{path}: must be one of {schema['enum']}"
    kind = schema.get("type")
    if kind and not _type_ok(value, kind):
        return f"{path}: must be {kind}"
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            return f"{path}: shorter than {schema['minLength']}"
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            return f"{path}: longer than {schema['maxLength']}"
        if "pattern" in schema and not _pattern(schema["pattern"]).search(value):
            return f"{path}: does not match {schema['pattern']}"
        if schema.get("format") == "date-time" and not _timestamp_ok(value):
            return f"{path}: not a date-time"
    if isinstance(value, int) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            return f"{path}: below {schema['minimum']}"
        if "maximum" in schema and value > schema["maximum"]:
            return f"{path}: above {schema['maximum']}"
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            return f"{path}: needs at least {schema['minItems']} items"
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            return f"{path}: allows at most {schema['maxItems']} items"
        if schema.get("uniqueItems") and len({canonical(item) for item in value}) != len(value):
            return f"{path}: items must be unique"
        if "items" in schema:
            for index, item in enumerate(value):
                problem = errors(item, schema["items"], f"{path}[{index}]")
                if problem:
                    return problem
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                return f"{path}: missing {key}"
        extra = schema.get("additionalProperties", True)
        for key, item in value.items():
            if key in properties:
                problem = errors(item, properties[key], f"{path}.{key}")
            elif extra is False:
                problem = f"{path}: unknown field {key}"
            elif isinstance(extra, dict):
                problem = errors(item, extra, f"{path}.{key}")
            else:
                problem = None
            if problem:
                return problem
    return None


def check(value, definition):
    return errors(value, {"$ref": f"#/$defs/{definition}"})


def check_request(request):
    """Validate against the command's own definition so messages name the real field."""
    if not isinstance(request, dict):
        fail("INVALID_REQUEST", "request must be a JSON object")
    version = request.get("protocolVersion")
    if isinstance(version, int) and not isinstance(version, bool) and version != 1:
        fail("UNSUPPORTED_VERSION", f"protocolVersion {version} is not supported")
    command = request.get("command")
    name = "Request_" + command.replace(".", "_") if isinstance(command, str) else None
    problem = check(request, name) if name in DEFS else check(request, "Request")
    if problem:
        fail("INVALID_REQUEST", problem)
