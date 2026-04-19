#!/usr/bin/env node
// Round-trip smoke test for the rhwp bridge.
//
// Creates an empty document in memory, exports to HWPX bytes,
// writes to a temp file, then re-runs the extractor against it.
// This proves the @rhwp/core integration works end-to-end
// without needing an external sample file.

import { mkdtempSync, writeFileSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { resolve, dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

globalThis.measureTextWidth = (_font, text) => (text?.length ?? 0) * 8;

const HERE = dirname(fileURLToPath(import.meta.url));
const WASM_PATH = resolve(HERE, "node_modules/@rhwp/core/rhwp_bg.wasm");

async function loadRhwp() {
  const wasmBytes = readFileSync(WASM_PATH);
  const mod = await import("@rhwp/core");
  if (typeof mod.initSync === "function") {
    mod.initSync({ module: wasmBytes });
  } else {
    await mod.default({ module_or_path: wasmBytes });
  }
  return mod;
}

function die(message) {
  console.error(`SMOKE FAIL: ${message}`);
  process.exit(1);
}

async function main() {
  const { HwpDocument } = await loadRhwp();

  const doc = HwpDocument.createEmpty();
  const blankMeta = JSON.parse(doc.createBlankDocument());
  if (!blankMeta.sectionCount || blankMeta.sectionCount < 1) {
    die(`createBlankDocument returned no sections: ${JSON.stringify(blankMeta)}`);
  }

  const expected = "안녕 Hello 123";
  const insertResult = JSON.parse(doc.insertText(0, 0, 0, expected));
  if (!insertResult.ok) die(`insertText failed: ${JSON.stringify(insertResult)}`);

  const sectionCount = doc.getSectionCount();
  if (sectionCount < 1) die(`expected >=1 section after blank+insert, got ${sectionCount}`);

  const hwpxBytes = doc.exportHwpx();
  if (!hwpxBytes || hwpxBytes.byteLength < 100) {
    die(`exportHwpx returned suspiciously small payload: ${hwpxBytes?.byteLength}`);
  }

  const tmp = mkdtempSync(join(tmpdir(), "master-of-hwp-smoke-"));
  const hwpxPath = join(tmp, "empty.hwpx");
  writeFileSync(hwpxPath, Buffer.from(hwpxBytes));

  const extractor = resolve(HERE, "rhwp_extract.mjs");
  const run = spawnSync(process.execPath, [extractor, hwpxPath], {
    encoding: "utf-8",
  });

  if (run.status !== 0) {
    rmSync(tmp, { recursive: true, force: true });
    die(`extractor exited ${run.status}: ${run.stderr}`);
  }

  let parsed;
  try {
    parsed = JSON.parse(run.stdout);
  } catch (err) {
    rmSync(tmp, { recursive: true, force: true });
    die(`could not parse extractor stdout: ${err}\n---\n${run.stdout}`);
  }
  rmSync(tmp, { recursive: true, force: true });

  if (!parsed.ok) die(`extractor returned ok=false: ${JSON.stringify(parsed)}`);
  if (parsed.source_format !== "hwpx") die(`unexpected source_format: ${parsed.source_format}`);
  if (typeof parsed.text !== "string") die(`text missing from output: ${JSON.stringify(parsed)}`);
  if (!parsed.text.includes(expected)) {
    die(`extracted text missing "${expected}": got "${parsed.text}"`);
  }

  console.log(
    JSON.stringify(
      {
        ok: true,
        sections: parsed.section_count,
        paragraphs: parsed.paragraph_count,
        chars: parsed.char_count,
        sample: parsed.text.slice(0, 80),
      },
      null,
      2,
    ),
  );
}

main().catch((err) => die(String(err?.stack ?? err)));
