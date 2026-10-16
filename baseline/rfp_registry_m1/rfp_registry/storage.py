"""Local blob boundary and SQLite migrations; no network or publishing authority."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Protocol

from .engine import hash_file, utc_now
from .safety import reject_link_chain


class BlobStore(Protocol):
    def verified_path(self, relative: str, digest: str) -> Path: ...


class LocalBlobs:
    def __init__(self, root: Path):
        self.root = root.resolve(strict=True)

    def verified_path(self, relative: str, digest: str) -> Path:
        path = self.root / relative
        reject_link_chain(path)
        resolved = path.resolve(strict=True)
        if not resolved.is_relative_to(self.root) or not resolved.is_file():
            raise ValueError("Blob outside package")
        if hash_file(resolved) != digest:
            raise ValueError("Blob integrity mismatch")
        return resolved


class Registry:
    """Schema 1 is created transactionally. Unknown newer databases are refused."""

    def __init__(self, path: Path):
        reject_link_chain(path)
        self.db = sqlite3.connect(path)
        self.db.execute("PRAGMA foreign_keys=ON")
        version = self.db.execute("PRAGMA user_version").fetchone()[0]
        if version not in (0, 1):
            self.db.close()
            raise ValueError("Unsupported registry schema version")
        if version == 0:
            self.db.executescript("""
                BEGIN;
                CREATE TABLE packages(id TEXT PRIMARY KEY, project TEXT NOT NULL,
                    manifest_sha256 TEXT NOT NULL, status TEXT NOT NULL);
                CREATE TABLE blobs(sha256 TEXT PRIMARY KEY, size INTEGER NOT NULL);
                CREATE TABLE entries(package_id TEXT NOT NULL REFERENCES packages(id),
                    id TEXT NOT NULL, parent_id TEXT, blob_sha256 TEXT REFERENCES blobs(sha256),
                    payload TEXT NOT NULL, PRIMARY KEY(package_id,id));
                CREATE TABLE extractions(package_id TEXT NOT NULL, entry_id TEXT NOT NULL,
                    parser_version TEXT NOT NULL, content_sha256 TEXT NOT NULL,
                    result TEXT NOT NULL, PRIMARY KEY(package_id,entry_id,parser_version),
                    FOREIGN KEY(package_id,entry_id) REFERENCES entries(package_id,id));
                CREATE TABLE audit_events(id INTEGER PRIMARY KEY, package_id TEXT NOT NULL,
                    entry_id TEXT, actor TEXT NOT NULL, event TEXT NOT NULL, created_utc TEXT NOT NULL);
                CREATE TRIGGER audit_no_update BEFORE UPDATE ON audit_events BEGIN
                    SELECT RAISE(ABORT,'append-only audit'); END;
                CREATE TRIGGER audit_no_delete BEFORE DELETE ON audit_events BEGIN
                    SELECT RAISE(ABORT,'append-only audit'); END;
                PRAGMA user_version=1;
                COMMIT;
            """)

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        with self.db:
            yield self.db

    def event(self, package: str, entry: str | None, event: str) -> None:
        self.db.execute(
            "INSERT INTO audit_events(package_id,entry_id,actor,event,created_utc) VALUES(?,?,?,?,?)",
            (package, entry, "local-operator", event, utc_now()),
        )

    def close(self) -> None:
        self.db.close()
