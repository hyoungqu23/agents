"""Small behavioral smoke suite. Graders stay outside the executor workspace.

These checks are intentionally narrower than the skills' full qualitative rubrics.
They inspect actual output artifacts, never an executor's self-assigned score.
"""
import json
import re
import shutil
from pathlib import Path

CASES = ("design-existing", "content-fidelity", "review-runtime", "review-check")
SKILLS = {"design-existing": ("design", "design-brief"),
          "content-fidelity": ("content", "un-ai"),
          "review-runtime": ("review", "review-code"),
          "review-check": ("review", "review-check")}


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


def grade(case, before, after):
    results = []
    def check(name, passed):
        results.append({"check": name, "passed": bool(passed)})
    def text(path):
        return after.get(path, b"").decode("utf-8", errors="replace")
    allowed = {"design-existing": {"apps/dashboard/DESIGN_SYSTEM.md"},
               "content-fidelity": {"edited.md"},
               "review-runtime": {"review.json"},
               "review-check": {"report.md", "report.json"}}[case]
    changed = {p for p in before.keys() | after.keys() if before.get(p) != after.get(p)}
    check("only_requested_output_changed", bool(changed) and changed <= allowed)
    if case == "design-existing":
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
