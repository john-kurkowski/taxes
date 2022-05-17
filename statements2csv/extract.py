"""Functions for parsing a PDF bank statement."""

import logging
import pathlib
import re
from typing import Generator

import camelot  # type: ignore[import]

from .extractors import ALL_EXTRACTORS, Extraction

YEAR_RE = re.compile(r"^\d{4}$")


def extract_dataframes(fil: pathlib.Path) -> Generator[Extraction, None, None]:
    """Parses the given PDF's tables for bank transactions, lazily yielding one
    table at a time. Excludes non-transaction tables. For each table, tries all
    supported banks in a consistent order. The first bank that yields a result
    yields from this function. If no banks match, the table is skipped."""

    year = _parse_year_from_absolute_filepath(fil.resolve())

    tables = camelot.read_pdf(str(fil), pages="all", flavor="stream")
    last_extraction = None
    for table in tables:
        try:
            extractor, extraction = next(
                (extractor, extraction)
                for extractor in ALL_EXTRACTORS
                if (extraction := extractor(year, table.df))
            )
        except StopIteration:
            continue

        is_duplicate_extraction = last_extraction and extraction.dataframe.equals(
            last_extraction.dataframe
        )
        if is_duplicate_extraction:
            logging.info('Extractor "%s" found duplicate table. Skipping', extractor)
            continue

        last_extraction = extraction
        logging.info('Extractor "%s" found something', extractor)
        yield extraction


def _parse_year_from_absolute_filepath(fil: pathlib.Path) -> int:
    year_candidates = [
        int(match.group(0)) for part in fil.parts if (match := YEAR_RE.match(part))
    ]

    if len(year_candidates) != 1:
        raise ValueError(
            f"{len(year_candidates)} possible statement years found in filepath"
            f" {fil}. Must be exactly 1."
        )
    return year_candidates[0]
