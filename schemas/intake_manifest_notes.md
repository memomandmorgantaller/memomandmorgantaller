# Manifest/registry schema guidance

Baseline `manifest.schema.json` lives under `baseline/rfp_registry_m1`; retain compatibility or ship a versioned successor.

Minimum source-entry fields: `entry_id`, `package_id`, `parent_entry_id`, `source_logical_path`, `original_name`, `record_kind`, `status`, `error_code`, `size_bytes`, `sha256`, `blob_ref`, `archive_depth`, `source_root_hash` or source snapshot ref, `parser_status`, `created_utc`.

Minimum package summary: number of source files, archives, directory entries, extracted leaf files, blocked entries, failures, duplicates by content hash, reconciled-entry count, run status, failed causes, total input/expanded bytes, quota settings, schema version.

Invariant: each discovered archive member has exactly one source-entry record. An entry may be blocked, unsupported, or failed, but never disappear; parent-child archive chains are queryable; content hash matches blob; no physical destination derives from untrusted archive path.
