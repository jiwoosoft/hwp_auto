#!/usr/bin/env node
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve, extname, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

function failAndExit(errorCode, message, extra = {}) {
  process.stderr.write(JSON.stringify({ ok: false, error_code: errorCode, message, ...extra }));
  process.exit(1);
}

const args = process.argv.slice(2);
if (args.length < 2) {
  failAndExit('BRIDGE_USAGE', 'usage: rhwp_save <input> <output> [--ops-json=/path/to/ops.json]');
}

const inputPathArg = args[0];
const outputPathArg = args[1];
const opsArg = args.find((arg) => arg.startsWith('--ops-json='));
const opsPathArg = opsArg ? opsArg.slice('--ops-json='.length) : '';

const HERE = dirname(fileURLToPath(import.meta.url));
const WASM_PATH = resolve(HERE, 'node_modules/@rhwp/core/rhwp_bg.wasm');

globalThis.measureTextWidth = (_font, text) => (text?.length ?? 0) * 8;

async function loadRhwp() {
  let wasmBytes;
  try {
    wasmBytes = readFileSync(WASM_PATH);
  } catch (err) {
    failAndExit(
      'BRIDGE_WASM_MISSING',
      `Could not read @rhwp/core wasm at ${WASM_PATH}. Run npm install inside mcp-server/bridges.`,
      { cause: String(err?.message ?? err) },
    );
  }

  const mod = await import('@rhwp/core');
  if (typeof mod.initSync === 'function') {
    mod.initSync({ module: wasmBytes });
  } else {
    await mod.default({ module_or_path: wasmBytes });
  }
  return mod;
}

function parseOps(opsPath) {
  if (!opsPath) return [];
  try {
    const raw = readFileSync(resolve(opsPath), 'utf8');
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch (err) {
    failAndExit('BRIDGE_OPS_READ_FAILED', `Cannot read ops JSON from ${opsPath}`, {
      cause: String(err?.message ?? err),
    });
  }
}

function toInt(value, defaultValue = 0) {
  return Number.isInteger(value) ? value : defaultValue;
}

function applyOperations(doc, ops) {
  for (const op of ops) {
    const type = String(op?.type || '');
    const sectionIndex = toInt(op?.section_index, 0);
    const paraIndex = toInt(op?.para_index, 0);
    if (type === 'replace_paragraph_text') {
      const currentLength = doc.getParagraphLength(sectionIndex, paraIndex);
      const result = JSON.parse(doc.replaceText(sectionIndex, paraIndex, 0, currentLength, String(op?.new_text || '')));
      if (!result?.ok) {
        failAndExit('BRIDGE_REPLACE_FAILED', 'replace_paragraph_text failed during save replay', { op, result });
      }
      continue;
    }
    if (type === 'insert_paragraph_after') {
      const currentLength = doc.getParagraphLength(sectionIndex, paraIndex);
      const result = JSON.parse(doc.insertText(sectionIndex, paraIndex, currentLength, `\n\n${String(op?.new_text || '')}`));
      if (!result?.ok) {
        failAndExit('BRIDGE_INSERT_FAILED', 'insert_paragraph_after failed during save replay', { op, result });
      }
      continue;
    }
    if (type === 'create_table') {
      const currentLength = doc.getParagraphLength(sectionIndex, paraIndex);
      const result = JSON.parse(doc.createTable(sectionIndex, paraIndex, currentLength, toInt(op?.row_count, 1), toInt(op?.col_count, 1)));
      if (!result?.ok) {
        failAndExit('BRIDGE_CREATE_TABLE_FAILED', 'create_table failed during save replay', { op, result });
      }
      continue;
    }
    failAndExit('BRIDGE_UNKNOWN_OP', `Unsupported operation type: ${type}`, { op });
  }
}

async function main() {
  const inputPath = resolve(inputPathArg);
  const outputPath = resolve(outputPathArg);
  const outputExt = extname(outputPath).slice(1).toLowerCase();
  if (outputExt !== 'hwp' && outputExt !== 'hwpx') {
    failAndExit('BRIDGE_UNSUPPORTED_OUTPUT', `Only .hwp or .hwpx output is supported. Got: ${outputExt || 'unknown'}`);
  }

  const mod = await loadRhwp();
  const ops = parseOps(opsPathArg);

  if (!ops.length && extname(inputPath).toLowerCase() === '.txt') {
    let text;
    try {
      text = readFileSync(inputPath, 'utf8');
    } catch (err) {
      failAndExit('BRIDGE_INPUT_READ_FAILED', `Cannot read ${inputPath}`, {
        cause: String(err?.message ?? err),
      });
    }
    let doc;
    try {
      doc = mod.HwpDocument.createEmpty();
      doc.createBlankDocument();
      const insertResult = JSON.parse(doc.insertText(0, 0, 0, text));
      if (!insertResult.ok) {
        failAndExit('BRIDGE_INSERT_FAILED', 'Failed to insert text into blank HWP document', { insertResult });
      }
      const bytes = outputExt === 'hwp' ? doc.exportHwp() : doc.exportHwpx();
      writeFileSync(outputPath, bytes);
      process.stdout.write(JSON.stringify({
        ok: true,
        output_path: outputPath,
        output_format: outputExt,
        bytes_len: bytes.length,
        char_count: text.length,
        mode: 'blank-document-text-export',
        note: 'Text content is preserved, but original document formatting and rich structure are not preserved in this phase.',
      }));
      return;
    } catch (err) {
      failAndExit('BRIDGE_SAVE_FAILED', String(err?.message ?? err), { stack: err?.stack });
    } finally {
      doc?.free?.();
    }
  }

  let bytes;
  try {
    bytes = readFileSync(inputPath);
  } catch (err) {
    failAndExit('BRIDGE_INPUT_READ_FAILED', `Cannot read ${inputPath}`, {
      cause: String(err?.message ?? err),
    });
  }

  let doc;
  try {
    doc = new mod.HwpDocument(new Uint8Array(bytes));
    applyOperations(doc, ops);
    const out = outputExt === 'hwp' ? doc.exportHwp() : doc.exportHwpx();
    writeFileSync(outputPath, out);
    process.stdout.write(JSON.stringify({
      ok: true,
      output_path: outputPath,
      output_format: outputExt,
      bytes_len: out.length,
      operation_count: ops.length,
      mode: 'roundtrip-operation-replay',
      note: 'Original document is loaded and recorded operations are replayed before export. Fidelity is improved but not guaranteed for all complex structures yet.',
    }));
  } catch (err) {
    failAndExit('BRIDGE_SAVE_FAILED', String(err?.message ?? err), {
      stack: err?.stack,
    });
  } finally {
    doc?.free?.();
  }
}

main().catch((err) => {
  failAndExit('BRIDGE_UNEXPECTED', String(err?.message ?? err), {
    stack: err?.stack,
  });
});
