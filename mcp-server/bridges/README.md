# rhwp Node Bridge

Node.js ↔ `@rhwp/core` (WASM) bridge that lets the Python MCP adapter read HWP/HWPX files locally.

## Why this exists

`@rhwp/core` is a Rust + WebAssembly viewer/editor published to npm. Cargo is not required on the host — Node ≥ 20 is enough. The Python adapter spawns `node rhwp_extract.mjs <path>` and parses the stdout JSON.

## Setup

```bash
cd mcp-server/bridges
npm install
```

Node ≥ 20 is required (uses `initSync({ module })`, top-level `await`, ESM).

## Scripts

| Command | Purpose |
|---------|---------|
| `npm run extract -- <path>` | Extract text from a single `.hwp` / `.hwpx` file. JSON on stdout, errors on stderr. |
| `npm run smoke` | Round-trip test: create empty doc → insert text → export `.hwpx` → re-read through the extractor. No external fixture required. |

## Contract

`rhwp_extract.mjs` writes exactly one JSON object to stdout:

```json
{
  "ok": true,
  "source_format": "hwpx",
  "section_count": 1,
  "paragraph_count": 1,
  "char_count": 12,
  "truncated": false,
  "text": "안녕 Hello 123",
  "paragraphs": [{ "section": 0, "paragraph": 0, "text": "안녕 Hello 123" }]
}
```

Failures exit non-zero and write `{ "ok": false, "error_code": "...", "message": "..." }` to stderr.

Error codes:

- `BRIDGE_USAGE` — no path given.
- `BRIDGE_WASM_MISSING` — `npm install` has not been run.
- `BRIDGE_UNSUPPORTED_FORMAT` — extension is not `.hwp` / `.hwpx`.
- `BRIDGE_FILE_READ_FAILED` — the file could not be opened.
- `BRIDGE_PARSE_FAILED` — rhwp rejected the bytes.
- `BRIDGE_UNEXPECTED` — everything else.

## Flags

```
node rhwp_extract.mjs <path> [--include-tables=true|false] [--max-chars=N]
```

`--max-chars` truncates the concatenated text payload (paragraphs are still returned intact). `--include-tables` is reserved for future filtering.
