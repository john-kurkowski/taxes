"""Functions for parsing a PDF bank statement."""

import logging
import pathlib
import re
from collections.abc import Iterator

import camelot  # type: ignore[import]

from .extractors import ALL_EXTRACTORS, Extraction

YEAR_RE = re.compile(r"^\d{4}$")


def extract_dataframes(fil: pathlib.Path) -> Iterator[Extraction]:
    """Parse the given PDF's tables for bank transactions, lazily yielding one table at a time.

    Exclude non-transaction tables. For each table, tries all supported banks.
    The first bank that yields a result yields from this function. If no banks
    match, the table is skipped.
    """
    year = _parse_year_from_absolute_filepath(fil.resolve())

    try:
        tables = camelot.read_pdf(str(fil), pages="all", flavor="stream")
    except IndexError:
        # Work around `IndexError: list index out of range` in
        # "camelot/parsers/stream.py", line 386, in <listcomp>
        #   if t.x0 > cols[-1][1] or t.x1 < cols[0][0]
        #
        # The uncaught error happens on 1 of my 121 Wells Fargo PDFs. For such
        # an exceptional case, I don't think more aggressive error handling is
        # warranted.
        return

    last_extraction = None
    for table in tables:
        matching_extractors = [
            (extractor, next_extraction)
            for extractor in ALL_EXTRACTORS
            if (next_extraction := extractor(year, table.df))
        ]
        if not matching_extractors:
            continue
        elif len(matching_extractors) > 1:
            logging.warning(
                'Multiple extractors matched file "%s": "%s"',
                fil,
                [extractor for (extractor, _) in matching_extractors],
            )

        extractor, extraction = matching_extractors[0]
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
