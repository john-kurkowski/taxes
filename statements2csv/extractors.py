"""TODO"""

import datetime
from typing import NamedTuple, Optional

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


ALL_EXTRACTORS = (extract_applecard, extract_capitalone, extract_chase)
