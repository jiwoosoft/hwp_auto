#!/usr/bin/env node
// Text extractor bridge for @rhwp/core.
//
// Usage:
//   node rhwp_extract.mjs <path-to-hwp-or-hwpx> [--include-tables=true|false] [--max-chars=N]
//
// Contract:
//   stdout: single JSON object with keys {ok, text, char_count, truncated,
//           source_format, section_count, paragraph_count, paragraphs, tables}
//   stderr: single JSON object on failure {ok:false, error_code, message}
//   exit:   0 on success, non-zero otherwise.
//
// The Python adapter reads the stdout JSON and re-wraps it in its own tool response.

import { readFileSync } from "node:fs";
import { resolve, dirname, extname } from "node:path";
import { fileURLToPath } from "node:url";

// rhwp's pagination path calls globalThis.measureTextWidth for layout.
// We only extract text, so a cheap heuristic is enough to avoid crashes.
globalThis.measureTextWidth = (_font, text) => (text?.length ?? 0) * 8;

const HERE = dirname(fileURLToPath(import.meta.url));
const WASM_PATH = resolve(HERE, "node_modules/@rhwp/core/rhwp_bg.wasm");

function failAndExit(errorCode, message, extra = {}) {
  process.stderr.write(
    JSON.stringify({ ok: false, error_code: errorCode, message, ...extra }),
  );
  process.exit(1);
}

function parseArgs(argv) {
  if (argv.length < 1) {
    failAndExit(
      "BRIDGE_USAGE",
      "usage: rhwp_extract <path> [--include-tables=true|false] [--max-chars=N]",
    );
  }
  const options = { path: argv[0], includeTables: true, maxChars: 50_000 };
  for (const raw of argv.slice(1)) {
    const [key, value] = raw.split("=", 2);
    if (key === "--include-tables") {
      options.includeTables = value !== "false";
    } else if (key === "--max-chars") {
      const parsed = Number.parseInt(value, 10);
      if (Number.isFinite(parsed) && parsed > 0) options.maxChars = parsed;
    }
  }
  return options;
}

async function loadRhwp() {
  let wasmBytes;
  try {
    wasmBytes = readFileSync(WASM_PATH);
  } catch (err) {
    failAndExit(
      "BRIDGE_WASM_MISSING",
      `Could not read @rhwp/core wasm at ${WASM_PATH}. Run "npm install" inside mcp-server/bridges.`,
      { cause: String(err?.message ?? err) },
    );
  }
  const mod = await import("@rhwp/core");
  // Prefer initSync — deterministic and avoids fetch in Node.
  if (typeof mod.initSync === "function") {
    mod.initSync({ module: wasmBytes });
  } else {
    await mod.default({ module_or_path: wasmBytes });
  }
  return mod;
}

function extractParagraphs(doc, { includeTables }) {
  const sectionCount = doc.getSectionCount();
  const paragraphs = [];
  for (let s = 0; s < sectionCount; s++) {
    const paraCount = doc.getParagraphCount(s);
    for (let p = 0; p < paraCount; p++) {
      const length = doc.getParagraphLength(s, p);
      const text = length > 0 ? doc.getTextRange(s, p, 0, length) : "";
      paragraphs.push({ section: s, paragraph: p, text });
    }
  }
  // Table text is already included in paragraph structure via rhwp's model.
  // includeTables=false is reserved for future filtering; we keep the flag for API stability.
  void includeTables;
  return { sectionCount, paragraphs };
}

function extractTables(doc) {
  const tables = [];
  const pageCount = doc.pageCount();
  for (let page = 0; page < pageCount; page++) {
    let layout;
    try {
      layout = JSON.parse(doc.getPageControlLayout(page));
    } catch {
      continue;
    }
    const controls = Array.isArray(layout?.controls) ? layout.controls : [];
    for (const control of controls) {
      if (control?.type !== 'table') continue;
      tables.push({
        pageIndex: page,
        section: Number.isInteger(control.secIdx) ? control.secIdx : 0,
        paragraph: Number.isInteger(control.paraIdx) ? control.paraIdx : 0,
        controlIndex: Number.isInteger(control.controlIdx) ? control.controlIdx : 0,
        rowCount: Number.isInteger(control.rowCount) ? control.rowCount : 0,
        colCount: Number.isInteger(control.colCount) ? control.colCount : 0,
        cellCount: Array.isArray(control.cells) ? control.cells.length : 0,
        bbox: {
          x: control.x ?? null,
          y: control.y ?? null,
          w: control.w ?? null,
          h: control.h ?? null,
        },
      });
    }
  }
  return tables;
}

async function main() {
  const { path, includeTables, maxChars } = parseArgs(process.argv.slice(2));
  const absolutePath = resolve(path);
  const ext = extname(absolutePath).slice(1).toLowerCase();
  if (ext !== "hwp" && ext !== "hwpx") {
    failAndExit(
      "BRIDGE_UNSUPPORTED_FORMAT",
      `Only .hwp or .hwpx is handled by this bridge. Got: ${ext || "unknown"}`,
    );
  }

  let bytes;
  try {
    bytes = readFileSync(absolutePath);
  } catch (err) {
    failAndExit("BRIDGE_FILE_READ_FAILED", `Cannot read ${absolutePath}`, {
      cause: String(err?.message ?? err),
    });
  }

  const mod = await loadRhwp();
  let doc;
  try {
    doc = new mod.HwpDocument(new Uint8Array(bytes));
  } catch (err) {
    failAndExit("BRIDGE_PARSE_FAILED", `Failed to parse ${ext.toUpperCase()}`, {
      cause: String(err?.message ?? err),
    });
  }

  let result;
  let tables = [];
  try {
    result = extractParagraphs(doc, { includeTables });
    tables = extractTables(doc);
  } finally {
    doc.free?.();
  }

  const joined = result.paragraphs.map((p) => p.text).join("\n");
  const truncated = joined.length > maxChars;
  const text = truncated ? joined.slice(0, maxChars) : joined;

  process.stdout.write(
    JSON.stringify({
      ok: true,
      source_format: ext,
      section_count: result.sectionCount,
      paragraph_count: result.paragraphs.length,
      table_count: tables.length,
      char_count: joined.length,
      truncated,
      text,
      paragraphs: result.paragraphs,
      tables,
    }),
  );
}

main().catch((err) => {
  failAndExit("BRIDGE_UNEXPECTED", String(err?.message ?? err), {
    stack: err?.stack,
  });
});
