# handoff/

Claude ↔ Codex 공동작업의 파일 기반 전달 채널.

**반드시 [docs/CODEX_COLLABORATION.md](../docs/CODEX_COLLABORATION.md)를 먼저 읽을 것.**

## 디렉토리

- `codex/` — Claude가 Codex에게 요청한 작업
- `claude/` — Codex가 Claude에게 요청한 작업
- `review/` — 상호 리뷰 요청
- `*/done/` — 완료된 작업의 아카이브

## 상태 조회

```bash
# 대기 중 작업
grep -l "status: pending" handoff/**/*.md 2>/dev/null

# 현재 진행 중
grep -l "status: in_progress" handoff/**/*.md 2>/dev/null
```

## 파일 이름 규칙

```
<id:3자리 숫자>_<kebab-case-slug>.md
예: 001_hwp_binary_parser_spike.md
```

ID는 모노톤 증가. 같은 디렉토리 안에서 유일.
