# Local registry — desktop and CLI (v0.3.0)

Run local intake and extraction without network credentials or a model server.
All documents remain pending human review. See the root README for the roadmap.

## End users: no PowerShell needed

Use the tested Windows installer or portable executable from this repository's desktop
release. The installer creates a desktop shortcut. Click **Try the built-in demonstration**,
then **Process package**, then **Open results folder**. Python and libraries are bundled.
See [desktop instructions](../../docs/13_WINDOWS_DESKTOP.md) for scope and signing status.
The remaining instructions below are for source development and troubleshooting.

## Install and test on Windows

Python 3.12, PowerShell, non-admin account, endpoint scanning, a private local NTFS
output directory and adequate free disk are required. From this directory:

```powershell
.\setup_windows.ps1
.\test_windows.ps1
```

If script execution is disallowed, use the explicit equivalent commands without
changing execution policy:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements.lock
.\.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e .
.\.venv\Scripts\python.exe -m pytest -q
```

Installation downloads only pinned, hash-verified dependencies. For an offline
installation, obtain the exact wheels via your approved package mirror and use
`--no-index --find-links C:\ApprovedWheels` with the hash-verified pip command.
Runtime processing makes no network requests. Restrict source/output ACLs and use
company encryption/retention policies. Read-only file attributes are an application
safeguard, **not** WORM storage or protection against another process running as you.

## Operator workflow

Select the project explicitly; use a new output directory outside the input tree:

```powershell
.\.venv\Scripts\python.exe -m rfp_registry --source "C:\RFP\Sanitized\package.zip" --project "CS202" --output "C:\RFP\Results\run01"
```

A source folder or individual supported file also works. Input/output ancestry,
existing nonempty output directories, symlink/reparse-point paths and root links
are refused. Do not ingest a directory being actively edited. Source stability
checks detect ordinary races but cannot create a filesystem-wide atomic snapshot
or defend against a malicious process with the same filesystem privileges.

The baseline command and flags remain accepted. New default behavior also parses
leaf documents. Add `--intake-only` for the original intake-only workflow.
`--max-depth 3 --max-total-gb 2` can reduce budgets.

Exit codes: **0** = intake/extraction complete; **2** = explicit exceptions needing
review (including unsupported/empty/OCR/deferred documents); **1** = fatal error;
argparse usage errors also exit 2. A zero exit does not mean classified or approved.

## Reports and retained bytes

- `manifest.json` (v1.1): authoritative inventory, archive ancestry, hashes, storage
  paths, per-entry errors and `enumeration_complete`.
- `manifest.csv`: spreadsheet-safe view; formula-like values prefixed with `'`.
  Exact source names remain in JSON. Never treat CSV as an import manifest.
- `originals/`: separate read-only source file/ZIP copies captured before recursive
  archive processing; each source occurrence links to its snapshot and SHA-256.
- `extracted/`: opaque, read-only stored blobs, including nested archives. No source
  name becomes a physical path. Repeated names/content remain separate occurrences.
- `extractions.json` (v1.0): document statuses, text, offsets and page/paragraph/cell/
  line references bound to entry ID, package ID and source content SHA-256.
- `registry.sqlite3` (user_version 1): packages, source entries, unique content hashes,
  per-parser-version results and append-only application audit events. SQLite is the
  durable extraction checkpoint; JSON is regenerated on resume.

`stored` means retained bytes, never approved/safe content. Unsupported and blocked
entries are recorded. When an archive cannot safely be enumerated, its bytes and an
archive issue are recorded and enumeration is explicitly incomplete. The tool does
not claim an inventory of unknowable descendants in encrypted/corrupt/over-budget
archives. Do not proceed to filing with those exceptions.

## Resume and recovery

```powershell
.\.venv\Scripts\python.exe -m rfp_registry --resume --output "C:\RFP\Results\run01"
```

Resume requires a complete manifest; it rechecks stored hashes, reuses completed
per-entry extraction transactions, and processes missing/deferred tasks. It rejects
a changed manifest. Parser errors/unsupported results are retained rather than
retried in a loop. Correct the source/parser and create a new intake to reevaluate.
There is no in-place resume of an interrupted *intake*; preserve that output for
inspection and restart intake in a fresh directory.

The exclusive `.registry.lock` is removed on ordinary exceptions/cancellation. After
an OS crash/forced kill, verify its recorded PID is no longer running and no other
operator owns the package, then remove only that stale lock before resuming. No
automatic lock stealing. Orphan `.registry-*.tmp` files after a forced kill are never
used as results; they may be removed after the same ownership check.

## Bounds and format scope

Intake defaults: depth 4, 10,000 stored files, 20,000 inventory records (+ terminal
issue), 1 GB/file, 5 GB aggregate stored blobs, 2 GB/archive, 8 MB ZIP central directory,
300 seconds, 64 MB free-disk reserve and 200:1 expansion check above 1 MB. Source
snapshots consume additional space; plan for at least twice the intake budget plus
derived artifacts. Quotas are enforced while streaming; failures remain explicit.
Only stored/deflate ZIPs; ZIP64/multidisk and other compression features are blocked.

Parsers: <=32 MB input, <=1 million text characters, <=10,000 evidence units,
<=500 PDF pages, <=16 MB expanded Office package. Office XML uses defusedxml,
never evaluates formulas/macros or resolves links. XLSX formula cells expose cached
values marked `cached_formula`; DOCX main-document paragraphs include table text,
but headers/footers/comments/embedded objects are not extracted in this slice.
Worksheet evidence uses exact XML part and cell coordinates, not display sheet names.
TXT accepts UTF-8 (optional BOM) and BOM-marked UTF-16; other encodings are exceptions.
PDF requires a PDF signature; scanned/blank PDFs need OCR. OCR, CAD, legacy DOC/XLS,
RAR/7z and macro-enabled Office parsing are not implemented. No document splitting.

Each parser runs in a disposable subprocess with a 20-second deadline. Linux workers
also have a 512 MiB address-space and 15-second CPU limit. Windows workers currently
have a deadline and format quotas, but **no verified OS memory limit/sandbox**. Use
only sanitized input until Windows containment and endpoint controls are validated.
Each extraction invocation has a 300-second package deadline and 8 MB UTF-8 aggregate
text budget; exhausted work is explicitly deferred. Repeated resume cannot bypass
the aggregate text budget; larger packages require deliberate quota design/tuning.

Extracted quality is `text_present_unvalidated` or `no_text`, not a confidence score
or a claim of semantic correctness. Content is untrusted evidence, never instructions.

## Synthetic demonstration

```powershell
.\.venv\Scripts\python.exe examples\create_vertical_slice.py --output "$env:TEMP\rfp-demo.zip"
.\.venv\Scripts\python.exe -m rfp_registry --source "$env:TEMP\rfp-demo.zip" --project "DEMO" --output "$env:TEMP\rfp-demo-result"
```

Expected: 8 inventory records, 7 stored files, four parsed leaf documents, one
unsupported CAD leaf, no intake failures, exit 2. Unverified addendum naming supplies
lineage only; it does not verify issuance or grant a filing destination.

## Linux development verification

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements.lock
.venv/bin/python -m pip install --no-deps --no-build-isolation -e .
.venv/bin/python -m pytest -q
```

Static validation used Ruff 0.17.1 and mypy 2.4.0; install these in a separate tooling
environment, then run `ruff check rfp_registry tests examples ci`, `ruff format --check
rfp_registry tests examples ci`, and `mypy rfp_registry ci`. Windows and Linux test
jobs plus static checks passed for `3ad2d1e` in
[GitHub Actions](https://github.com/memomandmorgantaller/memomandmorgantaller/actions/runs/38917255658). Local Linux validation after the fixes: 61 passed,
1 Windows-only test skipped. This does not validate restricted workstation deployment,
Windows parser memory containment or real customer data. See
`docs/09_SPRINT_0_1_DELIVERY.md` at repo root.
