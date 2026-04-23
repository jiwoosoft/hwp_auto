# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## master-of-hwp-studio [0.8.3] - 2026-04-23

### Changed (documentation correction only)

- Corrects the 0.8.2 changelog. The workaround in 0.8.2 is still the right thing
  to ship, but the **diagnosis** in the 0.8.2 entry was wrong.
- The real symptom is **layout escape**, not content loss. After a Rust-level
  round-trip test, all 16 original body paragraphs, the pre-existing 18x2 schedule
  table, and the new 2x2 nested table are all present in the re-parsed bytes.
  What the user saw in Hancom Office ("표 따로 한 장, 텍스트 따로 한 장") is the
  layout engine rendering the new nested table outside its cell, shifting everything
  to separate pages. `master_of_hwp`'s Python `section_texts` accessor happens to
  skip content that sits on a paragraph whose table control has drifted, which is
  what made the 587 → 142 character drop *look* like deletion.
- Flag-level evidence from the nested-table regression test: after export and
  re-parse, our new 2×2 nested table has the same `attr = 0x002A0310` (bit 13 /
  `restrictInPage` = 0) as the original 18×2 schedule table inside the same cell.
  The outer-cell layout issue therefore is **not** caused by a missing
  `restrictInPage` flag — this ruled out the first hypothesis (see
  `docs/upstream-rhwp-issue.md`). A pre-existing `TYPESET_VERIFY: sec0 페이지 수
  차이 (paginator=2, typeset=1)` also shows up on the untouched original file,
  suggesting the discrepancy is in rhwp's layout engine rather than the save path.

### Kept from 0.8.2

- Safety workaround in `studio/master_of_hwp_studio/web/app.js` that intercepts
  "insert table inside cell" requests and routes them to a body-level insertion
  below the outer table. This still prevents the Hancom layout split, so it
  remains the correct user-facing behavior until the upstream rhwp fix lands.
- `patches/rhwp-nested-tables/` recovery set (create/insert Rust edits + WASM
  bindings) retained for the future re-enable.

### Added

- `docs/upstream-rhwp-issue.md` — ready-to-file issue template for
  https://github.com/edwardkim/rhwp that captures the real bug (layout escape,
  not serialization loss), the test evidence, and the patches that introduced
  the nested-table APIs.

## master-of-hwp-studio [0.8.2] - 2026-04-23 (superseded by 0.8.3 correction)

### Fixed

- Adds a studio-level safety patch that stops `createTableInCell` /
  `insertTextInNestedCell` from reaching the editor, instead inserting the
  requested table at body level below the outer table. Prevents the Hancom
  layout split that users saw when saving after a "table inside a cell" edit.

### Known (at the time; corrected in 0.8.3)

- This entry originally described the symptom as "76% content loss"; that was a
  misreading of `master_of_hwp.section_texts` output after the inner table had
  drifted. No content was ever lost; the nested table was rendered in the wrong
  place by the HWP5 layout engine. See 0.8.3 above for the corrected analysis.

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
