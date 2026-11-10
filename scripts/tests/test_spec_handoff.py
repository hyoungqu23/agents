"""Mechanical handoff contract regressions, not a model quality evaluation."""
import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / 'plugins/product/skills/spec'
_module = importlib.util.spec_from_file_location('spec_check', SKILL / 'scripts/spec_check.py')
gate = importlib.util.module_from_spec(_module)
_module.loader.exec_module(gate)


def sample():
    spec = '''---
id: "spec:projects"
revision: 1
handoff_version: 1
status: ready
questions: ./QUESTIONS.md
---
# 프로젝트 필터
## 1. 목표·범위·제약
읽기 전용 필터. 삭제는 제외(사용자 요청).
## 2. 근거 자료·확정된 결정
request.md의 AC-list/AC-empty와 api.md 대상 v2 계약을 읽음. 배포 미확인.
## 3. 화면·사용자 흐름·상태 전이
활성 선택 시 실제 결과와 개수. 빈 성공은 오류와 구분.
## 4. UI 규칙·입력 검증·권한
필터 외 편집 없음. 내부 컴포넌트 선택은 개발자 재량.
## 5. API 계약·데이터 매핑·오류 처리
GET /projects?status=active → 200 {items: Array}. items는 필수·non-null.
## 6. AC·검증 시나리오
### 6.1 AC 연결
| AC ID | 근거 | 사전 조건 | 행동 | 기대 관찰 결과 | 관련 화면·흐름·API | 확인 방법·미결 참조 |
| --- | --- | --- | --- | --- | --- | --- |
| AC-list | request.md | 목록 로드 | 활성 선택 | 응답 items와 개수 표시 | GET /projects?status=active | 실제 응답 ID와 표시 ID 대조 |
| AC-empty | request.md | 성공 items=[] | 결과 렌더 | 결과 없음, 오류와 구분 | 목록 UI | 빈 성공/오류 대조 |
### 6.2 명세 검토 결과
| 검토 | 수행 범위·방식 | 결과와 한계 |
| --- | --- | --- |
| 구조·ID·상호 참조 | 두 문서 정본 대조 | ID 유지 |
| 원자료·권위·판본 대조 | request/API 직접 읽음 | v2 계획 계약, 배포 미확인 |
| 화면·정책·API·AC 정합성 | 두 AC 경로 자체 검토 | 런타임 미실행 |
| AC별 구현 내용 재구성 | 자기 검토 | 별도 리더 호출 안 함 |
'''
    questions = '''---
id: "questions:projects"
revision: 1
handoff_version: 1
spec: ./SPEC.md
---
## 1. 질문 목록
| ID | 종류 | 질문 요약 | 영향 절·AC·범위 | 미해결 시 차단 | 상태 |
| --- | --- | --- | --- | --- | --- |
## 2. 질문 상세
선언한 읽기 범위 미결 없음. 삭제 권한은 범위 밖임.
'''
    return spec, questions


class SpecHandoffTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.spec, self.q = self.root / 'SPEC.md', self.root / 'QUESTIONS.md'
        s, q = sample()
        self.spec.write_text(s); self.q.write_text(q)

    def check(self):
        return gate.check(self.spec, self.q)

    def test_complete_korean_contract_and_opaque_ids(self):
        self.assertEqual(self.check()['structure'], 'valid')
        self.assertEqual(self.check()['ac_ids'], ['AC-list', 'AC-empty'])

    def test_templates_cannot_pass_as_finished_documents(self):
        for name in ('SPEC', 'QUESTIONS'):
            shutil.copyfile(SKILL / 'assets' / (name + '.template.md'), self.root / (name + '.md'))
        self.assertEqual(self.check()['structure'], 'invalid')

    def test_deferred_yes_is_active_and_conflicts_with_ready(self):
        self.q.write_text(self.q.read_text().replace('## 2.', '| Q-1 | decision | policy | AC-list | yes | deferred |\n## 2.'))
        self.assertEqual(self.check()['structure'], 'invalid')
        self.spec.write_text(self.spec.read_text().replace('status: ready', 'status: blocked'))
        self.assertEqual(self.check()['structure'], 'valid')
        self.assertEqual(self.check()['active_blockers'][0]['acs'], ['AC-list'])

    def test_resolved_yes_and_open_no_are_not_active(self):
        self.q.write_text(self.q.read_text().replace('## 2.', '| Q-1 | decision | policy | AC-list | yes | resolved |\n| Q-2 | wording | text | AC-empty | no | open |\n## 2.'))
        self.assertEqual(self.check()['structure'], 'valid')
        self.assertEqual(self.check()['active_blockers'], [])

    def test_unknown_active_impact_is_not_ignored(self):
        self.q.write_text(self.q.read_text().replace('## 2.', '| Q-1 | decision | policy | AC-list, AC-missing | yes | open |\n## 2.'))
        self.assertEqual(self.check()['structure'], 'invalid')

    def test_duplicate_ac_fails(self):
        self.spec.write_text(self.spec.read_text().replace('| AC-empty |', '| AC-list |'))
        self.assertEqual(self.check()['structure'], 'invalid')

    def test_missing_companion_and_wrong_backlink_fail(self):
        self.q.write_text(self.q.read_text().replace('./SPEC.md', './other.md'))
        self.assertEqual(self.check()['structure'], 'invalid')
        self.q.unlink()
        self.assertEqual(self.check()['structure'], 'invalid')

    def test_source_change_changes_record_identity(self):
        before = self.check()['sources']
        self.spec.write_text(self.spec.read_text().replace('응답 items와 개수 표시', '응답 items만 표시'))
        self.assertNotEqual(self.check()['sources'], before)

    def test_no_review_record_is_not_ready_structure(self):
        self.spec.write_text(self.spec.read_text().replace('| AC별 구현 내용 재구성 | 자기 검토 | 별도 리더 호출 안 함 |', ''))
        self.assertEqual(self.check()['structure'], 'invalid')

    def test_fenced_example_is_not_canonical(self):
        self.spec.write_text(self.spec.read_text().replace('### 6.1', '```markdown\n### 6.1').replace('### 6.2', '```\n### 6.2'))
        self.assertEqual(self.check()['structure'], 'invalid')

    def test_unsupported_version_and_flag_fail_closed(self):
        self.spec.write_text(self.spec.read_text().replace('handoff_version: 1', 'handoff_version: 2'))
        self.assertEqual(self.check()['structure'], 'invalid')

    def test_source_symlink_rejected(self):
        actual = self.spec.with_name('actual.md'); self.spec.rename(actual); self.spec.symlink_to(actual)
        self.assertEqual(self.check()['structure'], 'invalid')

    def test_ac_row_without_leading_pipe_is_rejected_not_omitted(self):
        self.spec.write_text(self.spec.read_text().replace('| AC-empty |', 'AC-empty |'))
        self.assertEqual(self.check()['structure'], 'invalid')

    def test_active_question_without_leading_pipe_is_rejected(self):
        self.q.write_text(self.q.read_text().replace('## 2.', 'Q-1 | decision | policy | AC-list | yes | deferred |\n## 2.'))
        self.assertEqual(self.check()['structure'], 'invalid')

    def test_ac_row_without_trailing_pipe_is_rejected(self):
        self.spec.write_text(self.spec.read_text().replace('빈 성공/오류 대조 |', '빈 성공/오류 대조'))
        self.assertEqual(self.check()['structure'], 'invalid')

    def test_identity_is_detected_only_in_actual_frontmatter(self):
        quoted = '# Direct request\n```yaml\nid: spec:example\nhandoff_version: 1\n```\n'
        self.assertFalse(gate.handoff.is_spec(quoted))
        self.assertTrue(gate.handoff.is_spec(self.spec.read_bytes()))
        self.assertFalse(gate.handoff.is_spec(self.q.read_bytes()))

    def test_bad_utf8_body_keeps_spec_identity_and_fails_check(self):
        self.spec.write_bytes(self.spec.read_bytes() + b'\xff')
        self.assertTrue(gate.handoff.is_spec(self.spec.read_bytes()))
        self.assertEqual(self.check()['structure'], 'invalid')

    def test_indented_fence_cannot_supply_the_canonical_table(self):
        self.spec.write_text(self.spec.read_text().replace('### 6.1', '  ```markdown\n### 6.1').replace('### 6.2', '  ````\n### 6.2'))
        self.assertEqual(self.check()['structure'], 'invalid')


if __name__ == '__main__':
    unittest.main()
