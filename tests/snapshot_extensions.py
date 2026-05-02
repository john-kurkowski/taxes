"""syrupy snapshot extensions."""

from pathlib import Path
from typing import Any

from syrupy.data import SnapshotCollection, SnapshotCollections
from syrupy.extensions.amber import AmberSnapshotExtension
from syrupy.extensions.amber.serializer import AmberDataSerializer
from syrupy.extensions.base import AbstractSyrupyExtension

from taxes.paths import decrypted_path, decrypted_root, repository_root


def _is_encrypted(filepath: str) -> bool:
    try:
        Path(filepath).read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return True
    return False


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

    def discover_snapshots(
        self,
        *,
        test_location: Any,
        ignore_extensions: list[str] | None = None,
    ) -> SnapshotCollections:
        """Skip unreadable snapshots when readable copies live elsewhere."""
        discovered = super().discover_snapshots(
            test_location=test_location,
            ignore_extensions=ignore_extensions,
        )
        if decrypted_root() == repository_root():
            return discovered

        readable = SnapshotCollections()
        for snapshot_collection in discovered:
            if _is_encrypted(snapshot_collection.location):
                continue
            readable.add(snapshot_collection)
        return readable


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
            if default.is_absolute():
                relative_default = default.relative_to(repository_root())
            else:
                relative_default = default
            secrets = decrypted_path(relative_default, "secrets")
            if additional_folder_names:
                secrets /= additional_folder_names
            return str(secrets)

    return SecretsDirectoryExtension
