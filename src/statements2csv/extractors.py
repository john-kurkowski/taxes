"""Callables to identify and extract transaction data from supported banks' statements."""

import datetime
import re
from abc import abstractmethod
from collections.abc import Sequence
from typing import Any, NamedTuple, Protocol, cast

import dateutil.parser
import pandas


class ExtractionValidationError(ValueError):
    """Extracted table data had unexpected values."""


class Extraction(NamedTuple):
    """Tabular transaction data for one table from one bank's statement."""

    df: pandas.DataFrame

    @property
    def date_start(self) -> datetime.date:
        """The earliest date in the extracted table."""
        return cast(datetime.date, self.df["Date"].min())


class Extractor(Protocol):
    """Callable to identify and extract transaction data from 1 table from 1 particular bank's statement.

    Skip non-transaction data, like headers. Determine the bank and data from 1
    table at a time (this module does not, for example, consider 1 table in
    relation to the n other tables in the same PDF). Parse dates in the table
    to have the provided year, if the statement omits the year. If no data is
    found matching the particular bank, return `None`.
    """

    def __call__(self, year: int, df: pandas.DataFrame) -> Extraction | None:
        """Override."""
        if not self.is_match(df):
            return None

        extraction = self._extract(year, df)
        if extraction.df.empty:
            return None

        return extraction

    def _extract(self, year: int, df: pandas.DataFrame) -> Extraction:
        """Core transaction table extraction steps, shared by all banks."""
        column_names = self.column_names(df)

        trimmed_df = df.drop(
            columns=[col for col in df.columns if col not in column_names],  # type: ignore[comparison-overlap]
        )
        if len(column_names) != len(trimmed_df.columns):
            raise ExtractionValidationError(
                f"Expected {len(column_names)} columns, actual {len(trimmed_df.columns)}"
            )
        trimmed_df.rename(columns=column_names, inplace=True)

        trimmed_df["Date"] = _date_column_parse(year, trimmed_df["Date"])

        trimmed_df.drop(
            index=trimmed_df.loc[self.unwanted_rows(trimmed_df)].index,
            inplace=True,
        )
        trimmed_df.reset_index(drop=True, inplace=True)

        return Extraction(trimmed_df)

    @abstractmethod
    def is_match(self, df: pandas.DataFrame) -> bool:
        """Whether this Extractor can handle the 1 table for its particular bank."""

    @abstractmethod
    def column_names(self, df: pandas.DataFrame) -> dict[int, str]:
        """Map column integer indexes to human-friendly display names.

        There are at least the same 3 columns in every bank transaction PDF:
        Date, Description, and Amount.
        """

    def unwanted_rows(self, df: pandas.DataFrame) -> pandas.Series:  # type: ignore[type-arg]
        """Select dataframe rows to be dropped, after parsing is complete, before data is returned to the caller.

        For example, select rows with invalid dates.
        """
        is_empty_or_a_label = (
            df["Date"].isnull() | df["Amount"].eq("") | df["Amount"].str.isalpha()
        )

        return is_empty_or_a_label


class ExtractorAppleCard(Extractor):
    """Extract transactions from Apple Card statements.

    They have a "Daily Cash" column. Date parsing is not technically necessary,
    because the statements already include the year.
    """

    def is_match(self, df: pandas.DataFrame) -> bool:
        """Override."""

        def is_row_match(row: pandas.core.series.Series) -> bool:  # type: ignore[type-arg]
            row_texts = {cell_text.lower().strip() for cell_text in row}
            return "date" in row_texts and "daily cash" in row_texts

        return any(is_row_match(df.iloc[row_i]) for row_i in df.index)

    def column_names(self, df: pandas.DataFrame) -> dict[int, str]:
        """Override."""
        date_header_idx = [val.lower() for val in df[0].values].index("date")

        amount_col_idx = (
            df.loc[date_header_idx]
            .loc[
                # Work around incomplete type stub. It accepts a Callable.
                cast(Any, lambda x: x == "Amount")
            ]
            .index[0]
        )
        return {
            0: "Date",
            1: "Description",
            amount_col_idx: "Amount",
        }


class ExtractorBankOfAmerica(Extractor):
    """Extract transactions from Bank of America statements.

    They have 2 date columns, for transaction date and posting date. Drop the
    extra date. Some transactions span multiple rows with metadata, like flight
    arrival time. Drop these extra rows.
    """

    def is_match(self, df: pandas.DataFrame) -> bool:
        """Override."""

        def is_row_match(row_i: int) -> bool:
            try:
                return df.iat[row_i, 0] == df.iat[row_i, 1] == "Date"  # type: ignore[no-any-return]
            except IndexError:
                return False

        return any(is_row_match(row_i) for row_i in df.index)

    def column_names(self, df: pandas.DataFrame) -> dict[int, str]:
        """Override."""
        return {
            0: "Date",
            2: "Description",
            5: "Amount",
        }


class ExtractorCapitalOne(Extractor):
    """Extract transactions from Capital One statements.

    They have the headers "Date" and "Balance" somewhere in the first several
    columns. "Date" is always in the first column. "Amount" and "Balance" are
    variable, in the last 2 columns.
    """

    def is_match(self, df: pandas.DataFrame) -> bool:
        """Override."""
        try:
            maybe_dates = [val.lower() for val in df[0].values]
            maybe_amounts = [val.lower() for val in df[df.columns[-2]].values]
            maybe_balances = [val.lower() for val in df[df.columns[-1]].values]
        except IndexError:
            return False

        return (
            "date" in maybe_dates
            and "amount" in maybe_amounts
            and "balance" in maybe_balances
        )

    def column_names(self, df: pandas.DataFrame) -> dict[int, str]:
        """Override."""
        date_header_idx = [val.lower() for val in df[0].values].index("date")

        amount_col_idx = (
            df.loc[date_header_idx]
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
    """Extract transactions from Chase statements.

    They have 1 of a few words in the first cell of the table.
    """

    IS_MATCH_RE = re.compile(
        r"\s+".join(("Merchant", "Name", "or", "Transaction", "Description"))
    )

    def is_match(self, df: pandas.DataFrame) -> bool:
        """Override."""
        return bool(self.IS_MATCH_RE.search(df.to_string()))

    def column_names(self, df: pandas.DataFrame) -> dict[int, str]:
        """Override."""
        return {
            0: "Date",
            1: "Description",
            2: "Amount",
        }


class ExtractorWellsFargo(Extractor):
    """Extract transactions from Wells Fargo statements.

    They have separate columns for additions and subtractions.
    """

    def is_match(self, df: pandas.DataFrame) -> bool:
        """Override."""
        try:
            maybe_additions = [val.lower() for val in df[df.columns[-3]].values]
            maybe_subtractions = [val.lower() for val in df[df.columns[-2]].values]
        except IndexError:
            return False

        return "additions" in maybe_additions and "subtractions" in maybe_subtractions

    def column_names(self, df: pandas.DataFrame) -> dict[int, str]:
        """Override."""
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
    """Convert a transaction date string to a date object, with the given, explicit year.

    Explicitly setting the year is necessary, because the parsing assumes the
    current year if the year is omitted in the string. This application usually
    handles historical dates from years past.
    """
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
    """Convert a transaction date string to an optional date object, with the given, explicit year.

    Same as _date_parse, but ignores non-date strings by catching a date parse
    error, and returning `None`.
    """
    try:
        return _date_parse(year, text)
    except dateutil.parser.ParserError:
        return None


def _date_column_parse(
    year: int,
    column: pandas.Series,  # type: ignore[type-arg]
) -> list[datetime.date | None]:
    """Convert a transaction column to column of dates, with the given, explicit year."""
    raw_dates = [_maybe_date_parse(year, date) for date in column]
    is_crossing_year_boundary = {date.month for date in raw_dates if date} == {1, 12}
    if not is_crossing_year_boundary:
        return raw_dates

    def fix_date_on_year_boundary(date: datetime.date | None) -> datetime.date | None:
        if date is None or date.month == 1:
            return date
        return date.replace(year=year - 1)

    return [fix_date_on_year_boundary(date) for date in raw_dates]
