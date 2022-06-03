"""Helper functions for the CLI for this package. See also __main__.py."""

import logging
import pathlib

from .extract import extract_dataframes
from .extractors import Extraction


def extract_file(fil: pathlib.Path) -> list[Extraction]:
    """Convert 1 bank statement PDF to a list of its tables that contain
    transactions.

    This function lives in its own file, to work around a multiprocessing
    pickling limitation."""

    result = sorted(
        extract_dataframes(fil), key=lambda extraction: extraction.date_start
    )
    if not result:
        logging.warning('File "%s" had nothing to extract', fil)
    return result
