# Implementation roadmap and prioritized backlog

## Guiding principle
Implement small vertical slices; produce runnable, tested demonstrations at every stage. Avoid building a six-agent framework before basic extraction, review and classification quality are proven.

### Sprint 0 — baseline verification and hardening (first Codex task)
- Run baseline tests; document platform coverage; inspect baseline security gaps; preserve CLI compatibility.
- Refactor bounded ZIP engine into clear tested modules with documented quotas, entry-level reconciliation, predictable exit codes, atomic manifests and safe preservation of originals.
- Address weaknesses: directory member validation, ZIP encryption errors, archive integrity checks, Windows reparse/junction handling, disk/memory budget, partial output and cancellation, output/source collision, path edge cases, extensive tests. Do not assert security without adversarial tests.
- Introduce stable manifest schema version/migration and golden synthetic fixtures; add CI and pinned dependencies.
**Done:** clean Windows setup scripts, security tests, repeatable manifest for fixture and zero silent omissions.

### Sprint 1 — content extraction and canonical registry
- SQLite persistence (Alembic-ready or migration tooling), durable processing state, snapshot/storage abstractions.
- PDF/DOCX/XLSX/TXT extraction (avoid executing macros); page/paragraph/cell evidence provenance; unsupported/legacy/CAD explicitly flagged.
- File content-type verification, text extraction quality scores, no unsupported format guesswork.
**Done:** each supported doc has status, text/metadata references, source lineage, bounded processing and meaningful errors.

### Sprint 2 — nine-folder deterministic classification and reviewable plan
- Code/YAML-backed folder registry and decision rules; addendum/clarification context detection as evidence with verified/unverified distinction; vendor-vs-project drawings.
- Rule engine proposes destination or `review_required`; create JSON/CSV filing plan and audit log.
- Local UI for package inventory and document review; no SharePoint access yet.
**Done:** mandated cases pass unit/integration tests and UI can approve/override and export with no overwrite.

### Sprint 3 — local AI two-agent integration
- Add local Ollama/llama.cpp adapter, offline smoke test and settings; typed A1 document analysis and A5 filing specialist.
- Strict outputs, prompt profile versioning, evidence links, retries/timeouts, negative tests for hallucination/prompt injection; deterministic fallback when inference unavailable.
- Add verified historical examples, retrieval (start keyword/structured; vector only if value measured), with document/project level holdout evaluation.
**Done:** improved classification benchmark relative to deterministic baseline, no unauthorized writes.

### Sprint 4 — operator workflow maturity and quality
- Batch review, filters by folder/status/reason, conflict resolution, replayable audit, collisions/revisions, export hashing/reconciliation, failure recovery and performance profiling.
- Test using sanitized complex CS202-style RFP and previously verified historical examples; no training/test leakage.
**Done:** documented coverage, accuracy by folder, calibration, exception rate, sample throughput and known limitations.

### Sprint 5 — controlled SharePoint integration (separate approval)
- Read-only discovery of selected site/project root and nine folder IDs; compare actual structure. Strict permission scopes.
- Human-approved upload using Graph, collisions, resumable sessions, throttle/retry, verification, transaction receipts, cleanup/recovery; safe test library first.
**Done:** no unapproved upload/overwrite, integrity and audit coverage, production launch checklist.

### Sprint 6 — selective autonomy + specialist agents (measured)
- Promote defined low-risk classes only when sufficient held-out evaluations show appropriate precision/calibration, no mandatory review, clear policy and operational monitoring.
- Add Engineering/Commercial/Quality specialized profiles only when benchmark shows advantage; independent audit and kill switch.
**Done:** documented approval by business owner and IT/security, roll-back and monitoring.

## Recommended release artifacts
`README`, Windows setup/start/test scripts, manifest schemas, typed API contracts, ERD/migrations, rulebook YAML, test fixtures, synthetic sample package, reproducible benchmarks, security checklist, operator guide, admin/deployment guide, and append-only decision log.

## Dependencies on stakeholder
Sanitized sample package, verified correctly filed RFP package(s), approved SharePoint test site and folder mappings, Windows workstation hardware specs, security/licensing requirements, source retention policy, naming collisions policy, and user roles/approval matrix.
