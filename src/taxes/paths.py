"""Project path helpers."""

import os
from pathlib import Path

DECRYPTED_ROOT_ENV_VAR = "TAXES_DECRYPTED_ROOT"


def repository_root() -> Path:
    """Return the root of this checkout."""
    return Path(__file__).resolve().parents[2]


def decrypted_root() -> Path:
    """Return the checkout that contains readable git-crypt files."""
    configured_root = os.environ.get(DECRYPTED_ROOT_ENV_VAR)
    if configured_root:
        return Path(configured_root).expanduser()
    return repository_root()


def decrypted_path(*parts: str | Path) -> Path:
    """Build a path under the checkout with readable git-crypt files."""
    return decrypted_root().joinpath(*parts)
