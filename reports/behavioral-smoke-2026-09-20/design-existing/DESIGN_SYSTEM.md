# Dashboard conventions

## 화면 색

Accent #175cd3. Surface #f8fafc. Text #182230.

Token source: `src/theme.css`의 `:root` (`--accent`, `--surface`, `--ink`). 패널 radius 12px와 padding 24px도 같은 파일의 `.panel`에서 확인한다.

## Component design

Use compound components for related controls. Keep existing public prop names.

## Motion

Use short opacity transitions; honor reduced motion.

## Decisions Log

| Decision | Scope | Reason | Source | Date | Status |
| --- | --- | --- | --- | --- | --- |
| Accent, surface, text는 각각 `--accent`, `--surface`, `--ink`를 사용한다. | Dashboard colors | 구현에 정의된 기존 토큰을 유지한다. | `src/theme.css` `:root` | 2026-09-20 | Observed |
| 관련 control은 compound components로 구성하고 기존 public prop names를 유지한다. | Dashboard components | 기존 컴포넌트 규칙과 API 호환성을 보존한다. | 이 문서의 Component design | 2026-09-20 | Observed |
| Motion은 짧은 opacity transition을 사용하고 reduced motion을 존중한다. | Dashboard motion | 기존 motion 및 접근성 규칙을 보존한다. | 이 문서의 Motion | 2026-09-20 | Observed |
