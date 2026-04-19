from __future__ import annotations

import json
import subprocess
from typing import TypedDict


class ClaudeRunResult(TypedDict):
    ok: bool
    raw_text: str
    structured: dict[str, object]


class ClaudeWrapperError(Exception):
    """Raised when Claude CLI execution fails or returns invalid output."""


def run_claude_json(prompt: str) -> ClaudeRunResult:
    command = [
        "claude",
        "-p",
        "--output-format",
        "json",
        "--permission-mode",
        "bypassPermissions",
        prompt,
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        stderr = result.stderr.strip() or "no stderr provided"
        raise ClaudeWrapperError(f"claude cli failed: {stderr}")

    stdout = result.stdout.strip()
    if not stdout:
        raise ClaudeWrapperError("claude cli returned empty output")

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise ClaudeWrapperError(f"claude cli returned invalid JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise ClaudeWrapperError("claude cli returned a non-object payload")

    raw_text = str(payload.get("result", "")).strip()
    if not raw_text:
        raise ClaudeWrapperError("claude cli JSON did not include a result field")

    try:
        structured = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ClaudeWrapperError(
            f"claude result was not valid JSON as instructed: {exc}; raw={raw_text[:300]}"
        ) from exc

    if not isinstance(structured, dict):
        raise ClaudeWrapperError("claude result JSON was not an object")

    return {
        "ok": True,
        "raw_text": raw_text,
        "structured": structured,
    }
