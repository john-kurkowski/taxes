"""syrupy snapshot extensions."""

from pathlib import Path
from typing import Any

from syrupy.data import SnapshotCollection
from syrupy.extensions.amber import AmberSnapshotExtension
from syrupy.extensions.amber.serializer import AmberDataSerializer
from syrupy.extensions.base import AbstractSyrupyExtension


class CryptAwareSerializer(AmberDataSerializer):
    """Catch exception when deserializing encrypted snapshots.

    Eases skipping tests.
    """

    @classmethod
    def read_file(cls, filepath: str) -> SnapshotCollection:
        """Override."""
        try:
            return super().read_file(filepath)
        except UnicodeDecodeError:
            empty = SnapshotCollection(location=filepath)
            return empty


class CryptAwareExtension(AmberSnapshotExtension):
    """Catch exception when discovering encrypted snapshots.

    Eases skipping tests.
    """

    serializer_class = CryptAwareSerializer


def secrets_directory_extension_factory(
    additional_folder_names: Path | None = None,
) -> type[AbstractSyrupyExtension]:
    """Use custom snapshots folder.

    Using a separate folder eases distinguishing which files should be
    encrypted or not.
    """

    class SecretsDirectoryExtension(AmberSnapshotExtension):
        serializer_class = CryptAwareSerializer

        @classmethod
        def dirname(cls, *args: Any, **kwargs: Any) -> str:
            """Override."""
            default = Path(super().dirname(*args, **kwargs))
            secrets = default / "secrets"
            if additional_folder_names:
                secrets /= additional_folder_names
            return str(secrets)

    return SecretsDirectoryExtension
