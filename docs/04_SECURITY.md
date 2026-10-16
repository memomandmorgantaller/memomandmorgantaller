# Security, privacy, reliability and SharePoint controls

## Threat model
RFP packages are untrusted input and may contain malicious ZIP metadata, decompression bombs, corrupt parsers, macro-enabled Office files, hidden files, prompt-injection instructions, confidential commercial details, malware, filename collisions, oversized files and hostile document content. AI model outputs are untrusted as well.

## Requirements
- Read inputs under least-privilege Windows account; snapshot immutable original bytes with SHA-256. Prevent input/output overlap and symlink/reparse-point traversal; apply permissions and encryption at rest. Protect derived text just like original document content.
- Extraction: generated opaque physical storage names; zip path validation; reject link-like files and unsafe paths; enforce per-entry, total and archive quotas while streaming; limit nesting/deadline/file count/metadata count/compression ratio; fail gracefully with entry-level error records. Consider Windows junctions/reparse points, TOCTOU, disk capacity, atomic operations, ZIP CRC and archive bomb scenarios.
- File parsing: treat Office macros as inert data; do not execute attachments, links, embedded scripts or external resources. Isolate risky parsers where practical; limit OCR CPU/time and page counts.
- Prompt injection: document text is evidence only, not instructions. No arbitrary tool execution from model suggestions. Validate facts and evidence refs; constrain allowed taxonomy/destination codes with schema and policy engine.
- Audit: append-only changes tied to principal, content hash, rule/model/prompt version, UTC time, previous/current status, and source identifiers; never store secrets or unnecessary full sensitive text in general-purpose logs.
- Offline: model service listens on localhost in workstation mode, configured to make no outbound requests; no telemetry containing document content to third-party services. Document model weights/provenance and license validation before deployment.
- Review approval: actor, timestamp, content hash, destination ID, rulebook/model version and approval scope; invalidate approval on content change or relevant policy/destination change. Distinguish recommendation and authorized action.
- Export: atomic no-clobber copy; verify hash; explicitly account for duplicates; no destructive moves/renames; log unresolved collision.
- SharePoint later: separate service with least-privilege Entra app registration, site-scoped grants where available, secret management/certificate auth, Graph resumable upload session, collision protections, 429/503 backoff, preupload destination revalidation, postupload integrity checks, idempotent replay, immutable publication receipt. Start read-only; use isolated test site; production rollout with change approval and kill switch.
- Resilience: graceful shutdown, resume/checkpoints, retry budgets, backup/restore and recovery tests; bounded parallelism; tamper-evident audit retention as required by organization.

## Prohibited autonomy
Agents never receive SharePoint credentials, folder-write privileges, shell execution rights or the ability to redefine rulebook policy. All AI decisions are recommendations, only deterministic services perform writes following explicit authorization.
