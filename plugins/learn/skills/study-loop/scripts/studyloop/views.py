"""Packets, query views, regenerable projection files and exports."""

import json

from . import policy
from .contracts import fail

LEARNER_TEXT_LIMIT = 16000
HIDDEN = ("expectedAnswer", "correctOptionIds")


def public_question(question):
    return {key: value for key, value in question.items() if key not in HIDDEN}


def _shown(state):
    """The question, answer and assessment the current wait is about."""
    session = state.sessions.get(state.current) if state.current else None
    if session is None:
        return None, None, None, None
    pending = session["pending"]
    continuation = state.cont.get(session["sessionId"])
    question_id = answer_id = assessment_id = None
    if pending and pending["kind"] in ("question", "assessment"):
        question_id, answer_id = pending["questionId"], pending.get("answerId")
    elif continuation and continuation["kind"] != "resolve":
        question_id, answer_id = continuation["questionId"], continuation["answerId"]
        assessment_id = continuation["assessmentId"]
    return session, question_id, answer_id, assessment_id


def context_packet(state, learner_text):
    session, question_id, answer_id, assessment_id = _shown(state)
    if session is None and state.session_order:
        session = state.sessions[state.session_order[-1]]
    revealed = None
    continuation = state.cont.get(state.current) if state.current else None
    if continuation and continuation["kind"] == "reveal":
        question = state.questions[continuation["questionId"]]["q"]
        revealed = {
            "questionId": question["questionId"], "text": question["expectedAnswer"],
            "correctOptionIds": question["correctOptionIds"],
        }
    draft = state.plans.get(state.latest_version) if state.latest_version > (state.accepted_version or 0) else None
    return {
        "kind": "context",
        "workspace": state.workspace,
        "revision": state.revision,
        "session": session,
        "acceptedPlan": policy.accepted_plan(state),
        "draftPlan": draft,
        "progress": policy.all_progress(state),
        "question": public_question(state.questions[question_id]["q"]) if question_id else None,
        "revealedSolution": revealed,
        "answer": state.answers[answer_id]["a"] if answer_id else None,
        "assessment": state.assessments[assessment_id]["x"] if assessment_id else None,
        "hints": state.hints.get(question_id, []) if question_id else [],
        "learnerText": learner_text[:LEARNER_TEXT_LIMIT],
        "nextAction": policy.next_action(state),
    }


def assessor_packet(state, answer_id):
    session, _, _, _ = _shown(state)
    pending = session["pending"] if session else None
    continuation = state.cont.get(state.current) if state.current else None
    target = None
    if pending and pending["kind"] == "assessment":
        target = pending["answerId"]
    elif pending and pending["kind"] in ("continuation", "repair") and continuation and continuation["assessmentId"]:
        target = continuation["answerId"]
    if target is None or answer_id not in (None, target):
        fail("INVALID_TRANSITION", "the assessor view is only for the pending or still-correctable answer")
    answer = state.answers[target]["a"]
    return {
        "kind": "assessor",
        "question": state.questions[answer["questionId"]]["q"],
        "answer": answer,
        "hints": state.hints.get(answer["questionId"], []),
    }


# ---- query ------------------------------------------------------------------

def _require_null(payload, *names):
    for name in names:
        if payload[name] is not None:
            fail("INVALID_REQUEST", f"view={payload['view']} takes {name}=null")


def _page(state, items, payload):
    offset = 0
    if payload["cursor"]:
        revision, _, position = payload["cursor"].partition(":")
        if not (revision.isdigit() and position.isdigit()):
            fail("INVALID_REQUEST", "cursor is <revision>:<offset>")
        if int(revision) != state.revision:
            fail("REVISION_CONFLICT", f"the cursor was made at revision {revision}; the workspace is at {state.revision}")
        offset = int(position)
    end = offset + payload["limit"]
    following = f"{state.revision}:{end}" if end < len(items) else None
    return {"kind": "collection", "items": items[offset:end], "nextCursor": following}


def _matches(search, *texts):
    needle = search.casefold()
    return any(needle in text.casefold() for text in texts)


def passage(state, event_id):
    record = state.event_data.get(event_id)
    kind, data = (record["type"], record["data"]) if record else (None, None)
    speaker, passage_type, text = "teacher", None, None
    if kind == "question_posed" and data["lessonText"]:
        passage_type, text = "lesson", data["lessonText"]
    elif kind == "answer_recorded":
        speaker, passage_type, text = "learner", "answer", data["text"]
    elif kind == "assessment_recorded":
        passage_type, text = "feedback", data["feedback"]
    elif kind == "diagnosis_completed":
        passage_type, text = "diagnosis", data["summary"]
    elif kind == "question_revealed":
        passage_type, text = "solution", state.questions[data["questionId"]]["q"]["expectedAnswer"]
    if text is None:
        fail("INVALID_REFERENCE", f"event {event_id} has no readable lesson, answer, feedback, diagnosis or revealed solution")
    return {
        "eventId": event_id, "sessionId": record["sessionId"], "revision": record["revision"],
        "speaker": speaker, "passageType": passage_type, "text": text,
    }


def query(state, payload, learner_text):
    view = payload["view"]
    if view in ("resume", "status"):
        _require_null(payload, "id", "search", "cursor")
        return context_packet(state, learner_text)
    if view == "assessor":
        _require_null(payload, "search", "cursor")
        return assessor_packet(state, payload["id"])
    if view == "operation":
        _require_null(payload, "search", "cursor")
        if payload["id"] is None:
            fail("INVALID_REQUEST", "view=operation needs id=<operationId>")
        operation = state.ops.get(payload["id"])
        return {
            "kind": "operation", "found": operation is not None,
            "revision": operation["revision"] if operation else None,
            "requestHash": operation["requestHash"] if operation else None,
            "entityIds": operation["entityIds"] if operation else {},
        }
    if view == "record":
        _require_null(payload, "search", "cursor")
        if payload["id"] is None:
            fail("INVALID_REQUEST", "view=record needs id=<eventId>")
        item = {"id": payload["id"], "recordType": "passage", "data": passage(state, payload["id"])}
        return {"kind": "collection", "items": [item], "nextCursor": None}
    if view == "events":
        _require_null(payload, "search")
        items = [
            {"id": header["eventId"], "recordType": "event_header", "data": header}
            for header in state.events
            if payload["id"] is None or header["sessionId"] == payload["id"]
        ]
        return _page(state, items, payload)
    if view == "sources":
        sources = sorted(state.sources.values(), key=lambda item: item["sourceId"])
        if payload["id"]:
            sources = [item for item in sources if item["sourceId"] == payload["id"]]
            if not sources:
                fail("INVALID_REFERENCE", f"source {payload['id']} is not registered")
        if payload["search"]:
            sources = [item for item in sources if _matches(payload["search"], item["title"], item["origin"])]
        items = [{"id": item["sourceId"], "recordType": "source", "data": item} for item in sources]
        return _page(state, items, payload)
    # knowledge
    items = [{"id": key, "recordType": "proposition", "data": value} for key, value in state.props.items()]
    if payload["search"] is None:
        items += [{"id": key, "recordType": "chain", "data": value} for key, value in state.chains.items()]
    else:
        items = [
            item for item in items
            if _matches(payload["search"], item["data"]["name"], item["data"]["statement"], *item["data"]["aliases"])
        ]
    if payload["id"]:
        items = [item for item in items if item["id"] == payload["id"]]
        if not items:
            fail("INVALID_REFERENCE", f"{payload['id']} is not a proposition or chain")
    return _page(state, sorted(items, key=lambda item: item["id"]), payload)


# ---- projections --------------------------------------------------------------

def _json(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _marker(state):
    return f"<!-- study-loop revision {state.revision}: generated from records/events.jsonl; edits are overwritten -->\n"


def plan_markdown(state):
    goal = state.workspace["goal"]
    lines = [_marker(state), f"# 학습 계획: {goal['title']}", "", f"목표: {goal['description']} (깊이: {goal['depth']})", ""]
    plan = policy.accepted_plan(state)
    status = {item["nodeId"]: item for item in policy.all_progress(state)}
    if plan:
        lines += [f"## 승인된 계획 v{plan['version']} (목표 노드: {plan['goalNodeId']})", "",
                  "| 노드 | 목표 | 선행 | 상태 |", "| --- | --- | --- | --- |"]
        for node in plan["nodes"]:
            lines.append(
                f"| {node['title']} (`{node['nodeId']}`) | {node['objective']} | "
                f"{', '.join(node['prerequisites']) or '-'} | {status[node['nodeId']]['status']} |"
            )
        lines.append("")
    else:
        lines += ["아직 승인된 계획이 없다.", ""]
    if state.latest_version > (state.accepted_version or 0):
        draft = state.plans[state.latest_version]
        lines += [f"## 승인 대기 초안 v{draft['version']}", ""]
        lines += [f"- {node['title']} (`{node['nodeId']}`): {node['objective']}" for node in draft["nodes"]]
        lines.append("")
    return "\n".join(lines).encode("utf-8")


def session_markdown(state, session_id):
    session = state.sessions[session_id]
    lines = [
        _marker(state),
        f"# 세션 {session['startedAt']} ({session['mode']})", "",
        f"- 상태: {session['lifecycle']} · {session['phase']} · 결과 {session['outcome'] or '-'}",
        f"- 시작 요청: {session['startRequestText']}", "",
    ]
    for header in state.events:
        if header["sessionId"] != session_id:
            continue
        record = state.event_data[header["eventId"]]
        data, kind = record["data"], record["type"]
        if kind == "question_posed":
            lines += [f"## 질문 · {data['purpose']} · {data['nodeId'] or '진단'} ({header['recordedAt']})", ""]
            if data["lessonText"]:
                lines += [data["lessonText"], ""]
            lines += [f"**질문:** {data['prompt']}", ""]
            lines += [f"- ({option['optionId']}) {option['text']}" for option in data["options"]]
        elif kind == "hint_recorded":
            lines += [f"**힌트 {data['level']} ({data['kind']}):** {data['text']}", ""]
        elif kind == "answer_recorded":
            confidence = "미제출" if data["confidence"] is None else data["confidence"]
            lines += [f"**답변:** {data['text']}", "", f"- 확신도 {confidence} · 도움 {data['assistance']}", ""]
            if data["thinking"]:
                lines += [f"**생각:** {data['thinking']}", ""]
        elif kind == "assessment_recorded":
            label = "평가 교정" if data["replacesAssessmentId"] else "평가"
            lines += [f"**{label} ({data['verdict']}):** {data['feedback']}", ""]
        elif kind == "question_revealed":
            lines += [f"**풀이 공개:** {state.questions[data['questionId']]['q']['expectedAnswer']}", ""]
        elif kind == "question_skipped":
            lines += ["**건너뜀**", ""]
        elif kind == "diagnosis_completed":
            lines += ["## 진단 정리", "", data["summary"], ""]
        elif kind == "plan_proposed":
            lines += [f"## 계획 v{data['version']} 제안", ""]
        elif kind == "plan_accepted":
            lines += [f"## 계획 v{data['version']} 승인: {data['userText']}", ""]
        elif kind in ("session_paused", "session_resumed", "session_finished", "continuation_accepted", "content_resolved"):
            lines += [f"- {kind}: {data.get('userText') or data.get('correction', '')}", ""]
    return "\n".join(lines).encode("utf-8")


def projections(state, packet):
    files = {
        "workspace.json": _json({"revision": state.revision, "workspace": state.workspace}),
        "state.json": _json(packet),
        "plan.md": plan_markdown(state),
        "knowledge/propositions.json": _json({"revision": state.revision, "propositions": state.props}),
        "knowledge/chains.json": _json({"revision": state.revision, "chains": state.chains}),
    }
    for session_id in state.session_order:
        files[f"sessions/{session_id}.md"] = session_markdown(state, session_id)
    return files


def export_bytes(state, form):
    if form == "markdown":
        parts = [plan_markdown(state)] + [session_markdown(state, item) for item in state.session_order]
        names = [f"- {prop['name']}: {prop['statement']}" for prop in sorted(state.props.values(), key=lambda p: p["propositionId"])]
        if names:
            parts.append(("## 명제\n\n" + "\n".join(names) + "\n").encode("utf-8"))
        return b"\n".join(parts)
    questions = []
    for entry in sorted(state.questions.values(), key=lambda item: item["revision"]):
        shown = public_question(entry["q"])
        if entry["status"] == "revealed":
            shown["expectedAnswer"] = entry["q"]["expectedAnswer"]
        questions.append({**shown, "status": entry["status"]})
    return _json({
        "revision": state.revision,
        "workspace": state.workspace,
        "sessions": [state.sessions[item] for item in state.session_order],
        "plans": [state.plans[version] for version in sorted(state.plans)],
        "acceptedVersion": state.accepted_version,
        "progress": policy.all_progress(state),
        "questions": questions,
        "hints": [hint for key in sorted(state.hints) for hint in state.hints[key]],
        "answers": [item["a"] for item in sorted(state.answers.values(), key=lambda item: item["revision"])],
        "assessments": [item["x"] for item in sorted(state.assessments.values(), key=lambda item: item["revision"])],
        "diagnoses": [state.diagnoses[key] for key in sorted(state.diagnoses)],
        "sources": [state.sources[key] for key in sorted(state.sources)],
        "propositions": [state.props[key] for key in sorted(state.props)],
        "chains": [state.chains[key] for key in sorted(state.chains)],
    })
