"""Functions to identify and extract transaction data from all supported banks'
statements. Skips non-transaction data, like headers. Determines the bank and
data from 1 table at a time (it does not, for example, consider 1 table in
relation to the n other tables in the same PDF). Parses dates in the table to
have the provided year, if the statement omits the year. If a function doesn't
find data matching its particular bank, it returns `None`."""

from typing import Callable, NamedTuple, Optional, Sequence

import dateutil.parser
import pandas


class Extraction(NamedTuple):
    """Tabular transaction data for one table from one bank's statement."""

    dataframe: pandas.core.frame.DataFrame


Extractor = Callable[[int, pandas.core.frame.DataFrame], Optional[Extraction]]


def extract_applecard(
    _year: int, dataframe: pandas.core.frame.DataFrame
) -> Optional[Extraction]:
    """Extract transactions from Apple Card statements. They have the word
    "Transactions" somewhere in the first column."""

    def is_match(cell_text):
        return cell_text.lower().strip() == "transactions"

    found_transactions_idx = next(
        (row_i for row_i in dataframe.index if is_match(dataframe.iat[row_i, 0])), None
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

    date_col_i = 0
    for row_i in dataframe[date_header_idx + 1 :].index:
        cell_text = dataframe.iat[row_i, date_col_i]
        if not cell_text:
            # This column is sometimes blank. Otherwise it will contain a date.
            continue
        date = dateutil.parser.parse(cell_text).replace(year=year).date()
        dataframe.iat[row_i, date_col_i] = date

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

    date_col_i = 0
    for row_i in dataframe.index:
        try:
            dataframe.iat[row_i, date_col_i] = (
                dateutil.parser.parse(dataframe.iat[row_i, date_col_i])
                .replace(year=year)
                .date()
            )
        except ValueError:
            # This column doesn't always have a date.
            continue

    data_starts_at_idx = 2
    return Extraction(dataframe[data_starts_at_idx:])


ALL_EXTRACTORS: Sequence[Extractor] = (
    extract_applecard,
    extract_capitalone,
    extract_chase,
)
