# Audited baseline implementation, as received

## What actually exists
Source: `baseline/rfp_registry_m1` copied from delivered `RFP_Document_Registry_Milestone_1.zip`. Contains Python package with CLI, bounded recursive ZIP extraction, opaque extracted filenames, SHA-256, `manifest.json` and `manifest.csv`, a JSON schema, PowerShell setup script, synthetic package and pytest tests.

## Verification in this handoff environment
`python -m pytest -q` executed against the extracted baseline: **10 passed in 0.14s** on Linux in this runtime. This does not verify Windows, all archive security properties, or handling of real CS202 data. Prior assistant also described 10 passing tests; independently reconfirmed here.

## Gaps / caveats Codex must not overlook
- Does **not** contain FastAPI/web UI, database, document text extraction, AI agents, verified company examples, nine-folder classifier, approval workflow or SharePoint connector.
- README says originals are left untouched at source but `run()` does not create an immutable source copy in a dedicated intake archive; intake preservation contract remains to be implemented.
- ZIP directory entries are listed before path validation; potentially unsafe names get recorded as listed, though none written using those names. Normalize validation/status for all entries.
- `file_count` counts stored files rather than all reported entries; large malicious archives can potentially create an oversized manifest before hitting stored-file limit. Enforce metadata/entry count globally.
- ZIP content integrity/CRC validation relies on `zipfile` extraction behavior; add explicit tests for corruption and broader error paths.
- Windows-specific reparse points/junction handling and TOCTOU protections need implementation/testing; symlink checks alone are incomplete.
- On scan/streaming failures, some archive entries may be `stored` while descendants are `failed`; determine package-level success explicitly; ensure caller exit status and output reconciliation.
- Source/output overlap and source snapshots need additional tests (including output as ancestor, source modification during run).
- Quota defaults, disk space reservation and safe resource budget for thousand-file packages require tuning and configuration.
- Flat folder rulebook exists only in this handoff config; not integrated into baseline code.
- Baseline `pyproject.toml` supports Python >=3.10; target **recommendation** is Python 3.12; migration decision should be explicit.
- Setup/test output must be verified on actual Windows machine before describing as Windows-tested.

## Recommended approach
Reuse and harden this code incrementally, not blindly rewrite the whole engine. Preserve the visible baseline CLI/manifest behavior where useful; version any schema/API changes and provide migrations. Establish adversarial archive fixtures and Windows CI or test machine validation.
