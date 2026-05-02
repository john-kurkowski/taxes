"""Run the repository's static checks."""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

PYTHON_TARGETS = ("scripts", "src", "tests")
IGNORED_SCRIPT_DIRS = {
    ".git",
    ".jj",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "htmlcov",
}


def main(argv: Sequence[str] | None = None) -> int:
    """Run all static checks and return a combined exit code."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--fix", action="store_true", help="apply automatic fixes")
    args = parser.parse_args(argv)

    commands = _python_commands(fix=args.fix)
    shell_scripts = _shell_script_paths()
    if shell_scripts:
        commands.append(("shellcheck", *map(str, shell_scripts)))
    else:
        print("Skipping ShellCheck: no shell scripts found.")

    failed = False
    for command in commands:
        _print_command(command)
        result = subprocess.run(command, check=False)
        failed = failed or result.returncode != 0

    return 1 if failed else 0


def _python_commands(*, fix: bool) -> list[tuple[str, ...]]:
    ruff_check: tuple[str, ...] = ("ruff", "check", *PYTHON_TARGETS)
    ruff_format: tuple[str, ...] = ("ruff", "format", "--check", *PYTHON_TARGETS)
    if fix:
        ruff_check = ("ruff", "check", "--fix", *PYTHON_TARGETS)
        ruff_format = ("ruff", "format", *PYTHON_TARGETS)

    return [
        ruff_check,
        ruff_format,
        ("mypy", *PYTHON_TARGETS),
        ("pyright",),
        ("ty", "check"),
    ]


def _shell_script_paths() -> list[str]:
    result = subprocess.run(
        ("git", "ls-files", "*.sh"),
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    if result.returncode == 0:
        return sorted(path for path in result.stdout.splitlines() if path)

    return sorted(
        str(path)
        for path in Path().glob("**/*.sh")
        if not IGNORED_SCRIPT_DIRS.intersection(path.parts)
    )


def _print_command(command: Sequence[str]) -> None:
    print()
    print("+ " + " ".join(command), flush=True)


if __name__ == "__main__":
    sys.exit(main())
