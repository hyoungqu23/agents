"""Study Loop engine: contract fixtures, the 44 acceptance cases and the CLI."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "plugins/learn/skills/study-loop"
FIXTURES = ROOT / "scripts/tests/fixtures/study-loop"
SPEC = ROOT / "docs/plans/learnharness-v1"  # local design notes; not part of the repository
sys.path.insert(0, str(SKILL / "scripts"))

from studyloop import cli  # noqa: E402
from studyloop.contracts import check  # noqa: E402

WS = "11111111-1111-4111-8111-111111111111"
OTHER_WS = "33333333-3333-4333-8333-333333333333"
CLAUDE = {"host": "claude-code", "hostVersion": None, "model": None, "authMode": "subscription"}
CODEX = {"host": "codex", "hostVersion": None, "model": None, "authMode": "subscription"}
READS = ("workspace.query", "workspace.validate", "workspace.export")


def crit(*ids):
    return [{"criterionId": item, "description": f"{item}를 보인다"} for item in ids]


def node(node_id, prerequisites=(), criteria=("state-result",), objective=None):
    return {
        "nodeId": node_id, "title": node_id, "objective": objective or f"{node_id}를 설명한다",
        "depth": "explain", "prerequisites": list(prerequisites), "criteria": crit(*criteria), "sourceRefs": [],
    }


@unittest.skipIf(sys.version_info < (3, 10), "study-loop needs Python 3.10+")
class Lab(unittest.TestCase):
    """A workspace driven through the engine's run() with a controllable clock."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "ws"
        self.count = 0
        self.now = "2026-11-06T00:00:00Z"
        self.revision = 0
        self.actor = CLAUDE

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ---- transport --------------------------------------------------------------

    def new_op(self):
        self.count += 1
        return f"22222222-2222-4222-8222-{self.count:012x}"

    def request(self, command, payload, expected=..., op=None, ws=WS):
        if expected is ...:
            expected = 0 if command == "workspace.init" else None if command in READS else self.revision
        return {
            "protocolVersion": 1, "workspaceId": ws, "operationId": op or self.new_op(),
            "expectedRevision": expected, "actor": self.actor, "command": command, "payload": payload,
        }

    def call(self, request, **kwargs):
        response, code = cli.run(json.dumps(request, ensure_ascii=False).encode(), str(self.root), lambda: self.now, **kwargs)
        self.assertIsNone(check(response, "Response"), response)
        if response["ok"]:
            self.revision = response["revision"]
            self.assertEqual(code, 0)
        self.code = code
        return response

    def send(self, command, payload, **kwargs):
        return self.call(self.request(command, payload, **{k: v for k, v in kwargs.items() if k in ("expected", "op", "ws")}))

    def ok(self, command, payload, **kwargs):
        response = self.send(command, payload, **kwargs)
        self.assertTrue(response["ok"], response.get("error"))
        return response["result"]

    def refuse(self, code, command, payload, **kwargs):
        before = self.journal()
        response = self.send(command, payload, **kwargs)
        self.assertFalse(response["ok"], response)
        self.assertEqual(response["error"]["code"], code, response["error"])
        self.assertEqual(self.journal(), before, "a refused request must not change the journal")
        return response

    def journal(self):
        path = self.root / "records/events.jsonl"
        return path.read_bytes() if path.exists() else b""

    def packet(self):
        return self.ok("workspace.query", {"view": "resume", "id": None, "search": None, "cursor": None, "limit": 20})

    @property
    def sid(self):
        return self.packet()["session"]["sessionId"]

    # ---- learning steps -----------------------------------------------------------

    def init(self, learner="수학을 복습한다."):
        return self.ok("workspace.init", {
            "goal": {"title": "덧셈", "description": "덧셈을 설명한다", "depth": "explain"},
            "utcOffsetMinutes": 540, "learnerText": learner,
        })

    def start(self, mode="learning", start_at="auto", targets=(), max_items=None):
        return self.ok("session.start", {
            "mode": mode, "startAt": start_at, "targetNodeIds": list(targets), "maxItems": max_items, "userText": "시작하자",
        })["packet"]

    def question(self, purpose=None, prompt="2+3은 무엇이며 왜 그런가?", **overrides):
        packet = self.packet()
        move = packet["session"]["requiredMove"]
        purpose = purpose or move["purpose"]
        node_id = None if purpose == "diagnostic" else packet["session"]["currentNodeId"]
        plan = packet["acceptedPlan"]
        criteria = crit("state-result")
        if node_id:
            criteria = next(item["criteria"] for item in plan["nodes"] if item["nodeId"] == node_id)
        draft = {
            "purpose": purpose, "nodeId": node_id, "planVersion": plan["version"] if node_id else None,
            "format": "open", "prompt": prompt, "options": [], "selectionCriterionId": None,
            "expectedAnswer": "5. 둘과 셋을 합치면 다섯이다.", "correctOptionIds": [], "criteria": criteria,
            "lessonText": "덧셈은 개수를 합쳐 세는 것이다." if purpose == "check" else None,
            "sourceRefs": [], "variationReason": None, "parentQuestionId": None,
        }
        draft.update(overrides)
        return draft

    def pose(self, draft=None, **overrides):
        draft = draft or self.question(**overrides)
        result = self.ok("question.pose", {"sessionId": self.sid, "question": draft})
        return result["entityIds"]["questionId"]

    def answer(self, question_id, text="5. 둘과 셋을 합치면 다섯이다.", kind="answer", confidence=None, help="none", selected=()):
        result = self.ok("answer.record", {"sessionId": self.sid, "answer": {
            "questionId": question_id, "responseKind": kind, "text": text, "selectedOptionIds": list(selected),
            "thinking": None, "confidence": confidence, "reportedExternalHelp": help,
        }})
        return result["entityIds"]["answerId"]

    def assessment(self, answer_id, results, replaces=None, reason=None, issue=None, refs=()):
        return {
            "answerId": answer_id, "replacesAssessmentId": replaces,
            "criterionResults": [{"criterionId": key, "result": value, "evidence": "실제 답변에서 확인"} for key, value in results.items()],
            "feedback": "피드백: 합과 이유를 확인했다.", "errorStep": None, "sourceRefs": list(refs),
            "issue": issue, "changeReason": reason,
        }

    def assess(self, answer_id, results=None, **kwargs):
        results = results or {"state-result": "met"}
        result = self.ok("assessment.record", {"sessionId": self.sid, "assessment": self.assessment(answer_id, results, **kwargs)})
        return result

    def attempt(self, results=None, help="none", **question):
        question_id = self.pose(**question)
        answer_id = self.answer(question_id, help=help)
        return question_id, answer_id, self.assess(answer_id, results)

    def proceed(self, intent="next"):
        return self.ok("continuation.accept", {"sessionId": self.sid, "intent": intent, "userText": "계속하자"})["packet"]

    def diagnose(self):
        question_id = self.pose()
        answer_id = self.answer(question_id)
        self.assess(answer_id)
        self.ok("diagnosis.complete", {
            "sessionId": self.sid, "summary": "기초는 안다.", "heldConcepts": [], "gaps": [],
            "evidenceAnswerIds": [answer_id], "skipRequested": False, "userText": None,
        })

    def propose(self, nodes, goal=None, base=None, reason=None):
        return self.ok("plan.propose", {
            "sessionId": self.sid, "baseVersion": self.packet_latest_version() if base is None else base,
            "goalNodeId": goal or nodes[-1]["nodeId"], "nodes": nodes, "diagnosisSummary": "기초는 안다.",
            "revisionReason": reason,
        })

    def packet_latest_version(self):
        packet = self.packet()
        plans = [plan["version"] for plan in (packet["draftPlan"], packet["acceptedPlan"]) if plan]
        return max(plans, default=0)

    def ready(self, nodes=None):
        """Initialized, diagnosed and learning with an accepted plan."""
        self.init()
        self.start()
        self.diagnose()
        self.propose(nodes or [node("addition")])
        self.ok("plan.accept", {"sessionId": self.sid, "version": self.packet_latest_version(), "userText": "좋아"})
        return self.packet()


class ContractFixtureTests(Lab):
    @unittest.skipUnless((SPEC / "contracts.schema.json").exists(), "design notes are not checked out")
    def test_schema_copy_matches_spec(self):
        self.assertEqual(
            (SKILL / "scripts/studyloop/contracts.schema.json").read_bytes(),
            (SPEC / "contracts.schema.json").read_bytes(),
        )

    def test_happy_path_fixture(self):
        fixture = json.loads((FIXTURES / "happy-path.json").read_text(encoding="utf-8"))
        self.now = fixture["clock"]
        for step in fixture["steps"]:
            with self.subTest(step=step["id"]):
                response = self.call(step["request"])
                self.assertTrue(response["ok"], response.get("error"))
                result = response["result"]
                packet = result.get("packet", result)
                expect = step["expect"]
                self.assertEqual(response["revision"], expect["revision"])
                self.assertEqual(response["committed"], expect["committed"])
                if "resultKind" in expect:
                    self.assertEqual(result["kind"], expect["resultKind"])
                if "nextAction" in expect:
                    self.assertEqual(packet["nextAction"]["kind"], expect["nextAction"])
                if "pendingQuestionId" in expect:
                    self.assertEqual(packet["session"]["pending"]["questionId"], expect["pendingQuestionId"])
                if "expectedAnswer" in expect:
                    self.assertEqual(result["question"]["expectedAnswer"], expect["expectedAnswer"])
        final = fixture["finalExpect"]
        packet = self.packet()
        self.assertEqual(packet["session"]["pending"]["kind"], final["pending"])
        self.assertEqual([item["nodeId"] for item in packet["progress"] if item["qualified"]], final["qualifiedNodeIds"])

    def test_protocol_examples_are_reproduced(self):
        examples = json.loads((FIXTURES / "protocol-examples.json").read_text(encoding="utf-8"))
        fixture = json.loads((FIXTURES / "happy-path.json").read_text(encoding="utf-8"))
        self.now = fixture["clock"]
        response = self.call(fixture["steps"][0]["request"])
        commit = json.loads(self.journal().splitlines()[0])
        self.assertEqual(commit, examples["commit"])
        self.assertEqual(json.loads((self.root / "records/.init.json").read_text()), examples["initIntent"])
        self.assertEqual(response, examples["successResponse"])
        for name in ("initIntent", "commit", "successResponse", "failureResponse"):
            definition = {"initIntent": "InitIntent", "commit": "Commit"}.get(name, "Response")
            self.assertIsNone(check(examples[name], definition), name)

    def test_structural_negative_cases(self):
        cases = json.loads((FIXTURES / "acceptance-cases.json").read_text(encoding="utf-8"))["structuralNegativeCases"]
        for case in cases:
            with self.subTest(case=case["id"]):
                response = self.call(case["request"])
                self.assertFalse(response["ok"])
                expected = "UNSUPPORTED_VERSION" if case["id"] == "unsupported-protocol" else "INVALID_REQUEST"
                self.assertEqual(response["error"]["code"], expected)
                self.assertFalse(self.root.exists())

    def test_every_acceptance_case_has_a_test(self):
        cases = json.loads((FIXTURES / "acceptance-cases.json").read_text(encoding="utf-8"))["semanticCases"]
        names = {name for cls in (AcceptanceTests,) for name in dir(cls) if name.startswith("test_ac")}
        for case in cases:
            number = case["id"].split("-")[1]
            self.assertTrue(any(name.startswith(f"test_ac{number}_") for name in names), case["id"])


class AcceptanceTests(Lab):
    def test_ac01_empty_start(self):
        self.init()
        packet = self.start()
        self.assertEqual(self.revision, 2)
        self.assertEqual(packet["session"]["phase"], "diagnosing")
        self.assertIsNone(packet["session"]["pending"])
        self.assertEqual(packet["nextAction"]["kind"], "ask_diagnostic")

    def test_ac02_wait_for_real_answer(self):
        self.init()
        self.start()
        self.pose()
        self.refuse("INVALID_TRANSITION", "question.pose", {"sessionId": self.sid, "question": self.question("diagnostic")})

    def test_ac03_missing_prerequisite(self):
        self.ready([node("a"), node("b", ["a"])])
        draft = self.question()
        draft.update(nodeId="b")
        self.refuse("TARGET_NOT_ALLOWED", "question.pose", {"sessionId": self.sid, "question": draft})

    def test_ac04_partial_answer(self):
        self.ready([node("addition", criteria=("state-result", "explain-reason"))])
        _, _, result = self.attempt({"state-result": "met", "explain-reason": "not_met"})
        packet = result["packet"]
        self.assertEqual(packet["assessment"]["verdict"], "partial")
        self.assertFalse(packet["progress"][0]["qualified"])
        self.assertEqual(packet["nextAction"]["recommendedMove"], "targeted_repair")

    def test_ac05_correct_reasoning(self):
        self.ready()
        packet = self.attempt()[2]["packet"]
        self.assertEqual(packet["assessment"]["verdict"], "correct")
        self.assertEqual(packet["progress"][0]["status"], "demonstrated")
        self.assertEqual(packet["session"]["pending"]["kind"], "continuation")

    def test_ac06_right_answer_wrong_reason(self):
        self.ready([node("a", criteria=("answer", "reason")), node("b", ["a"])])
        packet = self.attempt({"answer": "met", "reason": "not_met"})[2]["packet"]
        self.assertEqual(packet["assessment"]["verdict"], "partial")
        after = self.proceed()
        self.assertEqual(after["session"]["currentNodeId"], "a")
        self.assertEqual(after["session"]["requiredMove"], {"purpose": "check", "teachingMove": "targeted_repair"})

    def test_ac07_hinted_correct(self):
        self.ready()
        question_id = self.pose()
        self.ok("hint.record", {"sessionId": self.sid, "questionId": question_id, "kind": "cue", "text": "개수를 세어 봐", "userText": "힌트 줘"})
        answer_id = self.answer(question_id)
        packet = self.assess(answer_id)["packet"]
        self.assertEqual(packet["answer"]["assistance"], "hinted")
        self.assertFalse(packet["progress"][0]["qualified"])
        self.assertEqual(packet["progress"][0]["status"], "supported")
        self.assertEqual(packet["nextAction"]["recommendedMove"], "fresh_check")

    def test_ac08_solution_exposed(self):
        self.ready()
        question_id = self.pose()
        packet = self.ok("question.reveal", {"sessionId": self.sid, "questionId": question_id, "userText": "풀이 보여줘"})["packet"]
        self.assertEqual(packet["session"]["pending"]["kind"], "continuation")
        self.assertIsNone(packet["answer"])
        self.assertEqual(packet["revealedSolution"]["questionId"], question_id)
        self.assertEqual(packet["nextAction"]["recommendedMove"], "fresh_check")
        export = json.loads(self._export_json())
        self.assertEqual([item for item in export["answers"] if item["questionId"] == question_id], [])
        self.assertEqual(export["questions"][-1]["status"], "revealed")

    def _export_json(self, path="artifacts/all.json", overwrite=True):
        self.ok("workspace.export", {"format": "json", "outputPath": path, "overwrite": overwrite})
        return (self.root / path).read_text(encoding="utf-8")

    def test_ac09_dont_know(self):
        self.ready()
        question_id = self.pose()
        self.refuse("INVALID_ANSWER", "answer.record", {"sessionId": self.sid, "answer": {
            "questionId": question_id, "responseKind": "dont_know", "text": "모르겠다", "selectedOptionIds": [],
            "thinking": None, "confidence": 30, "reportedExternalHelp": "none",
        }})
        answer_id = self.answer(question_id, text="모르겠다", kind="dont_know")
        packet = self.assess(answer_id, {"state-result": "not_met"})["packet"]
        self.assertEqual(packet["assessment"]["verdict"], "not_recalled")
        self.assertEqual(packet["answer"]["confidence"], None)

    def test_ac10_missing_confidence(self):
        self.ready()
        answer_id = self.answer(self.pose(), confidence=None)
        self.assertIsNone(self.packet()["answer"]["confidence"])
        self.assertIn('"confidence":null', self.journal().decode())
        self.assertTrue(answer_id)

    def test_ac11_delayed_performance(self):
        self.ready([node("a"), node("b", ["a"])])
        question_id = self.pose()
        self.ok("hint.record", {"sessionId": self.sid, "questionId": question_id, "kind": "cue", "text": "세어 봐", "userText": "힌트"})
        self.assess(self.answer(question_id))
        self.proceed()  # fresh_check
        self.now = "2026-11-07T00:00:00Z"
        question_id = self.pose(prompt="사과 4개와 1개는 모두 몇 개인가?", variationReason="다른 수와 상황으로 다시 확인")
        answer_id = self.answer(question_id)
        packet = self.assess(answer_id)["packet"]
        progress = packet["progress"][0]
        self.assertEqual(progress["delayedEvidenceAnswerIds"], [answer_id])
        self.assertTrue(progress["qualified"])
        self.assertEqual(set(progress), {"nodeId", "qualified", "status", "latestAssessmentId", "qualifyingAssessmentId", "failureStreak", "delayedEvidenceAnswerIds"})

    def test_ac12_same_day_repeat(self):
        self.ready([node("a"), node("b", ["a"])])
        question_id = self.pose()
        self.ok("hint.record", {"sessionId": self.sid, "questionId": question_id, "kind": "cue", "text": "세어 봐", "userText": "힌트"})
        self.assess(self.answer(question_id))
        self.proceed()
        packet = self.attempt(variationReason="같은 날 반복")[2]["packet"]
        progress = packet["progress"][0]
        self.assertTrue(progress["qualified"])
        self.assertEqual(progress["delayedEvidenceAnswerIds"], [])

    def test_ac13_duplicate_operation(self):
        self.init()
        request = self.request("session.start", {"mode": "learning", "startAt": "auto", "targetNodeIds": [], "maxItems": None, "userText": "시작"})
        first = self.call(request)
        again = self.call(request)
        self.assertTrue(again["replayed"])
        self.assertEqual(again["revision"], first["revision"])
        self.assertEqual(again["result"]["entityIds"], first["result"]["entityIds"])
        self.assertEqual(len(self.journal().splitlines()), 2)

    def test_ac14_operation_collision(self):
        self.init()
        request = self.request("session.start", {"mode": "learning", "startAt": "auto", "targetNodeIds": [], "maxItems": None, "userText": "시작"})
        self.call(request)
        request["payload"]["userText"] = "다른 요청"
        before = self.journal()
        response = self.call(request)
        self.assertEqual(response["error"]["code"], "OPERATION_CONFLICT")
        self.assertEqual(self.code, 3)
        self.assertEqual(self.journal(), before)

    def test_ac15_stale_client(self):
        self.ready()
        self.refuse("REVISION_CONFLICT", "session.pause", {"sessionId": self.sid, "userText": "쉬자"}, expected=self.revision - 1)
        self.assertEqual(self.code, 3)

    def test_ac16_writer_conflict(self):
        self.init()
        holder = subprocess.Popen(
            [sys.executable, "-c", "import fcntl,sys,time; f=open(sys.argv[1],'a'); fcntl.flock(f, fcntl.LOCK_EX); print('locked', flush=True); time.sleep(30)",
             str(self.root / "records/.lock")],
            stdout=subprocess.PIPE, text=True,
        )
        try:
            self.assertEqual(holder.stdout.readline().strip(), "locked")
            before = self.journal()
            response = self.call(self.request("session.start", {"mode": "learning", "startAt": "auto", "targetNodeIds": [], "maxItems": None, "userText": "시작"}), lock_timeout=0.3)
            self.assertEqual(response["error"]["code"], "LOCK_BUSY")
            self.assertTrue(response["error"]["retryable"])
            self.assertEqual(self.journal(), before)
            self.assertTrue((self.root / "records/.lock").exists())
        finally:
            holder.kill()
            holder.wait()
            holder.stdout.close()
        self.start()

    def test_ac17_crash_before_commit(self):
        self.init()
        temp = self.root / "records" / ".study-loop-events-22222222-2222-4222-8222-000000000002.tmp"
        temp.write_bytes(self.journal() + b'{"half":')
        self.assertEqual(self.packet()["revision"], 1)
        self.start()
        self.assertEqual(self.revision, 2)
        self.assertTrue(temp.exists(), "the engine must not adopt or delete an earlier temp file")

    def test_ac18_crash_after_commit(self):
        self.init()
        request = self.request("session.start", {"mode": "learning", "startAt": "auto", "targetNodeIds": [], "maxItems": None, "userText": "시작"})
        stale = (self.root / "state.json").read_bytes()
        first = self.call(request)
        (self.root / "state.json").write_bytes(stale)
        again = self.call(request)
        self.assertTrue(again["replayed"])
        self.assertEqual(again["result"]["entityIds"], first["result"]["entityIds"])
        self.assertEqual(len(self.journal().splitlines()), 2)
        self.assertEqual(json.loads((self.root / "state.json").read_text())["revision"], 2)

    def test_ac19_corrupt_journal(self):
        self.ready()
        path = self.root / "records/events.jsonl"
        path.write_bytes(path.read_bytes()[:-20])
        damaged = path.read_bytes()
        query = self.send("workspace.query", {"view": "resume", "id": None, "search": None, "cursor": None, "limit": 20})
        self.assertEqual(query["error"]["code"], "CORRUPT_JOURNAL")
        self.assertEqual(self.code, 4)
        write = self.send("session.pause", {"sessionId": "44444444-4444-4444-8444-444444444444", "userText": "쉬자"})
        self.assertEqual(write["error"]["code"], "CORRUPT_JOURNAL")
        self.assertEqual(path.read_bytes(), damaged)

    def test_ac20_future_format(self):
        self.init()
        path = self.root / "records/events.jsonl"
        future = json.loads(path.read_text().splitlines()[0])
        future.update(schemaVersion=2, revision=2, operationId="55555555-5555-4555-8555-555555555555")
        path.write_bytes(path.read_bytes() + json.dumps(future).encode() + b"\n")
        before = path.read_bytes()
        response = self.send("workspace.query", {"view": "status", "id": None, "search": None, "cursor": None, "limit": 1})
        self.assertEqual(response["error"]["code"], "UNSUPPORTED_VERSION")
        self.assertEqual(self.code, 5)
        self.assertEqual(path.read_bytes(), before)

    def test_ac21_cross_host_question(self):
        self.ready()
        question_id = self.pose()
        self.ok("session.pause", {"sessionId": self.sid, "userText": "나중에 하자"})
        self.actor = CODEX
        packet = self.packet()
        self.assertEqual(packet["session"]["pending"], {"kind": "question", "questionId": question_id})
        self.assertNotIn("expectedAnswer", packet["question"])
        self.assertEqual(packet["nextAction"]["kind"], "resume_session")
        resumed = self.ok("session.resume", {"sessionId": self.sid, "userText": "이어서 하자"})["packet"]
        self.assertEqual(resumed["session"]["pending"]["questionId"], question_id)
        self.assertEqual(resumed["nextAction"]["kind"], "await_answer")

    def test_ac22_wrong_workspace(self):
        self.init()
        before = self.journal()
        for command, payload in (
            ("workspace.query", {"view": "resume", "id": None, "search": None, "cursor": None, "limit": 1}),
            ("session.start", {"mode": "learning", "startAt": "auto", "targetNodeIds": [], "maxItems": None, "userText": "시작"}),
        ):
            response = self.send(command, payload, ws=OTHER_WS)
            self.assertEqual(response["error"]["code"], "WORKSPACE_MISMATCH")
        self.assertEqual(self.journal(), before)

    def test_ac23_plan_cycle(self):
        self.init()
        self.start()
        self.diagnose()
        self.refuse("INVALID_PLAN", "plan.propose", {
            "sessionId": self.sid, "baseVersion": 0, "goalNodeId": "a", "nodes": [node("a", ["b"]), node("b", ["a"])],
            "diagnosisSummary": "s", "revisionReason": None,
        })

    def test_ac24_redefine_node(self):
        self.ready([node("a")])
        self.attempt()
        self.proceed("replan")
        self.refuse("NODE_REDEFINED", "plan.propose", {
            "sessionId": self.sid, "baseVersion": 1, "goalNodeId": "a", "nodes": [node("a", objective="다른 목표")],
            "diagnosisSummary": "s", "revisionReason": "범위를 바꾼다",
        })

    def test_ac25_replan_pending(self):
        self.ready()
        self.pose()
        self.refuse("INVALID_TRANSITION", "plan.propose", {
            "sessionId": self.sid, "baseVersion": 1, "goalNodeId": "b", "nodes": [node("b")],
            "diagnosisSummary": "s", "revisionReason": "다시",
        })

    def test_ac26_alternative_solution(self):
        self.ready()
        question_id = self.pose()
        answer_id = self.answer(question_id, text="손가락으로 3에서 두 번 더 세면 5가 된다.")
        self.assertEqual(self.assess(answer_id)["packet"]["assessment"]["verdict"], "correct")

    def test_ac27_ambiguous_material(self):
        self.ready()
        question_id = self.pose()
        answer_id = self.answer(question_id)
        packet = self.assess(answer_id, {"state-result": "unassessable"}, issue={"kind": "ambiguous_question", "description": "어떤 덧셈인지 모호하다"})["packet"]
        self.assertEqual(packet["assessment"]["verdict"], "ungradable")
        self.assertEqual(packet["session"]["pending"]["kind"], "repair")
        self.assertFalse(packet["progress"][0]["qualified"])
        self.refuse("CONTENT_REPAIR_REQUIRED", "question.pose", {"sessionId": self.sid, "question": self.question("recheck")})
        resolved = self.ok("content.resolve", {
            "sessionId": self.sid, "assessmentId": packet["assessment"]["assessmentId"], "resolution": "new_question",
            "correction": "질문을 명확히 다시 쓴다.", "sourceRefs": [],
        })["packet"]
        self.assertEqual(resolved["nextAction"]["kind"], "wait_for_continue")
        self.assertEqual(self.proceed()["session"]["requiredMove"]["purpose"], "check")

    def test_ac28_fix_assessment(self):
        self.ready()
        question_id = self.pose()
        answer_id = self.answer(question_id)
        first = self.assess(answer_id)["packet"]["assessment"]
        self.assertTrue(self.packet()["progress"][0]["qualified"])
        fixed = self.assess(answer_id, {"state-result": "not_met"}, replaces=first["assessmentId"], reason="이유 설명이 없었다")["packet"]
        self.assertEqual(fixed["assessment"]["verdict"], "incorrect")
        self.assertFalse(fixed["progress"][0]["qualified"])
        export = json.loads(self._export_json())
        mine = [item for item in export["assessments"] if item["answerId"] == answer_id]
        self.assertEqual([item["replacesAssessmentId"] for item in mine], [None, first["assessmentId"]])

    def test_ac29_late_assessment_edit(self):
        self.ready([node("a"), node("b", ["a"])])
        _, answer_id, result = self.attempt()
        old = result["packet"]["assessment"]["assessmentId"]
        self.proceed()
        self.pose()
        self.refuse("ASSESSMENT_FINALIZED", "assessment.record", {
            "sessionId": self.sid,
            "assessment": self.assessment(answer_id, {"state-result": "not_met"}, replaces=old, reason="다시 보니 틀렸다"),
        })

    def test_ac30_unsafe_path(self):
        self.init()
        (self.tmp / "outside.md").write_text("밖", encoding="utf-8")
        (self.root / "materials" / "link.md").symlink_to(self.tmp / "outside.md")
        for path in ("../outside.md", "materials/../../outside.md", "materials/link.md", "learner.md"):
            with self.subTest(path=path):
                self.refuse("PATH_OUTSIDE_WORKSPACE", "source.register", {
                    "relativePath": path, "title": "t", "originKind": "local_file", "origin": path,
                })
        for path in ("../out.json", "plan.json", "artifacts/../state.json"):
            with self.subTest(path=path):
                response = self.send("workspace.export", {"format": "json", "outputPath": path, "overwrite": True})
                self.assertEqual(response["error"]["code"], "PATH_OUTSIDE_WORKSPACE")
        self.assertFalse((self.tmp / "out.json").exists())

    def register(self, text="첫 줄\n덧셈은 개수를 합친다.\n셋째 줄\n", name="notes.md"):
        (self.root / "materials" / name).write_text(text, encoding="utf-8")
        return self.ok("source.register", {
            "relativePath": f"materials/{name}", "title": "노트", "originKind": "local_file", "origin": name,
        })["entityIds"]["sourceId"]

    def test_changed_or_non_utf8_snapshot_cannot_support_a_new_citation(self):
        self.ready()
        source_id = self.register()
        snapshot = self.root / "sources" / f"{source_id}.txt"
        for data in (b"Changed snapshot\n", b"\xff\n"):
            with self.subTest(data=data):
                snapshot.write_bytes(data)
                ref = {"kind": "material", "sourceId": source_id, "startLine": 1, "endLine": 1, "quote": "Changed snapshot"}
                self.refuse("CORRUPT_JOURNAL", "question.pose", {"sessionId": self.sid, "question": self.question(sourceRefs=[ref])})

    def test_malformed_event_containers_return_structured_corruption(self):
        self.init()
        path = self.root / "records/events.jsonl"
        original = json.loads(path.read_text().splitlines()[0])
        for events in (1, True, "wrong", {}, None):
            with self.subTest(events=events):
                damaged = dict(original, events=events)
                path.write_text(json.dumps(damaged) + "\n")
                self.refuse("CORRUPT_JOURNAL", "workspace.query", {"view": "status", "id": None, "search": None, "cursor": None, "limit": 1})

    def test_snapshot_directory_alias_cannot_write_outside_workspace(self):
        self.init()
        self.register()
        (self.root / "sources").rename(self.root / "saved-sources")
        outside = self.tmp / "outside"; outside.mkdir()
        (self.root / "sources").symlink_to(outside, target_is_directory=True)
        (self.root / "materials/next.md").write_text("New material\n")
        self.refuse("PATH_OUTSIDE_WORKSPACE", "source.register", {
            "relativePath": "materials/next.md", "title": "next", "originKind": "local_file", "origin": "next.md",
        })
        self.assertEqual(list(outside.iterdir()), [])

    def test_artifact_directory_alias_cannot_overwrite_append_only_journal(self):
        self.init()
        artifacts = self.root / "artifacts"
        if artifacts.exists(): artifacts.rmdir()
        artifacts.symlink_to(self.root / "records", target_is_directory=True)
        self.refuse("PATH_OUTSIDE_WORKSPACE", "workspace.export", {
            "format": "json", "outputPath": "artifacts/events.jsonl", "overwrite": True,
        })

    def test_record_directory_alias_is_refused_before_external_lock_or_append(self):
        self.init()
        original = self.journal()
        (self.root / "records").rename(self.root / "saved-records")
        outside = self.tmp / "outside"; outside.mkdir()
        (outside / "events.jsonl").write_bytes(original)
        (self.root / "records").symlink_to(outside, target_is_directory=True)
        self.refuse("PATH_OUTSIDE_WORKSPACE", "session.start", {
            "mode": "learning", "startAt": "auto", "targetNodeIds": [], "maxItems": None, "userText": "시작",
        })
        self.assertFalse((outside / ".lock").exists())

    def test_protected_projection_reports_stale_after_a_real_commit(self):
        self.init()
        learner = (self.root / "learner.md").read_bytes()
        (self.root / "state.json").unlink()
        (self.root / "state.json").symlink_to(self.root / "learner.md")
        response = self.send("session.start", {
            "mode": "learning", "startAt": "auto", "targetNodeIds": [], "maxItems": None, "userText": "시작",
        })
        self.assertTrue(response["ok"]); self.assertTrue(response["committed"])
        self.assertEqual(response["viewsStatus"], "stale")
        self.assertEqual(len(self.journal().splitlines()), 2)
        self.assertEqual((self.root / "learner.md").read_bytes(), learner)

    def test_ac31_bad_citation(self):
        self.ready()
        source = self.register()
        bad = {"kind": "material", "sourceId": source, "startLine": 1, "endLine": 1, "quote": "덧셈은 개수를 합친다."}
        good = dict(bad, startLine=2, endLine=2)
        self.refuse("INVALID_REFERENCE", "question.pose", {"sessionId": self.sid, "question": self.question(sourceRefs=[bad])})
        question_id = self.pose(sourceRefs=[good])
        answer_id = self.answer(question_id)
        self.refuse("INVALID_REFERENCE", "assessment.record", {"sessionId": self.sid, "assessment": self.assessment(answer_id, {"state-result": "met"}, refs=[bad])})
        self.refuse("INVALID_REFERENCE", "knowledge.commit", {"extraction": {
            "scopeRefs": [bad], "propositions": [], "chains": [], "identityLinks": [],
        }})
        self.assess(answer_id)
        self.proceed("replan")
        self.refuse("INVALID_REFERENCE", "plan.propose", {
            "sessionId": self.sid, "baseVersion": 1, "goalNodeId": "addition-2", "nodes": [dict(node("addition-2"), sourceRefs=[bad])],
            "diagnosisSummary": "s", "revisionReason": "자료 반영",
        })

    def scope(self):
        source = self.register()
        return source, {"kind": "material", "sourceId": source, "startLine": 1, "endLine": 3, "quote": "덧셈은 개수를 합친다."}

    def prop(self, key, ref):
        return {"localKey": key, "name": key, "statement": f"{key} 명제", "sourceRefs": [ref]}

    def test_ac32_joint_premises(self):
        self.init()
        _, ref = self.scope()
        result = self.ok("knowledge.commit", {"extraction": {
            "scopeRefs": [ref], "propositions": [self.prop("a", ref), self.prop("b", ref), self.prop("c", ref)],
            "chains": [{"premises": [{"kind": "local", "id": "a"}, {"kind": "local", "id": "b"}], "conclusion": {"kind": "local", "id": "c"}, "sourceRefs": [ref]}],
            "identityLinks": [],
        }})
        chains = json.loads((self.root / "knowledge/chains.json").read_text())["chains"]
        self.assertEqual(len(chains), 1)
        chain = next(iter(chains.values()))
        ids = result["entityIds"]
        self.assertEqual(chain["premises"], sorted([ids["prop:a"], ids["prop:b"]]))
        self.assertEqual(chain["conclusion"], ids["prop:c"])

    def test_ac33_identity_link(self):
        self.init()
        _, ref = self.scope()
        first = self.ok("knowledge.commit", {"extraction": {"scopeRefs": [ref], "propositions": [self.prop("sum", ref)], "chains": [], "identityLinks": []}})
        existing = first["entityIds"]["prop:sum"]
        other = self.register("다른 자료\n덧셈은 수를 모은다.\n", "other.md")
        ref2 = {"kind": "material", "sourceId": other, "startLine": 2, "endLine": 2, "quote": "덧셈은 수를 모은다."}
        draft = dict(self.prop("gather", ref2), statement="덧셈은 수를 모으는 것이다.")
        second = self.ok("knowledge.commit", {"extraction": {
            "scopeRefs": [ref2], "propositions": [draft], "chains": [],
            "identityLinks": [{"localKey": "gather", "existingId": existing, "reason": "같은 주장을 다르게 표현했다"}],
        }})
        self.assertEqual(second["entityIds"]["prop:gather"], existing)
        props = json.loads((self.root / "knowledge/propositions.json").read_text())["propositions"]
        self.assertEqual(props[existing]["statement"], "sum 명제")
        self.assertIn("덧셈은 수를 모으는 것이다.", props[existing]["aliases"])
        self.assertEqual(len(props[existing]["sourceRefs"]), 2)

    def test_ac34_graph_not_mastery(self):
        self.ready()
        before = self.packet()
        _, ref = self.scope()
        after = self.ok("knowledge.commit", {"extraction": {"scopeRefs": [ref], "propositions": [self.prop("a", ref)], "chains": [], "identityLinks": []}})["packet"]
        self.assertEqual(after["progress"], before["progress"])
        self.assertEqual(after["session"], before["session"])

    def test_ac35_early_finish(self):
        self.ready()
        self.refuse("INVALID_TRANSITION", "session.finish", {"sessionId": self.sid, "outcome": "goal_demonstrated", "abandonPending": False, "userText": "끝"})
        self.ok("session.finish", {"sessionId": self.sid, "outcome": "partial", "abandonPending": False, "userText": "끝"})

    def test_ac36_finish_with_pending(self):
        self.ready()
        question_id = self.pose()
        session = self.sid
        self.refuse("INVALID_TRANSITION", "session.finish", {"sessionId": session, "outcome": "partial", "abandonPending": False, "userText": "그만"})
        self.ok("session.finish", {"sessionId": session, "outcome": "partial", "abandonPending": True, "userText": "그만"})
        export = json.loads(self._export_json())
        self.assertEqual([item for item in export["answers"] if item["questionId"] == question_id], [])
        self.assertEqual([item for item in export["assessments"] if item["questionId"] == question_id], [])
        self.assertEqual([item["status"] for item in export["questions"] if item["questionId"] == question_id], ["abandoned"])

    def test_ac37_export_retry(self):
        self.ready()
        payload = {"format": "markdown", "outputPath": "artifacts/summary.md", "overwrite": False}
        first = self.ok("workspace.export", payload)
        self.assertTrue(first["changed"])
        self.assertFalse(self.ok("workspace.export", payload)["changed"])
        self.ok("session.pause", {"sessionId": self.sid, "userText": "쉬자"})
        response = self.send("workspace.export", payload)
        self.assertEqual(response["error"]["code"], "FILE_EXISTS")
        self.assertTrue(self.ok("workspace.export", dict(payload, overwrite=True))["changed"])

    def test_ac38_oversized_context(self):
        self.init()
        self.start()
        self.diagnose()
        long = "a" * 1000
        nodes = []
        for index in range(32):
            item = node(f"n{index}", [f"n{index - 1}"] if index else [], criteria=[f"c{k}" for k in range(8)], objective="b" * 2000)
            item["criteria"] = [{"criterionId": f"c{k}", "description": long} for k in range(8)]
            nodes.append(item)
        self.refuse("CONTEXT_LIMIT", "plan.propose", {
            "sessionId": self.sid, "baseVersion": 0, "goalNodeId": "n31", "nodes": nodes, "diagnosisSummary": "s", "revisionReason": None,
        })

    def test_ac39_hint_limit(self):
        self.ready()
        question_id = self.pose()
        for level in range(3):
            self.ok("hint.record", {"sessionId": self.sid, "questionId": question_id, "kind": "cue", "text": f"힌트 {level}", "userText": "힌트"})
        self.refuse("HINT_LIMIT", "hint.record", {"sessionId": self.sid, "questionId": question_id, "kind": "scaffold", "text": "더", "userText": "더 줘"})
        allowed = self.packet()["nextAction"]["allowedCommands"]
        self.assertNotIn("hint.record", allowed)
        self.assertIn("question.reveal", allowed)
        self.answer(question_id)

    def test_ac40_read_only_query(self):
        self.ready()
        self.pose()
        files = lambda: {path: path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        for paused in (False, True):
            before = files()
            for view in ("resume", "status", "events", "sources", "knowledge"):
                self.ok("workspace.query", {"view": view, "id": None, "search": None, "cursor": None, "limit": 5})
            self.ok("workspace.validate", {})
            self.assertEqual(files(), before)
            if not paused:
                self.ok("session.pause", {"sessionId": self.sid, "userText": "쉬자"})

    def test_ac41_init_before_intent(self):
        records = self.root / "records"
        records.mkdir(parents=True)
        (records / ".lock").write_bytes(b"")
        leftover = records / ".study-loop-init-22222222-2222-4222-8222-000000000001.tmp"
        leftover.write_bytes(b"partial")
        self.init()
        self.assertEqual(self.revision, 1)
        self.assertEqual(leftover.read_bytes(), b"partial")
        (self.tmp / "dirty").mkdir()
        (self.tmp / "dirty" / "notes.txt").write_text("x")
        self.root = self.tmp / "dirty"
        response = self.send("workspace.init", {"goal": {"title": "t", "description": "d", "depth": "explain"}, "utcOffsetMinutes": 0, "learnerText": None})
        self.assertEqual(response["error"]["code"], "WORKSPACE_NOT_EMPTY")

    def test_ac42_init_after_intent(self):
        request = self.request("workspace.init", {"goal": {"title": "t", "description": "d", "depth": "explain"}, "utcOffsetMinutes": 0, "learnerText": "배경"})
        with mock.patch("studyloop.storage.Store.append", side_effect=SystemExit("crash before journal replace")):
            with self.assertRaises(SystemExit):
                self.call(request)
        self.assertTrue((self.root / "records/.init.json").exists())
        self.assertFalse((self.root / "records/events.jsonl").exists())
        first_time = self.now
        self.now = "2026-11-06T05:00:00Z"
        self.assertTrue(self.call(request)["ok"])
        lines = self.journal().splitlines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(json.loads(lines[0])["events"][0]["data"]["workspace"]["createdAt"], first_time)
        other = self.request("workspace.init", {"goal": {"title": "t", "description": "d", "depth": "explain"}, "utcOffsetMinutes": 0, "learnerText": "배경"})
        self.assertEqual(self.call(other)["error"]["code"], "REVISION_CONFLICT")

    def test_ac43_cross_host_regrade(self):
        self.ready()
        question_id = self.pose()
        answer_id = self.answer(question_id)
        first = self.assess(answer_id)["packet"]["assessment"]
        self.actor = CODEX
        assessor = self.ok("workspace.query", {"view": "assessor", "id": None, "search": None, "cursor": None, "limit": 1})
        self.assertEqual(assessor["question"]["expectedAnswer"], "5. 둘과 셋을 합치면 다섯이다.")
        self.assertEqual(assessor["answer"]["answerId"], answer_id)
        packet = self.assess(answer_id, {"state-result": "not_met"}, replaces=first["assessmentId"], reason="다른 호스트에서 다시 보니 이유가 없다")["packet"]
        self.assertFalse(packet["progress"][0]["qualified"])
        export = json.loads(self._export_json())
        mine = [item["verdict"] for item in export["assessments"] if item["answerId"] == answer_id]
        self.assertEqual(sorted(mine), ["correct", "incorrect"])

    def test_ac44_replan_after_practice(self):
        self.ready()
        self.ok("session.finish", {"sessionId": self.sid, "outcome": "partial", "abandonPending": False, "userText": "끝"})
        packet = self.start("practice", targets=["addition"], max_items=1)
        self.assertEqual(packet["session"]["requiredMove"], {"purpose": "practice", "teachingMove": None})
        answer_id = self.answer(self.pose())
        repair = self.assess(answer_id, {"state-result": "unassessable"}, issue={"kind": "bad_rubric", "description": "기준이 틀렸다"})["packet"]
        self.refuse("INVALID_TRANSITION", "content.resolve", {
            "sessionId": self.sid, "assessmentId": repair["assessment"]["assessmentId"], "resolution": "replan",
            "correction": "기준 수정", "sourceRefs": [],
        })
        self.ok("session.finish", {"sessionId": self.sid, "outcome": "partial", "abandonPending": True, "userText": "계획을 고치자"})
        planning = self.start("learning", "replan")
        self.assertEqual(planning["session"]["phase"], "planning")
        self.assertIsNone(planning["question"])
        self.assertEqual(planning["nextAction"]["kind"], "propose_plan")
        self.propose([node("addition-v2")], reason="rubric 오류를 고친다")
        self.assertEqual(self.packet()["nextAction"]["kind"], "await_plan_approval")


class DecisionTests(Lab):
    """The 2026-11-06 decisions 1A, 2A, 3B, 4-1 and 4-2."""

    def test_diagnosis_continues_with_next_only(self):
        self.init()
        self.start()
        for index in range(3):
            answer_id = self.answer(self.pose(prompt=f"진단 {index}"))
            self.assertIsNone(self.assess(answer_id)["packet"]["nextAction"]["recommendedMove"])
            if index == 0:
                self.refuse("INVALID_TRANSITION", "continuation.accept", {"sessionId": self.sid, "intent": "retry", "userText": "다시"})
            packet = self.proceed()
            self.assertEqual(packet["session"]["phase"], "diagnosing")
        self.assertEqual(packet["nextAction"]["kind"], "complete_diagnosis")
        self.refuse("INVALID_TRANSITION", "question.pose", {"sessionId": self.sid, "question": self.question("diagnostic")})

    def test_engine_fills_required_move(self):
        self.init()
        self.assertEqual(self.start()["session"]["requiredMove"], {"purpose": "diagnostic", "teachingMove": None})
        self.diagnose()
        self.propose([node("a")])
        accepted = self.ok("plan.accept", {"sessionId": self.sid, "version": 1, "userText": "좋아"})["packet"]
        self.assertEqual(accepted["session"]["requiredMove"], {"purpose": "check", "teachingMove": "initial_explanation"})
        self.assertEqual(accepted["session"]["currentNodeId"], "a")

    def test_planning_rejects_questions_and_paused_session_can_finish(self):
        self.init()
        self.start()
        self.diagnose()
        self.refuse("INVALID_TRANSITION", "question.pose", {"sessionId": self.sid, "question": self.question("diagnostic")})
        self.ok("session.pause", {"sessionId": self.sid, "userText": "쉬자"})
        self.refuse("INVALID_TRANSITION", "plan.propose", {
            "sessionId": self.sid, "baseVersion": 0, "goalNodeId": "a", "nodes": [node("a")], "diagnosisSummary": "s", "revisionReason": None,
        })
        self.ok("session.finish", {"sessionId": self.sid, "outcome": "partial", "abandonPending": False, "userText": "그만"})

    def test_workspace_commands_run_while_paused(self):
        self.init()
        self.start()
        self.ok("session.pause", {"sessionId": self.sid, "userText": "쉬자"})
        _, ref = AcceptanceTests.scope(self)
        self.ok("knowledge.commit", {"extraction": {"scopeRefs": [ref], "propositions": [], "chains": [], "identityLinks": []}})
        self.assertIn("knowledge.commit", self.packet()["nextAction"]["allowedCommands"])

    register = AcceptanceTests.register


class PolicyTests(Lab):
    def test_failure_ladder_probes_prerequisite_then_replans(self):
        self.ready([node("a"), node("b", ["a"])])
        self.attempt()
        self.proceed()
        moves = []
        for _ in range(2):
            moves.append(self.attempt({"state-result": "not_met"})[2]["packet"]["nextAction"]["recommendedMove"])
            packet = self.proceed()
        self.assertEqual(moves, ["targeted_repair", "prerequisite_probe"])
        self.assertEqual(packet["session"]["currentNodeId"], "a")
        self.assertEqual(packet["session"]["requiredMove"]["purpose"], "prerequisite_probe")
        packet = self.attempt()[2]["packet"]
        self.assertEqual(self.proceed()["session"]["currentNodeId"], "b")
        third = self.attempt({"state-result": "not_met"})[2]["packet"]
        self.assertEqual(third["nextAction"]["recommendedMove"], "replan")
        self.assertEqual(self.proceed()["session"]["phase"], "planning")

    def test_goal_needs_independent_transfer(self):
        self.ready()
        packet = self.attempt()[2]["packet"]
        self.assertEqual(packet["nextAction"]["recommendedMove"], "advance")
        self.assertEqual(self.proceed()["session"]["requiredMove"]["purpose"], "transfer")
        self.refuse("INVALID_TRANSITION", "session.finish", {"sessionId": self.sid, "outcome": "goal_demonstrated", "abandonPending": False, "userText": "끝"})
        packet = self.attempt(prompt="빵 3개와 4개는 모두 몇 개이며 왜인가?", variationReason="새 상황")[2]["packet"]
        self.assertEqual(packet["nextAction"]["recommendedMove"], "finish")
        self.assertEqual(self.proceed()["nextAction"]["kind"], "offer_finish")
        self.ok("session.finish", {"sessionId": self.sid, "outcome": "goal_demonstrated", "abandonPending": False, "userText": "끝"})

    def test_practice_queue_prefers_recent_failures(self):
        self.ready([node("a"), node("b", ["a"]), node("c", ["b"])])
        self.attempt()
        self.proceed()
        self.attempt({"state-result": "not_met"})
        self.ok("session.finish", {"sessionId": self.sid, "outcome": "partial", "abandonPending": False, "userText": "끝"})
        packet = self.start("review", max_items=3)
        self.assertEqual(packet["session"]["targetNodeIds"], ["b", "c", "a"])
        self.assertEqual(packet["session"]["phase"], "reviewing")

    def test_solution_seen_follows_prompt(self):
        self.ready()
        question_id = self.pose()
        self.ok("question.reveal", {"sessionId": self.sid, "questionId": question_id, "userText": "풀이"})
        self.proceed()
        answer_id = self.answer(self.pose())
        self.assertEqual(self.packet()["answer"]["assistance"], "solution_seen")
        self.assertTrue(answer_id)


class RuleCoverageTests(Lab):
    """Each test fails if the named rule is removed (2026-11-06 review)."""

    def hint(self, question_id):
        self.ok("hint.record", {"sessionId": self.sid, "questionId": question_id, "kind": "cue", "text": "세어 봐", "userText": "힌트"})

    def helped_then_alone(self, second_prompt, second_time):
        question_id = self.pose()
        self.hint(question_id)
        self.assess(self.answer(question_id))
        self.proceed()
        self.now = second_time
        answer_id = self.answer(self.pose(prompt=second_prompt, variationReason="다른 상황으로 확인"))
        return answer_id, self.assess(answer_id)["packet"]["progress"][0]

    def test_delayed_evidence_needs_a_later_local_date(self):
        self.ready([node("a"), node("b", ["a"])])
        _, progress = self.helped_then_alone("사과 4개와 1개는?", "2026-11-06T05:00:00Z")
        self.assertTrue(progress["qualified"])
        self.assertEqual(progress["delayedEvidenceAnswerIds"], [])

    def test_delayed_evidence_needs_a_new_prompt(self):
        self.ready([node("a"), node("b", ["a"])])
        _, progress = self.helped_then_alone("2+3은 무엇이며 왜 그런가?", "2026-11-07T05:00:00Z")
        self.assertEqual(progress["delayedEvidenceAnswerIds"], [])

    def test_local_date_uses_the_workspace_offset(self):
        self.ready([node("a"), node("b", ["a"])])  # UTC+9
        self.now = "2026-11-06T14:00:00Z"  # 23:00 local
        answer_id, progress = self.helped_then_alone("사과 4개와 1개는?", "2026-11-06T15:30:00Z")  # 00:30 next local day
        self.assertEqual(progress["delayedEvidenceAnswerIds"], [answer_id])

    def test_deferred_prerequisite_blocks_its_dependents(self):
        self.ready([node("a"), node("b", ["a"])])
        question_id = self.pose()
        self.ok("question.skip", {"sessionId": self.sid, "questionId": question_id, "userText": "넘어가자"})
        packet = self.proceed("skip_target")
        self.assertEqual(packet["session"]["deferredNodeIds"], ["a"])
        self.assertIsNone(packet["session"]["currentNodeId"])
        self.assertEqual(packet["nextAction"]["kind"], "offer_finish")

    def test_seen_solution_does_not_qualify(self):
        self.ready()
        question_id = self.pose()
        self.ok("question.reveal", {"sessionId": self.sid, "questionId": question_id, "userText": "풀이"})
        self.proceed()
        packet = self.assess(self.answer(self.pose()))["packet"]
        self.assertFalse(packet["progress"][0]["qualified"])
        self.assertEqual(packet["progress"][0]["status"], "supported")
        self.assertEqual(packet["nextAction"]["recommendedMove"], "fresh_check")

    def test_reported_help_is_not_independent(self):
        for help, assistance in (("hint", "hinted"), ("solution", "solution_seen"), ("unknown", "unknown")):
            with self.subTest(help=help):
                self.root, self.revision = self.tmp / f"ws-{help}", 0
                self.ready()
                packet = self.attempt(help=help)[2]["packet"]
                self.assertEqual(packet["answer"]["assistance"], assistance)
                self.assertFalse(packet["progress"][0]["qualified"])

    def choice(self, form="single_choice", correct=("five",)):
        options = [{"optionId": "five", "text": "5"}, {"optionId": "six", "text": "6"}, {"optionId": "seven", "text": "7"}]
        return self.question(format=form, options=options, correctOptionIds=list(correct), selectionCriterionId="choose")

    def test_choice_selection_is_graded_by_the_engine(self):
        self.ready([node("pick", criteria=("choose", "why"))])
        question_id = self.pose(self.choice())
        for selected in (["eight"], ["five", "six"]):
            self.refuse("INVALID_ANSWER", "answer.record", {"sessionId": self.sid, "answer": {
                "questionId": question_id, "responseKind": "answer", "text": "고름", "selectedOptionIds": selected,
                "thinking": None, "confidence": None, "reportedExternalHelp": "none",
            }})
        answer_id = self.answer(question_id, selected=["six"])
        self.refuse("RUBRIC_MISMATCH", "assessment.record", {"sessionId": self.sid,
                    "assessment": self.assessment(answer_id, {"choose": "met", "why": "met"})})
        self.assertEqual(self.assess(answer_id, {"choose": "not_met", "why": "met"})["packet"]["assessment"]["verdict"], "partial")
        self.proceed()
        answer_id = self.answer(self.pose(self.choice("multiple_choice", ("five", "seven"))), selected=["seven", "five"])
        self.assertEqual(self.assess(answer_id, {"choose": "met", "why": "met"})["packet"]["assessment"]["verdict"], "correct")

    def test_wrong_answer_key_goes_to_repair(self):
        self.ready([node("pick", criteria=("choose",))])
        answer_id = self.answer(self.pose(self.choice(correct=("six",))), selected=["five"])
        packet = self.assess(answer_id, {"choose": "unassessable"}, issue={"kind": "bad_rubric", "description": "정답 키가 6으로 잘못됐다"})["packet"]
        self.assertEqual(packet["assessment"]["verdict"], "ungradable")
        self.assertEqual(packet["session"]["pending"]["kind"], "repair")

    def test_a_different_init_cannot_take_over_an_intent(self):
        payload = {"goal": {"title": "t", "description": "d", "depth": "explain"}, "utcOffsetMinutes": 0, "learnerText": None}
        with mock.patch("studyloop.storage.Store.append", side_effect=SystemExit("crash")):
            with self.assertRaises(SystemExit):
                self.call(self.request("workspace.init", payload))
        self.assertEqual(self.call(self.request("workspace.init", payload))["error"]["code"], "OPERATION_CONFLICT")
        self.assertFalse((self.root / "records/events.jsonl").exists())

    def test_default_lock_wait_is_two_seconds(self):
        self.init()
        holder = subprocess.Popen(
            [sys.executable, "-c", "import fcntl,sys,time; f=open(sys.argv[1],'a'); fcntl.flock(f, fcntl.LOCK_EX); print('locked', flush=True); time.sleep(30)",
             str(self.root / "records/.lock")],
            stdout=subprocess.PIPE, text=True,
        )
        try:
            holder.stdout.readline()
            started = time.monotonic()
            response = self.send("session.start", {"mode": "learning", "startAt": "auto", "targetNodeIds": [], "maxItems": None, "userText": "시작"})
            self.assertEqual(response["error"]["code"], "LOCK_BUSY")
            self.assertGreaterEqual(time.monotonic() - started, 1.9)
        finally:
            holder.kill()
            holder.wait()
            holder.stdout.close()


class ReviewFixTests(Lab):
    """Regressions for the defects fixed after the 2026-11-06 review."""

    def test_trailing_newline_ids_are_refused(self):
        payload = {"goal": {"title": "t", "description": "d", "depth": "explain"}, "utcOffsetMinutes": 0, "learnerText": None}
        self.assertEqual(self.send("workspace.init", payload, ws=WS + "\n")["error"]["code"], "INVALID_REQUEST")
        self.assertFalse(self.root.exists())
        self.init()
        self.refuse("INVALID_REQUEST", "session.start",
                    {"mode": "learning", "startAt": "auto", "targetNodeIds": [], "maxItems": None, "userText": "시작"},
                    op="22222222-2222-4222-8222-0000000000aa\n")

    def test_repeated_criterion_is_refused(self):
        self.init()
        self.start()
        draft = self.question("diagnostic", criteria=crit("same", "same"))
        self.refuse("INVALID_REQUEST", "question.pose", {"sessionId": self.sid, "question": draft})

    def test_diagnosis_can_always_be_skipped(self):
        self.init()
        self.assertIn("diagnosis.complete", self.start()["nextAction"]["allowedCommands"])
        for index in range(3):
            question_id = self.pose(prompt=f"진단 {index}")
            self.ok("question.skip", {"sessionId": self.sid, "questionId": question_id, "userText": "모르겠어, 넘어가"})
            packet = self.proceed()
        self.assertEqual(packet["nextAction"]["kind"], "complete_diagnosis")
        self.assertIn("diagnosis.complete", packet["nextAction"]["allowedCommands"])
        done = {"sessionId": self.sid, "summary": "진단 없이 시작", "heldConcepts": [], "gaps": [], "evidenceAnswerIds": []}
        self.refuse("INVALID_TRANSITION", "diagnosis.complete", dict(done, skipRequested=False, userText=None))
        packet = self.ok("diagnosis.complete", dict(done, skipRequested=True, userText="진단은 건너뛰고 계획부터 하자"))["packet"]
        self.assertEqual(packet["nextAction"]["kind"], "propose_plan")

    def test_wrong_path_leaves_no_trace(self):
        missing = self.tmp / "typo" / "deep"
        self.root = missing
        response = self.send("session.pause", {"sessionId": "44444444-4444-4444-8444-444444444444", "userText": "쉬자"}, expected=1)
        self.assertEqual(response["error"]["code"], "WORKSPACE_MISSING")
        self.assertFalse((self.tmp / "typo").exists())
        self.root = self.tmp / "documents"
        self.root.mkdir()
        (self.root / "notes.txt").write_text("남의 파일")
        for command, payload, expected in (
            ("workspace.export", {"format": "json", "outputPath": "artifacts/a.json", "overwrite": False}, None),
            ("workspace.rebuild", {}, 1),
        ):
            self.assertEqual(self.send(command, payload, expected=expected)["error"]["code"], "WORKSPACE_MISSING")
        self.assertEqual(sorted(path.name for path in self.root.iterdir()), ["notes.txt"])

    def raw(self, data):
        response, code = cli.run(data, str(self.root), lambda: self.now)
        self.assertIsNone(check(response, "Response"), response)
        return response, code

    def test_bad_inputs_get_json_errors(self):
        init = json.dumps(self.request("workspace.init", {"goal": {"title": "t", "description": "d", "depth": "explain"}, "utcOffsetMinutes": 0, "learnerText": "x"}))
        surrogate = init.replace('"learnerText": "x"', '"learnerText": "\\ud800"').encode()
        deep = b"[" * 200000 + b"]" * 200000
        for data in (surrogate, deep):
            response, code = self.raw(data)
            self.assertEqual((response["error"]["code"], code), ("INVALID_REQUEST", 2))
        self.assertFalse(self.root.exists())
        self.init()
        (self.root / "artifacts" / "folder").mkdir(parents=True)
        for path in ("artifacts/folder", "artifacts/" + "a" * 300):
            with self.subTest(path=path[:20]):
                response = self.send("workspace.export", {"format": "json", "outputPath": path, "overwrite": True})
                # Python 3.14's exists() swallows ENAMETOOLONG, so the write itself reports it.
                self.assertIn(response["error"]["code"], ("INVALID_REQUEST", "WRITE_FAILED"))
        response = self.send("source.register", {"relativePath": "materials/" + "a" * 300, "title": "t", "originKind": "local_file", "origin": "x"})
        self.assertEqual(response["error"]["code"], "INVALID_REQUEST")
        outside = self.tmp / "outside"
        outside.mkdir()
        (outside / "x.md").write_text("밖")
        shutil.rmtree(self.root / "materials")
        (self.root / "materials").symlink_to(outside)
        response = self.send("source.register", {"relativePath": "materials/x.md", "title": "t", "originKind": "local_file", "origin": "x"})
        self.assertEqual(response["error"]["code"], "PATH_OUTSIDE_WORKSPACE")

    def test_skip_target_moves_on(self):
        self.ready([node("a"), node("b", ["a"])])
        self.ok("session.finish", {"sessionId": self.sid, "outcome": "partial", "abandonPending": False, "userText": "끝"})
        self.start("practice", targets=["a", "b"], max_items=2)
        repair = self.assess(self.answer(self.pose()), {"state-result": "unassessable"},
                             issue={"kind": "ambiguous_question", "description": "모호하다"})["packet"]
        self.ok("content.resolve", {"sessionId": self.sid, "assessmentId": repair["assessment"]["assessmentId"],
                                    "resolution": "new_question", "correction": "다시 쓴다", "sourceRefs": []})
        packet = self.proceed("skip_target")
        self.assertEqual((packet["session"]["currentNodeId"], packet["session"]["queueIndex"]), ("b", 1))

    def test_skipping_the_final_transfer_offers_finish(self):
        self.ready()
        self.attempt()
        self.proceed()
        question_id = self.pose(prompt="빵 3개와 4개는?", variationReason="새 상황")
        self.ok("question.skip", {"sessionId": self.sid, "questionId": question_id, "userText": "이건 넘어가자"})
        packet = self.proceed("skip_target")
        self.assertIsNone(packet["session"]["requiredMove"])
        self.assertEqual(packet["nextAction"]["kind"], "offer_finish")

    def test_learner_file_edges(self):
        payload = {"goal": {"title": "t", "description": "d", "depth": "explain"}, "utcOffsetMinutes": 0, "learnerText": None}
        self.root.mkdir()
        (self.root / "learner.md").write_text("가" * 16001, encoding="utf-8")
        self.assertEqual(self.send("workspace.init", payload)["error"]["code"], "INVALID_REQUEST")
        self.assertFalse((self.root / "records/.init.json").exists())
        (self.root / "learner.md").write_bytes("배경\r\n메모".encode())
        self.assertTrue(self.send("workspace.init", dict(payload, learnerText="배경\r\n메모"))["ok"])

    def test_pending_is_checked_before_change_reason(self):
        self.ready()
        self.pose()
        assessment = self.assessment("55555555-5555-4555-8555-555555555555", {"state-result": "met"}, reason="이유")
        self.refuse("INVALID_TRANSITION", "assessment.record", {"sessionId": self.sid, "assessment": assessment})

    def test_inconsistent_journal_is_reported(self):
        self.init()
        self.start()
        path = self.root / "records/events.jsonl"
        lines = path.read_text(encoding="utf-8").splitlines()
        commit = json.loads(lines[1])
        commit["events"][0]["data"]["pending"] = {"kind": "continuation", "afterEventId": "66666666-6666-4666-8666-666666666666"}
        path.write_text("\n".join([lines[0], json.dumps(commit, ensure_ascii=False)]) + "\n", encoding="utf-8")
        response = self.send("workspace.query", {"view": "resume", "id": None, "search": None, "cursor": None, "limit": 1})
        self.assertEqual((response["error"]["code"], self.code), ("CORRUPT_JOURNAL", 4))


class CommandLineTests(Lab):
    def run_cli(self, data, workspace=None, python=None):
        return subprocess.run(
            [python or sys.executable, str(SKILL / "scripts/study_loop.py"), "--workspace", workspace or str(self.root)],
            input=data, capture_output=True,
        )

    def test_stdin_stdout_and_exit_codes(self):
        init = json.dumps(self.request("workspace.init", {"goal": {"title": "t", "description": "d", "depth": "explain"}, "utcOffsetMinutes": 0, "learnerText": None}), ensure_ascii=False).encode()
        done = self.run_cli(init)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertTrue(json.loads(done.stdout)["ok"])
        self.assertEqual(self.run_cli(init.replace(b'"protocolVersion": 1', b'"protocolVersion": 1, "protocolVersion": 1')).returncode, 2)
        self.assertEqual(self.run_cli(init.replace(b'"utcOffsetMinutes": 0', b'"utcOffsetMinutes": NaN')).returncode, 2)
        self.assertEqual(self.run_cli(init, workspace="relative/path").returncode, 2)
        self.assertEqual(json.loads(self.run_cli(b"not json").stdout)["error"]["code"], "INVALID_REQUEST")

    def test_old_python_is_refused(self):
        old = shutil.which("python3.9") or "/usr/bin/python3"
        version = subprocess.run([old, "-c", "import sys; print(sys.version_info[:2] < (3, 10))"], capture_output=True, text=True)
        if version.stdout.strip() != "True":
            self.skipTest("no Python older than 3.10 here")
        result = self.run_cli(b"{}", python=old)
        self.assertEqual(result.returncode, 5)
        self.assertEqual(json.loads(result.stdout)["error"]["code"], "RUNTIME_UNSUPPORTED")

    def test_unconfirmed_replace_is_reported(self):
        self.init()
        with mock.patch("studyloop.storage.os.replace", side_effect=OSError("disk gone")):
            response = self.send("session.start", {"mode": "learning", "startAt": "auto", "targetNodeIds": [], "maxItems": None, "userText": "시작"})
        self.assertEqual(response["error"]["code"], "COMMIT_STATUS_UNKNOWN")
        self.assertIsNone(response["committed"])
        self.assertEqual(self.code, 4)


if __name__ == "__main__":
    unittest.main()
