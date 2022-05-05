"""Functions to identify and extract transaction data from all supported banks'
statements. Parses dates in the table to have the provided year, if the
statement omits the year. If a function doesn't find data for its particular
bank, it returns `None`."""

import datetime
from typing import NamedTuple, Optional

import dateutil.parser
import pandas


class Extraction(NamedTuple):
    """Tabular transaction data for one table from one bank's statement."""

    dataframe: pandas.core.frame.DataFrame


def extract_applecard(
    _: int, dataframe: pandas.core.frame.DataFrame
) -> Optional[Extraction]:
    """Extract transactions from Apple Card statements. They have the word
    "Transactions" somewhere in the first column."""

    def is_match(cell):
        return cell.lower().strip() == "transactions"

    found_transactions_idx = next(
        (idx for idx in dataframe.index if is_match(dataframe.iat[idx, 0])), None
    )
    if found_transactions_idx is None:
        return None

    return Extraction(dataframe[found_transactions_idx + 1 :])


def extract_capitalone(
    year: int, dataframe: pandas.core.frame.DataFrame
) -> Optional[Extraction]:
    """Extract transactions from Capital One statements. They have the headers
    "Date" and "Balance" somewhere in the first several columns. "Date" is
    always in the first column. "Balance" is variable, in the last column."""

    if len(dataframe.columns) <= 4:
        return None

    maybe_dates = [val.lower() for val in dataframe[0].values]
    maybe_balances = [val.lower() for val in dataframe[dataframe.columns[-1]].values]
    try:
        date_header_idx = maybe_dates.index("date")
        maybe_balances.index("balance")
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
    """Extract transactions from Chase statements. They have 1 of a few words
    in the first cell of the table."""

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
