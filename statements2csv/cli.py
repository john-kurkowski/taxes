"""Helper functions for the CLI for this package. See also __main__.py."""

import logging
import pathlib

import click

from .extract import extract_dataframes


def extract_file(fil: pathlib.Path) -> None:
    """Convert 1 bank statement PDF to CSV on stdout."""
    extractions = extract_dataframes(fil)
    is_empty = True
    for extraction in extractions:
        is_empty = False
        click.echo(extraction.dataframe.to_csv(index=False))

    if is_empty:
        logging.warning('File "%s" had nothing to extract', fil)
