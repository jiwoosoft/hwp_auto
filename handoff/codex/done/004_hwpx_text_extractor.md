---
id: 004
from: claude
to: codex
status: done
created: 2026-04-21
priority: high
---

# HWPX 섹션 텍스트 추출 스파이크

## 배경 / 진행 상태

- #001 HWP5 섹션 카운트 ✅
- #002 HWPX 섹션 카운트 ✅
- #003 HWP5 섹션 **텍스트** 추출 ✅
- #004 **이 작업** — HWPX 섹션 **텍스트** 추출

이것만 끝나면 `HwpDocument.section_texts`가 두 포맷 모두에서 동작합니다.

## 목적

HWPX (OOXML/ZIP) 의 `Contents/sectionN.xml` 에서 **평문 텍스트만 추출**.

## In-Scope

1. `master_of_hwp/adapters/hwpx_reader.py` 에 함수 추가:
   ```python
   def extract_section_texts(raw_bytes: bytes) -> list[str]:
       """Return the plain text of each HWPX section XML part, one string per section."""
   ```

2. 구현 요구사항:
   - ZIP 안의 `Contents/section0.xml`, `section1.xml`, ... 순서대로 읽기 (섹션 인덱스 오름차순 정렬)
   - XML 네임스페이스는 무시하고 **local name이 `t`** 인 모든 요소의 텍스트를 추출 (HWPX 스펙의 `<hp:t>` 요소)
   - 같은 문단 내 여러 `<hp:t>`는 이어붙이고, 문단 경계는 `\n` (HWPX 평문 관례)
   - 반환 길이는 `count_sections(raw_bytes)` 와 정확히 일치

3. 테스트 (`tests/unit/test_hwpx_reader.py`):
   - 빈 바이트 → 기존 `HwpxFormatError`/`ValueError`
   - 실 샘플 (`samples/public-official/table-vpos-01.hwpx`) → 리스트 길이가 `count_sections`와 일치하고, 적어도 하나는 비어있지 않음

## Out-of-Scope

- 서식/표/이미지/주석
- HWP 5.0 쪽 — #003에서 완료됨
- `HwpDocument` 수정 — Claude가 후속 커밋에서 `NotImplementedError` 제거

## 인수 기준

- [ ] `extract_section_texts(raw_bytes)` 구현
- [ ] 반환 길이 == `count_sections(raw_bytes)` 항상
- [ ] 모든 공개 심볼에 타입 힌트 + docstring
- [ ] `ruff`, `black`, `mypy strict`, `pytest` 전부 통과 (현재 38 → 40+ passed)
- [ ] 외부 runtime 의존성 추가 금지 — stdlib `zipfile` + `xml.etree.ElementTree` 만

## 구현 힌트 (참고용)

```python
import re
import zipfile
from io import BytesIO
from xml.etree import ElementTree

_SECTION_PART_PATTERN = re.compile(r"Contents/section(\d+)\.xml", re.IGNORECASE)


def _local_name(tag: str) -> str:
    return tag.rsplit("}", maxsplit=1)[-1]


def extract_section_texts(raw_bytes: bytes) -> list[str]:
    if not raw_bytes:
        raise ValueError("HWPX raw_bytes must not be empty.")
    try:
        with zipfile.ZipFile(BytesIO(raw_bytes)) as archive:
            entries = sorted(
                (
                    (int(m.group(1)), name)
                    for name in archive.namelist()
                    if (m := _SECTION_PART_PATTERN.fullmatch(name))
                ),
                key=lambda pair: pair[0],
            )
            if not entries:
                # fallback to manifest-derived ordering — consider reusing
                # the spine logic from count_sections
                ...
            return [_extract_text_from_section_xml(archive.read(name)) for _, name in entries]
    except zipfile.BadZipFile as exc:
        raise HwpxFormatError(f"Not a valid HWPX (ZIP) container: {exc}") from exc


def _extract_text_from_section_xml(xml_bytes: bytes) -> str:
    try:
        root = ElementTree.fromstring(xml_bytes)
    except ElementTree.ParseError as exc:
        raise HwpxFormatError(f"Invalid section XML: {exc}") from exc
    # Strategy: concat all <t> text in document order, with '\n' between
    # paragraphs (<p> containers).
    ...
```

## 완료 후 할 일

1. `git mv handoff/codex/004_*.md handoff/codex/done/`
2. `handoff/review/004_review_hwpx_text_extractor.md` 생성
3. 커밋: `feat(adapters): add HWPX section text extractor (spike #004)`
4. 트레일러: `Confidence / Scope-risk / Reversibility / Directive / Tested / Not-tested`
5. `git push origin main`

## 스타일 가이드

- `hwpx_reader.py`의 기존 스타일 유지
- 새 예외 만들지 말고 `HwpxFormatError` 재사용
- `_local_name` 등 기존 helper가 있으면 재사용
- Private helper는 `_name` 접두사
