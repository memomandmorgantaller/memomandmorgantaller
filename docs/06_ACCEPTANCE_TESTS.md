# Test plan / acceptance gates

## Run baseline
From `baseline/rfp_registry_m1`:
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
.\.venv\Scripts\python.exe -m pytest -q
```
(Unix verification performed in the handoff environment, not Windows.)

## Intake and archive security (must automate)
- Folder and ZIP sources, nested ZIP and ZIP-in-ZIP, 0-byte files, duplicate basenames and duplicate exact paths, strange Unicode names, huge number of tiny entries, unexpected extension/content mismatch.
- Path traversal (`../`), absolute and drive paths, ADS (`:`), reserved Windows names, trailing periods/spaces, backslashes, symlinks and reparse points/junctions; no escapes outside workspace.
- Oversized source, ZIP bomb/high ratio, depth, aggregate expanded bytes, long name, malformed central directory, truncated member, corrupt ZIP/CRC, encrypted/password ZIP, unsupported ZIP compression; bounded resources and explicit errors.
- Interrupted job, retry/resume, partial storage cleanup, concurrent runs, output directory exists, input/output overlap, access denied, low disk space; intact originals and reconcilable manifest.
- Every source directory/entry and archive ancestor explicitly recorded; failure isn't omission. Every stored blob's hash matches actual bytes.

## Filing business rules
- Exactly nine and only nine flat destinations, canonical folder strings.
- Verified addendum PDF/Office/drawing → 06, with leaves extracted individually; originals preserved.
- Verified clarification → 07 unless covered by a verified addendum.
- Project engineering drawing → 04; vendor reference drawing → 05; ambiguous → review.
- Pricing workbook → 01 when confirmed; technical specification → 03; scope document → 02; site safety → 08.
- Compound document → remain intact pending formal splitting rules; no hidden auto-splitting.
- Unrecognized content, low extraction quality, ambiguous source context or unsupported format → explicit review, never guess.
- Different-content same export name → no overwrite, human review. Exact duplicates preserve every source occurrence; no silent drop.

## Agent contract tests
- Input malformed/untrusted; no unrestricted tools; model offline; JSON schema reject unknown folder IDs/invalid evidence refs; bounded timeout/retries.
- Embed prompt-injection commands in PDF text and confirm they cannot override policy or access tools.
- Deterministic addendum override even if A5 recommends Drawings; no model-generated folder creation.
- Benchmark accuracy/coverage separately from model self-reported confidence. Hold out entire projects to prevent leakage.

## Review/publisher security tests
- Approval based on immutable content hash, destination, user and version; invalidation on changes; only approved exports; audit reviewer overrides.
- No-clobber atomic exports, hash verification, disconnected/offline mode.
- SharePoint later: read-only first, dev site, least privilege, idempotency, duplicate retry, destination rename/move, throttling, upload failure, permission loss, no unauthorized writes, verifiable publication receipt and stop switch.

## Proposed goals, NOT achieved results
- 100% accountability for source entries (success or explicit error).
- 100% approved export destination compliance and audit lineage.
- 0 unapproved overwrites or uploads.
- Aim ≥95% primary-folder classification on a vetted holdout set, with separate class precision/recall and sufficient sample sizes before any autonomy promotion. These are engineering targets, not warranties.
