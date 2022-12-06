"""Integration tests for the entire project. Keep to a minimum.
https://testing.googleblog.com/2015/04/just-say-no-to-more-end-to-end-tests.html
"""

# pylint: disable=missing-function-docstring

import glob
import os.path
from pathlib import Path

from click.testing import CliRunner

from statements2csv.__main__ import main


def test_integration() -> None:
    with open(
        Path(os.path.dirname(__file__)) / "secrets" / "all_pdfs.lnk", encoding="utf-8"
    ) as fil:
        all_pdfs_input = glob.glob(fil.read().strip())

    assert all_pdfs_input

    with open(
        Path(os.path.dirname(__file__)) / "secrets" / "all_pdfs_snapshot.txt",
        encoding="utf-8",
    ) as fil:
        all_pdfs_output = fil.read()

    result = CliRunner().invoke(main, all_pdfs_input)

    assert result.exit_code == 0
    assert result.output == all_pdfs_output
