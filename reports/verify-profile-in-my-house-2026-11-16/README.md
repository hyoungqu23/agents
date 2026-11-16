# 검증 프로필 시범 · 불 꺼진 집 친구 초대

**기본 자료만 제공한 A와 수동 프로필을 추가한 B 모두 첫 브라우저 실행에서 같은 방의 손님 입장을 확인했다.** 이 여정에서 프로필로 해소된 막힘은 관찰되지 않았다. 생성·유지 스킬 구현과 다른 소비자로의 확대를 보류한다.

대상은 [in-my-house f97c4b3](https://github.com/hyoungqu23/in-my-house/commit/f97c4b3df6f9d83f887b62dfd363f4046731b02b)이다. 동일 커밋의 별도 복사본 두 개에 같은 잠금 파일의 의존성을 설치했다. 각 복사본의 Next.js 16.2.11 서버는 별도 루프백 포트와 빈 메모리 저장소를 사용했다. 외부 초대 메시지 전송이나 Supabase 연결은 없었다.

| 항목 | A · 기본 자료 | B · 수동 프로필 |
| --- | --- | --- |
| 입력 | 앱 소스, 기존 문서·테스트, dogfood 지침, [공통 요청](prompt.txt) | 같은 자료와 요청에 [프로필](PROFILE.md) 경로 한 줄 추가 |
| 모델 | Codex gpt-6-astra, low, 새 ephemeral 세션 | 동일. 명령 기록에서 프로필 열람 확인 |
| 프로그램 작성 중 완료된 셸 호출 | [11건](a/commands.json) | [11건](b/commands.json) |
| 모델 시작부터 프로그램 파일 작성까지 | 약 69초 | 약 63초 |
| 모델 시작부터 명단 증거·결과 저장까지 | 약 136초 | 약 170초 |
| 실제 실행 | [프로그램](a/trial.cjs) · [판정](a/trial-result.json) · [호스트 명단](a/trial.png) | [프로그램](b/trial.cjs) · [판정](b/trial-result.json) · [호스트 명단](b/trial.png) |

각 세션이 독립적으로 Playwright 프로그램을 작성했다. 코디네이터가 프로그램을 검토하고 Chromium 149.0.7827.55로 실행했다. 두 프로그램 모두 게임 카드를 선택하고 호스트가 닉네임을 입력한 뒤 실제 로비의 초대 UI를 사용했다. 새 브라우저 컨텍스트에서 손님이 참가하고 호스트 명단에 나타나는지 검증했다. 캡처 범위는 명단으로 제한했고 실험 후 두 서버를 종료했다.

**해석 범위.** 호스트와 모델의 브라우저 실행 권한 차이를 통제하기 위해 서버 시작과 브라우저 실행은 양쪽 모두 코디네이터가 맡았다. 자동 프로필 발견이나 모델의 독립적인 설치·서버 기동 능력은 측정하지 않았다. 앱에는 이미 시작법과 다중 브라우저 테스트가 있다. 프로필 작성에는 저장소의 실행 문서·초대 UI·기존 E2E를 읽는 추가 작업이 들었다. 작성 시간과 유지 비용은 독립적으로 계측하지 않았다. 한 쌍의 결과로 실행 시간이나 토큰 절감 효과를 추정할 수 없다.

## 재현 절차

게임 커밋 `f97c4b3`의 별도 복사본 두 개를 준비한다. 각 앱 루트에서 `pnpm install --frozen-lockfile --ignore-scripts`를 실행한다. 모델에 제공한 dogfood 지침은 [agents 8d26bdd의 build/skills/dogfood](https://github.com/hyoungqu23/agents/tree/8d26bdd/plugins/build/skills/dogfood)이며, 두 앱의 `.eval-skills/dogfood/`에 복사했다. B에만 이 보고서의 PROFILE.md를 `.agents/verify/web/PROFILE.md`로 복사하고 공통 요청 끝에 다음 한 줄을 추가했다.

> Consult .agents/verify/web/PROFILE.md for this journey.

저장된 프로그램을 재실행하려면 각 앱 루트에 이 보고서의 해당 `a/trial.cjs` 또는 `b/trial.cjs`를 `trial.cjs`로 복사한다. 프로젝트의 Playwright 버전에 맞는 Chromium을 준비한다. 각 앱 루트에서 서버 전용 터미널과 실행 전용 터미널을 사용한다.

| 실행 | 서버 터미널 | 실행 터미널 |
| --- | --- | --- |
| A | `GAME_STORE=memory NEXT_TELEMETRY_DISABLED=1 pnpm exec next dev --hostname 127.0.0.1 --port 34671` | `BASE_URL=http://127.0.0.1:34671 GAME_STORE=memory node trial.cjs` |
| B | `GAME_STORE=memory NEXT_TELEMETRY_DISABLED=1 pnpm exec next dev --hostname 127.0.0.1 --port 34672` | `BASE_URL=http://127.0.0.1:34672 GAME_STORE=memory node trial.cjs` |

브라우저 프로그램은 A가 종료된 뒤 B를 실행한다. 각 앱 루트에 trial-result.json과 trial.png가 생성된다. 결과를 확인한 뒤 해당 서버 터미널에서 Ctrl-C로 종료한다.

## 경과 시간의 원자료

아래는 임시 실행 파일에서 읽은 UTC 시각이다. 시작은 모델 이벤트 파일의 생성 시각, 프로그램 작성과 결과 저장은 각 파일의 마지막 수정 시각이다.

| 실행 | 시작 (UTC) | trial.cjs 작성 (UTC) | trial-result.json 저장 (UTC) |
| --- | --- | --- | --- |
| A | 2026-11-15T17:00:26.172Z | 2026-11-15T17:01:34.892Z | 2026-11-15T17:02:42.616Z |
| B | 2026-11-15T17:00:27.832Z | 2026-11-15T17:01:30.422Z | 2026-11-15T17:03:18.126Z |

‘모델 시작부터 명단 증거·결과 저장까지’에는 코디네이터의 프로그램 검토와 실행 대기가 포함된다. B의 170초에는 A의 브라우저 실행을 기다린 시간도 들어 있어 두 값으로 속도 차이를 판단할 수 없다.
