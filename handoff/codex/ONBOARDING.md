# Codex Onboarding — master-of-hwp

> 이 문서 하나만 읽으면 당신(Codex)이 이 프로젝트의 첫 작업을 수행할 수 있다.
> 모르는 것이 있으면 파일을 직접 열어서 확인할 것. 이 문서가 유일한 진실의 원천은 아니다.

---

## 1. 프로젝트 미션 (1분 요약)

**master-of-hwp** 는 한국 공공/교육 영역에서 사실상 표준인 한컴 HWP/HWPX 문서를 AI가 **원본 포맷 그대로 안전하게 편집**할 수 있게 해주는 **오픈소스 플랫폼**이다. 콘텐츠 앱이 아니라 인프라를 지향한다.

- 상태: **v0.0.x (Phase 0)**, 실험적. API 파괴적 변경 허용.
- 팀: 솔로 개발자 + Claude Code + Codex (지금 읽는 당신) 공동작업.
- 핵심 가치: **Round-trip fidelity**(열고 저장해도 구조 훼손 없음) — 측정 가능한 계약.

## 2. 지금 있는 것

### 저장소 구조 (상위)
```
master-of-hwp/
├── master_of_hwp/              # ⭐ Python Core API 패키지 (현재 포커스)
│   ├── core/                   # HwpDocument, SourceFormat
│   ├── operations/             # 편집 연산 (아직 비어있음)
│   ├── ai/                     # 자연어 → EditIntent 파서
│   ├── fidelity/               # 왕복 재현율 측정
│   └── adapters/               # 외부 엔진 브리지 (여기가 당신이 건드릴 곳)
├── tests/                      # pytest (현재 27개 통과)
│   ├── unit/
│   └── fidelity/
├── vendor/rhwp-main/           # 기존 Rust/WASM 파서 (참고용)
├── mcp-server/                 # FastMCP 서버 (Layer 1 Core로 이관 중)
├── samples/                    # HWP/HWPX 샘플 파일
├── docs/
│   ├── ROADMAP.md              # 반드시 읽기
│   ├── ARCHITECTURE.md         # 반드시 읽기
│   └── CODEX_COLLABORATION.md  # 공동작업 규칙
├── handoff/
│   └── codex/
│       ├── ONBOARDING.md       # ← 지금 읽는 이 파일
│       └── 001_*.md            # ← 지금 수행할 작업
├── pyproject.toml
└── README.md
```

### 기술 스택
- Python 3.11+ (엄격)
- pytest + hypothesis
- ruff + black + mypy
- hatchling 빌드 백엔드

## 3. 코딩 규칙 (엄수)

1. **타입 힌트 100%**: 공개 함수 파라미터와 반환 타입 필수
2. **Docstring 100%**: 공개 심볼은 모두 설명 포함
3. **`from __future__ import annotations`** 파일 상단에
4. **불변성**: `@dataclass(frozen=True)` 우선, mutation 지양
5. **커스텀 예외**: 빈 문자열 raise 금지, 맥락 포함
6. **print 금지**: 로깅이 필요하면 `logging` 모듈
7. **파일은 작게**: 400줄 이하 권장, 800 최대
8. **함수는 짧게**: 50줄 이하

### Lint / 포맷 (커밋 전 반드시)
```bash
ruff check master_of_hwp tests
black --check master_of_hwp tests
```

### 테스트 실행
```bash
# 의존성 설치 (최초 1회)
python3.11 -m venv .venv
.venv/bin/pip install -e ".[dev]"

# 전체 테스트
.venv/bin/pytest tests/ -q

# 단위 테스트만
.venv/bin/pytest -m unit -q
```

## 4. 공동작업 프로토콜 (핵심만)

- **Claude Code**와 병렬 작업. 같은 파일 동시 편집 금지.
- 당신(Codex)이 수행할 작업은 `handoff/codex/` 안의 `status: pending` 파일.
- 작업 완료 시:
  1. 파일을 `handoff/codex/done/`으로 이동
  2. 커밋
  3. `handoff/review/` 에 리뷰 요청 파일 생성 (선택이지만 권장)
- 자세한 건 `docs/CODEX_COLLABORATION.md`

## 5. ⭐ 지금 수행할 작업

**파일**: `handoff/codex/001_hwp_binary_parser_spike.md`

**한 줄 요약**: HWP 5.0 바이너리 포맷에서 섹션 개수를 세는 최소 파서를 `master_of_hwp/adapters/hwp5_reader.py`에 구현.

**왜**: Core API가 현재 파일을 바이트로만 읽는다. 구조에 접근하는 첫 다리를 놓는다. Claude Code가 후속으로 이것을 `HwpDocument.sections_count` 속성에 통합할 예정이다.

**인수 기준 (요약)**:
- `count_sections(raw_bytes: bytes) -> int` 함수
- `Hwp5FormatError` 커스텀 예외
- 최소 3개의 단위 테스트
- 기존 27개 테스트 전부 유지 통과
- ruff / black 통과

**허용 의존성**: `olefile` (pure Python CFBF 리더)를 `pyproject.toml`의 dependencies에 추가해도 좋다.

**참고 구현**:
- `vendor/rhwp-main/` (Rust 파서 — 로직 참고)
- HWP 5.0 스펙 (CFBF 기반): BodyText 스토리지 아래 Section0, Section1, ... 스트림

## 6. 완료 정의 (Definition of Done)

- [ ] `master_of_hwp/adapters/hwp5_reader.py` 존재, 공개 API 문서화
- [ ] `tests/unit/test_hwp5_reader.py` 신설, 3개 이상 케이스
- [ ] `.venv/bin/pytest tests/ -q` → 30개 이상 통과, 실패 0
- [ ] `ruff check master_of_hwp tests` → 경고 0
- [ ] `black --check master_of_hwp tests` → diff 0
- [ ] `handoff/codex/001_*.md` → `handoff/codex/done/` 로 이동
- [ ] Git 커밋 메시지: `feat(adapters): add minimal HWP 5.0 section counter (spike #001)`

## 7. 막혔을 때

- 스펙이 모호 → `handoff/codex/001_*.md` 원본을 다시 읽기
- 테스트가 플레이키 → `samples/` 누락 가능성 확인, `pytest.skip` 허용
- 아키텍처 판단 필요 → `docs/ARCHITECTURE.md` 확인, 그래도 불명확하면 작업을 **blocked** 상태로 표시하고 그 이유를 파일 상단에 기록한 뒤 중단 — Claude가 이어받는다

## 8. 하지 말 것

- ❌ 에디터 (`vendor/rhwp-main/rhwp-studio/`) 변경 — Feature Freeze
- ❌ `mcp-server/` 변경 — 향후 Core API 어댑터가 될 영역, 현재 건드리지 말 것
- ❌ `README.md` 프로젝트 설명 변경
- ❌ 새 최상위 디렉토리 추가
- ❌ 테스트를 스킵으로만 처리 (실제 검증 회피)
- ❌ 전역 상태/싱글톤 도입

## 9. 환영사

이 프로젝트는 "이전에 없던 것을 만드는 것"이 사명이다. 한국 생태계의 고유한 문서 포맷에 AI 접근성을 오픈소스로 열어주는 일이다. 당신의 작업이 인프라의 첫 층을 얹는다. **정확하고, 검증 가능하고, 작게**.

---

**시작하려면**: `handoff/codex/001_hwp_binary_parser_spike.md`를 지금 열어라.
