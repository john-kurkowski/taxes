#!/usr/bin/env python


"""TODO"""


import datetime
import logging
import sys
from typing import Generator, NamedTuple, Optional

import camelot
import dateutil.parser
import pandas


class Extraction(NamedTuple):
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


def extract_dataframes(fil: str) -> Generator[Extraction, None, None]:
    """TODO"""
    extractors = (extract_applecard,)

    tables = camelot.read_pdf(fil, pages="all", flavor="stream")
    for table in tables:
        for extractor in extractors:
            extraction = extractor(table.df)
            if extraction:
                yield extraction


def main(files) -> None:
    """TODO"""
    for fil in files:
        extractions = sorted(
            extract_dataframes(fil), key=lambda extraction: extraction.date
        )
        if not extractions:
            logging.warning('File "%s" had nothing to extract', fil)

        for extraction in extractions:
            print(extraction.dataframe.to_csv())


if __name__ == "__main__":
    logging.basicConfig()
    main(sys.argv[1:])
