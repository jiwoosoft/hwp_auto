# master-of-hwp Roadmap

> **한 줄 요약**: HWP 문서를 AI가 안전하게 편집할 수 있게 하는 오픈소스 플랫폼.
> 콘텐츠 앱이 아닌 **인프라**를 지향한다.

## 철학

1. **Platform-first** — 템플릿 앱이 아니라 확장 가능한 편집 플랫폼.
2. **왕복 재현율(Round-trip fidelity)이 계약** — 열고-저장해도 구조 훼손 없음을 수치로 증명.
3. **Agentic document intelligence** — 문서가 자기 자신을 이해하도록.
4. **솔로 오픈소스 · 시간 무제한 · 완벽주의** — 상용 압박 없음, 품질만 본다.

## 레이어 구조

```
┌─────────────────────────────────────────┐
│  Layer 4: Agentic Capabilities          │  이해/계획/검증 에이전트
├─────────────────────────────────────────┤
│  Layer 3: Recipes (community-driven)    │  템플릿, 예시 (외부 기여)
├─────────────────────────────────────────┤
│  Layer 2: Editor (rhwp-studio)          │  WASM 기반 UI (유지보수 모드)
├─────────────────────────────────────────┤
│  Layer 1: Core API (master_of_hwp)      │  ⭐ 현재 집중 영역
├─────────────────────────────────────────┤
│  Engine: rhwp (Rust) / file parsers     │
└─────────────────────────────────────────┘
```

## 현재 결정: **Core API 우선**

에디터(Layer 2)는 Feature Freeze. 3개월간 Core API(Layer 1)를 PyPI 배포 가능한 수준까지 끌어올린다.

**근거**:
- 테스트 경제학: pytest는 결정적, Playwright는 플레이키
- 계층 의존성: 에디터 버그의 80%는 Core에서 내려온다
- 기여 동역학: Python 기여자가 TS/WASM 기여자보다 10배
- 후회 최소화: 방향 틀려도 손실 작음

## 측정 가능한 목표 (사용성 지표)

| 항목 | 목표 |
|---|---|
| 설치 → 첫 AI 편집 | 5분 이내 |
| 왕복 재현율 | 95%+ |
| 자연어 명령 1-shot 성공률 | 80%+ |
| API 레퍼런스 예제 | 100개+ |
| 외부 기여자 (6개월 내) | ≥ 3명 |

## Phase별 계획

### Phase 0: Foundation (완료 ✅)
- [x] 이슈 #12~#15 에디터 UX 수정
- [x] `master_of_hwp/` 패키지 스켈레톤
- [x] `HwpDocument.open()` Core API
- [x] Fidelity 벤치마크 하네스
- [x] GitHub Actions CI (ruff/black/mypy/pytest)
- [x] CONTRIBUTING / 이슈 템플릿

### Phase 1: Core v0.1 (2026-04-21 릴리스 준비 중)
- [x] `HwpDocument` 읽기 API 완성 (sections, paragraphs, tables, plain_text, iter_paragraphs, find_paragraphs, summary)
- [x] HWPX `replace_paragraph` (write path, byte-level fidelity)
- [x] HWP 5.0 `replace_paragraph` — same-length only (xfail로 기록된 gap)
- [x] Property-based testing (Hypothesis) — replace idempotency, locality
- [x] Type hints 100%, docstring 100%, mypy strict 통과
- [x] `ai/` 패키지 스켈레톤 (Phase 2 공개 surface 고정)
- [ ] PyPI 배포 — `v0.1.0` 태그 + Trusted Publishing (수동 단계)

### Phase 2: v0.2 — Write path 확장
- [ ] HWP 5.0 CFBF stream resize writer (다른 길이 replace)
- [ ] `insert_paragraph` / `delete_paragraph` (두 포맷)
- [ ] 표 셀 편집 프리미티브
- [ ] LLM provider 추상화 (Claude 기본, 교체 가능)

### Phase 3: v0.3 — Agentic 편집 루프
- [ ] `doc.ai_edit(자연어)` 풀 루프 (의도→위치→연산→검증→롤백)
- [ ] `ai/locator.locate_targets()` 실 구현 (find_paragraphs + LLM 재랭킹)
- [ ] `ai/rollback.RollbackTransaction.apply()` 트랜잭셔널 실행
- [ ] 노트북 예제 3개

### Phase 4: Ecosystem Open
- [ ] Recipes 프레임워크 공개
- [ ] 에디터 재작성 (깔끔한 Core API 소비)
- [ ] 쇼케이스 3종 (가정통신문/기안문/논문)

### Phase ∞: v1.0 계약 고정
v1.0 릴리스 = API 호환성 계약 시작. 그 전까지는 실험적.

## 의도적 비목표 (Non-goals)

- ❌ SaaS / 수익화 모델
- ❌ 자체 AI 파인튜닝
- ❌ 클라우드 동기화
- ❌ 모바일 지원
- ❌ 플러그인 시스템 (v2.0까지)
- ❌ 멀티 에이전트 오케스트레이션

## 관련 문서

- [ARCHITECTURE.md](./ARCHITECTURE.md) — 레이어별 세부 설계
- [../CONTRIBUTING.md](../CONTRIBUTING.md) — 기여 가이드
