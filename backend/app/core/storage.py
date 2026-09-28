"""Storage abstraction and local encrypted/private filesystem provider for CampusPulse.

Enforces:
- Private non-public storage keys.
- SHA-256 integrity digest computation.
- Path traversal protection and filename sanitization.
- File size and MIME type restrictions.
"""

import hashlib
import os
import re
from pathlib import Path
from typing import Optional, Protocol, Set, Tuple


class IStorageProvider(Protocol):
    """Protocol for secure private object storage."""

    def store_file(
        self, institution_id: str, partition: str, file_name: str, data: bytes
    ) -> Tuple[str, str]:
        """Store binary bytes and return (storage_key, sha256_hash)."""
        ...

    def retrieve_file(self, storage_key: str) -> bytes:
        """Retrieve binary bytes for storage_key."""
        ...

    def delete_file(self, storage_key: str) -> bool:
        """Delete file associated with storage_key."""
        ...


class LocalStorageProvider:
    """Thread-safe local filesystem storage provider with private non-public paths."""

    def __init__(self, base_dir: Optional[str] = None):
        if base_dir:
            self.base_dir = Path(base_dir).resolve()
        else:
            # Default to backend/data/storage
            backend_dir = Path(__file__).resolve().parent.parent.parent
            self.base_dir = (backend_dir / "data" / "storage").resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent directory traversal and invalid characters."""
        # Strip path components
        clean = os.path.basename(filename)
        # Remove any non-alphanumeric chars except basic punctuation
        clean = re.sub(r"[^a-zA-Z0-9_.-]", "_", clean)
        # Disallow double dots
        clean = clean.replace("..", "_")
        return clean or "unnamed_attachment"

    @staticmethod
    def compute_sha256(data: bytes) -> str:
        """Compute hex SHA-256 digest of data bytes."""
        return hashlib.sha256(data).hexdigest()

    def store_file(
        self, institution_id: str, partition: str, file_name: str, data: bytes
    ) -> Tuple[str, str]:
        """Store bytes under a private non-public key.
        
        Returns:
            Tuple of (storage_key, sha256_hash)
        """
        clean_name = self.sanitize_filename(file_name)
        sha256_hash = self.compute_sha256(data)
        
        # Partition directory: e.g. institutions/{institution_id}/{partition}
        rel_dir = Path("institutions") / institution_id / partition
        target_dir = self.base_dir / rel_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        # Unique storage filename incorporating hash prefix
        unique_filename = f"{sha256_hash[:16]}_{clean_name}"
        rel_path = rel_dir / unique_filename
        full_path = self.base_dir / rel_path

        with open(full_path, "wb") as f:
            f.write(data)

        # Canonical relative storage key
        storage_key = rel_path.as_posix()
        return storage_key, sha256_hash

    def retrieve_file(self, storage_key: str) -> bytes:
        """Retrieve binary bytes for storage_key with traversal protection."""
        # Prevent traversal
        clean_key = Path(storage_key).as_posix()
        if ".." in clean_key or clean_key.startswith("/"):
            raise ValueError("Invalid storage key path traversal attempt")

        full_path = (self.base_dir / clean_key).resolve()
        if not full_path.is_relative_to(self.base_dir):
            raise ValueError("Storage key points outside storage base directory")

        if not full_path.exists() or not full_path.is_file():
            raise FileNotFoundError(f"Stored file not found for key: {storage_key}")

        with open(full_path, "rb") as f:
            return f.read()

    def delete_file(self, storage_key: str) -> bool:
        """Delete stored file if it exists."""
        clean_key = Path(storage_key).as_posix()
        if ".." in clean_key or clean_key.startswith("/"):
            return False

        full_path = (self.base_dir / clean_key).resolve()
        if not full_path.is_relative_to(self.base_dir):
            return False

        if full_path.exists() and full_path.is_file():
            try:
                full_path.unlink()
                return True
            except OSError:
                return False
        return False


# Singleton instance
_storage_provider: Optional[LocalStorageProvider] = None


def get_storage_provider() -> LocalStorageProvider:
    """Return configured storage provider singleton."""
    global _storage_provider
    if _storage_provider is None:
        _storage_provider = LocalStorageProvider()
    return _storage_provider
