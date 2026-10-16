"""Local read-only intake and bounded ZIP decomposition.

Threat model: untrusted archives and filenames. Not a sandbox for malicious parsers;
scan inputs with corporate endpoint security before processing.
"""

from __future__ import annotations

import csv
import hashlib
import os
import shutil
import stat
import time
import uuid
import zipfile
import zlib
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from .safety import atomic_json, is_link, reject_link_chain, zip_metadata

SCHEMA_VERSION = "1.1"


@dataclass(frozen=True)
class Limits:
    max_entries: int = 20000
    max_metadata_bytes: int = 8_000_000
    max_seconds: float = 300
    min_free_bytes: int = 64_000_000
    max_depth: int = 4
    max_files: int = 10000
    max_file_bytes: int = 1_000_000_000
    max_total_bytes: int = 5_000_000_000
    max_archive_bytes: int = 2_000_000_000
    max_compression_ratio: float = 200.0
    max_path_chars: int = 240


@dataclass
class Entry:
    entry_id: str
    parent_id: str | None
    source_path: str
    original_name: str
    kind: str
    status: str
    size_bytes: int | None = None
    sha256: str | None = None
    extracted_relative_path: str | None = None
    error_code: str | None = None
    detail: str | None = None
    depth: int = 0
    snapshot_relative_path: str | None = None


class LimitError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as inp:
        for chunk in iter(lambda: inp.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_member_name(name: str, max_chars: int) -> str:
    """Validate zip logical paths; extraction uses generated filenames, not these paths."""
    if not name or "\x00" in name or "\\" in name or len(name) > max_chars:
        raise LimitError("UNSAFE_PATH", "Invalid or overlong archive entry path")
    if name.startswith("/") or name.startswith("//") or ":" in name:
        raise LimitError("UNSAFE_PATH", "Absolute/drive or alternate stream path")
    if any(ord(c) < 32 or c in '<>"|?*' for c in name):
        raise LimitError("UNSAFE_PATH", "Windows-incompatible characters")
    parts = PurePosixPath(name).parts
    if not parts or any(part in ("..", ".", "") for part in name.rstrip("/").split("/")):
        raise LimitError("UNSAFE_PATH", "Traversal or ambiguous path")
    if any(
        part.rstrip(" .") != part
        or part.upper().split(".")[0]
        in {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            *(f"COM{i}" for i in range(1, 10)),
            *(f"LPT{i}" for i in range(1, 10)),
            *(f"COM{i}" for i in "¹²³"),
            *(f"LPT{i}" for i in "¹²³"),
        }
        for part in parts
    ):
        raise LimitError("UNSAFE_PATH", "Windows-incompatible path component")
    return name


class Processor:
    def __init__(self, source: Path, output: Path, project: str, limits: Limits | None = None):
        limits = limits or Limits()
        reject_link_chain(source.absolute())
        reject_link_chain(output.absolute())
        self.source = source.resolve(strict=True)
        self.output = output.resolve()
        self.project = project
        self.limits = limits
        self.entries: list[Entry] = []
        self.total_bytes = 0
        self.file_count = 0
        self.intake_id = "PKG-" + uuid.uuid4().hex[:12].upper()
        self.files_dir = self.output / "extracted"
        self.started = time.monotonic()
        self.enumeration_complete = True
        for value in asdict(limits).values():
            if value < 0:
                raise ValueError("Limits must not be negative")

    def add(
        self,
        parent: str | None,
        source_path: str,
        name: str,
        kind: str,
        status: str,
        depth: int = 0,
        **kwargs: Any,
    ) -> Entry:
        if len(self.entries) >= self.limits.max_entries:
            self.enumeration_complete = False
            raise LimitError(
                "ENTRY_COUNT_LIMIT", "Entry inventory limit reached; remaining tree not inspected"
            )
        row = Entry(
            entry_id=f"E{len(self.entries) + 1:07d}",
            parent_id=parent,
            source_path=source_path,
            original_name=name,
            kind=kind,
            status=status,
            depth=depth,
            **kwargs,
        )
        self.entries.append(row)
        return row

    def check_runtime(self, reserve: int = 0) -> None:
        if time.monotonic() - self.started >= self.limits.max_seconds:
            raise LimitError("TIME_LIMIT", "Package deadline exceeded")
        if shutil.disk_usage(self.output).free < self.limits.min_free_bytes + reserve:
            raise LimitError("DISK_LIMIT", "Insufficient disk reserve")

    def ensure_budget(self, declared: int) -> None:
        self.check_runtime(declared)
        if self.file_count >= self.limits.max_files:
            raise LimitError("FILE_COUNT_LIMIT", "Maximum number of extracted files reached")
        if declared > self.limits.max_file_bytes:
            raise LimitError("FILE_SIZE_LIMIT", "Entry exceeds per-file size limit")
        if self.total_bytes + declared > self.limits.max_total_bytes:
            raise LimitError("TOTAL_SIZE_LIMIT", "Total extracted size limit exceeded")

    def stream_to_store(self, src: Any, declared: int | None = None) -> tuple[str, int, str]:
        self.ensure_budget(declared or 0)
        self.files_dir.mkdir(parents=True, exist_ok=True)
        dest_name = uuid.uuid4().hex + ".bin"
        target = self.files_dir / dest_name
        digest = hashlib.sha256()
        count = 0
        try:
            with target.open("xb") as out:
                while chunk := src.read(1024 * 1024):
                    self.check_runtime(len(chunk))
                    count += len(chunk)
                    if count > self.limits.max_file_bytes:
                        raise LimitError("FILE_SIZE_LIMIT", "Streaming per-file limit exceeded")
                    if self.total_bytes + count > self.limits.max_total_bytes:
                        raise LimitError("TOTAL_SIZE_LIMIT", "Streaming total limit exceeded")
                    if declared is not None and count > declared:
                        raise LimitError("SIZE_MISMATCH", "Uncompressed size exceeded stated size")
                    out.write(chunk)
                    digest.update(chunk)
            if declared is not None and count != declared:
                raise LimitError("SIZE_MISMATCH", "Source size changed while reading")
            self.total_bytes += count
            self.file_count += 1
            return (Path("extracted") / dest_name).as_posix(), count, digest.hexdigest()
        except BaseException:
            target.unlink(missing_ok=True)
            raise

    def handle_file(self, path: Path, logical_path: str, parent: str | None, depth: int) -> None:
        kind = "archive" if path.suffix.lower() == ".zip" else "file"
        entry = self.add(parent, logical_path, path.name, kind, "pending", depth)
        try:
            if is_link(path):
                raise LimitError("SYMLINK", "Symbolic links are not accepted")
            safe_member_name(logical_path, self.limits.max_path_chars)
            if not path.is_file():
                raise LimitError("NOT_REGULAR_FILE", "Not a regular file")
            if kind == "archive" and path.stat().st_size > self.limits.max_archive_bytes:
                raise LimitError("ARCHIVE_SIZE_LIMIT", "ZIP archive too large")
            reject_link_chain(path)
            before = path.stat()
            with path.open("rb") as inp:
                opened = os.fstat(inp.fileno())
                if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
                    opened.st_dev,
                    opened.st_ino,
                    opened.st_size,
                    opened.st_mtime_ns,
                ):
                    raise LimitError("SOURCE_CHANGED", "Source changed before opening")
                rel, size, digest = self.stream_to_store(inp, opened.st_size)
                entry.extracted_relative_path, entry.size_bytes, entry.sha256 = rel, size, digest
                after = os.fstat(inp.fileno())
                if (opened.st_size, opened.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                    raise LimitError("SOURCE_CHANGED", "Source changed while reading")
            originals = self.output / "originals"
            originals.mkdir(exist_ok=True)
            snapshot = originals / (entry.entry_id + ".bin")
            self.check_runtime(size)
            pending_snapshot = snapshot.with_suffix(".tmp")
            try:
                with (self.output / rel).open("rb") as inp, pending_snapshot.open("xb") as out:
                    while chunk := inp.read(1024 * 1024):
                        self.check_runtime(len(chunk))
                        out.write(chunk)
                    out.flush()
                    os.fsync(out.fileno())
                pending_snapshot.replace(snapshot)
            finally:
                pending_snapshot.unlink(missing_ok=True)
            snapshot.chmod(stat.S_IREAD)
            entry.snapshot_relative_path = snapshot.relative_to(self.output).as_posix()
            entry.extracted_relative_path, entry.size_bytes, entry.sha256 = rel, size, digest
            entry.status = "stored"
            with (self.output / rel).open("rb") as stored:
                magic = stored.read(4)
            if magic in (
                b"PK\x03\x04",
                b"PK\x05\x06",
                b"PK\x07\x08",
            ) and path.suffix.lower() not in (".docx", ".xlsx", ".pptx"):
                kind = entry.kind = "archive"
            (self.output / rel).chmod(stat.S_IREAD)
            if kind == "archive":
                self.inspect_archive(self.output / rel, logical_path, entry.entry_id, depth + 1)
        except LimitError as e:
            entry.status, entry.error_code, entry.detail = "failed", e.code, str(e)
        except (OSError, zipfile.BadZipFile, EOFError) as e:
            entry.status, entry.error_code, entry.detail = "failed", "READ_ERROR", str(e)[:300]

    def inspect_archive(self, archive_path: Path, origin: str, parent: str, depth: int) -> None:
        if depth > self.limits.max_depth:
            self.enumeration_complete = False
            self.add(
                parent,
                origin + "!/",
                "(archive depth)",
                "archive_issue",
                "failed",
                depth,
                error_code="DEPTH_LIMIT",
                detail="Maximum nested archive depth exceeded",
            )
            return
        try:
            self.check_runtime()
            zip_metadata(
                archive_path,
                self.limits.max_entries - len(self.entries),
                self.limits.max_metadata_bytes,
            )
            with zipfile.ZipFile(archive_path) as zf:
                if len(zf.infolist()) > self.limits.max_entries - len(self.entries):
                    raise ValueError("ZIP actual entry count exceeds budget")
                for info in zf.infolist():
                    member_name = info.orig_filename
                    logical = origin + "!/" + member_name
                    entry = self.add(
                        parent,
                        logical,
                        member_name,
                        "directory"
                        if info.is_dir()
                        else ("archive" if info.filename.lower().endswith(".zip") else "file"),
                        "pending",
                        depth,
                    )
                    try:
                        self.check_runtime()
                        safe_member_name(member_name, self.limits.max_path_chars)
                        mode = (info.external_attr >> 16) & 0xFFFF
                        if stat.S_ISLNK(mode) or info.external_attr & 0x400:
                            raise LimitError("SYMLINK", "ZIP symbolic link refused")
                        if info.flag_bits & 1:
                            raise LimitError("ENCRYPTED", "Encrypted ZIP entry")
                        if info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
                            raise LimitError(
                                "COMPRESSION_UNSUPPORTED", "Only stored/deflated ZIP supported"
                            )
                        if mode and stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR):
                            raise LimitError("SPECIAL_FILE", "ZIP special file refused")
                        if info.is_dir():
                            entry.status = "listed"
                            continue
                        if info.file_size > self.limits.max_file_bytes:
                            raise LimitError(
                                "FILE_SIZE_LIMIT", "Declared uncompressed file too large"
                            )
                        ratio = info.file_size / max(1, info.compress_size)
                        if (
                            ratio > self.limits.max_compression_ratio
                            and info.file_size > 1024 * 1024
                        ):
                            raise LimitError("COMPRESSION_RATIO", "Suspicious ZIP expansion ratio")
                        if (
                            info.filename.lower().endswith(".zip")
                            and info.file_size > self.limits.max_archive_bytes
                        ):
                            raise LimitError("ARCHIVE_SIZE_LIMIT", "Nested ZIP too large")
                        with zf.open(info) as inp:
                            rel, size, digest = self.stream_to_store(inp, info.file_size)
                        if size != info.file_size:
                            (self.output / rel).unlink(missing_ok=True)
                            raise LimitError("SIZE_MISMATCH", "Uncompressed size mismatch")
                        entry.extracted_relative_path, entry.size_bytes, entry.sha256 = (
                            rel,
                            size,
                            digest,
                        )
                        entry.status = "stored"
                        stored_path = self.output / rel
                        with stored_path.open("rb") as stored:
                            magic = stored.read(4)
                        if magic in (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08") and Path(
                            info.filename
                        ).suffix.lower() not in (
                            ".docx",
                            ".xlsx",
                            ".pptx",
                        ):
                            entry.kind = "archive"
                        stored_path.chmod(stat.S_IREAD)
                        if entry.kind == "archive":
                            self.inspect_archive(
                                self.output / rel, logical, entry.entry_id, depth + 1
                            )
                    except LimitError as e:
                        entry.status, entry.error_code, entry.detail = "failed", e.code, str(e)
                    except (
                        OSError,
                        RuntimeError,
                        ValueError,
                        EOFError,
                        zipfile.BadZipFile,
                        NotImplementedError,
                        zlib.error,
                    ) as e:
                        entry.status, entry.error_code, entry.detail = (
                            "failed",
                            "EXTRACTION_ERROR",
                            str(e)[:300],
                        )
        except (OSError, zipfile.BadZipFile, ValueError) as e:
            self.enumeration_complete = False
            self.add(
                parent,
                origin + "!/(archive error)",
                "(archive error)",
                "archive_issue",
                "failed",
                depth,
                error_code="INVALID_ARCHIVE",
                detail=str(e)[:300],
            )

    def run(self) -> dict[str, Any]:
        if not self.project.strip():
            raise ValueError("Project ID is required")
        if (
            self.source == self.output
            or self.source in self.output.parents
            or self.output in self.source.parents
        ):
            raise ValueError("Input and output must not overlap")
        # Exclusive directory reservation prevents concurrent jobs sharing an output.
        if self.output.exists():
            if any(self.output.iterdir()):
                raise ValueError("Output directory must be empty or nonexistent")
            self.output.rmdir()
        self.output.mkdir(parents=True, exist_ok=False)
        try:
            if self.source.is_file():
                self.handle_file(self.source, self.source.name, None, 0)
            elif self.source.is_dir():

                def walk_error(error: OSError) -> None:
                    self.enumeration_complete = False
                    self.add(
                        None,
                        str(error.filename),
                        "(directory read error)",
                        "directory",
                        "failed",
                        error_code="DIRECTORY_READ_ERROR",
                        detail=str(error)[:300],
                    )

                for root, dirs, files in os.walk(
                    self.source, followlinks=False, onerror=walk_error
                ):
                    root_path = Path(root)
                    dirs.sort()
                    for dirname in list(dirs):
                        p = root_path / dirname
                        if is_link(p):
                            self.add(
                                None,
                                str(p.relative_to(self.source)),
                                dirname,
                                "directory",
                                "failed",
                                error_code="SYMLINK",
                                detail="Directory symlink refused",
                            )
                            dirs.remove(dirname)
                        else:
                            row = self.add(
                                None,
                                p.relative_to(self.source).as_posix(),
                                dirname,
                                "directory",
                                "listed",
                            )
                            try:
                                safe_member_name(row.source_path, self.limits.max_path_chars)
                            except LimitError as error:
                                row.status, row.error_code, row.detail = (
                                    "failed",
                                    error.code,
                                    str(error),
                                )
                                self.enumeration_complete = False
                                dirs.remove(dirname)
                    for name in sorted(files):
                        p = root_path / name
                        self.handle_file(p, p.relative_to(self.source).as_posix(), None, 0)
            else:
                raise ValueError("Source must be a file or directory")
        except (LimitError, KeyboardInterrupt, OSError) as error:
            self.enumeration_complete = False
            # Reserve one explicit package issue even when the inventory cap was hit.
            self.entries.append(
                Entry(
                    f"E{len(self.entries) + 1:07d}",
                    None,
                    "(package issue)",
                    "(package issue)",
                    "archive_issue",
                    "failed",
                    error_code=getattr(
                        error,
                        "code",
                        "CANCELLED" if isinstance(error, KeyboardInterrupt) else "FILESYSTEM_ERROR",
                    ),
                    detail=str(error),
                )
            )
        finally:
            for row in self.entries:
                if row.status == "pending":
                    row.status, row.error_code = "failed", "INTERRUPTED"
            self.write_manifest()
        return self.summary()

    def summary(self) -> dict[str, Any]:
        return {
            "enumeration_complete": self.enumeration_complete,
            "entries": len(self.entries),
            "stored_files": sum(e.status == "stored" for e in self.entries),
            "failed_entries": sum(e.status == "failed" for e in self.entries),
            "total_stored_bytes": self.total_bytes,
            "package_id": self.intake_id,
            "manifest_path": str(self.output / "manifest.json"),
        }

    def write_manifest(self) -> None:
        data = {
            "schema_version": SCHEMA_VERSION,
            "package_id": self.intake_id,
            "project_id": self.project,
            "generated_utc": utc_now(),
            "source": str(self.source),
            "limits": asdict(self.limits),
            "summary": self.summary(),
            "entries": [asdict(e) for e in self.entries],
        }
        atomic_json(self.output / "manifest.json", data)
        columns = list(Entry.__dataclass_fields__)
        with (self.output / "manifest.csv.tmp").open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()

            # Prevent spreadsheet formula execution; authoritative JSON keeps exact names.
            def cell(value: Any) -> Any:
                return (
                    "'" + value
                    if isinstance(value, str) and value.startswith(("=", "+", "-", "@", "\t", "\r"))
                    else value
                )

            writer.writerows({k: cell(v) for k, v in asdict(e).items()} for e in self.entries)
        (self.output / "manifest.csv.tmp").replace(self.output / "manifest.csv")
