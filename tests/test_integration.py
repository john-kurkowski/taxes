"""Integration tests for the entire project.

Keep to a minimum. https://testing.googleblog.com/2015/04/just-say-no-to-more-end-to-end-tests.html.
"""

import datetime
import os.path
from pathlib import Path

import freezegun
import pytest
from click.testing import CliRunner
from syrupy.assertion import SnapshotAssertion
from wcmatch import glob

from greptransactions.__main__ import main as greptransactions
from statements2csv.__main__ import main as statements2csv

from .snapshot_extensions import secrets_directory_extension_factory


@pytest.fixture
def all_pdfs_input() -> list[str] | None:
    """List all PDFs used in the tests.

    Reads a file containing a path with glob expressions. Returns None if the
    file is encrypted.
    """
    try:
        with open(
            Path(os.path.dirname(__file__)) / "secrets" / "all_pdfs.lnk",
            encoding="utf-8",
        ) as fil:
            glob_str = fil.read()
    except UnicodeDecodeError:
        return None

    result = glob.glob(glob_str.strip(), flags=glob.BRACE | glob.GLOBTILDE)
    result.sort()

    assert result
    return result


@pytest.fixture
def secret_snapshot(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Return a Syrupy snapshot with _some_ encrypted files."""
    return snapshot.use_extension(secrets_directory_extension_factory())


@pytest.fixture
def secret_snapshot_all_pdfs(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Return a Syrupy snapshot with _all_ encrypted files."""
    return snapshot.use_extension(secrets_directory_extension_factory(Path("all")))


def test_statements2csv_one_file(
    all_pdfs_input: list[str] | None,
    secret_snapshot: SnapshotAssertion,
) -> None:
    """Test the `statements2csv` command with one input file.

    This integration test case runs fairly quickly, so consider running only
    the test case for quick development cycles, and save the entire test suite
    for later.
    """
    if all_pdfs_input is None:
        pytest.skip("Can't test encrypted files")
        return

    some_index = 33
    one_pdfs_input = [all_pdfs_input[some_index]]

    result = CliRunner().invoke(statements2csv, one_pdfs_input)

    assert result.output == secret_snapshot
    assert result.exit_code == 0
    assert result.output


def test_statements2csv_all_files(
    all_pdfs_input: list[str] | None, secret_snapshot_all_pdfs: SnapshotAssertion
) -> None:
    """Test the `statements2csv` command with multiple files.

    This integration test case takes a long time to run, so consider excluding
    it during development.
    """
    if all_pdfs_input is None:
        pytest.skip("Can't test encrypted files")
        return

    result = CliRunner().invoke(statements2csv, all_pdfs_input)

    assert result.output == secret_snapshot_all_pdfs
    assert result.exit_code == 0
    assert result.output


@freezegun.freeze_time(datetime.datetime(2022, 4, 20))
def test_greptransactions_default_year(
    all_pdfs_input: list[str] | None,
    capfd: pytest.CaptureFixture[str],
    secret_snapshot: SnapshotAssertion,
) -> None:
    """Test the `greptransactions` command.

    Depending on the default year, a single specified year, and multiple
    specified years, grep output should differ.
    """
    if all_pdfs_input is None:
        pytest.skip("Can't test encrypted files")
        return

    pattern = "(output|tulip)"
    result1 = CliRunner().invoke(greptransactions, pattern)
    output1, err1 = capfd.readouterr()

    result2 = CliRunner().invoke(greptransactions, ["--year", "2022", pattern])
    output2, err2 = capfd.readouterr()

    result3 = CliRunner().invoke(
        greptransactions, ["--year", "2021", "--year", "2022", pattern]
    )
    output3, err3 = capfd.readouterr()

    assert output1 == secret_snapshot
    assert output2 == secret_snapshot
    assert output3 == secret_snapshot
    assert result1.exit_code == 0
    assert result2.exit_code == 0
    assert result3.exit_code == 0
    assert not err1
    assert not err2
    assert not err3
    assert output1
    assert output2
    assert output3
    assert output1 != output2
    assert output1 != output3
    assert output2 != output3
