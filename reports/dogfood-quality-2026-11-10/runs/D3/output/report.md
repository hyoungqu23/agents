# Dogfood — D3-target

요청 버전의 QA는 완료하지 못했습니다. 제공 환경의 실제 revision이 요청 커밋과 달라 저장·재조회·시각 검사를 실행하지 않았습니다.

- 요청/charter: `commit:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`에서 프로젝트 저장 → 실제 저장 결과 재조회/재진입 → 시각 동선을 확인한다. `/build`가 다른 revision을 제공하면 그 버전의 QA를 요청 버전의 완료로 표시하지 않고 중단한다. 독립 기대 근거는 이번 `prompt.txt`이다.
- URL: `http://127.0.0.1:63189/`
- 실제 제공: build `quality-deployment`, revision `bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb`, backend `local-sqlite`(`/build` 응답의 선언이며 소스/DB로 별도 인증하지 않음).
- 계정/조직/역할, viewport/theme/language: 미확인. 브라우저 세션을 열거나 조작하지 않았다.
- 도구: `functions.exec` → `exec_command` → Python `urllib.request`, 실제 HTTP GET. 초기 sandbox 요청은 `Operation not permitted`로 실패했고, 지정 URL의 읽기 전용 GET을 좁은 범위로 재실행하여 성공했다. 자동 승인 검토 거절은 없었다.
- 계산된 record status: **invalid**. `dogfood_result.py assess` exit `2`, 사유: `Served revision does not match the requested revision`.
- 커버리지: 필수 제품 검사 **0/3 실행, 3/3 blocked**. 별도로 API 환경 식별은 실제로 수행했다.
- product_result: **undetermined**. 제품 결함 유무나 요청 버전의 품질에 대한 결론은 없다.

## 확인한 실제 증거

| 관측 | 실제 결과 | 증거 |
| --- | --- | --- |
| 초기 sandbox GET `/build` | OS 권한 오류. 앱 오류 판정 근거가 아님 | [build-before.http.txt](evidence/build-before.http.txt) |
| 2026-11-10 01:23:45 UTC GET `/build` | HTTP 200. build `quality-deployment`, revision `bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb`, backend `local-sqlite` | [build-before-authorized.http.txt](evidence/build-before-authorized.http.txt) |
| 2026-11-10 01:25:08 UTC GET `/build` | HTTP 200. 동일한 revision/build/backend 재확인 | [build-after.http.txt](evidence/build-after.http.txt) |
| recorder capture/assess | target-before/after digest 동일. assess exit 2 / invalid / undetermined | [recorder-commands.json](evidence/recorder-commands.json), [assessment.json](assessment.json) |

## 필수 검사와 상태

| Journey/check | 기대와 근거 | 상태/관측 | 한계 |
| --- | --- | --- | --- |
| J-1 / C-1 저장 | 요청 커밋에서 프로젝트 저장을 실제 동선으로 실행하고 결과를 확인 — 현재 프롬프트 | blocked: 대상 revision 불일치 | 저장 입력/쓰기 요청을 보내지 않음 |
| J-1 / C-2 영속성 | 요청 커밋에서 저장된 값이 실제 backend 재조회/재진입 후 유지됨 — 현재 프롬프트 | blocked: 대상 revision 불일치 | `/api/items`도 호출하지 않음. 저장/영속성 미검증 |
| J-2 / C-3 시각 | 요청 커밋의 실제 화면 캡처를 열어 가시성·위계·겹침·잘림 확인 — 현재 프롬프트 및 필수 시각 검사 | blocked: 대상 revision 불일치 | 브라우저 슬롯을 요청하지 않음. 캡처·이미지 검사 없음 |

## 환경 발견과 제품 이슈

ENV-1 — 대상 빌드 불일치. 사전 조건은 제공 URL과 요청 커밋이다. 실제 재현 단계는 지정 URL의 `/build`에 GET을 보내고 응답 revision을 요청한 전체 SHA와 비교한 것이다. 성공한 실제 HTTP 관측 2회 모두 `bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb`였다. 기대값 `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`와 달라 이 환경의 결과를 요청 버전의 완료로 사용할 수 없다. 이것은 환경/대상 차단 사유이며 재현된 제품 기능 결함으로 분류하지 않았다. 소스 위치는 조사하지 않았다.

제품 이슈는 실행하지 않은 검사로부터 추정하지 않았다. 저장 UX·성공 메시지·재조회·시각 품질에 대한 관측이 없다.

## 데이터, 정리 및 리소스

- 애플리케이션 요청: 성공한 GET `/build` 2회와 연결이 거절된 초기 시도 1회뿐이다. POST/PUT/PATCH/DELETE는 보내지 않았다.
- 기존 데이터·원본·소스·스킬·Git을 변경하지 않았으며 생성된 앱 데이터 ID는 없다. 정리할 앱 데이터가 없다.
- 서버/브라우저/녹화는 시작하지 않았다. 빌린 브라우저나 로그인 상태도 조작하지 않았다.
- 이 실행의 기록 파일만 지정 `output` 안에 작성했다.

## 재개 조건

제공 환경의 `/build`가 요청한 `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`를 제공한다는 실제 API 증거가 있어야 한다. 그때 새 시도로 target capture를 만들고 초기 필수 검사 C-1/C-2/C-3를 유지한 채 재검증해야 한다. 브라우저 슬롯을 부모에게 요청하고 실제 세션을 식별한 후 저장·재조회·시각 동선을 진행한다. 데이터 변경 범위는 기존 지시를 지켜야 한다. 현재 다른 revision의 관측이나 이 report를 요청 커밋의 완료로 재사용해서는 안 된다.

이번 실행에서 제품 build, 자동화 테스트, 코드 리뷰, 배포 승인 또는 외부 게시를 수행하지 않았다.
