from __future__ import annotations

import json
import subprocess
from typing import TypedDict


class OpenCodeRunResult(TypedDict):
    ok: bool
    raw_text: str
    structured: dict[str, object]


class OpenCodeWrapperError(Exception):
    """Raised when OpenCode CLI execution fails or returns invalid output."""


def run_opencode_json(prompt: str, *, workdir: str) -> OpenCodeRunResult:
    command = [
        'opencode',
        'run',
        '--format',
        'json',
        '--dir',
        workdir,
        prompt,
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0 and not result.stdout.strip():
        stderr = result.stderr.strip() or 'no stderr provided'
        raise OpenCodeWrapperError(f'opencode cli failed: {stderr}')

    parsed = _parse_last_event(result.stdout)
    if parsed is None:
        stderr = result.stderr.strip() or 'no stdout returned'
        raise OpenCodeWrapperError(f'opencode cli returned no parsable JSON event: {stderr}')

    if parsed.get('type') == 'error':
        error = parsed.get('error')
        if isinstance(error, dict):
            message = str(error.get('data', {}).get('message') or error.get('message') or 'opencode cli error')
        else:
            message = 'opencode cli error'
        raise OpenCodeWrapperError(message)

    raw_text = str(parsed.get('text', '')).strip()
    if not raw_text:
        raise OpenCodeWrapperError('opencode cli did not return a structured final message')
    try:
        structured = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise OpenCodeWrapperError(
            f'opencode result was not valid JSON as instructed: {exc}; raw={raw_text[:300]}'
        ) from exc
    if not isinstance(structured, dict):
        raise OpenCodeWrapperError('opencode result JSON was not an object')
    return {'ok': True, 'raw_text': raw_text, 'structured': structured}


def _parse_last_event(stdout: str) -> dict[str, object] | None:
    last = None
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            last = payload
    return last
