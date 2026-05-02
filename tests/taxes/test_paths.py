"""Tests for project path helpers."""

from pathlib import Path

import pytest

from taxes import paths


def test_decrypted_root_defaults_to_repository_root(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Use the current checkout when no decrypted checkout is configured."""
    checkout = tmp_path / "checkout"
    monkeypatch.setattr(paths, "repository_root", lambda: checkout)
    monkeypatch.delenv(paths.DECRYPTED_ROOT_ENV_VAR, raising=False)

    assert paths.decrypted_root() == checkout
    assert paths.decrypted_path("tests", "secrets") == checkout / "tests" / "secrets"


def test_decrypted_root_uses_environment_override(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Use the configured checkout for files that may require git-crypt."""
    monkeypatch.setenv(paths.DECRYPTED_ROOT_ENV_VAR, str(tmp_path))

    assert paths.decrypted_root() == tmp_path
    assert paths.decrypted_path("tests", "secrets") == tmp_path / "tests" / "secrets"
