"""TODO"""

import logging
import pathlib
import re
from typing import Generator

import camelot  # type: ignore[import]

from .extractors import ALL_EXTRACTORS, Extraction

YEAR_RE = re.compile(r"^\d{4}$")


def extract_dataframes(fil: pathlib.Path) -> Generator[Extraction, None, None]:
    """TODO"""

    resolved_fil = fil.resolve()
    year_candidates = [
        int(match.group(0))
        for part in resolved_fil.parts
        if (match := YEAR_RE.match(part))
    ]
    if len(year_candidates) != 1:
        raise ValueError(
            f"{len(year_candidates)} possible statement years found in filepath"
            f" {resolved_fil}. Must be exactly 1."
        )
    year = year_candidates[0]

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
