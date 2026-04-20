from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import TypedDict


class CodexRunResult(TypedDict):
    ok: bool
    raw_text: str
    structured: dict[str, object]


class CodexWrapperError(Exception):
    """Raised when Codex CLI execution fails or returns invalid output."""


def run_codex_json(prompt: str, *, workdir: str) -> CodexRunResult:
    schema = {
        'type': 'object',
        'properties': {
            'task_type': {'type': 'string'},
            'title': {'type': 'string'},
            'preview': {'type': 'string'},
            'content': {'type': 'string'},
        },
        'required': ['task_type', 'title', 'preview', 'content'],
        'additionalProperties': False,
    }
    with tempfile.NamedTemporaryFile('w', suffix='.json', encoding='utf-8', delete=False) as tmp:
        schema_path = Path(tmp.name)
        json.dump(schema, tmp, ensure_ascii=False)

    command = [
        'codex',
        'exec',
        '--skip-git-repo-check',
        '--json',
        '--output-schema',
        str(schema_path),
        '-C',
        workdir,
        prompt,
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    schema_path.unlink(missing_ok=True)

    if result.returncode != 0:
        stderr = result.stderr.strip() or 'no stderr provided'
        raise CodexWrapperError(f'codex cli failed: {stderr}')

    raw_text = _extract_agent_message(result.stdout)
    if not raw_text:
        raise CodexWrapperError('codex cli did not return an agent_message result')

    try:
        structured = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise CodexWrapperError(
            f'codex result was not valid JSON as instructed: {exc}; raw={raw_text[:300]}'
        ) from exc

    if not isinstance(structured, dict):
        raise CodexWrapperError('codex result JSON was not an object')

    return {'ok': True, 'raw_text': raw_text, 'structured': structured}


def _extract_agent_message(stdout: str) -> str:
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if payload.get('type') != 'item.completed':
            continue
        item = payload.get('item')
        if isinstance(item, dict) and item.get('type') == 'agent_message':
            return str(item.get('text', '')).strip()
    return ''
