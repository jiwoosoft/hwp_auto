# rhwp-nested-tables recovered patches

## Why this folder exists

Between master-of-hwp releases 0.8.0 and 0.8.1, two Rust functions were added to a
local clone of [edwardkim/rhwp](https://github.com/edwardkim/rhwp) to support
"insert a table inside a table cell":

| Function | File |
| --- | --- |
| `create_table_in_cell_native` | `src/document_core/commands/object_ops.rs` |
| `insert_text_in_nested_cell_native` | `src/document_core/commands/text_editing.rs` |
| `createTableInCell` / `insertTextInNestedCell` WASM bindings | `src/wasm_api.rs` |

The original build workspace was `/tmp/rhwp/`, which macOS cleaned up. **The source
was never committed to edwardkim/rhwp and never stored anywhere else.** The compiled
artifacts (`vendor/rhwp-main/pkg/rhwp_bg.wasm` etc.) went into this repo; the source
did not.

The patches here were recovered from Claude Code session transcripts
(`~/.claude/projects/-Users-moon-Desktop-master-of-hwp/*.jsonl`) and are safe to
re-apply on a fresh clone of edwardkim/rhwp.

## Current status (0.8.2)

The recovered functions compile cleanly and the insert operations themselves
produce a correct in-memory IR — but rhwp's HWP5 serializer (`src/serializer/`)
drops outer-cell sibling paragraphs when the cell contains a nested Table control.
Round-trip loses ~76% of a typical teacher template's body content.

Because of that serializer bug, **0.8.2 blocks the nested-table path at the
studio level** (`studio/master_of_hwp_studio/web/app.js` falls back to a
body-level insert below the outer table). These patches are kept here so that,
once upstream rhwp ships a fix, we can re-apply the patches, rebuild WASM, and
re-enable the feature in the studio.

## File format

Each `.json` file is:

```json
{
  "target_path": "src/…",
  "anchor_old_string": "<unique snippet from the target file>",
  "new_string": "<full replacement>",
  "source_transcript_timestamp": "…"
}
```

`anchor_old_string` is a short unique anchor; the new block is inserted by
replacing that anchor. Order matters: apply by filename (00 → 01 → 02 → 03).

## How to re-apply

```bash
# 1. clone rhwp into a build workspace (gitignored in this repo)
git clone https://github.com/edwardkim/rhwp.git vendor/rhwp-src

# 2. apply patches with Python
python3 <<'PY'
import json, pathlib
root = pathlib.Path('vendor/rhwp-src')
for p in sorted(pathlib.Path('patches/rhwp-nested-tables').glob('*.json')):
    spec = json.loads(p.read_text())
    t = root / spec['target_path']
    c = t.read_text()
    assert c.count(spec['anchor_old_string']) == 1, f'ambiguous anchor in {t}'
    t.write_text(c.replace(spec['anchor_old_string'], spec['new_string'], 1))
    print(f'applied {p.name}')
PY

# 3. verify
cd vendor/rhwp-src && cargo check --lib
```

## Upstream tracking

- rhwp repository: https://github.com/edwardkim/rhwp
- Serializer bug to report: outer-cell sibling paragraphs dropped by `export_hwp`
  when a cell paragraph contains a nested `Control::Table`. Evidence +
  minimal repro available in this project's issue tracker.

## Manifest

1. `00-object_ops-2026-04-22T12-27.json` → `src/document_core/commands/object_ops.rs`
   (adds `create_table_in_cell_native`)
2. `01-wasm_api-2026-04-22T12-27.json` → `src/wasm_api.rs`
   (exposes `createTableInCell` via `#[wasm_bindgen]`)
3. `02-text_editing-2026-04-22T15-13.json` → `src/document_core/commands/text_editing.rs`
   (adds `insert_text_in_nested_cell_native`)
4. `03-wasm_api-2026-04-22T15-13.json` → `src/wasm_api.rs`
   (exposes `insertTextInNestedCell` via `#[wasm_bindgen]`)
