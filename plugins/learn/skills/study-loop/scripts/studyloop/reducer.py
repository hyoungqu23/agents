"""Replay commits into state and decide the single event of a new write.

`decide_*` validate a request against current state and return event data;
`apply` mutates state from a commit. Neither touches files or the clock: the
caller passes `now` and a `read_source(sourceId)` callable.
"""

import copy

from . import policy
from .contracts import (
    EVENT_TYPE, POLICY_VERSION, StudyError, canonical, check, entity_id, fail, named_id, prompt_hash,
)

FAILURES = policy.FAILURES
ABANDONABLE = ("question", "assessment", "plan_approval", "repair")
KNOWN_EVENTS = set(EVENT_TYPE.values())


class State:
    def __init__(self):
        self.revision = 0
        self.workspace = None
        self.initial_learner_text = ""
        self.ops = {}
        self.events = []
        self.event_data = {}
        self.sessions = {}
        self.session_order = []
        self.current = None
        self.plans = {}
        self.latest_version = 0
        self.accepted_version = None
        self.node_defs = {}
        self.questions = {}
        self.answers = {}
        self.assessments = {}
        self.effective = {}
        self.hints = {}
        self.revealed_hashes = set()
        self.cont = {}
        self.diagnoses = {}
        self.resolutions = {}
        self.sources = {}
        self.props = {}
        self.chains = {}


# ---- replay -----------------------------------------------------------------

def replay(commits):
    state = State()
    for commit in commits:
        verify_commit(state, commit)
        apply(state, commit)
    return state


def verify_commit(state, commit):
    where = f"journal revision {state.revision + 1}"
    if not isinstance(commit, dict):
        fail("CORRUPT_JOURNAL", f"{where}: not an object")
    version = commit.get("schemaVersion")
    if isinstance(version, int) and not isinstance(version, bool) and version > 1:
        fail("UNSUPPORTED_VERSION", f"{where}: schemaVersion {version} is newer than this engine")
    for event in commit.get("events") or []:
        if isinstance(event, dict) and isinstance(event.get("type"), str) and event["type"] not in KNOWN_EVENTS:
            fail("UNSUPPORTED_VERSION", f"{where}: unknown event type {event['type']}")
    problem = check(commit, "Commit")
    if problem:
        fail("CORRUPT_JOURNAL", f"{where}: {problem}")
    if commit["revision"] != state.revision + 1:
        fail("CORRUPT_JOURNAL", f"{where}: found revision {commit['revision']}")
    if state.workspace is None and commit["command"] != "workspace.init":
        fail("CORRUPT_JOURNAL", "the first commit is not workspace.init")
    if state.workspace and commit["workspaceId"] != state.workspace["workspaceId"]:
        fail("CORRUPT_JOURNAL", f"{where}: workspaceId changed")
    if commit["operationId"] in state.ops:
        fail("CORRUPT_JOURNAL", f"{where}: operationId reused")
    event = commit["events"][0]
    if event["type"] != EVENT_TYPE[commit["command"]]:
        fail("CORRUPT_JOURNAL", f"{where}: {commit['command']} cannot write {event['type']}")
    if event["eventId"] in state.event_data:
        fail("CORRUPT_JOURNAL", f"{where}: eventId reused")
    data_session = event["data"].get("sessionId") if isinstance(event["data"], dict) else None
    if data_session and event["sessionId"] != data_session:
        fail("CORRUPT_JOURNAL", f"{where}: event sessionId does not match its data")


def apply(state, commit):
    event = commit["events"][0]
    try:
        APPLY[event["type"]](state, event, commit)
    except (KeyError, TypeError, IndexError, AttributeError) as error:
        raise StudyError("CORRUPT_JOURNAL", f"revision {commit['revision']}: dangling reference {error!r}")
    state.revision = commit["revision"]
    state.ops[commit["operationId"]] = {
        "revision": commit["revision"],
        "requestHash": commit["requestHash"],
        "entityIds": commit["entityIds"],
        "command": commit["command"],
    }
    header = {
        "eventId": event["eventId"],
        "type": event["type"],
        "sessionId": event["sessionId"],
        "revision": commit["revision"],
        "recordedAt": commit["recordedAt"],
    }
    state.events.append(header)
    state.event_data[event["eventId"]] = {**header, "data": event["data"]}


def _session(state, event):
    return state.sessions[event["sessionId"]]


def _continuation(state, session, event, kind, question, recommended, answer_id=None, assessment_id=None):
    session["pending"] = {"kind": "continuation", "afterEventId": event["eventId"]}
    session["requiredMove"] = None
    state.cont[session["sessionId"]] = {
        "kind": kind,
        "afterEventId": event["eventId"],
        "questionId": question["questionId"],
        "answerId": answer_id,
        "assessmentId": assessment_id,
        "nodeId": question["nodeId"],
        "purpose": question["purpose"],
        "recommendedMove": recommended,
    }


def _workspace_initialized(state, event, commit):
    state.workspace = event["data"]["workspace"]
    state.initial_learner_text = event["data"]["initialLearnerText"]


def _session_started(state, event, commit):
    session = copy.deepcopy(event["data"])
    state.sessions[session["sessionId"]] = session
    state.session_order.append(session["sessionId"])
    state.current = session["sessionId"]


def _session_paused(state, event, commit):
    _session(state, event)["lifecycle"] = "paused"


def _session_resumed(state, event, commit):
    _session(state, event)["lifecycle"] = "active"


def _session_finished(state, event, commit):
    session = _session(state, event)
    pending = session["pending"]
    if pending and pending["kind"] == "question":
        state.questions[pending["questionId"]]["status"] = "abandoned"
    session.update(
        lifecycle="completed", endedAt=commit["recordedAt"], outcome=event["data"]["outcome"],
        pending=None, requiredMove=None,
    )
    state.cont.pop(session["sessionId"], None)
    state.current = None


def _diagnosis_completed(state, event, commit):
    session = _session(state, event)
    session.update(phase="planning", pending=None, requiredMove=None, currentNodeId=None)
    state.cont.pop(session["sessionId"], None)
    state.diagnoses[session["sessionId"]] = event["data"]


def _plan_proposed(state, event, commit):
    plan = event["data"]
    state.plans[plan["version"]] = plan
    state.latest_version = plan["version"]
    for node in plan["nodes"]:
        state.node_defs.setdefault(node["nodeId"], node)
    _session(state, event)["pending"] = {"kind": "plan_approval", "planVersion": plan["version"]}


def _plan_accepted(state, event, commit):
    session = _session(state, event)
    state.accepted_version = event["data"]["version"]
    session.update(phase="learning", pending=None, deferredNodeIds=[])
    target, move = policy.learning_advance(state, session)
    session.update(currentNodeId=target, requiredMove=move)


def _question_posed(state, event, commit):
    question = event["data"]
    state.questions[question["questionId"]] = {
        "q": question, "status": "open", "revision": commit["revision"], "eventId": event["eventId"],
    }
    session = _session(state, event)
    session.update(pending={"kind": "question", "questionId": question["questionId"]}, requiredMove=None)


def _hint_recorded(state, event, commit):
    state.hints.setdefault(event["data"]["questionId"], []).append(event["data"])


def _question_revealed(state, event, commit):
    entry = state.questions[event["data"]["questionId"]]
    entry["status"] = "revealed"
    state.revealed_hashes.add(entry["q"]["promptHash"])
    recommended = None if entry["q"]["purpose"] == "diagnostic" else "fresh_check"
    _continuation(state, _session(state, event), event, "reveal", entry["q"], recommended)


def _question_skipped(state, event, commit):
    entry = state.questions[event["data"]["questionId"]]
    entry["status"] = "skipped"
    recommended = None if entry["q"]["purpose"] == "diagnostic" else "fresh_check"
    _continuation(state, _session(state, event), event, "skip", entry["q"], recommended)


def _answer_recorded(state, event, commit):
    answer = event["data"]
    state.answers[answer["answerId"]] = {"a": answer, "revision": commit["revision"], "eventId": event["eventId"]}
    state.questions[answer["questionId"]]["status"] = "answered"
    _session(state, event)["pending"] = {
        "kind": "assessment", "questionId": answer["questionId"], "answerId": answer["answerId"],
    }


def _assessment_recorded(state, event, commit):
    assessment = event["data"]
    state.assessments[assessment["assessmentId"]] = {
        "x": assessment, "revision": commit["revision"], "eventId": event["eventId"],
    }
    state.effective[assessment["answerId"]] = assessment["assessmentId"]
    session = _session(state, event)
    question = state.questions[assessment["questionId"]]["q"]
    answer = state.answers[assessment["answerId"]]["a"]
    state.questions[assessment["questionId"]]["status"] = "assessed"
    if assessment["verdict"] == "ungradable":
        _continuation(state, session, event, "repair", question, None, answer["answerId"], assessment["assessmentId"])
        session["pending"] = {
            "kind": "repair", "questionId": question["questionId"], "assessmentId": assessment["assessmentId"],
        }
        return
    recommended = policy.recommend(state, session, question, assessment, answer)
    _continuation(state, session, event, "assessment", question, recommended, answer["answerId"], assessment["assessmentId"])


def _continuation_accepted(state, event, commit):
    session = _session(state, event)
    continuation = state.cont.pop(session["sessionId"])
    fields = policy.follow(state, session, continuation, event["data"]["intent"])
    session.update(pending=None, **fields)


def _content_resolved(state, event, commit):
    session = _session(state, event)
    continuation = state.cont[session["sessionId"]]
    entry = state.questions[continuation["questionId"]]
    entry["status"] = "discarded"
    state.resolutions[event["data"]["assessmentId"]] = event["data"]
    if event["data"]["resolution"] == "replan":
        state.cont.pop(session["sessionId"])
        session.update(phase="planning", pending=None, requiredMove=None, currentNodeId=None)
        return
    _continuation(state, session, event, "resolve", entry["q"], None)


def _source_registered(state, event, commit):
    state.sources[event["data"]["sourceId"]] = event["data"]


def _knowledge_committed(state, event, commit):
    ids, chains = knowledge_ids(state, commit["workspaceId"], commit["operationId"], event["data"])
    extraction = event["data"]
    linked = {link["localKey"] for link in extraction["identityLinks"]}
    for draft in extraction["propositions"]:
        prop_id = ids[draft["localKey"]]
        if draft["localKey"] in linked:
            existing = state.props[prop_id]
            if draft["statement"] != existing["statement"] and draft["statement"] not in existing["aliases"]:
                existing["aliases"].append(draft["statement"])
            _merge_refs(existing["sourceRefs"], draft["sourceRefs"])
        else:
            state.props[prop_id] = {
                "propositionId": prop_id, "name": draft["name"], "statement": draft["statement"],
                "aliases": [], "sourceRefs": list(draft["sourceRefs"]),
            }
    for chain_id, premises, conclusion, refs in chains:
        if chain_id in state.chains:
            _merge_refs(state.chains[chain_id]["sourceRefs"], refs)
        else:
            state.chains[chain_id] = {
                "chainId": chain_id, "premises": premises, "conclusion": conclusion, "sourceRefs": list(refs),
            }


def _merge_refs(target, refs):
    seen = {canonical(ref) for ref in target}
    for ref in refs:
        if canonical(ref) not in seen:
            target.append(ref)
            seen.add(canonical(ref))


APPLY = {
    "workspace_initialized": _workspace_initialized,
    "session_started": _session_started,
    "session_paused": _session_paused,
    "session_resumed": _session_resumed,
    "session_finished": _session_finished,
    "diagnosis_completed": _diagnosis_completed,
    "plan_proposed": _plan_proposed,
    "plan_accepted": _plan_accepted,
    "question_posed": _question_posed,
    "hint_recorded": _hint_recorded,
    "question_revealed": _question_revealed,
    "question_skipped": _question_skipped,
    "answer_recorded": _answer_recorded,
    "assessment_recorded": _assessment_recorded,
    "continuation_accepted": _continuation_accepted,
    "content_resolved": _content_resolved,
    "source_registered": _source_registered,
    "knowledge_committed": _knowledge_committed,
}


# ---- shared checks ------------------------------------------------------------

class Context:
    def __init__(self, now, read_source=None, material=None):
        self.now = now
        self.read_source = read_source
        self.material = material


def current_session(state, session_id, allow_paused=False):
    session = state.sessions.get(session_id)
    if session is None or session_id != state.current:
        fail("INVALID_TRANSITION", f"session {session_id} is not the current incomplete session")
    if session["lifecycle"] == "paused" and not allow_paused:
        fail("INVALID_TRANSITION", "the session is paused; session.resume or session.finish first")
    return session


def require_pending(session, kinds, ids=None):
    """3B: a wrong or occupied wait is INVALID_TRANSITION, except an open repair."""
    pending = session["pending"]
    kind = pending["kind"] if pending else None
    if kind not in kinds:
        if kind == "repair":
            fail("CONTENT_REPAIR_REQUIRED", "a repair is pending; content.resolve first")
        waiting = f"pending={kind}" if kind else "nothing is pending"
        fail("INVALID_TRANSITION", f"{waiting}; this command needs pending in {list(kinds)}")
    for key, value in (ids or {}).items():
        if pending.get(key) != value:
            fail("INVALID_TRANSITION", f"pending {key} is {pending.get(key)}, not {value}")
    return pending


def check_refs(state, context, refs):
    for ref in refs:
        if ref["kind"] == "material":
            source = state.sources.get(ref["sourceId"])
            if source is None:
                fail("INVALID_REFERENCE", f"source {ref['sourceId']} is not registered")
            if not 1 <= ref["startLine"] <= ref["endLine"] <= source["lineCount"]:
                fail("INVALID_REFERENCE", f"lines {ref['startLine']}-{ref['endLine']} are outside the source")
            lines = context.read_source(ref["sourceId"]).split("\n")
            text = "\n".join(lines[ref["startLine"] - 1:ref["endLine"]])
        else:
            text = lesson_text(state, ref["eventId"])
        if ref["quote"] not in text:
            fail("INVALID_REFERENCE", f"quote is not in the cited range: {ref['quote'][:80]}")


def lesson_text(state, event_id):
    record = state.event_data.get(event_id)
    kind = record["type"] if record else None
    if kind == "question_posed" and record["data"]["lessonText"]:
        return record["data"]["lessonText"]
    if kind == "assessment_recorded":
        return record["data"]["feedback"]
    if kind == "question_revealed":
        return state.questions[record["data"]["questionId"]]["q"]["expectedAnswer"]
    fail("INVALID_REFERENCE", f"event {event_id} is not a lesson, feedback or revealed solution")


def _session_ids(state, session):
    return {"sessionId": session["sessionId"]}


# ---- decide: sessions ---------------------------------------------------------

def decide_session_start(state, request, context):
    payload = request["payload"]
    if state.current:
        fail("INVALID_TRANSITION", "an incomplete session exists; resume or finish it first")
    mode, plan = payload["mode"], policy.accepted_plan(state)
    session = {
        "sessionId": entity_id(request["workspaceId"], request["operationId"], "session"),
        "mode": mode, "startAt": payload["startAt"], "startRequestText": payload["userText"],
        "lifecycle": "active", "phase": "learning", "pending": None, "requiredMove": None,
        "currentNodeId": None, "targetNodeIds": [], "startedAt": context.now, "deferredNodeIds": [],
        "queueIndex": 0, "maxItems": payload["maxItems"], "endedAt": None, "outcome": None,
    }
    if mode == "learning":
        if payload["targetNodeIds"] or payload["maxItems"] is not None:
            fail("INVALID_REQUEST", "learning sessions use targetNodeIds=[] and maxItems=null")
        if payload["startAt"] == "replan":
            if not plan:
                fail("PLAN_REQUIRED", "startAt=replan needs an accepted plan")
            session["phase"] = "planning"
        elif plan:
            session["currentNodeId"], session["requiredMove"] = policy.learning_advance(state, session)
        elif state.diagnoses:
            session["phase"] = "planning"
            if state.latest_version:
                session["pending"] = {"kind": "plan_approval", "planVersion": state.latest_version}
        else:
            session["phase"] = "diagnosing"
            session["requiredMove"] = {"purpose": "diagnostic", "teachingMove": None}
    else:
        if payload["startAt"] != "auto":
            fail("INVALID_REQUEST", "startAt=replan is only for learning sessions")
        if not plan:
            fail("PLAN_REQUIRED", f"{mode} needs an accepted plan")
        if payload["maxItems"] is None:
            fail("INVALID_REQUEST", f"{mode} needs maxItems 1-10")
        known = {node["nodeId"] for node in plan["nodes"]}
        unknown = [item for item in payload["targetNodeIds"] if item not in known]
        if unknown:
            fail("TARGET_NOT_ALLOWED", f"{unknown} are not nodes of the accepted plan")
        queue = payload["targetNodeIds"][:payload["maxItems"]] or policy.practice_queue(state, payload["maxItems"])
        purpose = "practice" if mode == "practice" else "review"
        session.update(
            phase="practicing" if mode == "practice" else "reviewing", targetNodeIds=queue,
            currentNodeId=queue[0], requiredMove={"purpose": purpose, "teachingMove": None},
        )
    return session["sessionId"], session, {"sessionId": session["sessionId"]}


def decide_session_pause(state, request, context):
    payload = request["payload"]
    session = current_session(state, payload["sessionId"])
    return session["sessionId"], dict(payload), _session_ids(state, session)


def decide_session_resume(state, request, context):
    payload = request["payload"]
    session = current_session(state, payload["sessionId"], allow_paused=True)
    if session["lifecycle"] != "paused":
        fail("INVALID_TRANSITION", "the session is already active; use workspace.query view=resume")
    return session["sessionId"], dict(payload), _session_ids(state, session)


def decide_session_finish(state, request, context):
    payload = request["payload"]
    session = current_session(state, payload["sessionId"], allow_paused=True)
    outcome, mode = payload["outcome"], session["mode"]
    allowed = {"learning": ("goal_demonstrated", "partial"), "practice": ("practice_done", "partial"),
               "review": ("review_done", "partial")}[mode]
    if outcome not in allowed:
        fail("INVALID_TRANSITION", f"a {mode} session ends with {list(allowed)}")
    if outcome == "goal_demonstrated" and not policy.goal_demonstrated(state):
        fail("INVALID_TRANSITION", "goal_demonstrated needs every node qualified and an independent final transfer; finish as partial")
    pending = session["pending"]
    open_wait = pending["kind"] if pending and pending["kind"] in ABANDONABLE else None
    if open_wait and not payload["abandonPending"]:
        fail("INVALID_TRANSITION", f"pending {open_wait} would be abandoned; send abandonPending=true with the learner's request")
    if payload["abandonPending"] and not open_wait:
        fail("INVALID_REQUEST", "abandonPending=true but no question, assessment, plan approval or repair is pending")
    return session["sessionId"], dict(payload), _session_ids(state, session)


def decide_diagnosis_complete(state, request, context):
    payload = request["payload"]
    session = current_session(state, payload["sessionId"])
    require_pending(session, (None, "continuation"))
    if session["phase"] != "diagnosing":
        fail("INVALID_TRANSITION", f"diagnosis.complete needs phase=diagnosing, not {session['phase']}")
    if payload["skipRequested"]:
        if not payload["userText"]:
            fail("INVALID_REQUEST", "skipRequested=true needs the learner's actual request in userText")
    elif not policy.assessed_diagnostics(state, session):
        fail("INVALID_TRANSITION", "no diagnostic answer was assessed; ask one or send skipRequested=true")
    for answer_id in payload["evidenceAnswerIds"]:
        record = state.answers.get(answer_id)
        question = state.questions[record["a"]["questionId"]]["q"] if record else None
        if not question or question["sessionId"] != session["sessionId"] or question["purpose"] != "diagnostic":
            fail("INVALID_REFERENCE", f"answer {answer_id} is not a diagnostic answer of this session")
    return session["sessionId"], dict(payload), _session_ids(state, session)


def decide_plan_propose(state, request, context):
    payload = request["payload"]
    session = current_session(state, payload["sessionId"])
    require_pending(session, (None, "plan_approval"))
    if session["phase"] != "planning":
        fail("INVALID_TRANSITION", "plans are proposed in phase=planning; accept the continuation with intent=replan first")
    problem = policy.plan_errors(payload["nodes"], payload["goalNodeId"])
    if problem:
        fail("INVALID_PLAN", problem)
    if payload["baseVersion"] != state.latest_version:
        fail("INVALID_PLAN", f"baseVersion must be the latest proposed version {state.latest_version}")
    if state.accepted_version and not payload["revisionReason"]:
        fail("INVALID_PLAN", "a revision of an accepted plan needs revisionReason")
    for node in payload["nodes"]:
        earlier = state.node_defs.get(node["nodeId"])
        if earlier is not None and canonical(earlier) != canonical(node):
            fail("NODE_REDEFINED", f"{node['nodeId']} was defined differently before; use a new nodeId")
        check_refs(state, context, node["sourceRefs"])
    plan = {
        "planId": named_id(request["workspaceId"], "plan"), "version": state.latest_version + 1,
        "goalNodeId": payload["goalNodeId"], "nodes": payload["nodes"],
        "diagnosisSummary": payload["diagnosisSummary"], "revisionReason": payload["revisionReason"],
    }
    return session["sessionId"], plan, {"sessionId": session["sessionId"], "planId": plan["planId"]}


def decide_plan_accept(state, request, context):
    payload = request["payload"]
    session = current_session(state, payload["sessionId"])
    require_pending(session, ("plan_approval",), {"planVersion": payload["version"]})
    return session["sessionId"], dict(payload), _session_ids(state, session)


# ---- decide: questions --------------------------------------------------------

def decide_question_pose(state, request, context):
    payload = request["payload"]
    session = current_session(state, payload["sessionId"])
    require_pending(session, (None,))
    draft = payload["question"]
    move = session["requiredMove"]
    if session["phase"] == "planning":
        fail("INVALID_TRANSITION", "no questions during planning; propose the plan first")
    if move is None:
        fail("INVALID_TRANSITION", "no question is needed now; follow nextAction")
    if draft["purpose"] != move["purpose"]:
        fail("TARGET_NOT_ALLOWED", f"requiredMove.purpose is {move['purpose']}, not {draft['purpose']}")
    if draft["purpose"] == "diagnostic":
        if draft["nodeId"] or draft["planVersion"] or draft["lessonText"]:
            fail("INVALID_REQUEST", "diagnostic questions use nodeId, planVersion and lessonText = null")
        if policy.diagnostic_count(state, session) >= policy.DIAGNOSTIC_LIMIT:
            fail("INVALID_TRANSITION", "three diagnostic questions were asked; complete the diagnosis")
    else:
        plan = policy.accepted_plan(state)
        if not plan:
            fail("PLAN_REQUIRED", "questions on plan nodes need an accepted plan")
        if draft["planVersion"] != plan["version"]:
            fail("TARGET_NOT_ALLOWED", f"planVersion must be the accepted version {plan['version']}")
        if draft["nodeId"] != session["currentNodeId"]:
            fail("TARGET_NOT_ALLOWED", f"the next question must target {session['currentNodeId']}, not {draft['nodeId']}")
        node = policy.plan_node(plan, draft["nodeId"])
        if canonical(draft["criteria"]) != canonical(node["criteria"]):
            fail("RUBRIC_MISMATCH", f"criteria must equal the criteria of node {node['nodeId']}")
        if draft["purpose"] == "check" and not draft["lessonText"]:
            fail("INVALID_REQUEST", "a check question carries the lessonText it explains")
        if draft["purpose"] != "check" and draft["lessonText"] is not None:
            fail("INVALID_REQUEST", f"{draft['purpose']} questions do not teach first; lessonText must be null")
        if draft["purpose"] == "transfer":
            if draft["format"] != "open" or draft["nodeId"] != plan["goalNodeId"] or not draft["variationReason"]:
                fail("INVALID_REQUEST", "a final transfer is an open question on goalNodeId with variationReason")
            if prompt_hash(draft["prompt"]) == policy.first_check_hash(state, draft["nodeId"]):
                fail("INVALID_REQUEST", "the transfer prompt must differ from the first check")
    _check_format(draft)
    parent = draft["parentQuestionId"]
    if parent and parent not in state.questions:
        fail("INVALID_REFERENCE", f"parentQuestionId {parent} does not exist")
    check_refs(state, context, draft["sourceRefs"])
    question_id = entity_id(request["workspaceId"], request["operationId"], "question")
    question = {
        **draft, "questionId": question_id, "sessionId": session["sessionId"], "createdAt": context.now,
        "promptHash": prompt_hash(draft["prompt"]), "version": 1,
    }
    return session["sessionId"], question, {"sessionId": session["sessionId"], "questionId": question_id}


def _check_format(draft):
    options = [option["optionId"] for option in draft["options"]]
    if draft["format"] == "open":
        if options or draft["correctOptionIds"] or draft["selectionCriterionId"]:
            fail("INVALID_REQUEST", "open questions use options=[], correctOptionIds=[], selectionCriterionId=null")
        return
    if not 2 <= len(options) <= 6 or len(set(options)) != len(options):
        fail("INVALID_REQUEST", "choice questions need 2-6 distinct options")
    correct = draft["correctOptionIds"]
    if not correct or any(item not in options for item in correct):
        fail("INVALID_REQUEST", "correctOptionIds must be options of the question")
    if draft["format"] == "single_choice" and len(correct) != 1:
        fail("INVALID_REQUEST", "single_choice has exactly one correct option")
    criteria = [item["criterionId"] for item in draft["criteria"]]
    if draft["selectionCriterionId"] not in criteria:
        fail("INVALID_REQUEST", "selectionCriterionId must be one of the question criteria")


def decide_hint_record(state, request, context):
    payload = request["payload"]
    session = current_session(state, payload["sessionId"])
    require_pending(session, ("question",), {"questionId": payload["questionId"]})
    hints = state.hints.get(payload["questionId"], [])
    if len(hints) >= 3:
        fail("HINT_LIMIT", "this question already has three hints")
    hint = {
        "hintId": entity_id(request["workspaceId"], request["operationId"], "hint"),
        "questionId": payload["questionId"], "level": len(hints) + 1, "kind": payload["kind"],
        "text": payload["text"], "requestText": payload["userText"], "recordedAt": context.now,
    }
    return session["sessionId"], hint, {"sessionId": session["sessionId"], "hintId": hint["hintId"]}


def decide_question_close(state, request, context):
    payload = request["payload"]
    session = current_session(state, payload["sessionId"])
    require_pending(session, ("question",), {"questionId": payload["questionId"]})
    return session["sessionId"], dict(payload), _session_ids(state, session)


def decide_answer_record(state, request, context):
    payload = request["payload"]
    session = current_session(state, payload["sessionId"])
    answer = payload["answer"]
    require_pending(session, ("question",), {"questionId": answer["questionId"]})
    question = state.questions[answer["questionId"]]["q"]
    options = {option["optionId"] for option in question["options"]}
    selected = answer["selectedOptionIds"]
    if answer["responseKind"] == "dont_know":
        if answer["confidence"] is not None or selected:
            fail("INVALID_ANSWER", "dont_know uses confidence=null and selectedOptionIds=[]")
    elif question["format"] == "open" and selected:
        fail("INVALID_ANSWER", "open questions take no selectedOptionIds")
    elif question["format"] != "open":
        if not selected or any(item not in options for item in selected):
            fail("INVALID_ANSWER", "selectedOptionIds must be options of the question")
        if question["format"] == "single_choice" and len(selected) != 1:
            fail("INVALID_ANSWER", "single_choice takes exactly one selected option")
    hints = state.hints.get(answer["questionId"], [])
    reported = answer["reportedExternalHelp"]
    if reported == "solution" or question["promptHash"] in state.revealed_hashes:
        assistance = "solution_seen"
    elif hints or reported == "hint":
        assistance = "hinted"
    elif reported == "unknown":
        assistance = "unknown"
    else:
        assistance = "none_recorded"
    answer_id = entity_id(request["workspaceId"], request["operationId"], "answer")
    record = {
        **answer, "answerId": answer_id, "sessionId": session["sessionId"], "recordedAt": context.now,
        "hintIds": [hint["hintId"] for hint in hints], "assistance": assistance,
    }
    return session["sessionId"], record, {"sessionId": session["sessionId"], "answerId": answer_id}


def decide_assessment_record(state, request, context):
    payload = request["payload"]
    session = current_session(state, payload["sessionId"])
    assessment = payload["assessment"]
    replaces = assessment["replacesAssessmentId"]
    if replaces is None:
        if assessment["changeReason"] is not None:
            fail("INVALID_REQUEST", "changeReason is only for a corrected assessment")
        require_pending(session, ("assessment",), {"answerId": assessment["answerId"]})
    else:
        old = state.assessments.get(replaces)
        if old is None:
            fail("INVALID_REFERENCE", f"assessment {replaces} does not exist")
        continuation = state.cont.get(session["sessionId"])
        open_window = (
            session["pending"] and session["pending"]["kind"] in ("continuation", "repair")
            and continuation and continuation["assessmentId"] == replaces
            and state.effective.get(old["x"]["answerId"]) == replaces
        )
        if not open_window:
            fail("ASSESSMENT_FINALIZED", "only the latest assessment can be corrected before its continuation or repair is used")
        if assessment["answerId"] != old["x"]["answerId"]:
            fail("INVALID_REFERENCE", "a correction must assess the same answer")
        if not assessment["changeReason"]:
            fail("INVALID_REQUEST", "a correction needs changeReason")
    answer = state.answers[assessment["answerId"]]["a"]
    question = state.questions[answer["questionId"]]["q"]
    results = {item["criterionId"]: item["result"] for item in assessment["criterionResults"]}
    expected = [item["criterionId"] for item in question["criteria"]]
    if len(results) != len(assessment["criterionResults"]) or sorted(results) != sorted(expected):
        fail("RUBRIC_MISMATCH", f"assess each criterion exactly once: {expected}")
    selection = question["selectionCriterionId"]
    if selection:
        chosen = sorted(answer["selectedOptionIds"]) == sorted(question["correctOptionIds"])
        engine = "met" if answer["responseKind"] == "answer" and chosen else "not_met"
        if results[selection] != engine:
            fail("RUBRIC_MISMATCH", f"{selection} is decided by the selected options: {engine}")
    values = list(results.values())
    if "unassessable" in values:
        verdict = "ungradable"
    elif all(value == "met" for value in values):
        verdict = "correct"
    elif all(value == "not_met" for value in values):
        verdict = "not_recalled" if answer["responseKind"] == "dont_know" else "incorrect"
    else:
        verdict = "partial"
    if (verdict == "ungradable") != (assessment["issue"] is not None):
        fail("INVALID_REQUEST", "issue is required exactly when a criterion is unassessable")
    check_refs(state, context, assessment["sourceRefs"])
    assessment_id = entity_id(request["workspaceId"], request["operationId"], "assessment")
    record = {
        **assessment, "assessmentId": assessment_id, "questionId": question["questionId"],
        "sessionId": session["sessionId"], "recordedAt": context.now, "verdict": verdict,
    }
    return session["sessionId"], record, {"sessionId": session["sessionId"], "assessmentId": assessment_id}


def decide_continuation_accept(state, request, context):
    payload = request["payload"]
    session = current_session(state, payload["sessionId"])
    require_pending(session, ("continuation",))
    intent = payload["intent"]
    if session["phase"] == "diagnosing" and intent != "next":
        fail("INVALID_TRANSITION", "during diagnosis the only continuation is intent=next")
    if session["mode"] != "learning" and intent == "replan":
        fail(
            "INVALID_TRANSITION", "replan is only for learning sessions",
            "session.finish outcome=partial 후 session.start mode=learning startAt=replan으로 계획을 고친다.",
        )
    return session["sessionId"], dict(payload), _session_ids(state, session)


def decide_content_resolve(state, request, context):
    payload = request["payload"]
    session = current_session(state, payload["sessionId"])
    require_pending(session, ("repair",), {"assessmentId": payload["assessmentId"]})
    if payload["resolution"] == "replan" and session["phase"] != "learning":
        fail(
            "INVALID_TRANSITION", f"resolution=replan is not available in phase={session['phase']}",
            "new_question으로 해소하거나, 연습·복습이면 partial로 종료한 뒤 learning replan 세션을 시작한다.",
        )
    check_refs(state, context, payload["sourceRefs"])
    return session["sessionId"], dict(payload), _session_ids(state, session)


# ---- decide: workspace commands ---------------------------------------------------

def decide_source_register(state, request, context):
    payload, material = request["payload"], context.material
    origin = canonical({"originKind": payload["originKind"], "origin": payload["origin"]}).decode("utf-8")
    source_id = named_id(request["workspaceId"], f"source:{origin}:{material['contentHash']}")
    if source_id in state.sources:
        fail("FILE_EXISTS", f"this content and origin are already registered as {source_id}")
    source = {
        "sourceId": source_id, "snapshotPath": f"sources/{source_id}.txt",
        "contentHash": material["contentHash"], "materialPath": material["relativePath"],
        "byteLength": material["byteLength"], "lineCount": material["lineCount"],
        "title": payload["title"], "originKind": payload["originKind"], "origin": payload["origin"],
        "registeredAt": context.now,
    }
    return None, source, {"sourceId": source_id}


def knowledge_ids(state, workspace_id, operation_id, extraction):
    """Map localKeys to proposition IDs and resolve chains; validates references."""
    keys = [draft["localKey"] for draft in extraction["propositions"]]
    if len(keys) != len(set(keys)):
        fail("INVALID_REFERENCE", "localKey is repeated")
    links = {}
    for link in extraction["identityLinks"]:
        if link["localKey"] not in keys or link["localKey"] in links:
            fail("INVALID_REFERENCE", f"identity link for {link['localKey']} has no single new proposition")
        if link["existingId"] not in state.props:
            fail("INVALID_REFERENCE", f"proposition {link['existingId']} does not exist")
        links[link["localKey"]] = link["existingId"]
    ids = {key: links.get(key) or entity_id(workspace_id, operation_id, f"prop:{key}") for key in keys}

    def resolve(endpoint):
        if endpoint["kind"] == "local":
            if endpoint["id"] not in ids:
                fail("INVALID_REFERENCE", f"local proposition {endpoint['id']} is not in this extraction")
            return ids[endpoint["id"]]
        if endpoint["id"] not in state.props:
            fail("INVALID_REFERENCE", f"proposition {endpoint['id']} does not exist")
        return endpoint["id"]

    chains = []
    for draft in extraction["chains"]:
        premises = [resolve(item) for item in draft["premises"]]
        conclusion = resolve(draft["conclusion"])
        if len(set(premises)) != len(premises):
            fail("INVALID_REFERENCE", "a chain repeats a premise")
        if conclusion in premises:
            fail("INVALID_REFERENCE", "a chain cannot use its conclusion as a premise")
        premises = sorted(premises)
        chain_id = named_id(workspace_id, "chain:" + canonical({"premises": premises, "conclusion": conclusion}).decode("utf-8"))
        chains.append((chain_id, premises, conclusion, draft["sourceRefs"]))
    return ids, chains


def _within_scope(ref, scope):
    for item in scope:
        if item["kind"] != ref["kind"]:
            continue
        if ref["kind"] == "lesson" and item["eventId"] == ref["eventId"]:
            return True
        if (
            ref["kind"] == "material" and item["sourceId"] == ref["sourceId"]
            and item["startLine"] <= ref["startLine"] and ref["endLine"] <= item["endLine"]
        ):
            return True
    return False


def decide_knowledge_commit(state, request, context):
    extraction = request["payload"]["extraction"]
    check_refs(state, context, extraction["scopeRefs"])
    for draft in extraction["propositions"] + extraction["chains"]:
        check_refs(state, context, draft["sourceRefs"])
        for ref in draft["sourceRefs"]:
            if not _within_scope(ref, extraction["scopeRefs"]):
                fail("INVALID_REFERENCE", "a sourceRef is outside the selected scopeRefs")
    ids, chains = knowledge_ids(state, request["workspaceId"], request["operationId"], extraction)
    entity_ids = {f"prop:{key}": value for key, value in ids.items()}
    entity_ids.update({f"chain:{index}": chain[0] for index, chain in enumerate(chains)})
    return None, extraction, entity_ids


DECIDE = {
    "session.start": decide_session_start,
    "session.pause": decide_session_pause,
    "session.resume": decide_session_resume,
    "session.finish": decide_session_finish,
    "diagnosis.complete": decide_diagnosis_complete,
    "plan.propose": decide_plan_propose,
    "plan.accept": decide_plan_accept,
    "question.pose": decide_question_pose,
    "hint.record": decide_hint_record,
    "question.reveal": decide_question_close,
    "question.skip": decide_question_close,
    "answer.record": decide_answer_record,
    "assessment.record": decide_assessment_record,
    "continuation.accept": decide_continuation_accept,
    "content.resolve": decide_content_resolve,
    "source.register": decide_source_register,
    "knowledge.commit": decide_knowledge_commit,
}


def workspace_event(request, created_at, learner_text):
    payload = request["payload"]
    workspace = {
        "schemaVersion": 1, "workspaceId": request["workspaceId"], "createdAt": created_at,
        "utcOffsetMinutes": payload["utcOffsetMinutes"], "goal": payload["goal"], "policyVersion": POLICY_VERSION,
    }
    return None, {"workspace": workspace, "initialLearnerText": learner_text}, {"workspaceId": request["workspaceId"]}
