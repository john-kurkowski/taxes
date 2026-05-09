"""Run the repository's static checks."""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Sequence

PYTHON_TARGETS = ("scripts", "src", "tests")


def main(argv: Sequence[str] | None = None) -> int:
    """Run all static checks and return a combined exit code."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--fix", action="store_true", help="apply automatic fixes")
    args = parser.parse_args(argv)

    commands = _python_commands(fix=args.fix)

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


def _print_command(command: Sequence[str]) -> None:
    print()
    print("+ " + " ".join(command), flush=True)


if __name__ == "__main__":
    sys.exit(main())
