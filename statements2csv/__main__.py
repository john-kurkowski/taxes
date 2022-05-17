#!/usr/bin/env python


"""CLI for this package."""


import logging
import multiprocessing
import os
import pathlib
import sys
from typing import Iterable

import click

from .cli import extract_file


@click.command()
@click.argument("files", nargs=-1, required=True, type=pathlib.Path)
def main(files: Iterable[pathlib.Path]) -> None:
    """Convert FILES bank statement PDFs to CSV on stdout."""
    num_cores_that_hopefully_wont_max_out_machine = max(
        multiprocessing.cpu_count() // 2, 1
    )
    with multiprocessing.Pool(num_cores_that_hopefully_wont_max_out_machine) as pool:
        pool.map(extract_file, files)


if __name__ == "__main__":
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "WARNING").upper())
    main(sys.argv[1:])
