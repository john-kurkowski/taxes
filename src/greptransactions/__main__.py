"""CLI for this package."""

import datetime
import subprocess
import sys
from pathlib import Path

import click


def main() -> None:
    """Grep CSV transactions for the given year and pattern.

    Executes the given regex pattern against an existing snapshot of
    `statements2csv`, across all bank statements. Makes the grep command easier
    to type. Massages the CSV slightly, to be more suitable for copy and paste
    into a spreadsheet. Defaults to transactions from the previous calendar
    year, if year not provided.
    """
    if len(sys.argv) == 2:
        year = str(datetime.date.today().year - 1)
        *_, pattern = sys.argv
    elif len(sys.argv) == 3:
        *_, year, pattern = sys.argv
    else:
        raise click.UsageError("TODO: document and parse args")

    file = (
        Path(__file__).parent.parent.parent
        / "tests"
        / "statements2csv"
        / "__snapshots__"
        / "secrets"
        / "test_integration.ambr"
    )

    cmd: list[str | Path] = [
        Path(__file__).parent / "greptransactions.sh",
        year,
        pattern,
        file,
    ]

    subprocess.run(cmd, check=True, text=True)
