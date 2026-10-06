"""Small behavioral smoke suite. Graders stay outside the executor workspace.

These checks are intentionally narrower than the skills' full qualitative rubrics.
They inspect actual output artifacts, never an executor's self-assigned score.
"""
import json
import hashlib
import re
import shutil
from pathlib import Path

CASES = ("design-existing", "content-fidelity", "review-runtime", "review-check",
         "problem-observed", "problem-hypothesis", "problem-update",
         "prd-from-problem", "prd-update", "prd-direct",
         "gate-clean", "gate-policy", "gate-stale", "gate-missing", "product-chain")
SKILLS = {"design-existing": ("design", "design-brief"),
          "content-fidelity": ("content", "un-ai"),
          "review-runtime": ("review", "review-code"),
          "review-check": ("review", "review-check"),
          **{name: ("product", "problem-frame") for name in
             ("problem-observed", "problem-hypothesis", "problem-update")},
          **{name: ("product", "prd-write") for name in
             ("prd-from-problem", "prd-update", "prd-direct")},
          **{name: ("product", "prd-gate") for name in
             ("gate-clean", "gate-policy", "gate-stale", "gate-missing")},
          "product-chain": ("product", "problem-frame")}


def scenario(repo, plugin, skill, number):
    root = repo / "plugins" / plugin / "skills" / skill
    suite = json.loads((root / "evals/evals.json").read_text())
    return root, next(case for case in suite["evals"] if case["id"] == number)


def prepare(repo, case, workspace):
    """Return task text and private grading baseline; never copy expectations."""
    plugin, skill = SKILLS[case]
    # Keep the full reference hierarchy, but exclude grading/setup material.
    for name in ([plugin, "content"] if plugin == "review" else [plugin]):
        shutil.copytree(repo / "plugins" / name, workspace / ".eval-plugins" / name,
                        ignore=shutil.ignore_patterns("evals", "__pycache__"))
    entry = f".eval-plugins/{plugin}/skills/{skill}/SKILL.md"
    if case == "design-existing":
        root, source = scenario(repo, plugin, skill, 1)
        for path in source["files"]:
            destination = workspace / Path(path).relative_to("evals/files/existing-system")
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(root / path, destination)
        prompt = source["prompt"]
        origin = f"plugins/{plugin}/skills/{skill}/evals/evals.json#1"
    elif case.startswith("gate-"):
        number = {"gate-clean": 1, "gate-policy": 2, "gate-stale": 3, "gate-missing": 4}[case]
        root, source = scenario(repo, plugin, skill, number)
        for path in source["files"]:
            shutil.copy2(root / path, workspace / Path(path).name)
        prompt = source["prompt"] + "\n제공된 로컬 입력만 사용하고 외부 조회는 하지 마세요."
        origin = f"plugins/{plugin}/skills/{skill}/evals/evals.json#{number}"
    elif case == "product-chain":
        shutil.copy2(repo / "plugins/product/skills/prd-gate/evals/files/chain-notes.md", workspace / "chain-notes.md")
        prompt = (
            "chain-notes.md로 질문 없이 세 단계를 연결해줘. 이번 요청은 전체 순차 실행을 명시적으로 허용한다. "
            "problem-frame을 적용하여 problem.md를 작성하고, .eval-plugins/product/skills/prd-write/SKILL.md와 "
            "그 참조를 읽어 그 실제 산출물과 원자료로 prd.md를 작성해줘. "
            "각 단계의 파일을 임의로 시험 점수에 맞춰 고치지 마. "
            "작성 완료 후 problem.md와 prd.md의 실제 SHA-256을 authored.sha256.json에 기록해줘 "
            "(키는 파일명, 값은 digest). 그 다음 독립 검토는 반드시 별도 codex exec 호출로 수행해줘. "
            "검토자 요청은 review-prompt.txt에 저장하고, .eval-plugins/product/skills/prd-gate/SKILL.md 및 "
            "참조를 읽어 problem.md/prd.md/chain-notes.md를 검토하고 원본 수정 없이 report.md와 report.json을 "
            "저장하도록 지시해줘. 검토자에게 기대 판정이나 정답, 부모의 결론을 주지 마. "
            "검토 실행은 하네스가 제공하는 고정된 파일 요청 capability를 사용해줘. "
            "review-prompt.txt와 authored.sha256.json을 완성한 뒤 "
            "review-request.json에 {\"action\":\"review\",\"prompt_path\":\"review-prompt.txt\"}를 "
            "마지막으로 저장해줘. 하네스는 이 요청을 받아 같은 모델로 별도 Codex CLI 검토자를 실행한다. "
            "review-result.json의 status가 completed 또는 failed가 될 때까지 최대 850초 이내로 기다려줘. "
            "review-events.jsonl, review-stderr.log, review-result.json은 하네스/검토자가 쓰므로 직접 생성하거나 "
            "수정하지 마. 직접 nested CLI를 띄우거나 다른 검토 방법으로 대체하지 마. "
            "요청 실패 또는 시간 초과라면 결과를 발명하거나 자체 검토하지 말고 실패와 한계를 보고해줘. "
            "검토자의 보고서를 부모가 수정하지 마. 코드 구현·commit·외부 게시·외부 조회는 하지 마."
        )
        origin = "plugins/product/skills/prd-gate/evals/files/chain-notes.md:single orchestrating request"
    elif case.startswith("prd-"):
        number = {"prd-from-problem": 1, "prd-update": 2, "prd-direct": 3}[case]
        root, source = scenario(repo, plugin, skill, number)
        for path in source["files"]:
            shutil.copy2(root / path, workspace / Path(path).name)
        prompt = source["prompt"] + "\n제공된 로컬 입력만 사용하세요. 네트워크나 외부 조회는 사용하지 마세요."
        origin = f"plugins/{plugin}/skills/{skill}/evals/evals.json#{number}"
    elif case.startswith("problem-"):
        number = {"problem-observed": 1, "problem-hypothesis": 2, "problem-update": 4}[case]
        root, source = scenario(repo, plugin, skill, number)
        for path in source["files"]:
            shutil.copy2(root / path, workspace / Path(path).name)
        prompt = source["prompt"] + "\n제공된 로컬 입력만 사용하세요. 외부 조회나 네트워크는 사용하지 마세요."
        origin = f"plugins/{plugin}/skills/{skill}/evals/evals.json#{number}"
    elif case == "review-check":
        root, source = scenario(repo, plugin, skill, 5)
        shutil.copy2(root / source["files"][0], workspace / "review-snapshot.md")
        prompt = source["prompt"] + "\n입력은 review-snapshot.md입니다. 제공된 자료만 검토하고 외부 도구나 네트워크는 사용하지 마세요."
        origin = f"plugins/{plugin}/skills/{skill}/evals/evals.json#5"
    elif case == "review-runtime":
        root, source = scenario(repo, plugin, skill, 9)
        shutil.copy2(root / source["files"][0], workspace / "change.md")
        prompt = source["prompt"] + "\n첨부 자료는 change.md입니다. 외부 도구나 네트워크 없이 제공된 자료만 검토하세요."
        prompt += ('\n추가로 review.json을 작성하세요. 형식은 '
                   '{"findings":[{"file":"상대 경로","line":정수,"description":"원인과 영향",'
                   '"fix":"수정 제안"}],"tests_executed":불리언,"limitations":"검증 한계"}입니다.')
        origin = f"plugins/{plugin}/skills/{skill}/evals/evals.json#9"
    else:
        draft = ("안내드립니다. 지난 9월 12일, 24명의 사용자가 내보내기를 시도했고 3명이 실패했습니다. "
                 "원인은 아직 확인 중입니다. 재시도 버튼은 9월 23일에 배포할 예정이며 일정은 바뀔 수 있습니다.\n")
        (workspace / "draft.md").write_text(draft)
        prompt = ("draft.md의 고객 안내를 간결하게 편집해 edited.md에 저장해줘. "
                  "도입부의 ‘안내드립니다.’는 삭제해줘. 날짜·인원·불확실성·일정 변경 가능성은 그대로 유지하고, "
                  "새로운 원인이나 약속을 추가하지 마. 원문 파일은 보존하고 편집한 본문만 저장해줘.")
        origin = "scripts/behavioral/cases.py:content-fidelity"
    prompt = (f"Read and apply {entry} and the references it calls for. "
              "Only edit the task's output files; .eval-plugins contains the skill source, not output targets.\n"
              + prompt)
    baseline = snapshot(workspace)
    return prompt, baseline, origin


def snapshot(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*"))
            if p.is_file() and not p.is_symlink()}


def document_fields(text):
    # Narrow scalar checks for evaluation artifacts, not a general YAML parser.
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.S)
    fields = {}
    if match:
        for key in ("id", "revision", "status"):
            values = re.findall(r"^" + key + r":\s*([^\n]+)$", match.group(1), re.M)
            if len(values) == 1:
                fields[key] = values[0].strip().strip("\"'")
    return fields


def grade(case, before, after, reviewer_result=None):
    results = []
    def check(name, passed):
        results.append({"check": name, "passed": bool(passed)})
    def text(path):
        return after.get(path, b"").decode("utf-8", errors="replace")
    allowed = {"design-existing": {"apps/dashboard/DESIGN_SYSTEM.md"},
               "content-fidelity": {"edited.md"},
               "review-runtime": {"review.json"},
               "review-check": {"report.md", "report.json"},
               "problem-observed": {"problem.md"},
               "problem-hypothesis": {"problem.md"},
               "problem-update": {"existing-problem.md"},
               "prd-from-problem": {"prd.md"}, "prd-direct": {"prd.md"},
               "prd-update": {"existing-prd.md"},
               **{name: {"report.md", "report.json"} for name in
                  ("gate-clean", "gate-policy", "gate-stale", "gate-missing")},
               "product-chain": {"problem.md", "prd.md", "report.md", "report.json",
                   "authored.sha256.json", "review-prompt.txt", "review-request.json", "review-result.json",
                   "review-events.jsonl", "review-stderr.log"}}[case]
    changed = {p for p in before.keys() | after.keys() if before.get(p) != after.get(p)}
    check("only_requested_output_changed", bool(changed) and changed <= allowed)
    if case.startswith("gate-") or case == "product-chain":
        try:
            report = json.loads(text("report.json"))
            target = {"gate-clean": "clean-prd.md", "gate-policy": "policy-prd.md",
                      "gate-stale": "broken-prd.md", "gate-missing": "missing-prd.md",
                      "product-chain": "prd.md"}[case]
            target_fields = document_fields(text(target))
            check("actual_target_identity_and_digest", report["target"]["path"] == target and
                  report["target"]["id"] == target_fields.get("id") and
                  report["target"]["revision"] == int(target_fields["revision"]) and
                  report["target"]["sha256"] == hashlib.sha256(after[target]).hexdigest())
            coverage = report["coverage"]
            lenses = [c["lens"] for c in coverage]
            check("all_lenses_recorded", sorted(lenses) == ["R1","R2","R3","R4","R5"] and
                  all(c["status"] in ("assessed", "not_assessed") and c.get("note") for c in coverage))
            findings = report["findings"]
            check("findings_have_evidence_gate", isinstance(findings,list) and
                  all(f.get("id") and f.get("lens") in lenses and f.get("disposition") == "confirmed" and
                      f.get("location") and f.get("evidence") and f.get("impact") and f.get("action") for f in findings) and
                  len({f["id"] for f in findings}) == len(findings))
            expected = {"gate-clean":"ready_for_flow", "gate-policy":"needs_decision",
                        "gate-stale":"revise", "gate-missing":"incomplete", "product-chain":"ready_for_flow"}[case]
            check("fixture_disposition", report["verdict"] == expected)
            check("human_report_present", bool(text("report.md").strip()))
            if case in ("gate-clean", "product-chain"):
                check("no_forced_findings_or_blocking_choices", not findings and
                      all(not d["blocking"] for d in report["open_decisions"]) and
                      all(c["status"] == "assessed" for c in coverage))
            elif case == "gate-policy":
                check("blocking_choices_visible", any(d.get("blocking") and d.get("impact") and d.get("question") for d in report["open_decisions"]))
            elif case == "gate-stale":
                check("prior_review_stale", report["prior_review"]["status"] == "stale" and bool(report["prior_review"].get("reason")))
                check("scope_and_acceptance_defects_anchored", any("AC-001" in f["location"] for f in findings) and
                      any("FR-003" in f["location"] or "AC-003" in f["location"] for f in findings))
            else:
                check("missing_evidence_disclosed", bool(report["limitations"]) and
                      any(c["status"] == "not_assessed" for c in coverage))
            if case == "product-chain":
                prd,problem=text("prd.md"),text("problem.md")
                problem_fields=document_fields(problem)
                check("real_upstream_consumed", problem_fields.get("id", "").startswith("problem:") and
                      problem_fields["id"] in prd and "problem.md" in prd and
                      "FR-001" in prd and "AC-001" in prd)
                authored=json.loads(text("authored.sha256.json"))
                check("review_preserved_authored_documents", set(authored) == {"problem.md","prd.md"} and
                      all(authored[name] == hashlib.sha256(after[name]).hexdigest() for name in authored))
                events=[json.loads(line) for line in text("review-events.jsonl").splitlines() if line.strip()]
                check("separate_reviewer_completed", any(e.get("type") == "turn.completed" for e in events) and
                      not any(e.get("type") in ("turn.failed","error") for e in events) and
                      any(e.get("item",{}).get("type") == "command_execution" for e in events))
                # This value comes from the host bridge, never workspace files.
                host = reviewer_result if isinstance(reviewer_result, dict) else {}
                check("host_reviewer_completed", host.get("status") == "completed" and host.get("returncode") == 0)
                check("host_review_preserved_inputs", host.get("before_sha256") == host.get("after_sha256") and
                      host.get("after_sha256") == {name: hashlib.sha256(after[name]).hexdigest()
                          for name in ("problem.md", "prd.md", "chain-notes.md")})
                check("reviewer_reports_unchanged", host.get("report_sha256") ==
                      {name: hashlib.sha256(after[name]).hexdigest() for name in ("report.md", "report.json")})
                check("review_request_uses_gate", "prd-gate/SKILL.md" in text("review-prompt.txt"))
            # Human inspection still checks cited evidence, policy reasoning and actual
            # separate invocation in the outer trace. These checks are not a semantic judge.
        except (ValueError, KeyError, TypeError, AttributeError):
            check("valid_gate_report", False)
    elif case == "design-existing":
        target = "apps/dashboard/DESIGN_SYSTEM.md"
        old, new = before[target].decode(), text(target)
        # The request is additive: headings, tokens and original nonvisual rules survive.
        check("existing_rules_and_headings_preserved", all(line in new for line in old.splitlines() if line.strip()))
        check("css_source_mapped", "src/theme.css" in new and all(x in new for x in ("--accent", "--surface", "--ink")))
        check("decision_log_added", bool(re.search(r"(?i)decisions?\s*log|의사결정|결정\s*(기록|로그)", new)))
        check("app_tokens_preserved", all(x in new.lower() for x in ("#175cd3", "#f8fafc", "#182230")) and "#e26050" not in new.lower())
    elif case == "content-fidelity":
        new = text("edited.md")
        check("requested_intro_removed", "안내드립니다" not in new)
        check("dates_and_counts_preserved", all(x in new for x in ("9월 12일", "24명", "3명", "9월 23일")))
        check("cause_stays_unconfirmed", bool(re.search(r"원인.{0,30}(확인\s*중|조사\s*중|파악\s*중|확인되지)", new)))
        check("schedule_stays_tentative", "예정" in new and bool(re.search(r"(일정|배포).{0,40}(바뀔|변경될|달라질)\s*수", new)))
    elif case.startswith("prd-"):
        target = "existing-prd.md" if case == "prd-update" else "prd.md"
        new = text(target); fields = document_fields(new)
        check("prd_identity_and_maturity_recorded", fields.get("id", "").startswith("prd:") and
              fields.get("revision", "").isdigit() and int(fields["revision"]) >= 1 and
              fields.get("status") in ("draft", "needs_evidence", "needs_decision", "ready_for_review"))
        check("requirements_and_acceptance_present", bool(re.search(r"FR-\d+",new)) and bool(re.search(r"AC-\d+",new)))
        if case == "prd-from-problem":
            check("actual_upstream_cited", "problem:internal-document-revision-access" in new and "problem.md" in new)
            check("source_context_preserved", "observed-notes.md" in new and "OD-001" in new)
        elif case == "prd-direct":
            check("direct_source_cited", "direct-input.md" in new)
            check("hypothetical_maturity_retained", fields.get("status") in ("draft", "needs_evidence", "needs_decision"))
        else:
            check("prd_identity_and_revision_preserved", fields.get("id") == "prd:internal-revision-access" and fields.get("revision") == "3")
            check("requirement_ids_preserved", all(x in new for x in ("GOAL-001","FR-001","AC-001","FR-002","AC-002","DEC-001","OD-001")))
            check("untouched_requirement_text_preserved", 'FR-001: Internal recipients can access the revision selected for their review.' in new and
                  'The mobile-app launch date is 2026-11-12 and remains tentative.' in new)
            check("portal_change_recorded", bool(re.search(r"portal|포털",new,re.I)))
        # Whole-output review must verify the meaning of constraints, AC testability,
        # no invented policy/metrics, and links. These are narrow checks only.
    elif case.startswith("problem-"):
        target = "existing-problem.md" if case == "problem-update" else "problem.md"
        new = text(target)
        fields = document_fields(new)
        check("problem_identity_and_maturity_recorded", bool(fields.get("id")) and
              fields.get("revision", "").isdigit() and int(fields["revision"]) >= 1 and
              fields.get("status") in ("draft", "needs_evidence", "needs_decision", "ready_for_review"))
        if case == "problem-observed":
            check("reported_count_preserved", bool(re.search(r"(?:4.{0,30}12|12.{0,30}4)", new, re.S)))
            check("actual_source_cited", "observed-notes.md" in new)
            check("source_limit_stays_visible", bool(re.search(r"미검증|검증되지|독립.{0,30}(?:검증|확인).{0,20}(?:않|없|못)|검증.{0,15}(?:않|없|못)|unverified", new, re.I)))
        elif case == "problem-hypothesis":
            check("hypothesis_not_promoted_to_ready", fields.get("status") in ("draft", "needs_evidence", "needs_decision"))
            check("hypothetical_input_cited", "idea-only.md" in new)
        else:
            check("document_identity_and_revision_preserved", fields.get("id") == "problem:revision-access" and
                  fields.get("revision", "").isdigit() and int(fields["revision"]) == 3)
            check("stable_claim_ids_preserved", all(x in new for x in ("EV-001", "DEC-001", "OD-001")))
            check("unrelated_date_and_uncertainty_preserved", "2026-11-12" in new and "tentative" in new)
            check("updated_workflow_recorded", bool(re.search(r"email|이메일|메일",new,re.I)) and
                  bool(re.search(r"link|링크",new,re.I)))
        # Review source fidelity, decision preservation, fabricated claims and question
        # behavior manually against the exact inputs; matching words is insufficient.
    elif case == "review-check":
        try:
            report = json.loads(text("report.json"))
            by_id = {}
            primary_ids = [claim["id"] for claim in report["claims"]]
            duplicate = len(primary_ids) != len(set(primary_ids))
            # Fixture truth: only R1 and R6 describe the same concern. Matching
            # verdicts do not make unrelated claims interchangeable.
            allowed_aliases = {"R1": {"R6"}, "R6": {"R1"}}
            for claim in report["claims"]:
                aliases = claim.get("aliases", [])
                if not isinstance(aliases, list):
                    raise ValueError("aliases must be an array")
                duplicate |= not set(aliases) <= allowed_aliases.get(claim["id"], set())
                duplicate |= len(aliases) != len(set(aliases))
                for identity in [claim["id"], *aliases]:
                    # Aliases may reference another retained input record. Reject
                    # conflicting dispositions, not consistent cross-references.
                    if identity in by_id:
                        previous = by_id[identity]
                        duplicate |= any(previous.get(key) != claim.get(key)
                                         for key in ("verdict", "current_state"))
                    else:
                        by_id[identity] = claim
            expected = {"R1": "refuted", "R2": "partial", "R3": "unresolved",
                        "R4": "confirmed", "R5": "unresolved", "R6": "refuted"}
            check("all_claims_disposed_without_duplicate_ids",
                  not duplicate and set(by_id) == set(expected) and
                  all(by_id[k]["verdict"] == v for k, v in expected.items()))
            check("historical_bug_distinct_from_current_fix",
                  by_id["R4"].get("current_state") == "already_addressed" and
                  bool(by_id["R4"].get("evidence")))
            check("unknown_claims_keep_missing_evidence_without_severity",
                  all(by_id[k].get("verified_severity") is None and
                      bool(by_id[k].get("missing_evidence")) for k in ("R3", "R5")))
            check("claim_coverage_recorded",
                  set(report["coverage"]["input_ids"]) == set(expected) and
                  set(report["coverage"]["handled_ids"]) == set(expected))
            check("human_report_present", bool(text("report.md").strip()))
            # A human must still inspect whether the cited source supports the verdict.
            check("checks_recorded", bool(report["checks"]) and
                  all(isinstance(c.get("executed"), bool) and c.get("result")
                      for c in report["checks"]))
        except (ValueError, KeyError, TypeError, AttributeError):
            check("valid_claim_report", False)
    else:
        try:
            report = json.loads(text("review.json"))
            findings = report["findings"]
            matches = [f for f in findings if f.get("file") == "src/api/toInvoice.ts" and f.get("line") == 9]
            check("unsafe_cast_anchored", bool(matches))
            # A narrow content check, not a semantic judge: human review remains necessary.
            description = " ".join(str(f.get("description", "")) for f in matches)
            fix = " ".join(str(f.get("fix", "")) for f in matches)
            check("cross_file_contract_traced", all(x in description for x in ("archived", "InvoiceStatus", "InvoiceStatusLabel")))
            check("consumer_fix_requested", "archived" in fix and bool(re.search(r"(?i)label|라벨|레이블", fix)))
            check("nonrunnable_tests_not_claimed", report.get("tests_executed") is False and bool(report.get("limitations")))
        except (ValueError, KeyError, TypeError, AttributeError):
            check("valid_review_artifact", False)
    return results
