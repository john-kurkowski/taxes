"""CLI for this package."""

import csv
import datetime
import subprocess
import sys
from decimal import Decimal
from io import StringIO
from pathlib import Path

import click

from taxes.paths import decrypted_path

SortOption = str


def is_encrypted(file: Path) -> bool:
    """Read the first bit of a file to check for typical signs of encryption."""
    try:
        with open(file, encoding="utf-8") as fil:
            sample_size = 1024 * 1024  # 1MB
            fil.read(sample_size)
        return False
    except UnicodeDecodeError:
        return True


def parse_amount(amount: str) -> Decimal:
    """Parse transaction amount text into a sortable decimal value."""
    return Decimal(amount.translate(str.maketrans("", "", "$,+ ")))


def csv_to_tsv(
    input_text: str,
    *,
    sort: SortOption | None = None,
    reverse: bool = False,
) -> str:
    """Convert CSV text to tab-delimited text."""
    output = StringIO()
    rows = list(csv.reader(input_text.splitlines()))
    sort_keys = {
        "date": lambda row: row[0],
        "description": lambda row: row[1],
        "amount": lambda row: parse_amount(row[2]),
    }
    if sort is None:
        if reverse:
            rows.reverse()
    else:
        rows.sort(key=sort_keys[sort], reverse=reverse)

    writer = csv.writer(output, dialect="excel-tab", lineterminator="\n")

    for row in rows:
        writer.writerow(row)

    return output.getvalue()


@click.command()
@click.option(
    "-y",
    "--year",
    default=lambda: [datetime.date.today().year - 1],
    help="""Include transactions from the given year(s). Defaults to the previous calendar year.""",
    multiple=True,
    type=int,
)
@click.option(
    "--sort",
    "sort_option",
    type=click.Choice(["date", "description", "amount"]),
    help="Sort matching transactions by the selected field. Defaults to current date order.",
)
@click.option(
    "--reverse",
    is_flag=True,
    help="Reverse the selected sort order.",
)
@click.argument("pattern")
def main(
    year: list[int],
    sort_option: SortOption | None,
    reverse: bool,
    pattern: str,
) -> None:
    """Grep CSV transactions for the given year and pattern.

    Executes the given regex pattern against a pre-existing snapshot of
    `statements2csv`, across all bank statements.

    This pipes transactions through ripgrep so matches are highlighted.
    """
    file = decrypted_path(
        "tests",
        "__snapshots__",
        "secrets",
        "all",
        "test_integration.ambr",
    )

    if is_encrypted(file):
        raise click.ClickException(
            "Can't grep encrypted transaction data. Decrypt input data first."
        ) from None

    year_pattern = "|".join(str(y) for y in year)
    year_result = subprocess.run(
        [
            "rg",
            "--no-line-number",
            "--no-filename",
            rf"^\s*({year_pattern})-",
            file,
        ],
        check=False,
        stdout=subprocess.PIPE,
        text=True,
    )

    formatted_transactions = csv_to_tsv(
        year_result.stdout,
        sort=sort_option,
        reverse=reverse,
    )

    pattern_result = subprocess.run(
        ["rg", "--pcre2", f"({pattern})"],
        check=False,
        input=formatted_transactions,
        text=True,
    )
    sys.exit(pattern_result.returncode)


if __name__ == "__main__":  # pragma: no cover
    main()
