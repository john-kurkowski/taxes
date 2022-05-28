#!/usr/bin/env python


"""CLI for this package."""


import logging
import multiprocessing
import os
import pathlib
import sys
from typing import Sequence

import click

from .cli import extract_file


@click.command()
@click.argument("files", nargs=-1, required=True, type=pathlib.Path)
def main(files: Sequence[pathlib.Path]) -> None:
    """Convert FILES bank statement PDFs to CSV on stdout."""

    logging.basicConfig(level=os.environ.get("LOGLEVEL", "WARNING").upper())

    num_cores_that_hopefully_wont_max_out_machine = multiprocessing.cpu_count() // 2
    if len(files) <= 1 or num_cores_that_hopefully_wont_max_out_machine <= 1:
        extract_file(files[0])
        return

    # Let through child process logging to stderr. Note on macOS, this line is
    # considered unsafe.
    # https://docs.python.org/3/library/multiprocessing.html#contexts-and-start-methods
    multiprocessing.set_start_method("fork")

    with multiprocessing.Pool(num_cores_that_hopefully_wont_max_out_machine) as pool:
        pool.map(extract_file, files)


if __name__ == "__main__":
    main(sys.argv[1:])
