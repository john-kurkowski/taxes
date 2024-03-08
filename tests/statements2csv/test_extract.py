"""Test the extract module."""

from pathlib import Path

import camelot  # type: ignore[import]
import pytest

from statements2csv.extract import extract_dataframes


def test_extract_dataframes_must_contain_one_year(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test input path to `extract_dataframes` must contain one year."""
    monkeypatch.setattr(camelot, "read_pdf", lambda *_, **__: [])

    with pytest.raises(ValueError, match="possible statement years"):
        list(extract_dataframes(Path("years") / "000" / "a.pdf"))

    with pytest.raises(ValueError, match="possible statement years"):
        list(extract_dataframes(Path("years") / "2020" / "until" / "2029" / "a.pdf"))

    assert list(extract_dataframes(Path("years") / "2020" / "a.pdf")) == []
