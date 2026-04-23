# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## master-of-hwp-studio [0.8.2] - 2026-04-23

### Fixed

- **Nested-table content loss (CRITICAL data-safety fix)**: 0.8.0/0.8.1 "table inside a cell"
  (`createTableInCell` + `insertTextInNestedCell`) triggered an `export_hwp` serialization bug
  that dropped ~76% of the outer document's body content on save. Verified against a teacher
  template (`가정통신_20260421233205.hwp`): 587 characters → 142 characters after round-trip.
- Root cause is in rhwp's Rust HWP5 serializer (`src/serializer/body_text.rs` /
  `src/serializer/control.rs`), not in this project. While the insert operations succeed
  at the IR level (verified with `insert_text_in_nested_cell_native` returning `ok:true`
  for every cell and `export_hwp_verify recovered:true`), the on-disk bytes lose
  outer-cell sibling paragraphs.
- Interim safety patch: `studio/master_of_hwp_studio/web/app.js` now intercepts any
  "insert table inside cell" request and routes it to a **body-level insertion** just
  below the outer table. The user sees a one-line notice: `⚠ 셀 안에 표를 넣으면 저장 시 본문이
  대량 손실되는 문제가 있어, 외부 표 바로 아래에 삽입합니다.`
- HWPX export was also evaluated as a workaround but produces files Hancom Office flags as
  corrupted (empty `<hs:sec>` — zero tables and zero `<hp:t>` fragments), so it is not used.

### Added

- `patches/rhwp-nested-tables/` — 4 recovered Rust edits (`create_table_in_cell_native`,
  `insert_text_in_nested_cell_native`, and their WASM bindings) extracted from prior Claude
  Code session transcripts after the original `/tmp/rhwp/` build workspace was lost. Kept
  for the future upstream PR against edwardkim/rhwp and for local re-application when the
  serializer bug is fixed.

### Known Limitations

- Creating a nested table ("셀 안에 또 표") is temporarily unavailable. Users can still
  insert body-level tables, which round-trip cleanly. Tracking upstream at
  https://github.com/edwardkim/rhwp — will re-enable the feature once the serializer fix
  lands and we rebuild the vendored WASM.

## master-of-hwp-studio [0.2.0] - 2026-04-21

### Added

- **rhwp WYSIWYG editor bundled** — no separate Node.js install needed. `mohwp studio` now starts the bundled editor on `localhost:7700` automatically.
- HTTP API endpoints on the Studio server: `/api/status`, `/api/browse`, `/api/open`, `/api/structure`, `/api/save`, `/api/file-bytes`, `/api/ai/preview`, `/api/ai/apply`
- Help modal (❔ 도움말) with 5-section user guide
- Rebrand: header title "한글의 달인"
- Modern UI polish (glass surfaces, violet/indigo gradient, pulse status, bubble animations)
- `--with-editor / --no-editor` CLI flag

### Fixed

- `/api/file-bytes` returning wrong JSON key caused `atob` error on file open
- rhwp editor: auto-enter cell-selection mode on cross-cell drag

### Acknowledgments

The bundled WYSIWYG editor is based on [edwardkim/rhwp](https://github.com/edwardkim/rhwp). Thank you, @edwardkim.

## master-of-hwp [0.2.0] - 2026-04-21

### Added

- `HwpDocument.plain_text` — format-agnostic concatenation with HWP 5.0 `\r` → `\n` normalization
- `HwpDocument.iter_paragraphs()` — yields `(section_index, paragraph_index, text)` tuples in document order
- `HwpDocument.find_paragraphs(query, regex=, case_sensitive=)` — substring / regex search
- `HwpDocument.summary()` — JSON-serializable structural overview for AI context
- `HwpDocument.replace_table_cell_paragraph(...)` — HWPX table cell paragraph replacement
- `HwpDocument.ai_edit(natural_language_request, provider=, dry_run=, confidence_threshold=)` — natural-language edit pipeline (intent → locate → apply → verify)
- `master_of_hwp.ai.providers` — `LLMProvider` Protocol + `AnthropicProvider` (lazy import, `pip install master-of-hwp[ai]`)
- `master_of_hwp.ai.intent.parse_intent_llm()` — LLM-backed intent parsing with JSON schema
- `master_of_hwp.ai.locator.locate_targets()` — real implementation (find_paragraphs + LLM re-ranking)
- `AIEditResult` dataclass with `status` / `intent` / `locator` / `new_doc` / `fidelity_report` / `message`
- Hypothesis-based property tests for `replace_paragraph` idempotency and locality

### Changed

- `master_of_hwp.ai` package exports expanded to full pipeline (previously scaffold-only)

### Known Limitations

- HWP 5.0 write path still limited to same-length paragraph replacement (CFBF resize writer pending v0.3)
- Insert / delete paragraph operations not yet available (pending v0.3)
- Table cell editing available for HWPX only; HWP 5.0 raises `NotImplementedError`

## [0.1.0] - 2026-04-21

### Added

- `HwpDocument.open(path)` for `.hwp` and `.hwpx` files
- `HwpDocument.sections_count` to count sections in both formats
- `HwpDocument.section_texts` for plain text per section
- `HwpDocument.section_paragraphs` for paragraph lists per section
- `HwpDocument.section_tables` for nested table data as `[section][table][row][cell][paragraph]`
- `HwpDocument.replace_paragraph(section_index, paragraph_index, new_text)` with full HWPX support and HWP 5.0 same-text no-op support
- `master_of_hwp.fidelity` round-trip fidelity helpers for identity and replace checks
- Strict type hints and mypy-clean API surface on Python 3.11+
- Example scripts for reading sections, extracting tables, and editing a paragraph
- GitHub Actions release workflow for PyPI Trusted Publishing

### Known Limitations

- HWP 5.0 write path does not yet support arbitrary-length paragraph replacement
- Insert and delete paragraph operations are not available yet
- Table cell editing is not available yet
- AI editing loop and provider integration are planned for later releases
