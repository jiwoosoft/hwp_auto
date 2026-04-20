---
id: 002
from: codex
to: claude
status: pending
created: 2026-04-21
priority: high
---

# Review Request: HWPX Section Counter Spike

## Summary

Codex completed spike `002` for minimal HWPX section counting.

- Added `master_of_hwp/adapters/hwpx_reader.py`
- Implemented `count_sections(raw_bytes: bytes) -> int`
- Added `HwpxFormatError`
- Count logic prefers direct `Contents/sectionN.xml` ZIP entries
- Fallback parses `Contents/content.hpf` manifest/spine when direct section parts are absent
- Added unit tests for empty bytes, non-ZIP bytes, manifest fallback, and real sample file

## Verification

- `.venv/bin/python -c "from master_of_hwp.adapters.hwpx_reader import count_sections, HwpxFormatError"` → passed
- `.venv/bin/ruff check master_of_hwp tests` → passed
- `.venv/bin/black --check master_of_hwp tests` → passed
- `.venv/bin/pytest tests/ -q` → `34 passed, 2 xfailed`

## Review Focus

- Confirm `content.hpf` fallback should prefer `<spine>` counts and then fall back to manifest item counts.
- Confirm `HwpxFormatError` on zero discovered sections matches the same contract as `Hwp5FormatError`.
- Confirm keeping `master_of_hwp.adapters.__init__` untouched remains correct for the follow-up integration task.
