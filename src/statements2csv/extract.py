"""Functions for parsing a PDF bank statement."""

import logging
import pathlib
import re
from collections.abc import Iterator
from typing import Literal

import camelot

from .extractors import ALL_EXTRACTORS, Extraction

YEAR_RE = re.compile(r"^\d{4}$")


def extract_dataframes(
    fil: pathlib.Path, flavor: Literal["network", "stream"] | None
) -> Iterator[Extraction]:
    """Parse the given PDF's tables for bank transactions, yielding one table at a time.

    Exclude non-transaction tables. For each table, tries all supported banks.
    The first bank that yields a result yields from this function. If no banks
    match, the table is skipped.

    If no flavor given, tries whatever flavors are known to work best with the
    given bank statement, yielding from the flavor with the most transactions.
    """
    year = _parse_year_from_absolute_filepath(fil.resolve())

    flavors: dict[Literal["network", "stream"], list[Extraction]]
    if flavor is None and "Apple" in str(fil.resolve()):
        flavors = {"network": [], "stream": []}
    elif flavor is None:
        flavors = {"stream": []}
    else:
        flavors = {flavor: []}

    for flavor_choice, flavor_extractions in flavors.items():
        tables = camelot.io.read_pdf(str(fil), pages="all", flavor=flavor_choice)
        last_extraction: Extraction | None = None
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
                logging.info(
                    'Extractor "%s" found duplicate table. Skipping', extractor
                )
                continue

            last_extraction = extraction
            logging.info('Extractor "%s" found something', extractor)
            flavor_extractions.append(extraction)

    winning_extractions = max(flavors.values(), key=_sum_extracted_transactions)
    yield from winning_extractions


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


def _sum_extracted_transactions(extractions: list[Extraction]) -> int:
    return sum(len(extraction.dataframe) for extraction in extractions)
