#!/usr/bin/env python


"""TODO"""


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


def main(files) -> None:
    """TODO"""
    for fil in files:
        dataframes = list(extract_dataframes(fil))
        if not dataframes:
            print(f"File {fil} had nothing to extract", file=sys.stderr)

        for dataframe in dataframes:
            print(dataframe.to_csv())


if __name__ == "__main__":
    main(sys.argv[1:])
