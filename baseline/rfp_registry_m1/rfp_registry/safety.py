"""Filesystem and ZIP checks shared by intake and inert Office readers."""

from __future__ import annotations

import json
import os
import stat
import struct
import tempfile
from pathlib import Path
from typing import Any


def is_link(path: Path) -> bool:
    info = path.lstat()
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0) & 0x400  # FILE_ATTRIBUTE_REPARSE_POINT
    )


def reject_link_chain(path: Path) -> None:
    for part in (path, *path.parents):
        if part.exists() or part.is_symlink():
            if is_link(part):
                raise ValueError("Symlink/reparse-point path is not accepted")


def atomic_json(path: Path, value: Any) -> None:
    descriptor, name = tempfile.mkstemp(prefix=".registry-", suffix=".tmp", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as out:
            json.dump(value, out, ensure_ascii=True, indent=2)
            out.flush()
            os.fsync(out.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def zip_metadata(path: Path, max_entries: int, max_metadata_bytes: int) -> int:
    """Bound central-directory allocation BEFORE ZipFile reads it into memory.

    ZIP64/multidisk archives are intentionally unsupported in this first slice.
    The original bytes remain retained, with a blocked archive issue.
    """
    with path.open("rb") as source:
        source.seek(0, 2)
        length = source.tell()
        source.seek(max(0, length - 65557))
        tail = source.read()
    offset = tail.rfind(b"PK\x05\x06")
    if offset < 0 or len(tail) - offset < 22:
        raise ValueError("Missing ZIP end directory")
    _, disk, central_disk, disk_count, count, size, start, comment = struct.unpack_from(
        "<4s4H2LH", tail, offset
    )
    if offset + 22 + comment != len(tail):
        raise ValueError("Invalid ZIP end directory/trailing data")
    if disk or central_disk or disk_count != count:
        raise ValueError("Multidisk ZIP is unsupported")
    if count == 65535 or size == 0xFFFFFFFF or start == 0xFFFFFFFF:
        raise ValueError("ZIP64 is unsupported")
    if count > max_entries or size > max_metadata_bytes:
        raise ValueError(f"ZIP metadata budget exceeded; {count} declared entries not enumerated")
    if start + size > length - len(tail) + offset:
        raise ValueError("Invalid ZIP directory bounds")
    return count
