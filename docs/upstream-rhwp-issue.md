# Upstream rhwp issue draft — nested-table layout escape on save

**Target:** https://github.com/edwardkim/rhwp/issues
**From:** master-of-hwp-studio (downstream user)
**Status:** ready to file — copy the body below verbatim

---

## Title

Nested table (table inside a table cell) drifts out of its outer cell when
saved via `export_hwp` and re-opened in Hancom Office

## Body

### Summary

When a new nested table is created inside an outer cell via
`create_table_in_cell_native` and the document is then saved with
`export_hwp`, Hancom Office renders the inner table **outside** the outer
cell, pushing the outer cell's body content onto a separate page. In the
rhwp editor itself the layout looks correct, so the issue is limited to the
HWP5 save → Hancom re-open path.

A pre-existing nested table loaded from a teacher's template (an 18×2 form
table already living inside the same outer cell) does **not** drift. Only
newly created ones do. After export + re-parse, the new table's
`attr = 0x002A0310` matches the pre-existing one byte-for-byte (including
`restrictInPage = 0`), so the flag-based hypotheses (restrictInPage /
treatAsChar / wrap mode) are already ruled out.

### Environment

- rhwp: main @ `bea635bd708274a51ae3f557a71b07683d7c2454`
  (plus the two patches described in "Missing upstream API" below)
- Native build: `cargo check --lib` clean, no warnings
- Reproduction sample: a Korean school "가정통신문" HWP5 template whose
  section 0, paragraph 0, control 3 is a 1×1 "page frame" table. Its single
  cell already contains 16 paragraphs (title, body, footer) and a nested
  18×2 form table at `cell.paragraphs[12]`.

### Steps to reproduce

```rust
use rhwp::DocumentCore;

let bytes = std::fs::read("samples/ga_test_origin.hwp").unwrap();
let mut core = DocumentCore::from_bytes(&bytes).unwrap();

// Insert a 2×2 nested table at the empty spacer paragraph (cell_para = 1)
core.create_table_in_cell_native(
    /*section*/ 0,
    /*parent_para*/ 0,
    /*control*/ 3,
    /*cell*/ 0,
    /*cell_para*/ 1,
    /*char_offset*/ 0,
    /*rows*/ 2,
    /*cols*/ 2,
).unwrap();

// Fill each inner cell (optional — reproduces even without text)
let cells = [("헤더1", 0), ("헤더2", 1), ("값1", 2), ("값2", 3)];
for (txt, inner_cell_idx) in cells {
    core.insert_text_in_nested_cell_native(
        0, 0, 3, 0, 1, 0, inner_cell_idx, 0, 0, txt,
    ).unwrap();
}

let saved = core.export_hwp_native().unwrap();
std::fs::write("out.hwp", saved).unwrap();
```

Open `out.hwp` in Hancom Office 2022/2024. Expected: the new 2×2 table
stays inside the outer cell. Actual: the new 2×2 appears as a standalone
block and the outer cell's body text is split across two pages.

### Evidence

1. **IR round-trip is lossless.** Reloading `out.hwp` with rhwp shows all
   17 paragraphs of the outer cell intact (original 16 + one empty spacer
   added by `create_table_in_cell_native`), both the pre-existing 18×2
   table and the new 2×2 table present, and every character of the body
   text preserved.

2. **Identical flags to the working pre-existing inner table.** After
   round-trip:

   | | Pre-existing 18×2 (works) | New 2×2 (drifts) |
   |---|---|---|
   | `attr` | `0x002A0310` | `0x002A0310` |
   | `raw_ctrl_data[0..4]` | `10 03 2A 00` | `10 03 2A 00` |
   | `restrictInPage` (bit 13) | 0 | 0 |
   | `treatAsChar` | false | false |
   | `text_wrap` | `TopAndBottom` | `TopAndBottom` |
   | `vert_rel_to` / `horz_rel_to` | `Para` / `Para` | `Para` / `Para` |
   | outer margins | 283/283/283/283 HU | 283/283/283/283 HU |

   Only `raw_ctrl_data[16..20]` (height, correctly proportional to row
   count) and `raw_ctrl_data[32..36]` (instance-id hash) differ.

3. **Paragraph-level metadata also matches.** The container paragraph for
   the new table has the same `control_mask = 0x00000800`, same
   `para_shape_id = 25`, same `raw_header_extra = [01,00,00,00,01,00,00,00,00,00]`,
   same line-seg shape, etc. as the paragraph holding the pre-existing 18×2.
   Only `char_count_msb` differs (`true` on the new, `false` on the
   original), and the serializer overrides that based on position anyway.

4. **Layout engine disagreement pre-exists.** Running
   `roundtrip_without_edit_preserves_content` (no edits, just
   `DocumentCore::from_bytes` → `export_hwp_native` → `from_bytes`)
   already emits:

   ```
   TYPESET_VERIFY: sec0 페이지 수 차이 (paginator=2, typeset=1)
   ```

   The same message appears on the file we saved after our edits. This
   suggests the paginator/typeset mismatch is structural in the layout
   engine and is independent of the save path.

### Where we looked (ruled out)

- `src/serializer/control.rs::serialize_table` uses `table.raw_ctrl_data`
  verbatim when non-empty, so in-memory `table.attr` is actually ignored at
  write time. The bytes on disk for our new table match the pre-existing
  one flag-for-flag.
- `src/serializer/body_text.rs` recurses correctly: `serialize_paragraph_list`
  → `serialize_paragraph_with_msb` → `serialize_control(Control::Table)` →
  `serialize_table` → `serialize_cell` → `serialize_paragraph_list` again.
  Paragraph counts round-trip exactly.
- `exportHwpVerify` reports `recovered: true` with matching pageCount in
  the studio console.

### Where we think the bug lives

Because the flags and paragraph structure are identical after round-trip
but Hancom still treats the two tables differently, we suspect **the HWP5
layout engine (paginator / typeset)** is computing the outer cell's
available height without accounting for the newly inserted inner table's
reserved space, which drives Hancom to treat the new table as floating and
the outer cell as overflowing. The pre-existing `paginator=2 / typeset=1`
discrepancy on the untouched file points at the same area.

A likely fix path: when `create_table_in_cell_native` inserts a Table
control into a cell paragraph, re-measure the outer cell height and invoke
the same repagination path that Hancom's loader uses, so that the on-disk
`cell.height` reflects the nested content's real vertical footprint.

### Recovered Rust source for the missing APIs

Both `create_table_in_cell_native` and `insert_text_in_nested_cell_native`
were written in a local `/tmp/rhwp/` workspace that was lost to macOS's
`/tmp` cleanup before the Rust source could be committed upstream. The
source has since been recovered from Claude Code session transcripts and
is available as four apply-ready JSON patches in the downstream repo:

- `patches/rhwp-nested-tables/00-object_ops-...json`
  → `src/document_core/commands/object_ops.rs::create_table_in_cell_native`
- `patches/rhwp-nested-tables/01-wasm_api-...json`
  → `src/wasm_api.rs::create_table_in_cell` (`#[wasm_bindgen]`)
- `patches/rhwp-nested-tables/02-text_editing-...json`
  → `src/document_core/commands/text_editing.rs::insert_text_in_nested_cell_native`
- `patches/rhwp-nested-tables/03-wasm_api-...json`
  → `src/wasm_api.rs::insert_text_in_nested_cell` (`#[wasm_bindgen]`)

Repo: https://github.com/reallygood83/master-of-hwp —
`patches/rhwp-nested-tables/README.md` has the application script. Happy
to open a PR against `devel` with these four patches and a regression
test (see `vendor/rhwp-src/tests/nested_table_roundtrip.rs` in the same
downstream repo, currently gitignored as it lives in the local build
workspace) if that is useful.

### Downstream mitigation

Until this is fixed, master-of-hwp-studio 0.8.2+ intercepts the
"insert table inside cell" path at the app.js level and falls back to
inserting a body-level table below the outer table, which avoids the
layout escape. Users see a one-line notice explaining the fallback.

### Attachments

- `samples/ga_test_origin.hwp` — 120 KB reproduction file
- `out.hwp` — the broken save produced by the reproduction above
- Rust test code: `tests/nested_table_roundtrip.rs`
