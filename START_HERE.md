> Implementation update: the first Sprint 0/1 slice is now implemented. See
> `docs/09_SPRINT_0_1_DELIVERY.md` for verified scope and remaining gates.
> The original handoff below records the starting point.

# RFP Document Registry — Codex engineering handoff

**Read order:** `AGENTS.md` → `docs/01_PRODUCT_REQUIREMENTS.md` → `docs/02_ARCHITECTURE.md` → `docs/03_FILING_RULEBOOK.md` → `docs/04_SECURITY.md` → `docs/05_IMPLEMENTATION_PLAN.md` → `docs/06_ACCEPTANCE_TESTS.md` → `docs/07_EXISTING_CODE_AUDIT.md`.

## Mission
Build a robust, Windows-first, locally hosted application that receives large, messy industrial RFP packages, recursively decomposes archives, inventories every entry, interprets individual documents using local AI plus deterministic business rules and approved historical precedents, and recommends an approved **one-of-nine flat SharePoint destination**. Human reviewers approve output initially. Later, a narrowly permissioned publisher uploads approved files to SharePoint Online, with class-specific autonomy only after formal calibration and authorization.

## Start Codex with
> Read AGENTS.md and all docs in order. Inspect the existing source under `baseline/rfp_registry_m1`. Execute existing tests and report findings before modifying code. Implement Sprint 1 / the next vertical slice, including tests, typed data models, Windows setup, and a runnable demonstration. Preserve the nine-folder rulebook and security gates. Do not claim unimplemented integrations are working. Ask only for truly blocking information. Provide a working result, not just another proposal.

## Handoff contents
- `baseline/rfp_registry_m1/`: actual Milestone 1 code, scripts, tests, and synthetic fixture, copied from the previously delivered package.
- `docs/`: requirements, architecture, permissions, phased tasks, tests, decision history, and code audit.
- `config/filing_rules.v1.yaml`: human-readable source of truth for the nine destinations and precedence.
- `schemas/`: example agent/classification contract and a sample intake result structure.
- `reference/`: the two screenshots provided in the discussion; the desired nine-folder layout and the problematic CS202-like source package. Images are illustrative, not machine-verified data.
- `CODEX_KICKOFF_PROMPT.md`: suggested first Codex message.

## Important status notes
- Only Milestone 1 package intake / ZIP decomposition exists in runnable form. Later components are specifications, not implemented code.
- A sanitized real customer package was **not** supplied in this chat, only screenshots; do not imply the system has been validated on a real RFP.
- Do not connect to production SharePoint or upload documents without explicit authorization and safe test-environment verification.
- This is the full decision history distilled into an engineering contract; not a verbatim transcript.
