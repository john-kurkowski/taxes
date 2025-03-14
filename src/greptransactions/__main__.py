"""CLI for this package."""

import datetime
import subprocess
import sys
from pathlib import Path

import click


def is_encrypted(file: Path) -> bool:
    """Read the first bit of a file to check for typical signs of encryption."""
    try:
        with open(file, encoding="utf-8") as fil:
            sample_size = 1024 * 1024  # 1MB
            fil.read(sample_size)
        return False
    except UnicodeDecodeError:
        return True


@click.command()
@click.option(
    "-y",
    "--year",
    default=lambda: [datetime.date.today().year - 1],
    help="""Include transactions from the given year(s). Defaults to the previous calendar year.""",
    multiple=True,
    type=int,
)
@click.argument("pattern")
def main(year: list[int], pattern: str) -> None:
    """Grep CSV transactions for the given year and pattern.

    Executes the given regex pattern against a pre-existing snapshot of
    `statements2csv`, across all bank statements.

    This is a thin wrapper around some Bash commands piping in and out of
    Ripgrep.
    """
    file = (
        Path(__file__).parent.parent.parent
        / "tests"
        / "__snapshots__"
        / "secrets"
        / "all"
        / "test_integration.ambr"
    )

    if is_encrypted(file):
        raise click.ClickException(
            "Can't grep encrypted transaction data. Decrypt input data first."
        ) from None

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
