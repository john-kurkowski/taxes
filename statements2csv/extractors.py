"""TODO"""

import datetime
from typing import NamedTuple, Optional

import dateutil.parser
import pandas


class Extraction(NamedTuple):
    """TODO"""

    dataframe: pandas.core.frame.DataFrame


def extract_applecard(
    _: int, dataframe: pandas.core.frame.DataFrame
) -> Optional[Extraction]:
    """TODO"""
    is_match = dataframe[0][0].lower().strip() == "transactions"
    if not is_match:
        return None

    return Extraction(dataframe[1:])


def extract_capitalone(
    year: int, dataframe: pandas.core.frame.DataFrame
) -> Optional[Extraction]:
    """TODO"""
    maybe_dates = [val.lower() for val in dataframe[0].values]
    try:
        date_header_idx = maybe_dates.index("date")
    except ValueError:
        return None

    for row_i in dataframe[date_header_idx + 1 :].index:
        cell = dataframe.iat[row_i, 0]
        if not cell:
            continue
        date = dateutil.parser.parse(cell).replace(year=year).date()
        dataframe.iat[row_i, 0] = date

    return Extraction(dataframe[date_header_idx + 1 :])


def extract_chase(
    year: int, dataframe: pandas.core.frame.DataFrame
) -> Optional[Extraction]:
    """TODO"""
    first_cell_sentinels = ("account activity", "date of", "transaction")
    first_cell = dataframe[0][0].lower().strip()
    is_match = any(first_cell.startswith(sentinel) for sentinel in first_cell_sentinels)
    if not is_match:
        return None

    def try_date(cell) -> Optional[datetime.date]:
        try:
            return dateutil.parser.parse(cell).replace(year=year).date()
        except ValueError:
            return None

    for row_i in dataframe.index:
        date = try_date(dataframe.iat[row_i, 0])
        if date:
            dataframe.iat[row_i, 0] = date

    return Extraction(dataframe[2:])


ALL_EXTRACTORS = (extract_applecard, extract_capitalone, extract_chase)
