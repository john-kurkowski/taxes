"""Integration tests for the entire project.

Keep to a minimum. https://testing.googleblog.com/2015/04/just-say-no-to-more-end-to-end-tests.html.
"""

import datetime
import os.path
from pathlib import Path

import freezegun
import pytest
from click.testing import CliRunner
from syrupy import SnapshotAssertion
from wcmatch import glob

from greptransactions.__main__ import main as greptransactions
from statements2csv.__main__ import main as statements2csv

from .snapshot_extensions import secrets_directory_extension_factory


@pytest.fixture
def all_pdfs_input() -> list[str] | None:
    try:
        with open(
            Path(os.path.dirname(__file__)) / "secrets" / "all_pdfs.lnk",
            encoding="utf-8",
        ) as fil:
            result = glob.glob(fil.read().strip(), flags=glob.BRACE | glob.GLOBTILDE)
    except UnicodeDecodeError:
        return None

    assert result
    return result


@pytest.fixture
def secret_snapshot(snapshot):
    return snapshot.use_extension(secrets_directory_extension_factory())


@pytest.fixture
def secret_snapshot_all_pdfs(snapshot):
    return snapshot.use_extension(secrets_directory_extension_factory(Path("all")))


def test_statements2csv_one_file(
    all_pdfs_input: list[str] | None,
    secret_snapshot: SnapshotAssertion,
) -> None:
    if all_pdfs_input is None:
        pytest.skip("Can't test encrypted files")
        return

    one_pdfs_input = all_pdfs_input[:1]

    result = CliRunner().invoke(statements2csv, one_pdfs_input)

    assert result.exit_code == 0
    assert result.output
    assert result.output == secret_snapshot


def test_statements2csv_all_files(
    all_pdfs_input: list[str] | None, secret_snapshot_all_pdfs: SnapshotAssertion
) -> None:
    if all_pdfs_input is None:
        pytest.skip("Can't test encrypted files")
        return

    result = CliRunner().invoke(statements2csv, all_pdfs_input)

    assert result.exit_code == 0
    assert result.output
    assert result.output == secret_snapshot_all_pdfs


@freezegun.freeze_time(datetime.datetime(2022, 4, 20))
def test_greptransactions_default_year(
    all_pdfs_input: list[str] | None,
    capfd: pytest.CaptureFixture,
    secret_snapshot: SnapshotAssertion,
) -> None:
    if all_pdfs_input is None:
        pytest.skip("Can't test encrypted files")
        return

    pattern = "(output|tulip)"
    result1 = CliRunner().invoke(greptransactions, pattern)
    output1, err1 = capfd.readouterr()

    result2 = CliRunner().invoke(greptransactions, ["--year", "2022", pattern])
    output2, err2 = capfd.readouterr()

    assert result1.exit_code == 0
    assert result2.exit_code == 0
    assert not err1
    assert not err2
    assert output1
    assert output2
    assert output1 != output2
    assert output1 == secret_snapshot
    assert output2 == secret_snapshot
