"""Functions for parsing a PDF bank statement."""

import logging
import pathlib
import re
from collections.abc import Iterator
from typing import Literal

import camelot

from .extractors import ALL_EXTRACTORS, Extraction, ExtractionValidationError, Extractor

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
        for table in tables:
            maybe_extraction, errs = _extract_table(fil, year, table)
            validation_errors.extend(errs)
            if not maybe_extraction:
                continue

            extractor, extraction = maybe_extraction
            if flavor_extractions and _is_duplicate_extraction(
                flavor_extractions[-1], extraction
            ):
                logging.info(
                    'Extractor "%s" found duplicate table. Preferring newer table',
                    extractor,
                )
                flavor_extractions.pop()
            else:
                logging.info('Extractor "%s" found something', extractor)

            flavor_extractions.append(extraction)

    if validation_errors and not any(flavors.values()):
        raise ValueError(
            f"No extractors found valid data in file {fil}"
        ) from validation_errors[0]

    winning_extractions = max(flavors.values(), key=_sum_extracted_transactions)
    yield from winning_extractions


def _extract_table(
    fil: pathlib.Path,
    year: int,
    table: camelot.core.Table,  # pyright: ignore[reportAttributeAccessIssue]
) -> tuple[tuple[Extractor, Extraction] | None, list[ExtractionValidationError]]:
    """Try all extractors on the given table, returning the first successful one and its result, if any.

    Also returns all accumulated errors.
    """
    matching = []
    errors = []
    for extractor in ALL_EXTRACTORS:
        next_extraction = None
        try:
            next_extraction = extractor(year, table.df)
        except ExtractionValidationError as eve:
            logging.info('Extractor "%s" failed validation: %s', extractor, eve)
            errors.append(eve)

        if next_extraction:
            matching.append((extractor, next_extraction))

    if len(matching) > 1:
        logging.warning(
            'Multiple extractors matched file "%s": "%s"',
            fil,
            [extractor for (extractor, _) in matching],
        )

    return matching[0] if matching else None, errors


def _flavors_to_try(
    fil: pathlib.Path, flavor: Literal["network", "stream"] | None
) -> dict[Literal["network", "stream"], list[Extraction]]:
    if flavor is not None:
        return {flavor: []}

    filepath = str(fil.resolve())
    if any(part in filepath for part in ("Apple", "Chase")):
        return {"network": [], "stream": []}

    return {"stream": []}


def _is_duplicate_extraction(prev: Extraction, _next: Extraction) -> bool:
    """Check if the previous extraction is an exact duplicate or strict subset of the new one."""
    if prev.df.equals(_next.df):
        return True

    subset = prev.df.merge(_next.df, how="inner")
    return subset.equals(prev.df)


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
