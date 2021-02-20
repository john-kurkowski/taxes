#!/usr/bin/env python


"""TODO"""


import datetime
import logging
import sys
from typing import Generator

import camelot
import pandas


def extract_dataframes(fil: str) -> Generator[pandas.core.frame.DataFrame, None, None]:
    """TODO"""
    tables = camelot.read_pdf(fil, pages="all", flavor="stream")
    for table in tables:
        if table.df[0][0].lower().strip() == "transactions":
            yield table.df[1:]


def date(dataframe: pandas.core.frame.DataFrame) -> datetime.date:
    """TODO"""
    first_date = dataframe[0][2]
    month, day, year = [int(token) for token in first_date.split("/")]
    return datetime.date(year, month, day)


def main(files) -> None:
    """TODO"""
    for fil in files:
        dataframes = sorted(extract_dataframes(fil), key=date)
        if not dataframes:
            logging.warning('File "%s" had nothing to extract', fil)

        for dataframe in dataframes:
            print(dataframe.to_csv())


if __name__ == "__main__":
    logging.basicConfig()
    main(sys.argv[1:])
