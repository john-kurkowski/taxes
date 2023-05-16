"""CLI for this package."""

import datetime
import subprocess
import sys
from pathlib import Path

import click


@click.command()
@click.option(
    "-y",
    "--year",
    default=lambda: [datetime.date.today().year - 1],
    multiple=True,
    type=int,
)
@click.argument("pattern")
def main(year: list[int], pattern: str) -> None:
    """Grep CSV transactions for the given year and pattern.

    Executes the given regex pattern against a pre-existing snapshot of
    `statements2csv`, across all bank statements. A thin wrapper around
    Ripgrep, this command basically just makes the grep command easier to type.
    Defaults to transactions from the previous calendar year, if year not
    provided.
    """
    file = (
        Path(__file__).parent.parent.parent
        / "tests"
        / "__snapshots__"
        / "secrets"
        / "all"
        / "test_integration.ambr"
    )

    cmd: list[str | Path] = [
        Path(__file__).parent / "greptransactions.sh",
        "|".join(str(y) for y in year),
        pattern,
        file,
    ]

    proc = subprocess.run(cmd, text=True)
    sys.exit(proc.returncode)


if __name__ == "__main__":  # pragma: no cover
    main()
