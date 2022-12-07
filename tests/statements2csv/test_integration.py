"""Integration tests for the entire project. Keep to a minimum.
https://testing.googleblog.com/2015/04/just-say-no-to-more-end-to-end-tests.html
"""

# pylint: disable=missing-function-docstring,redefined-outer-name

import glob
import os.path
from pathlib import Path

from click.testing import CliRunner
import pytest

from statements2csv.__main__ import main


@pytest.fixture
def all_pdfs_input() -> list[str] | None:
    try:
        with open(
            Path(os.path.dirname(__file__)) / "secrets" / "all_pdfs.lnk",
            encoding="utf-8",
        ) as fil:
            result = glob.glob(fil.read().strip())
    except UnicodeDecodeError:
        return None

    assert result
    return result


@pytest.fixture
def all_pdfs_output() -> str | None:
    try:
        with open(
            Path(os.path.dirname(__file__)) / "secrets" / "all_pdfs_snapshot.txt",
            encoding="utf-8",
        ) as fil:
            result = fil.read()
    except UnicodeDecodeError:
        return None

    assert result
    return result


def test_integration(
    all_pdfs_input: list[str] | None, all_pdfs_output: str | None
) -> None:
    if not (all_pdfs_input and all_pdfs_output):
        pytest.skip("Can't test encrypted files")
        return

    result = CliRunner().invoke(main, all_pdfs_input)

    assert result.exit_code == 0
    assert result.output == all_pdfs_output
