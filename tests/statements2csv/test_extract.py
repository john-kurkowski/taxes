"""Test the extract module."""

from pathlib import Path

import camelot.io
import pytest

from statements2csv.extract import extract_dataframes


def test_extract_dataframes_must_contain_one_year(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test input path to `extract_dataframes` must contain one year."""
    monkeypatch.setattr(camelot.io, "read_pdf", lambda *_, **__: [])
    flavor = None

    with pytest.raises(ValueError, match="possible statement years"):
        list(extract_dataframes(Path("years") / "000" / "a.pdf", flavor))

    with pytest.raises(ValueError, match="possible statement years"):
        list(
            extract_dataframes(
                Path("years") / "2020" / "until" / "2029" / "a.pdf", None
            )
        )

    assert list(extract_dataframes(Path("years") / "2020" / "a.pdf", flavor)) == []
