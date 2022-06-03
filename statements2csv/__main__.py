#!/usr/bin/env python


"""CLI for this package."""


import itertools
import logging
import multiprocessing
import os
import pathlib
import sys
from typing import Sequence

import click

from .extract import extract_dataframes
from .extractors import Extraction


def extract_file(fil: pathlib.Path) -> list[Extraction]:
    """Convert 1 bank statement PDF to a list of its tables that contain
    transactions."""

    result = sorted(
        extract_dataframes(fil), key=lambda extraction: extraction.date_start
    )
    if not result:
        logging.warning('File "%s" had nothing to extract', fil)
    return result


@click.command()
@click.argument("files", nargs=-1, required=True, type=pathlib.Path)
def main(files: Sequence[pathlib.Path]) -> None:
    """Convert FILES bank statement PDFs to CSV on stdout."""

    logging.basicConfig(level=os.environ.get("LOGLEVEL", "WARNING").upper())

    num_cores_that_hopefully_wont_max_out_machine = multiprocessing.cpu_count() // 2
    if len(files) <= 1 or num_cores_that_hopefully_wont_max_out_machine <= 1:
        sorted_extractions = extract_file(files[0])
    else:
        # Let through child process logging to stderr. Note on macOS, this line is
        # considered unsafe.
        # https://docs.python.org/3/library/multiprocessing.html#contexts-and-start-methods
        multiprocessing.set_start_method("fork")

        with multiprocessing.Pool(
            num_cores_that_hopefully_wont_max_out_machine
        ) as pool:
            extractions = pool.map(extract_file, files)

        flattened_extractions = itertools.chain.from_iterable(extractions)
        sorted_extractions = sorted(
            flattened_extractions, key=lambda extraction: extraction.date_start
        )

    for extraction in sorted_extractions:
        click.echo(extraction.dataframe.to_csv(index=False))


if __name__ == "__main__":
    main(sys.argv[1:])
