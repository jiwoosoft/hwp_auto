from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

from master_of_hwp.ai import providers


class _FakeCLIProvider(providers._CLIProviderBase):
    executable = "fake"
    display_name = "Fake"


def test_windows_cmd_provider_uses_windows_quoting(monkeypatch, tmp_path: Path) -> None:
    calls = []
    fake_exe = tmp_path / "fake.cmd"
    fake_exe.write_text("@echo off\n", encoding="utf-8")

    def fake_which(name: str) -> str:
        assert name == "fake"
        return str(fake_exe)

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return SimpleNamespace(returncode=0, stdout="ok\n", stderr="")

    monkeypatch.setattr(providers.sys, "platform", "win32")
    monkeypatch.setattr(providers.shutil, "which", fake_which)
    monkeypatch.setattr(providers.subprocess, "run", fake_run)

    provider = _FakeCLIProvider()
    result = provider._run(
        ["exec", "--output-last-message", "C:\\Temp\\out file.txt", "hello prompt"]
    )

    assert result == "ok"
    assert calls[1][1]["shell"] is True
    assert calls[1][0] == subprocess.list2cmdline(
        [
            str(fake_exe),
            "exec",
            "--output-last-message",
            "C:\\Temp\\out file.txt",
            "hello prompt",
        ]
    )
    assert "'" not in calls[1][0]
