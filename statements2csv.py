#!/usr/bin/env python


"""TODO"""


import datetime
import logging
import os
import pathlib
import sys
from typing import Generator, Iterable, NamedTuple, Optional

import camelot
import click
import dateutil.parser
import pandas


class Extraction(NamedTuple):
    """TODO"""

    date: datetime.date
    dataframe: pandas.core.frame.DataFrame


def extract_applecard(dataframe: pandas.core.frame.DataFrame) -> Optional[Extraction]:
    """TODO"""
    is_match = dataframe[0][0].lower().strip() == "transactions"
    if not is_match:
        return None

    first_date_str = dataframe[0][3]
    first_date = dateutil.parser.parse(first_date_str)
    return Extraction(first_date, dataframe[1:])


def extract_capitalone(dataframe: pandas.core.frame.DataFrame) -> Optional[Extraction]:
    """TODO"""
    dates = [val.lower() for val in dataframe[0].values]
    try:
        header_idx = dates.index("date")
    except ValueError:
        return None

    first_date_str = dates[header_idx + 1]
    first_date = dateutil.parser.parse(first_date_str)
    return Extraction(first_date, dataframe[3:])


def extract_chase(dataframe: pandas.core.frame.DataFrame) -> Optional[Extraction]:
    """TODO"""
    first_cell = dataframe[0][0].lower().strip()
    is_match = any(
        first_cell.startswith(sentinel) for sentinel in ("account activity", "date of")
    )
    if not is_match:
        return None

    def try_date(cell) -> Optional[datetime.date]:
        try:
            return dateutil.parser.parse(cell)
        except ValueError:
            return None

    first_date = next(
        date for date in (try_date(cell) for cell in dataframe[0]) if date
    )
    return Extraction(first_date, dataframe[2:])


def extract_dataframes(fil: str) -> Generator[Extraction, None, None]:
    """TODO"""
    extractors = (extract_applecard, extract_capitalone, extract_chase)

    tables = camelot.read_pdf(fil, pages="all", flavor="stream")
    for table in tables:
        try:
            extractor, extraction = next(
                (extractor, extraction)
                for extractor in extractors
                if (extraction := extractor(table.df))
            )
        except StopIteration:
            continue

        logging.info('Extractor "%s" found something', extractor)
        yield extraction


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


if __name__ == "__main__":
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "WARNING").upper())
    main(sys.argv[1:])
