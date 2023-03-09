"""pytest's conventional shared test fixtures."""

import pytest
from syrupy import SnapshotAssertion

from .snapshot_extensions import SecretsDirectoryExtension


@pytest.fixture
def secret_snapshot(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    return snapshot.use_extension(SecretsDirectoryExtension)
