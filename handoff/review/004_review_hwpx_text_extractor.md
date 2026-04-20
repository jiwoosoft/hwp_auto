---
id: 004
from: codex
to: claude
status: pending
created: 2026-04-21
priority: high
---

# Review Request: HWPX Section Text Extractor Spike

## Verification

- `.venv/bin/ruff check master_of_hwp tests` → passed
- `.venv/bin/black --check master_of_hwp tests` → passed
- `.venv/bin/mypy master_of_hwp` → passed
- `.venv/bin/pytest tests/ -q` → `41 passed`

## Summary

Codex completed spike `004` for HWPX section text extraction.

- Added `extract_section_texts(raw_bytes: bytes) -> list[str]` to `master_of_hwp/adapters/hwpx_reader.py`
- Reused `HwpxFormatError` for malformed ZIP, manifest, missing part, and bad section XML cases
- Reads `Contents/sectionN.xml` in ascending section index order
- Falls back to `content.hpf` spine/manifest ordering when direct section entries are not discoverable
- Ignores namespaces and extracts text from elements whose local name is `t`
- Joins text runs within the same paragraph and separates paragraphs with `\n`
- Preserves the invariant `len(extract_section_texts(raw_bytes)) == count_sections(raw_bytes)` when returning successfully

## Review Focus

- Confirm the current paragraph boundary rule (`<p>` => `\n`) matches the intended `HwpDocument.section_texts` plain-text contract.
- Confirm fallback ordering via OPF spine first, manifest second, is the right behavior for malformed-but-readable HWPX containers.
- Confirm no additional normalization should happen yet for duplicate blank paragraphs visible in the sample output.
