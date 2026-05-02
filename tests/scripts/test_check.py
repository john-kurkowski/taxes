"""Check runner command behavior."""

from __future__ import annotations

import importlib.util
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol, cast

import pytest


class _CheckModule(Protocol):
    def main(self, argv: Sequence[str] | None = None) -> int: ...


def _load_check_module() -> _CheckModule:
    path = Path(__file__).parents[2] / "scripts" / "check.py"
    spec = importlib.util.spec_from_file_location("check", path)
    assert spec
    assert spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return cast(_CheckModule, module)


def test_fix_mode_runs_fixable_commands_before_checks(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Fix mode applies Ruff fixes before running read-only checks."""
    check = _load_check_module()
    (tmp_path / "script.sh").write_text("#!/usr/bin/env bash\n")
    monkeypatch.chdir(tmp_path)

    commands: list[tuple[str, ...]] = []

    def run(
        command: tuple[str, ...], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        if command == ("git", "ls-files", "*.sh"):
            return subprocess.CompletedProcess(command, 1, "")
        commands.append(command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, "run", run)

    assert check.main(["--fix"]) == 0
    assert commands == [
        ("ruff", "check", "--fix", "scripts", "src", "tests"),
        ("ruff", "format", "scripts", "src", "tests"),
        ("mypy", "scripts", "src", "tests"),
        ("pyright",),
        ("ty", "check"),
        ("shellcheck", "script.sh"),
    ]


def test_check_mode_runs_all_commands_after_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Check mode reports failure only after every check has run."""
    check = _load_check_module()
    monkeypatch.chdir(tmp_path)

    commands: list[tuple[str, ...]] = []

    def run(
        command: tuple[str, ...], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        if command == ("git", "ls-files", "*.sh"):
            return subprocess.CompletedProcess(command, 1, "")
        commands.append(command)
        returncode = 1 if command == ("ruff", "check", "scripts", "src", "tests") else 0
        return subprocess.CompletedProcess(command, returncode)

    monkeypatch.setattr(subprocess, "run", run)

    assert check.main([]) == 1
    assert commands == [
        ("ruff", "check", "scripts", "src", "tests"),
        ("ruff", "format", "--check", "scripts", "src", "tests"),
        ("mypy", "scripts", "src", "tests"),
        ("pyright",),
        ("ty", "check"),
    ]
