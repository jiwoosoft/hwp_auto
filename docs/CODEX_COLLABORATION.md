# Codex 공동작업 계획

> Claude Code와 OpenAI Codex CLI를 병행하여 **비동기적 병렬 개발**을 수행한다.
> 솔로 개발자가 두 명 몫을 하기 위한 설계.

## 왜 공동작업인가

| 관점 | 이점 |
|---|---|
| 속도 | 독립 모듈을 병렬 구현 → 대기시간 최소화 |
| 다양성 | 서로 다른 모델의 구현/리뷰 관점이 사각지대를 줄임 |
| 검증 | "한 모델이 작성, 다른 모델이 리뷰" 교차검증 |
| 회복력 | 한쪽이 막히면 다른 쪽이 진행 — 솔로의 번아웃 방지 |

## 역할 분담 (기본)

| 도메인 | 주로 Claude | 주로 Codex |
|---|---|---|
| 아키텍처/설계 | ✅ | 보조 |
| Core API 구현 | ✅ | 독립 모듈 한정 |
| 테스트 작성 | ✅ | 파라메트릭/엣지 케이스 |
| 파서/바이너리 해킹 | 공동 | ✅ (C 포맷 경험 강함) |
| 리팩토링 | 공동 | ✅ (기계적 변환) |
| 문서화 | ✅ | 코드 주석/docstring |
| 리뷰 | ✅ (설계 중심) | ✅ (스타일/엣지) |

**원칙**: 한 번에 한 모델만 같은 파일을 건드린다. 병렬은 **모듈 단위**로 분리.

## 핸드오프 프로토콜

### 디렉토리
```
handoff/
├── README.md                   # 규칙
├── codex/                      # Claude → Codex 작업 요청
│   ├── 001_xxx.md              # 완료 대기 중
│   ├── 002_yyy.md
│   └── done/                   # 완료된 작업 (아카이브)
├── claude/                     # Codex → Claude 작업 요청
│   └── ...
└── review/                     # 상호 리뷰 요청
    └── ...
```

### 핸드오프 파일 형식

각 요청은 다음 헤더로 시작하는 단일 마크다운:

```markdown
---
id: 001
from: claude
to: codex
status: pending  # pending | in_progress | review | done
created: 2026-04-21
priority: high | medium | low
---

# [작업 제목]

## 목적
(왜 이 작업이 필요한가)

## 범위 (In-Scope)
- ...

## 범위 외 (Out-of-Scope)
- ...

## 인수 기준 (Acceptance Criteria)
- [ ] ...

## 참고 파일
- `path/to/file.py` (읽기만)
- `path/to/spec.md` (규격)

## 테스트 요구사항
- `tests/unit/test_xxx.py` 에 N개 이상의 케이스

## 완료 후 할 일
- 이 파일을 `handoff/codex/done/`로 이동
- PR 생성 또는 `review/` 에 리뷰 요청 파일 작성
```

### 생명 주기
```
pending → in_progress → review → done
                ↓
             blocked (이유 기록 후 Claude로 반환)
```

## 동기화 규칙

1. **Branch 전략**: 각 모델은 자기 작업 브랜치
   - Claude: `feature/claude-xxx`
   - Codex: `feature/codex-xxx`
   - main은 병합만
2. **동시 편집 금지**: 같은 파일을 둘이 동시에 수정하지 않는다
3. **커밋 메시지 prefix**: `[claude]` / `[codex]` 로 주체 명시 (선택)
4. **테스트 필수**: 어느 쪽 PR이든 테스트 없이 병합 불가

## 교차 검증 루프

### 패턴 A: 구현 → 리뷰
```
Claude: 기능 X 구현 + 테스트
  → review/001_review_X.md 작성 (Codex에게 리뷰 요청)
Codex: 코드 읽고 피드백 추가
Claude: 반영
```

### 패턴 B: 스펙 → 병렬 구현 → 비교
```
Claude: spec.md 작성
  ├── Claude가 branch A에 구현
  └── Codex가 branch B에 구현
둘 다 같은 테스트 스위트를 통과
둘 중 더 나은 디자인 채택 또는 병합
```

### 패턴 C: 테스트 → 구현
```
Claude: 실패하는 테스트 작성 (RED)
Codex: 테스트를 통과하는 최소 구현 (GREEN)
Claude: 리팩토링 (REFACTOR)
```

## 현실적 제약

- **컨텍스트 분리**: 두 모델은 서로의 대화 컨텍스트를 공유하지 않음 → **파일이 유일한 진실의 원천**
- **동시성 한계**: 실제론 사용자가 번갈아 실행 → "비동기"는 사용자 시간 스케일
- **토큰 예산**: 두 번 쓰면 두 배로 든다 → 반복 작업에 우선 할당
- **일관성**: 스타일 가이드를 둘 다 따라야 — `pyproject.toml`의 ruff/black이 계약

## 첫 번째 실전 핸드오프

`handoff/codex/001_hwp_binary_parser_spike.md`: HWP 5.0 바이너리 포맷의 최소 파서 스파이크.
Codex의 C/바이너리 강점 활용 + Core API의 다음 단계(`HwpDocument.sections` 구현)에 필요.

## 실행 가이드 (사용자 관점)

### Codex 작업 시작
```bash
# 대기 중 작업 확인
ls handoff/codex/*.md | grep -v done

# Codex CLI로 작업 수행
cd /Users/moon/Desktop/master-of-hwp
codex exec --task handoff/codex/001_hwp_binary_parser_spike.md

# 완료 후 done/으로 이동
git mv handoff/codex/001_*.md handoff/codex/done/
```

### Claude에게 복귀
"codex가 001 완료했어. 리뷰 부탁해" → Claude가 변경사항 리뷰 + 다음 핸드오프 작성

### 작업 가시성
```bash
# 현재 상태 요약 (앞으로 스크립트화 예정)
find handoff -name "*.md" | xargs grep -l "status: pending"
```

## 도구 지원 아이디어 (Phase 1에서 구현)

- `scripts/handoff_new.py` — 핸드오프 파일 템플릿 생성
- `scripts/handoff_status.py` — 전체 대기/진행/완료 요약
- Git pre-commit hook — 핸드오프 파일 변경 시 상태 자동 검증
