from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

MCP_ROOT = Path(__file__).resolve().parent.parent
if str(MCP_ROOT) not in sys.path:
    sys.path.insert(0, str(MCP_ROOT))

BRIDGE_SCRIPT = MCP_ROOT / "bridges" / "rhwp_extract.mjs"
BRIDGE_WASM = MCP_ROOT / "bridges" / "node_modules" / "@rhwp" / "core" / "rhwp_bg.wasm"


def _node_available() -> bool:
    try:
        subprocess.run(
            ["node", "--version"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False
    return BRIDGE_SCRIPT.exists() and BRIDGE_WASM.exists()


@pytest.fixture(scope="session")
def sample_hwpx(tmp_path_factory: pytest.TempPathFactory) -> Path:
    if not _node_available():
        pytest.skip("node or @rhwp/core wasm not available for bridge tests")

    workspace = tmp_path_factory.mktemp("hwpx_fixtures")
    target = workspace / "roundtrip.hwpx"

    generator = r"""
globalThis.measureTextWidth = (_f, t) => (t?.length ?? 0) * 8;
import('@rhwp/core').then(async (mod) => {
  const fs = await import('node:fs');
  const wasm = fs.readFileSync(process.env.WASM_PATH);
  mod.initSync({ module: wasm });
  const doc = mod.HwpDocument.createEmpty();
  JSON.parse(doc.createBlankDocument());
  JSON.parse(doc.insertText(0, 0, 0, process.env.PAYLOAD_TEXT));
  const bytes = doc.exportHwpx();
  fs.writeFileSync(process.env.OUT_PATH, Buffer.from(bytes));
});
"""
    payload_text = "pytest 한글 roundtrip 123"
    subprocess.run(
        ["node", "-e", generator],
        cwd=BRIDGE_SCRIPT.parent,
        env={
            "PATH": __import__("os").environ.get("PATH", ""),
            "WASM_PATH": str(BRIDGE_WASM),
            "OUT_PATH": str(target),
            "PAYLOAD_TEXT": payload_text,
        },
        check=True,
        capture_output=True,
    )
    return target


@pytest.fixture(scope="session")
def sample_hwpx_text() -> str:
    return "pytest 한글 roundtrip 123"
