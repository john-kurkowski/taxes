"""TODO"""

import logging
from typing import Generator

import camelot  # type: ignore[import]

from .extractors import ALL_EXTRACTORS, Extraction


def extract_dataframes(fil: str) -> Generator[Extraction, None, None]:
    """TODO"""

    tables = camelot.read_pdf(fil, pages="all", flavor="stream")
    last_extraction = None
    for table in tables:
        try:
            extractor, extraction = next(
                (extractor, extraction)
                for extractor in ALL_EXTRACTORS
                if (extraction := extractor(table.df))
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
