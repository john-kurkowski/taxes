"""CLI for this package."""

import datetime
import subprocess
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
    `statements2csv`, across all bank statements. Makes the grep command easier
    to type. Massages the CSV slightly, to be more suitable for copy and paste
    into a spreadsheet. Defaults to transactions from the previous calendar
    year, if year not provided.
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

    subprocess.run(cmd, check=True, text=True)


if __name__ == "__main__":  # pragma: no cover
    main()
