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
        extractions = list(extract_dataframes(str(fil)))
        if not extractions:
            logging.warning('File "%s" had nothing to extract', fil)

        for extraction in extractions:
            click.echo(extraction.dataframe.to_csv())


logging.basicConfig(level=os.environ.get("LOGLEVEL", "WARNING").upper())
main(sys.argv[1:])
