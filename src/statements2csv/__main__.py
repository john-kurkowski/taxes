"""CLI for this package."""

from __future__ import annotations

import dataclasses
import datetime
import itertools
import logging
import multiprocessing
import os
from functools import partial
from pathlib import Path
from typing import Literal

import click

from .extract import extract_dataframes
from .extractors import Extraction


@dataclasses.dataclass
class FileExtraction:
    """A bank statement file and one of its extracted transaction tables."""

    fil: Path
    extraction: Extraction

    def __lt__(self, other: FileExtraction) -> bool:
        """Sort extractions in deterministic, roughly chronological order.

        So e.g. 2018-02 transactions come before 2019-01 transactions.

        Transactions can start on the same day of the month, so break ties
        using the source filename.

        Transactions aren't sorted within a table, so a few transactions may
        still be out of order when multiple files are merged into one output.
        Transactions should _tend_ to be adjacent, month to month.
        """
        return self._sort_key < other._sort_key

    @property
    def _sort_key(self) -> tuple[datetime.date, Path]:
        return self.extraction.date_start, self.fil.resolve()


def extract_file(
    fil: Path,
    flavor: Literal["network", "stream"] | None,
) -> list[FileExtraction]:
    """Convert 1 bank statement PDF to a list of its transaction tables."""
    result = sorted(
        FileExtraction(fil, extraction)
        for extraction in extract_dataframes(fil, flavor)
    )
    if not result:
        logging.warning('File "%s" had nothing to extract', fil)
    return result


@click.command()
@click.argument("files", nargs=-1, required=True, type=Path)
@click.option(
    "--flavor",
    help="""Flavor of PDF reader to use. Defaults to whatever is known to work with a given bank statement.""",
    type=click.Choice(["network", "stream"]),
)
def main(files: list[Path], flavor: Literal["network", "stream"] | None) -> None:
    """Convert FILES bank statement PDFs to CSV on stdout."""
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "WARNING").upper())

    num_cores_that_hopefully_wont_max_out_machine = multiprocessing.cpu_count() // 2
    do_serially = len(files) <= 1 or num_cores_that_hopefully_wont_max_out_machine <= 1
    if do_serially:
        extractions = [extract_file(fil, flavor) for fil in files]
    else:
        # Let through child process logging to stderr. Note on macOS, this line is
        # considered unsafe.
        # https://docs.python.org/3/library/multiprocessing.html#contexts-and-start-methods
        multiprocessing.set_start_method("fork")

        with multiprocessing.Pool(
            num_cores_that_hopefully_wont_max_out_machine
        ) as pool:
            extractions = pool.map(partial(extract_file, flavor=flavor), files)

    flattened_extractions = itertools.chain.from_iterable(extractions)
    sorted_extractions = sorted(flattened_extractions)

    for i, flattened_extraction in enumerate(sorted_extractions):
        is_first = i == 0
        is_last = i >= len(sorted_extractions) - 1
        click.echo(
            flattened_extraction.extraction.df.to_csv(header=is_first, index=False),
            nl=is_last,
        )


if __name__ == "__main__":  # pragma: no cover
    main()
