#!/usr/bin/env python


"""TODO"""


import logging
import os
import pathlib
import sys
from typing import Iterable

import click

from .extract import extract_dataframes


@click.command()
@click.argument("files", nargs=-1, required=True, type=pathlib.Path)
def main(files: Iterable[pathlib.Path]) -> None:
    """Convert FILES bank statement PDFs to CSV on stdout."""
    for fil in files:
        extractions = extract_dataframes(fil)
        is_empty = True
        for extraction in extractions:
            is_empty = False
            click.echo(extraction.dataframe.to_csv())

        if is_empty:
            logging.warning('File "%s" had nothing to extract', fil)


logging.basicConfig(level=os.environ.get("LOGLEVEL", "WARNING").upper())
main(sys.argv[1:])
