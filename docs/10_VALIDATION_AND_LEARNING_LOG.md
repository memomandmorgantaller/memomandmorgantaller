# Validation and future learning

## Repeatable change loop

1. Capture the observed failure and source fixture (synthetic or approved sanitized
   data), platform, tool versions, command, expected behavior and actual outcome.
2. Separate confirmed rules from assumptions. Unsettled issuance, naming, revisions,
   approvals and security policy stay conservative human-review defaults.
3. Add a failing regression test or measurable benchmark before changing behavior.
   Link it to the relevant filing rule/threat; never weaken an assertion to pass.
4. Make the smallest correction; rerun affected tests and required integration gates.
   Record skipped/unrun checks separately. Revalidate Windows-specific behavior on
   Windows, and real-data claims on approved representative input.
5. Append the decision and actual outcome here. Update operator/schema/migration
   instructions when contracts change; preserve content hashes and audit history.
6. For classification/AI later: version prompts, rules and models; compare held-out
   **projects** with a frozen deterministic baseline. Report per-folder precision,
   recall, exception rate, collision behavior and latency. Obtain explicit approval
   before promoting any class to a higher autonomy level. Never learn policy directly
   from an unreviewed model suggestion or user correction.

## Findings during this slice (2026-10-16)

| Finding | Correction / regression | Verified outcome |
|---|---|---|
| Loose PK prefix detection could misidentify plain text | Require a recognized ZIP signature | Plain `PK project...` text parses normally; regression added |
| Baseline had no separate retained original | `originals/`, source hash/stability checks | `test_snapshot_and_all_directory_occurrences`, source-change regression |
| ZIP directory paths bypassed validation | Validate metadata for directory and file entries | Nine unsafe directory variants rejected; safe sibling retained |
| Stored-file count did not bound metadata | EOCD/central-directory and global record budgets | Over-budget archive retained, count and incomplete enumeration explicit |
| Corrupt deflate could raise `zlib.error` outside handler | Record entry failure, delete partial blob | `test_crc_corruption_and_partial_cleanup` |
| Integrity failure audit was rolled back with raised error | Commit exception state/event before raising | Tampered cached blob rejected and durable audit asserted |
| Single manifest temporary name obstructed post-crash writes | Unique atomic temporary files | Resume uses durable SQLite; stale temporary results never promoted |
| Build dependency wheel 0.45.1 had CVE-2026-24049 | Pin/hash wheel 0.46.2 | Final full lock audit found no known vulnerabilities at audit time |
| Per-document limits alone allowed excessive package text | Aggregate text/deadline budget, explicit deferred state | Deferred work not cached as completed; later resume test parses it |
| Interruptions could waste completed parser work | Transaction per document, versioned task key | Interrupt on second document, resume invokes parser only once |

## Pending evidence and improvements

- Windows CI and real workstation execution, especially junctions, ACLs, process memory
  containment, cancellation and file-locking behavior. A Linux pass is not Windows evidence.
- Disk/network-share failure injection, concurrent hostile filesystem mutation, crash at
  every persistence boundary, backup/restore and large-package performance characterization.
- Sanitized representative RFP, verified correctly filed examples, workstation constraints,
  retention policy and approval/issuance authorities. None supplied yet; these do not
  block synthetic Sprint 1 development, but do block accuracy/production-readiness claims.
- Sprint 2 regression matrix must cover all nine exact folders, verified addendum
  precedence, clarification precedence, contextual vendor drawings, collisions and
  review-bound approved no-clobber exports. No automatic filing in this slice.
