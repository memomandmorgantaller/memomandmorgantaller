# Sprint 0 hardening and first Sprint 1 vertical slice

## Baseline assessment before modifying code

Imported the supplied handoff into the previously empty repository and read AGENTS,
START_HERE, kickoff and docs 01–08. Python 3.12.14/Linux baseline: **10 tests passed**.
Pytest was initially absent; it was installed in a separate virtual environment.
The engine already provided nested ZIP lineage, opaque filenames, hashes and manifests.
Gaps: no independent originals, local text parsing, database or failure exit status;
directory validation/metadata budgets, corrupt deflate and Windows behavior needed work.

## Working delivery

The baseline package evolved in place to **v0.2.0**; its original flags remain accepted.

- ZIP metadata preflight, all-member path validation, link/reparse-point rejection,
  entry/byte/disk/deadline quotas, corrupt/encrypted/unsupported-feature exceptions.
- Separate read-only source copies and retained nested archive bytes; generated storage
  keys and SHA-256 per occurrence. No destructive moves, source renaming or overwrites.
- Atomic JSON/CSV reports, spreadsheet-safe CSV, explicit complete/incomplete enumeration.
- Local, subprocess-isolated PDF/DOCX/XLSX/TXT extraction with bounded source-linked
  evidence offsets; unsupported/scanned/empty/malformed/deferred statuses are explicit.
- SQLite migration 0→1, package/entry/blob entities, version-keyed extraction checkpoints,
  append-only application audit events, hash-verifying idempotent parser resume.
- Pinned/hash-locked dependencies, Windows install/run/test scripts, synthetic genuine
  document fixtures and Linux/Windows CI definition.

## Actual validation

**54 passed, 1 skipped** (Windows junction test) on Linux. One intentional duplicate-ZIP
fixture warning. Tests cover traversal/Windows names/NUL preservation, unsafe directories,
duplicate occurrences, CRC/deflate corruption, encryption/compression features, metadata,
size/count/ratio/depth/deadline/disk limits, source changes/snapshots, real supported file
formats, XML entities, parser timeout/protocol, tamper audits, schema-version rejection,
interrupted extraction recovery, deferred recovery and CLI exit codes.

Commands from `baseline/rfp_registry_m1` (verification venv `/workspace/registry-verify`,
independent tooling venv `/workspace/registry-tools`):

```sh
python -m pip install --require-hashes -r requirements.lock
python -m pip install --no-deps --no-build-isolation -e .
python -m pytest -q
ruff check rfp_registry tests examples
ruff format --check rfp_registry tests examples
mypy --python-executable /workspace/registry-verify/bin/python rfp_registry
pip-audit --no-deps --disable-pip -r requirements.lock
python examples/create_vertical_slice.py --output artifacts/demo/input.zip
python -m rfp_registry --source artifacts/demo/input.zip --project SYNTHETIC-DEMO --output artifacts/demo/result
python -m rfp_registry --resume --output artifacts/demo/result
```

Fresh hash-locked install and local editable build passed; Ruff and mypy passed.
Final full-lock advisory check: no known vulnerabilities at audit time. Initial wheel
0.45.1 was rejected for CVE-2026-24049; fixed 0.46.2 was used for fresh verification.
The demo and resume produced **8 records, 7 stored blobs, 0 intake failures, 4 parsed
leaf documents and 1 unsupported CAD leaf**. Both CLI runs exit **2** as intended.
Generated files are in `baseline/rfp_registry_m1/artifacts/demo/result/` (ignored).
Every parsed result requires human review. No customer package was supplied or tested.

## Versioning and migration

- Python target raised from >=3.10 to >=3.12; validated on 3.12.14.
- Manifest 1.0→1.1 is additive: entry snapshot paths, limits and enumeration summary.
  Original schema retained in `schemas/manifest.v1.0.schema.json`.
- `--intake-only` selects the old workflow. `--resume` can read v1.0 manifests, but
  missing original snapshots cannot be retrospectively claimed or reconstructed.
- SQLite `user_version=1` initializes transactionally; unknown future versions refused.
- Extraction schema/parser version 1.0; per-entry/version results reused, never silently
  replaced. Parser behavior changes must bump its version. Changed manifest/content
  requires new intake. No approvals exist to migrate or carry forward.

## Remaining gates

This is a working first slice, **not full Sprint 0 security signoff or all of Sprint 1**.
Actual Windows/CI execution, Windows parser memory containment, full intake crash/resume,
hostile-filesystem TOCTOU/fuzzing, backup/restore, performance tuning and production
ACL/encryption/retention deployment remain. Read-only attributes are not WORM storage;
directory intake captures individual files, not a filesystem-atomic package snapshot.
Blocked descendants are explicitly uninspected, never claimed reconciled. Operator
bounds and recovery procedures are in the package README.

Classification, AI, review UI, approvals, flat exports and SharePoint are **not
implemented**. The exact nine-folder rulebook, verified addendum/clarification precedence,
contextual vendor drawings, original traceability, local processing and progressive
autonomy remain unchanged. No document receives a destination or upload authority.

## Next slice and stakeholder dependencies

Finish Windows containment/recovery gates, then Sprint 2: deterministic reviewable
nine-folder recommendations with verified issuance context; review/override UI bound
to hash and rule version; approved flat no-clobber export and hash verification.
Regression-test every confirmed filing rule before AI integration.

Needed before production evaluation: sanitized complex RFP, curated correct filings,
issuance/approval authority, collision/revision/retention policy, and Windows workstation
constraints. These do not block the next synthetic development increment. No SharePoint
access is requested. See the validation/learning log for how future findings are used.

Reusable cloud `install_script` was saved as a draft after current-instance validation.
Saving does not publish the environment; review/save settings and publish separately.
No service startup is needed for this CLI slice. Future tasks should use the existing
checkout, not create a Git worktree, and invoke `/workspace/registry-verify/bin/python`
from `baseline/rfp_registry_m1`. Git history records code delivery; environment publication is a separate action.
