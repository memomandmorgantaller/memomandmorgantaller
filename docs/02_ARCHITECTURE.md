# Target architecture, service contracts and storage

## Components
1. **Intake API + UI:** Windows localhost initially. Operator selects project and local source. Validate path/permissions/capacity; create immutable intake snapshot with digest.
2. **Safe archive engine:** bounded streaming, recursive ZIP, path/entry validation, scan hooks, logical lineage, quotas. Generated storage keys; no ZIP name used as physical destination.
3. **Document parsers:** file-type detection using magic/signature, PDF/Office/text readers, local OCR queue, metadata/title extraction, page/paragraph provenance; explicit unsupported status for legacy/CAD until supported.
4. **Knowledge registry:** structured approved folder definitions, rule versions, verified precedents, precedent permissions and provenance; local searchable index; optional vector retrieval after measurement.
5. **Deterministic orchestrator:** state machine, durable tasks, idempotent resume, bounded retries, timeouts, escalation and audit events; NOT an LLM agent.
6. **Local agent gateway:** model server abstracted; strict schemas; read-only context; local prompt profiles; no agent-to-agent arbitrary chat and no execution tools.
7. **Policy engine:** resolves enforced rules; checks eligibility, collisions, revision conflicts, security and evidence quality; only source of publish eligibility.
8. **Review UI:** triage exceptions, preview extracted evidence, edit candidate folder, approve by immutable content hash and version, audit all edits.
9. **Local exporter:** copies only approved leaf files into exact nine flat directories, resolving only nonconflicting names and validating hash after copy; produces reconciliation.
10. **SharePoint publisher (later):** separate process/identity, project-scoped selected-site permissions, Microsoft Graph upload sessions for large files, conflict detection, throttling, verification and audit; never run for MVP.

## Agent design (logical agents, can share one local model)
- A1 Document Analyst: input a bounded set of extracted evidence and source context; output document type, purpose, engineering discipline, issuance context, title/revision/equipment tags, uncertainty, provenance offsets. No final folder authority.
- A5 Filing Specialist: input validated A1 result, nine destination candidates, allowed rules, verified precedents; output proposed destination code or unresolved, alternatives and evidence references. No write authority.
- Optional A2 Engineering: technical drawing, specifications, vendor vs project origin, only when needed.
- Optional A3 Commercial: contracts, pricing, contractual purpose, confidentiality alerts.
- Optional A4 Knowledge: trusted precedent retrieval (prefer ordinary deterministic search as a tool, not an agent initially).
- Optional A6 Quality: challenge conflicting/high-risk results (must not be sole approval source).

## Communication and versions
Use Pydantic/JSON Schema internal messages with `schema_version`, `package_id`, `entry_id`, `content_sha256`, `model_id`, `model_config_version`, `rulebook_version`, `agent_profile_version`, `evidence_refs`, `candidate_destination_codes`, `status`, `errors`, `created_utc`. Consumers reject malformed or unexpected fields/IDs. Evidence refs must map to source artifacts or extracted text offsets. Store agent result append-only, never mutate history in place.

## State machine
`DISCOVERED → SNAPSHOTTED → STORED → PARSED → ANALYZED → CLASSIFIED → POLICY_CHECKED → PENDING_REVIEW → APPROVED → EXPORTED → VERIFIED` (publication states added later). Errors become `BLOCKED`/`EXCEPTION` with explicit cause; archives themselves are retained and enumerated but not automatically exported as leaf documents. Idempotent task keys `(package_id, entry_id, task_type, parser/rule/model_version)`.

## Storage schema (initial logical entities)
`projects`, `packages`, `source_entries`, `blobs`, `lineage_edges`, `extractions`, `classifications`, `evidence`, `agent_runs`, `filing_rules`, `precedents`, `reviews`, `exports`, `audit_events`; add `publications` later. Distinguish source entry (path occurrence) from content blob (same hash possible in multiple locations) and logical document identity (revisions). All entries uniquely addressable; use immutable content hashes for review binding.

## Windows → server migration
Use an abstraction over persistence (SQLite → PostgreSQL), blob storage (local NTFS → managed filesystem/object storage), queue (SQLite durable work queue → server queue), and inference (localhost model runtime → internal GPU inference service). Keep API/UI and business policy unchanged. Bind prototype to 127.0.0.1; server needs SSO, TLS, RBAC, network segmentation, backup/restore, observability.

## Operational constraints
Set per-entry size, total expansion, nesting-depth, file-count, elapsed-time, disk-free and model context limits. Consider archive entry metadata overhead and prevent duplicate entries with identical path from overwriting. Inference jobs bounded by tokens/time. Reserve space for original + extracted + derived + export; securely purge according to approved retention plan.
