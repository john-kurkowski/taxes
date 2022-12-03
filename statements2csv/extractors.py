"""Callables to identify and extract transaction data from supported banks'
statements."""

from abc import abstractmethod
import datetime
from collections.abc import Sequence
import re
from typing import Any, NamedTuple, Protocol, cast

import dateutil.parser
import pandas


class Extraction(NamedTuple):
    """Tabular transaction data for one table from one bank's statement."""

    dataframe: pandas.core.frame.DataFrame

    @property
    def date_start(self) -> datetime.date:
        """The earliest date in the extracted table."""
        return self.dataframe["Date"].min()


class Extractor(Protocol):
    """Callable to identify and extract transaction data from 1 table from 1
    particular bank's statement. Skip non-transaction data, like headers.
    Determine the bank and data from 1 table at a time (this module does not,
    for example, consider 1 table in relation to the n other tables in the same
    PDF). Parse dates in the table to have the provided year, if the statement
    omits the year. If no data is found matching the particular bank, return
    `None`."""

    def __call__(
        self, year: int, dataframe: pandas.core.frame.DataFrame
    ) -> Extraction | None:
        if not self.is_match(dataframe):
            return None

        return self._extract(year, dataframe)

    def _extract(self, year: int, dataframe: pandas.core.frame.DataFrame) -> Extraction:
        """The core transaction table extraction steps, shared by all banks."""

        column_names = self.column_names(dataframe)

        dataframe.drop(
            columns=[col for col in dataframe.columns if col not in column_names],
            inplace=True,
        )
        dataframe.rename(columns=column_names, inplace=True)

        dataframe["Date"] = [
            pandas.to_datetime(some_date)
            if (some_date := _maybe_date_parse(year, date))
            else None
            for date in dataframe["Date"]
        ]

        dataframe.drop(
            index=dataframe.loc[self.unwanted_rows(dataframe)].index,
            inplace=True,
        )

        return Extraction(dataframe)

    @abstractmethod
    def is_match(self, dataframe: pandas.core.frame.DataFrame) -> bool:
        """Whether this Extractor can handle the 1 table for its particular bank."""

    @abstractmethod
    def column_names(self, dataframe: pandas.core.frame.DataFrame) -> dict[int, str]:
        """Map column integer indexes to human-friendly display names. There
        are at least the same 3 columns in every bank transaction PDF: Date,
        Description, and Amount."""

    def unwanted_rows(self, dataframe: pandas.core.frame.DataFrame) -> pandas.Series:
        """Select dataframe rows to be dropped, after parsing is complete,
        before data is returned to the caller. For example, select rows with
        invalid dates."""

        is_empty_or_a_label = (
            dataframe["Date"].isnull()
            | dataframe["Amount"].eq("")
            | dataframe["Amount"].str.isalpha()
        )

        return is_empty_or_a_label


class ExtractorAppleCard(Extractor):
    """Extract transactions from Apple Card statements. They have a "Daily
    Cash" column. Date parsing is not technically necessary, because the
    statements already include the year."""

    def is_match(self, dataframe: pandas.core.frame.DataFrame) -> bool:
        def is_row_match(row: pandas.core.series.Series) -> bool:
            row_texts = set(cell_text.lower().strip() for cell_text in row)
            return "date" in row_texts and "daily cash" in row_texts

        return any(is_row_match(dataframe.iloc[row_i]) for row_i in dataframe.index)

    def column_names(self, dataframe: pandas.core.frame.DataFrame) -> dict[int, str]:
        return {
            0: "Date",
            1: "Description",
            4: "Amount",
        }


class ExtractorBankOfAmerica(Extractor):
    """Extract transactions from Bank of America statements. They have 2 date
    columns, for transaction date and posting date. Drop the extra date. Some
    transactions span multiple rows with metadata, like flight arrival time.
    Drop these extra rows."""

    def is_match(self, dataframe: pandas.core.frame.DataFrame) -> bool:
        def is_row_match(row_i: int) -> bool:
            try:
                return dataframe.iat[row_i, 0] == dataframe.iat[row_i, 1] == "Date"
            except IndexError:
                return False

        return any(is_row_match(row_i) for row_i in dataframe.index)

    def column_names(self, dataframe: pandas.core.frame.DataFrame) -> dict[int, str]:
        return {
            0: "Date",
            2: "Description",
            5: "Amount",
        }


class ExtractorCapitalOne(Extractor):
    """Extract transactions from Capital One statements. They have the headers
    "Date" and "Balance" somewhere in the first several columns. "Date" is
    always in the first column. "Amount" and "Balance" are variable, in the
    last 2 columns."""

    def is_match(self, dataframe: pandas.core.frame.DataFrame) -> bool:
        try:
            maybe_dates = [val.lower() for val in dataframe[0].values]
            maybe_amounts = [
                val.lower() for val in dataframe[dataframe.columns[-2]].values
            ]
            maybe_balances = [
                val.lower() for val in dataframe[dataframe.columns[-1]].values
            ]
        except IndexError:
            return False

        return (
            "date" in maybe_dates
            and "amount" in maybe_amounts
            and "balance" in maybe_balances
        )

    def column_names(self, dataframe: pandas.core.frame.DataFrame) -> dict[int, str]:
        date_header_idx = [val.lower() for val in dataframe[0].values].index("date")

        amount_col_idx = (
            dataframe.loc[date_header_idx]
            .loc[
                # Work around incomplete type stub. It accepts a Callable.
                cast(Any, lambda x: x == "AMOUNT")
            ]
            .index[0]
        )
        return {
            0: "Date",
            1: "Description",
            amount_col_idx: "Amount",
        }


class ExtractorChase(Extractor):
    """Extract transactions from Chase statements. They have 1 of a few words
    in the first cell of the table."""

    IS_MATCH_RE = re.compile(
        r"\s+".join(("Merchant", "Name", "or", "Transaction", "Description"))
    )

    def is_match(self, dataframe: pandas.core.frame.DataFrame) -> bool:
        return bool(self.IS_MATCH_RE.search(dataframe.to_string()))

    def column_names(self, dataframe: pandas.core.frame.DataFrame) -> dict[int, str]:
        return {
            0: "Date",
            1: "Description",
            2: "Amount",
        }


class ExtractorWellsFargo(Extractor):
    """Extract transactions from Wells Fargo statements. They have separate
    columns for additions and subtractions."""

    def is_match(self, dataframe: pandas.core.frame.DataFrame) -> bool:
        try:
            maybe_additions = [
                val.lower() for val in dataframe[dataframe.columns[-3]].values
            ]
            maybe_subtractions = [
                val.lower() for val in dataframe[dataframe.columns[-2]].values
            ]
        except IndexError:
            return False

        return "additions" in maybe_additions and "subtractions" in maybe_subtractions

    def column_names(self, dataframe: pandas.core.frame.DataFrame) -> dict[int, str]:
        return {
            0: "Date",
            2: "Description",
            4: "Amount",
        }


ALL_EXTRACTORS: Sequence[Extractor] = (
    ExtractorAppleCard(),
    ExtractorBankOfAmerica(),
    ExtractorCapitalOne(),
    ExtractorChase(),
    ExtractorWellsFargo(),
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


def _maybe_date_parse(year: int, text: str) -> datetime.date | None:
    """Same as _date_parse, but ignores non-date strings by catching a date
    parse error, and returning `None`."""

    try:
        return _date_parse(year, text)
    except dateutil.parser.ParserError:
        return None
