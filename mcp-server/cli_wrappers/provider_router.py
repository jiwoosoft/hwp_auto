from __future__ import annotations

from typing import TypedDict

from cli_wrappers.claude_wrapper import ClaudeWrapperError, run_claude_json
from cli_wrappers.codex_wrapper import CodexWrapperError, run_codex_json
from cli_wrappers.opencode_wrapper import OpenCodeWrapperError, run_opencode_json


class ProviderRunResult(TypedDict):
    ok: bool
    provider: str
    raw_text: str
    structured: dict[str, object]


class ProviderRouterError(Exception):
    """Raised when the requested provider fails or is unsupported."""


def run_provider_json(provider: str, prompt: str, *, workdir: str) -> ProviderRunResult:
    normalized = (provider or 'claude').strip().lower()
    try:
        if normalized == 'claude':
            result = run_claude_json(prompt)
        elif normalized == 'codex':
            result = run_codex_json(prompt, workdir=workdir)
        elif normalized == 'opencode':
            result = run_opencode_json(prompt, workdir=workdir)
        else:
            raise ProviderRouterError(f'Unsupported provider: {provider}')
    except (ClaudeWrapperError, CodexWrapperError, OpenCodeWrapperError) as exc:
        raise ProviderRouterError(str(exc)) from exc

    return {
        'ok': True,
        'provider': normalized,
        'raw_text': result['raw_text'],
        'structured': result['structured'],
    }
