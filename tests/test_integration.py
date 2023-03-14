"""Integration tests for the entire project.

Keep to a minimum. https://testing.googleblog.com/2015/04/just-say-no-to-more-end-to-end-tests.html.
"""

import os.path
from pathlib import Path

import pytest
from click.testing import CliRunner
from syrupy import SnapshotAssertion
from wcmatch import glob

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
