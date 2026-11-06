"""Pure policy over replayed state: progress, next moves and next action.

Nothing here reads files or clocks. Decision rule version 1.0.0.
"""

from datetime import datetime, timedelta

from .contracts import WORKSPACE_COMMANDS

FAILURES = ("partial", "incorrect", "not_recalled")
CHECK = {"purpose": "check", "teachingMove": "initial_explanation"}
DIAGNOSTIC_LIMIT = 3


# ---- plan -----------------------------------------------------------------

def accepted_plan(state):
    return state.plans.get(state.accepted_version) if state.accepted_version else None


def plan_node(plan, node_id):
    return next((node for node in plan["nodes"] if node["nodeId"] == node_id), None)


def plan_errors(nodes, goal_node_id):
    """Return the first structural problem of a proposed plan, or None."""
    seen = {}
    for index, node in enumerate(nodes):
        if node["nodeId"] in seen:
            return f"nodeId {node['nodeId']} is repeated"
        criteria = [item["criterionId"] for item in node["criteria"]]
        if len(criteria) != len(set(criteria)):
            return f"{node['nodeId']}: criterionId is repeated"
        for prerequisite in node["prerequisites"]:
            if prerequisite not in seen:
                return (
                    f"{node['nodeId']}: prerequisite {prerequisite} must exist and come earlier "
                    "(cycles and forward references are not allowed)"
                )
        seen[node["nodeId"]] = index
    if goal_node_id not in seen:
        return f"goalNodeId {goal_node_id} is not a plan node"
    needed, frontier = {goal_node_id}, [goal_node_id]
    by_id = {node["nodeId"]: node for node in nodes}
    while frontier:
        for prerequisite in by_id[frontier.pop()]["prerequisites"]:
            if prerequisite not in needed:
                needed.add(prerequisite)
                frontier.append(prerequisite)
    unrelated = [node["nodeId"] for node in nodes if node["nodeId"] not in needed]
    if unrelated:
        return f"nodes {unrelated} do not lead to the goal node"
    return None


# ---- evidence ---------------------------------------------------------------

def local_date(state, timestamp):
    moment = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    return (moment + timedelta(minutes=state.workspace["utcOffsetMinutes"])).date()


def attempts(state, node_id):
    """Effective assessments of non-diagnostic questions on a node, oldest first."""
    rows = []
    for assessment_id in state.effective.values():
        record = state.assessments[assessment_id]
        question = state.questions[record["x"]["questionId"]]["q"]
        if question["nodeId"] == node_id and question["purpose"] != "diagnostic":
            answer = state.answers[record["x"]["answerId"]]["a"]
            rows.append((record, question, answer))
    rows.sort(key=lambda row: row[0]["revision"])
    return rows


def _independent(record, answer):
    return record["x"]["verdict"] == "correct" and answer["assistance"] == "none_recorded"


def progress(state, node_id):
    rows = [row for row in attempts(state, node_id) if row[0]["x"]["verdict"] != "ungradable"]
    last_failure = max(
        (index for index, row in enumerate(rows) if row[0]["x"]["verdict"] in FAILURES), default=-1
    )
    after = rows[last_failure + 1:]
    qualifying = [row for row in after if _independent(row[0], row[2])]
    helped = [row for row in after if row[0]["x"]["verdict"] == "correct"]
    streak = 0
    for record, _, _ in reversed(rows):
        if record["x"]["verdict"] in FAILURES:
            streak += 1
        elif record["x"]["verdict"] == "correct":
            break
    if qualifying:
        status = "demonstrated"
    elif helped:
        status = "supported"
    elif rows:
        status = "needs_review"
    elif _exposed(state, node_id):
        status = "exposed"
    else:
        status = "unseen"
    return {
        "nodeId": node_id,
        "qualified": bool(qualifying),
        "status": status,
        "latestAssessmentId": rows[-1][0]["x"]["assessmentId"] if rows else None,
        "qualifyingAssessmentId": qualifying[-1][0]["x"]["assessmentId"] if qualifying else None,
        "failureStreak": streak,
        "delayedEvidenceAnswerIds": delayed_evidence(state, rows),
    }


def _exposed(state, node_id):
    for entry in state.questions.values():
        question = entry["q"]
        if question["nodeId"] == node_id and (question["lessonText"] or entry["status"] == "revealed"):
            return True
    return False


def delayed_evidence(state, rows):
    """Independent success on a later local date, on a different prompt, after a helped success."""
    found = []
    for index, (record, question, answer) in enumerate(rows):
        if not _independent(record, answer) or not question["variationReason"]:
            continue
        today = local_date(state, answer["recordedAt"])
        for earlier, earlier_question, earlier_answer in rows[:index]:
            if (
                earlier["x"]["verdict"] == "correct"
                and earlier_answer["assistance"] != "none_recorded"
                and local_date(state, earlier_answer["recordedAt"]) < today
                and earlier_question["promptHash"] != question["promptHash"]
            ):
                found.append(answer["answerId"])
                break
    return found


def all_progress(state):
    plan = accepted_plan(state)
    return [progress(state, node["nodeId"]) for node in plan["nodes"]] if plan else []


def first_check_hash(state, node_id):
    checks = sorted(
        (entry for entry in state.questions.values()
         if entry["q"]["nodeId"] == node_id and entry["q"]["purpose"] == "check"),
        key=lambda entry: entry["revision"],
    )
    return checks[0]["q"]["promptHash"] if checks else None


def final_transfer_done(state):
    plan = accepted_plan(state)
    if not plan:
        return False
    goal = plan["goalNodeId"]
    first = first_check_hash(state, goal)
    for record, question, answer in attempts(state, goal):
        if (
            question["purpose"] == "transfer"
            and question["format"] == "open"
            and question["variationReason"]
            and question["promptHash"] != first
            and _independent(record, answer)
        ):
            return True
    return False


def goal_demonstrated(state):
    plan = accepted_plan(state)
    return bool(plan) and all(item["qualified"] for item in all_progress(state)) and final_transfer_done(state)


# ---- choosing the next question -------------------------------------------

def default_target(state, session):
    plan = accepted_plan(state)
    if not plan:
        return None
    qualified = {item["nodeId"]: item["qualified"] for item in all_progress(state)}
    for node in plan["nodes"]:
        if (
            not qualified[node["nodeId"]]
            and node["nodeId"] not in session["deferredNodeIds"]
            and all(qualified[item] for item in node["prerequisites"])
        ):
            return node["nodeId"]
    return None


def learning_advance(state, session):
    """(nodeId, requiredMove) for the next new learning question, or (None, None)."""
    target = default_target(state, session)
    if target:
        return target, dict(CHECK)
    plan = accepted_plan(state)
    if (
        plan and plan["goalNodeId"] not in session["deferredNodeIds"]
        and all(item["qualified"] for item in all_progress(state)) and not final_transfer_done(state)
    ):
        return plan["goalNodeId"], {"purpose": "transfer", "teachingMove": None}
    return None, None


def probe_target(state, node_id):
    plan = accepted_plan(state)
    order = [node["nodeId"] for node in plan["nodes"]]
    prerequisites = plan_node(plan, node_id)["prerequisites"]
    return min(prerequisites, key=order.index) if prerequisites else None


def practice_queue(state, max_items):
    """needs_review by latest failure first, then oldest independent success, plan order on ties."""
    plan = accepted_plan(state)
    order = {node["nodeId"]: index for index, node in enumerate(plan["nodes"])}
    review, rest = [], []
    for node in plan["nodes"]:
        rows = attempts(state, node["nodeId"])
        node_id = node["nodeId"]
        if progress(state, node_id)["status"] == "needs_review":
            last_failure = max(
                (row[0]["revision"] for row in rows if row[0]["x"]["verdict"] in FAILURES), default=0
            )
            review.append((-last_failure, order[node_id], node_id))
        else:
            successes = [row[0]["revision"] for row in rows if _independent(row[0], row[2])]
            rest.append((max(successes) if successes else -1, order[node_id], node_id))
    ranked = [item[2] for item in sorted(review)] + [item[2] for item in sorted(rest)]
    return ranked[:max_items]


def recommend(state, session, question, assessment, answer):
    """recommendedMove right after an assessment (never for ungradable)."""
    if question["purpose"] == "diagnostic":
        return None
    node = progress(state, question["nodeId"])
    independent = assessment["verdict"] == "correct" and answer["assistance"] == "none_recorded"
    if session["mode"] != "learning":
        if independent:
            return "advance"
        return "replan" if node["failureStreak"] >= 3 else "fresh_check"
    if assessment["verdict"] == "correct":
        if not independent:
            return "fresh_check"
        node_id, _ = learning_advance(state, session)
        return "advance" if node_id else "finish"
    if node["failureStreak"] >= 3:
        return "replan"
    if node["failureStreak"] == 2:
        return "prerequisite_probe" if probe_target(state, question["nodeId"]) else "alternative_explanation"
    return "targeted_repair"


def follow(state, session, continuation, intent):
    """Session fields after continuation.accept. Assumes the intent was validated."""
    node_id = continuation["nodeId"]
    fields = {"requiredMove": None, "currentNodeId": None}
    if session["phase"] == "diagnosing":
        posed = diagnostic_count(state, session)
        if posed < DIAGNOSTIC_LIMIT:
            fields["requiredMove"] = {"purpose": "diagnostic", "teachingMove": None}
        return fields
    if session["mode"] != "learning":
        queue, index = session["targetNodeIds"], session["queueIndex"]
        following = _practice_at(session, queue[index + 1] if index + 1 < len(queue) else None, index + 1)
        if intent == "skip_target":
            return following
        move = continuation["recommendedMove"] if intent == "next" else None
        if intent == "retry" or move == "fresh_check" or continuation["kind"] == "resolve":
            return _practice_at(session, node_id, index)
        if move == "replan":
            return fields
        return following
    if intent == "replan":
        return {**fields, "phase": "planning"}
    if intent == "retry":
        return {**fields, "currentNodeId": node_id, "requiredMove": {"purpose": "recheck", "teachingMove": None}}
    if intent == "skip_target":
        deferred = list(session["deferredNodeIds"])
        if node_id and node_id not in deferred:
            deferred.append(node_id)
        target, move = learning_advance(state, {**session, "deferredNodeIds": deferred})
        return {"deferredNodeIds": deferred, "currentNodeId": target, "requiredMove": move}
    if continuation["kind"] == "resolve":
        purpose = continuation["purpose"]
        teaching = "initial_explanation" if purpose == "check" else None
        return {"currentNodeId": node_id, "requiredMove": {"purpose": purpose, "teachingMove": teaching}}
    move = continuation["recommendedMove"]
    if move == "replan":
        return {**fields, "phase": "planning"}
    if move == "fresh_check":
        return {"currentNodeId": node_id, "requiredMove": {"purpose": "recheck", "teachingMove": None}}
    if move in ("targeted_repair", "alternative_explanation"):
        return {"currentNodeId": node_id, "requiredMove": {"purpose": "check", "teachingMove": move}}
    if move == "prerequisite_probe":
        return {
            "currentNodeId": probe_target(state, node_id),
            "requiredMove": {"purpose": "prerequisite_probe", "teachingMove": None},
        }
    target, required = learning_advance(state, session)
    return {"currentNodeId": target, "requiredMove": required}


def _practice_at(session, node_id, index):
    if node_id is None:
        return {"requiredMove": None, "currentNodeId": None, "queueIndex": index}
    purpose = "practice" if session["mode"] == "practice" else "review"
    return {"requiredMove": {"purpose": purpose, "teachingMove": None}, "currentNodeId": node_id, "queueIndex": index}


def diagnostic_count(state, session):
    return sum(
        1 for entry in state.questions.values()
        if entry["q"]["sessionId"] == session["sessionId"]
        and entry["q"]["purpose"] == "diagnostic"
        and entry["status"] != "discarded"
    )


def assessed_diagnostics(state, session):
    count = 0
    for assessment_id in state.effective.values():
        assessment = state.assessments[assessment_id]["x"]
        question = state.questions[assessment["questionId"]]["q"]
        if (
            question["sessionId"] == session["sessionId"]
            and question["purpose"] == "diagnostic"
            and assessment["verdict"] != "ungradable"
        ):
            count += 1
    return count


# ---- next action ------------------------------------------------------------

def next_action(state):
    session = state.sessions.get(state.current) if state.current else None
    action = {"nodeId": None, "questionId": None, "answerId": None, "recommendedMove": None}

    def done(kind, reason, commands):
        return {"kind": kind, "reason": reason, **action, "allowedCommands": list(commands) + list(WORKSPACE_COMMANDS)}

    if session is None:
        return done("start_session", "학습 세션이 없다.", ["session.start"])
    if session["lifecycle"] == "paused":
        return done("resume_session", "세션이 일시 중단되었다. 재개하거나 종료한다.", ["session.resume", "session.finish"])
    pending = session["pending"]
    common = ["session.pause", "session.finish"]
    action["nodeId"] = session["currentNodeId"]
    if pending:
        kind = pending["kind"]
        action["questionId"] = pending.get("questionId")
        action["answerId"] = pending.get("answerId")
        if kind == "question":
            commands = ["answer.record", "question.reveal", "question.skip"]
            if len(state.hints.get(pending["questionId"], [])) < 3:
                commands.insert(1, "hint.record")
            return done("await_answer", "학습자의 실제 답변을 기다린다.", commands + common)
        if kind == "assessment":
            return done("assess_answer", "저장한 답변을 assessor packet으로 평가한다.", ["assessment.record"] + common)
        if kind == "plan_approval":
            return done(
                "await_plan_approval", "제안한 계획에 대한 학습자의 응답을 기다린다.",
                ["plan.accept", "plan.propose"] + common,
            )
        continuation = state.cont[session["sessionId"]]
        action["questionId"] = continuation["questionId"]
        action["answerId"] = continuation["answerId"]
        action["nodeId"] = continuation["nodeId"]
        regrade = ["assessment.record"] if continuation["assessmentId"] else []
        if kind == "repair":
            return done("repair_content", "문항·자료·rubric 문제를 먼저 해소한다.", ["content.resolve"] + regrade + common)
        action["recommendedMove"] = continuation["recommendedMove"]
        commands = ["continuation.accept"] + regrade
        if session["phase"] == "diagnosing":
            commands.append("diagnosis.complete")
        return done("wait_for_continue", "피드백을 보여준 뒤 학습자의 진행 의사를 기다린다.", commands + common)
    phase = session["phase"]
    if phase == "diagnosing":
        # diagnosis.complete is always possible: with an assessed diagnostic, or with
        # skipRequested and the learner's own words.
        commands = (["question.pose"] if session["requiredMove"] else []) + ["diagnosis.complete"]
        if session["requiredMove"]:
            return done("ask_diagnostic", "출발점을 찾을 진단 질문을 한다.", commands + common)
        return done("complete_diagnosis", "진단 질문을 모두 했다. 진단을 정리한다.", commands + common)
    if phase == "planning":
        return done("propose_plan", "진단을 근거로 학습 계획을 제안한다.", ["plan.propose"] + common)
    if session["requiredMove"]:
        return done("present_and_check", "requiredMove에 맞춰 설명하고 확인 질문을 한다.", ["question.pose"] + common)
    if session["mode"] == "learning" and goal_demonstrated(state):
        reason = "모든 노드와 최종 transfer 증거가 있다. 종료를 제안한다."
    elif session["mode"] == "learning":
        reason = "보류한 노드 외에 진행할 노드가 없다. partial 종료를 제안한다."
    else:
        reason = "연습 대기열을 마쳤거나 학습 세션의 재계획이 필요하다. 종료를 제안한다."
    return done("offer_finish", reason, common)
