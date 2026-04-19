# master-of-hwp MCP server

FastMCP server that exposes HWP/HWPX reading and text-level editing tools backed by the `@rhwp/core` WASM runtime through a Node.js bridge.

## Architecture

```
Client (Claude / CLI)
        │ MCP
        ▼
  FastMCP server (Python)         ◄── server.py, tools/*.py
        │
        ▼
  RHWPAdapter (Python)            ◄── adapters/rhwp_adapter.py
        │  subprocess
        ▼
  Node bridge (rhwp_extract.mjs)  ◄── bridges/
        │  WASM
        ▼
  @rhwp/core (Rust → wasm-bindgen)
```

The Python side never links Rust directly: `config.py` builds a `node path/to/rhwp_extract.mjs …` command string and the adapter invokes it via `subprocess`.

## Setup

Python (≥ 3.11):

```bash
python3.13 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/pip install pytest
```

Node bridge (≥ 20):

```bash
cd bridges
npm install
```

## Run

```bash
.venv/bin/python server.py
```

Or register in an MCP-compatible client using the `mcp-server` directory as the working directory.

## Tools (phase 1)

| Tool | Purpose |
|------|---------|
| `health_check` | Server readiness + implemented-tool list |
| `rhwp_integration_status` | Report whether the Node bridge is wired |
| `rhwp_save_status` | Report HWP/HWPX save readiness |
| `open_document` | Load a document and return `document_id` |
| `extract_document_text` | Pull text out of TXT / MD / HWP / HWPX |
| `extract_document_structure` | Editor-friendly outline (sections / paragraphs / tables) |
| `replace_paragraph_text` | Swap one paragraph in an open session |
| `insert_paragraph_after` | Append a paragraph after an anchor index |
| `save_as` | Write the session back to TXT / MD |
| `validate_document` | Confirm a saved file re-opens cleanly |

HWP/HWPX reading uses the bridge. HWP/HWPX saving is tracked separately — see `docs/RHWP_저장_실연동_가이드.md`.

## Configuration

| Env var | Default | Meaning |
|---------|---------|---------|
| `MASTER_OF_HWP_ALLOWED_WORKSPACE` | project root | Paths outside this directory are rejected |
| `RHWP_EXTRACT_COMMAND` | auto-detected (`node bridges/rhwp_extract.mjs …`) | Override to point at a different extractor |

The default command is resolved in `config._default_rhwp_extract_command` when `node` is on `PATH` and the bridge script exists.

## Tests

```bash
.venv/bin/pytest -q tests/
```

HWPX-path tests skip automatically when `node` or `@rhwp/core` WASM are missing.
