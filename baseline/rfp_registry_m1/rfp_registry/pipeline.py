"""Sprint 1: manifest -> verified local blobs -> durable evidence, no classification."""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .engine import hash_file, utc_now
from .extraction import PARSER_VERSION, Extraction, extract
from .safety import atomic_json, reject_link_chain
from .storage import LocalBlobs, Registry


def register(output: Path) -> dict[str, Any]:
    reject_link_chain(output.absolute())
    output = output.resolve(strict=True)
    lock = output / ".registry.lock"
    # Never share a writable package with another operator/process.
    with lock.open("x") as guard:
        guard.write(str(os.getpid()))
    try:
        return _register(output)
    finally:
        lock.unlink()


def _register(output: Path) -> dict[str, Any]:
    manifest_path = output / "manifest.json"
    reject_link_chain(manifest_path)
    if manifest_path.stat().st_size > 64_000_000:
        raise ValueError("Manifest exceeds metadata budget")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["schema_version"] not in ("1.0", "1.1"):
        raise ValueError("Unsupported manifest version")
    package = manifest["package_id"]
    manifest_hash = hash_file(manifest_path)
    blobs = LocalBlobs(output)
    registry = Registry(output / "registry.sqlite3")
    results = []
    deadline = time.monotonic() + 300
    text_bytes = 0
    try:
        with registry.transaction() as db:
            existing = db.execute(
                "SELECT manifest_sha256 FROM packages WHERE id=?", (package,)
            ).fetchone()
            if existing and existing[0] != manifest_hash:
                raise ValueError(
                    "Manifest changed; create a new intake rather than reuse approvals/results"
                )
            db.execute(
                "INSERT OR IGNORE INTO packages VALUES(?,?,?,?)",
                (package, manifest["project_id"], manifest_hash, "PROCESSING"),
            )
            if not existing:
                registry.event(package, None, "INTAKE_REGISTERED")
            for row in manifest["entries"]:
                if row["sha256"]:
                    db.execute(
                        "INSERT OR IGNORE INTO blobs VALUES(?,?)",
                        (row["sha256"], row["size_bytes"]),
                    )
                if not existing and row["status"] == "failed":
                    registry.event(
                        package,
                        row["entry_id"],
                        "INTAKE_ENTRY_FAILED:" + (row["error_code"] or "UNKNOWN"),
                    )
                db.execute(
                    "INSERT OR IGNORE INTO entries VALUES(?,?,?,?,?)",
                    (package, row["entry_id"], row["parent_id"], row["sha256"], json.dumps(row)),
                )

        def verify(row: dict[str, Any]) -> Path:
            try:
                path = blobs.verified_path(row["extracted_relative_path"], row["sha256"])
                if row.get("snapshot_relative_path"):
                    blobs.verified_path(row["snapshot_relative_path"], row["sha256"])
                return path
            except (OSError, ValueError):
                with registry.transaction() as db:
                    registry.event(package, row["entry_id"], "BLOB_INTEGRITY_FAILED")
                    db.execute("UPDATE packages SET status=? WHERE id=?", ("EXCEPTION", package))
                raise ValueError(
                    f"Stored bytes failed integrity verification: {row['entry_id']}"
                ) from None

        for row in manifest["entries"]:
            if row["sha256"] and row["extracted_relative_path"]:
                verify(row)
        for row in manifest["entries"]:
            if row["kind"] != "file" or row["status"] != "stored":
                continue
            entry = row["entry_id"]
            path = verify(row)
            with registry.transaction() as db:
                cached = db.execute(
                    "SELECT result FROM extractions WHERE package_id=? AND entry_id=? AND parser_version=?",
                    (package, entry, PARSER_VERSION),
                ).fetchone()
            if cached:
                result = json.loads(cached[0])
            else:
                if time.monotonic() >= deadline or text_bytes >= 8_000_000:
                    parsed = Extraction(status="deferred", error="PACKAGE_PARSE_BUDGET")
                else:
                    parsed = extract(
                        path, row["original_name"], timeout=min(20, deadline - time.monotonic())
                    )
                    if text_bytes + len(parsed.text.encode("utf-8")) > 8_000_000:
                        parsed = Extraction(status="deferred", error="PACKAGE_TEXT_BUDGET")
                verify(row)
                result = {
                    "schema_version": "1.0",
                    "package_id": package,
                    "entry_id": entry,
                    "content_sha256": row["sha256"],
                    "parent_id": row["parent_id"],
                    "source_path": row["source_path"],
                    "created_utc": utc_now(),
                    "review_required": True,
                    "extraction": asdict(parsed),
                }
                with registry.transaction() as db:
                    if parsed.status != "deferred":
                        db.execute(
                            "INSERT INTO extractions VALUES(?,?,?,?,?)",
                            (package, entry, PARSER_VERSION, row["sha256"], json.dumps(result)),
                        )
                    registry.event(package, entry, "EXTRACTION_" + parsed.status.upper())
            text_bytes += len(result["extraction"]["text"].encode("utf-8"))
            results.append(result)
        summary = {
            "documents": len(results),
            "parsed": sum(r["extraction"]["status"] == "parsed" for r in results),
            "exceptions": sum(r["extraction"]["status"] != "parsed" for r in results),
        }
        atomic_json(
            output / "extractions.json",
            {
                "schema_version": "1.0",
                "package_id": package,
                "summary": summary,
                "documents": results,
            },
        )
        with registry.transaction() as db:
            state = (
                "EXCEPTION"
                if summary["exceptions"] or manifest["summary"]["failed_entries"]
                else "PENDING_REVIEW"
            )
            old = db.execute("SELECT status FROM packages WHERE id=?", (package,)).fetchone()[0]
            db.execute("UPDATE packages SET status=? WHERE id=?", (state, package))
            if old != state:
                registry.event(package, None, state)
        return summary
    finally:
        registry.close()
