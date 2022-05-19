"""Functions to identify and extract transaction data from all supported banks'
statements. Skips non-transaction data, like headers. Determines the bank and
data from 1 table at a time (it does not, for example, consider 1 table in
relation to the n other tables in the same PDF). Parses dates in the table to
have the provided year, if the statement omits the year. If a function doesn't
find data matching its particular bank, it returns `None`."""

from typing import Callable, NamedTuple, Optional, Sequence

import datetime
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
    "Transactions" somewhere in the first column. No date parsing is necessary,
    because the statements already include the year."""

    def is_match(cell_text):
        return cell_text.lower().strip() == "transactions"

    try:
        next((row_i for row_i in dataframe.index if is_match(dataframe.iat[row_i, 0])))
    except StopIteration:
        return None

    column_names = {
        0: "Date",
        1: "Description",
        4: "Amount",
    }

    dataframe.drop(
        columns=[col for col in dataframe.columns if col not in column_names],
        inplace=True,
    )
    dataframe.rename(columns=column_names, inplace=True)

    is_empty_or_a_label = (
        dataframe["Date"].eq("")
        | dataframe["Date"].str.isalpha()
        | dataframe["Amount"].eq("")
        | dataframe["Amount"].str.isalpha()
    )

    dataframe.drop(
        index=dataframe.loc[is_empty_or_a_label].index,
        inplace=True,
    )

    return Extraction(dataframe)


def extract_bankofamerica(
    year: int, dataframe: pandas.core.frame.DataFrame
) -> Optional[Extraction]:
    """Extract transactions from Bank of America statements. They have 2 date
    columns, for transaction date and posting date. Drop the extra date. Some
    transactions span multiple rows with metadata, like flight arrival time.
    Drop these extra rows."""

    def is_match(row_i: int) -> bool:
        try:
            return dataframe.iat[row_i, 0] == dataframe.iat[row_i, 1] == "Date"
        except IndexError:
            return False

    try:
        found_transactions_idx = next(
            row_i for row_i in dataframe.index if is_match(row_i)
        )
    except StopIteration:
        return None

    date_col_i = 0
    unwanted_rows = []
    for row_i in dataframe.index:
        if row_i < found_transactions_idx + 1:
            unwanted_rows.append(row_i)
            continue

        try:
            blank_or_date_cell_text = dataframe.iat[row_i, date_col_i]
        except IndexError:
            blank_or_date_cell_text = ""

        if not blank_or_date_cell_text:
            unwanted_rows.append(row_i)
            continue

        date = _date_parse(year, blank_or_date_cell_text)
        dataframe.iat[row_i, date_col_i] = date

    dataframe.drop(index=unwanted_rows, inplace=True)

    column_names = {
        0: "Date",
        2: "Description",
        3: "Ref #",
        5: "Amount",
    }

    dataframe.drop(
        columns=[col for col in dataframe.columns if col not in column_names],
        inplace=True,
    )
    dataframe.rename(columns=column_names, inplace=True)

    return Extraction(dataframe)


def extract_capitalone(
    year: int, dataframe: pandas.core.frame.DataFrame
) -> Optional[Extraction]:
    """Extract transactions from Capital One statements. They have the headers
    "Date" and "Balance" somewhere in the first several columns. "Date" is
    always in the first column. "Amount" and "Balance" are variable, in the
    last 2 columns."""

    if len(dataframe.columns) <= 4:
        return None

    maybe_dates = [val.lower() for val in dataframe[0].values]
    maybe_balances = [val.lower() for val in dataframe[dataframe.columns[-1]].values]
    try:
        date_header_idx = maybe_dates.index("date")
        maybe_balances.index("balance")
    except ValueError:
        return None

    amount_col_idx = (
        dataframe.loc[date_header_idx].loc[lambda x: x == "AMOUNT"].index[0]
    )
    column_names = {
        0: "Date",
        1: "Description",
        amount_col_idx: "Amount",
    }
    dataframe.rename(columns=column_names, inplace=True)

    unwanted_rows = []
    for row_i in dataframe.index:
        if row_i <= date_header_idx or not dataframe.loc[row_i, "Amount"]:
            unwanted_rows.append(row_i)
            continue

        blank_or_date_cell_text = dataframe.loc[row_i, "Date"]
        if not blank_or_date_cell_text:
            continue
        date = _date_parse(year, blank_or_date_cell_text)
        dataframe.loc[row_i, "Date"] = date

    dataframe.drop(index=unwanted_rows, inplace=True)
    dataframe.drop(
        columns=[col for col in dataframe.columns if col not in column_names.values()],
        inplace=True,
    )

    return Extraction(dataframe)


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
    unwanted_rows = []
    for row_i in dataframe.index:
        sometimes_date = dataframe.iat[row_i, date_col_i]
        try:
            date = _date_parse(year, sometimes_date)
        except ValueError:
            unwanted_rows.append(row_i)
            continue
        else:
            dataframe.iat[row_i, date_col_i] = date

    dataframe.drop(index=unwanted_rows, inplace=True)

    column_names = {
        0: "Date",
        1: "Description",
        2: "Amount",
    }
    dataframe.rename(columns=column_names, inplace=True)

    return Extraction(dataframe)


ALL_EXTRACTORS: Sequence[Extractor] = (
    extract_applecard,
    extract_bankofamerica,
    extract_capitalone,
    extract_chase,
)


def _date_parse(year: int, text: str) -> datetime.date:
    """Convert a transaction date string to a date object, with the given,
    explicit year. Explicitly setting the year is necessary, because the
    parsing assumes the current year if the year is omitted in the string. This
    application usually handles historical dates from years past."""

    try:
        parsed = dateutil.parser.parse(text)
    except dateutil.parser.ParserError as perr:
        is_date_but_retry_with_explicit_year = "day is out of range" in repr(perr)
        if is_date_but_retry_with_explicit_year:
            parsed = dateutil.parser.parse(f"{year}/{text}")
        else:
            raise

    return parsed.replace(year=year).date()
