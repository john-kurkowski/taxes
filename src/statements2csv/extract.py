"""Functions for parsing a PDF bank statement."""

import logging
import pathlib
import re
from collections.abc import Iterator
from typing import Literal

import camelot

from .extractors import ALL_EXTRACTORS, Extraction, ExtractionValidationError

YEAR_RE = re.compile(r"^\d{4}$")


def extract_dataframes(
    fil: pathlib.Path, flavor: Literal["network", "stream"] | None
) -> Iterator[Extraction]:
    """Parse the given PDF's tables for bank transactions, yielding one table at a time.

    Exclude non-transaction tables. For each table, tries all supported banks.
    The first bank that yields a result yields from this function. If no banks
    match, the table is skipped. If banks match but all flavors fail
    validation, an `ExtractionValidationError` is reraised; the PDF's schema is
    unexpected. Tries whatever flavors are known to work best with the given
    bank statement, yielding from the flavor with the most transactions, if no
    flavor is given.
    """
    year = _parse_year_from_absolute_filepath(fil.resolve())

    flavors = _flavors_to_try(fil, flavor)

    validation_errors = []

    for flavor_choice, flavor_extractions in flavors.items():
        tables = camelot.io.read_pdf(str(fil), pages="all", flavor=flavor_choice)
        last_extraction: Extraction | None = None
        for table in tables:
            matching_extractors = []
            for extractor in ALL_EXTRACTORS:
                try:
                    next_extraction = extractor(year, table.df)
                except ExtractionValidationError as eve:
                    logging.info('Extractor "%s" failed validation: %s', extractor, eve)
                    validation_errors.append(eve)

                if next_extraction:
                    matching_extractors.append((extractor, next_extraction))

            if not matching_extractors:
                continue
            elif len(matching_extractors) > 1:
                logging.warning(
                    'Multiple extractors matched file "%s": "%s"',
                    fil,
                    [extractor for (extractor, _) in matching_extractors],
                )

            extractor, extraction = matching_extractors[0]
            is_duplicate_extraction = last_extraction and extraction.df.equals(
                last_extraction.df
            )
            if is_duplicate_extraction:
                logging.info(
                    'Extractor "%s" found duplicate table. Skipping', extractor
                )
                continue

            last_extraction = extraction
            logging.info('Extractor "%s" found something', extractor)
            flavor_extractions.append(extraction)

    if validation_errors and not any(flavors.values()):
        raise ValueError(
            f"No extractors found valid data in file {fil}"
        ) from validation_errors[0]

    winning_extractions = max(flavors.values(), key=_sum_extracted_transactions)
    yield from winning_extractions


def _flavors_to_try(
    fil: pathlib.Path, flavor: Literal["network", "stream"] | None
) -> dict[Literal["network", "stream"], list[Extraction]]:
    if flavor is not None:
        return {flavor: []}

    filepath = str(fil.resolve())
    if any(part in filepath for part in ("Apple", "Chase")):
        return {"network": [], "stream": []}

    return {"stream": []}


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
    return sum(len(extraction.df) for extraction in extractions)
