# Product requirements and scope

## Problem
Complex incoming industrial RFP packages contain nested ZIP archives, project drawings, technical specifications, pricing, contracts, vendor documents, safety material, addenda and clarifications. Customer-delivered organization is inconsistent and complex. The user wants individual files placed into an existing standardized SharePoint Online project folder structure.

## Confirmed product decisions
- Project/RFP selected explicitly by operator at intake.
- Exactly nine flat project subfolders, as listed in the rulebook; files directly in folders, never custom auto-generated subfolders.
- ZIP archives unpacked recursively and each file analyzed; preserve untouched source archives separately for audit.
- Official addenda preserved as a logical issuance group but **physically extracted as individual files directly under `06 - Addenda`**; no subfolder and no duplicate technical publication by default.
- Vendor-produced drawings decided by context between Drawings and Vendor Data; ambiguous → review.
- Historical correctly filed packages available to establish precedents, but real gold-standard examples still need to be supplied and curated.
- Local/offline AI processing on company infrastructure. SharePoint Online connectivity allowed for deliberate, controlled publishing.
- Development on Windows workstation with future move to internal shared server.
- Progressive autonomy: Level 0 recommendation-only, Level 1 human-approved local export and SharePoint publication, Level 2 selectively automatic for *approved classes* after measured validation, Level 3 exception-managed later.

## Personas and experiences
- Intake operator: selects existing project, selects folder/ZIP, verifies intake summary, starts processing.
- Document reviewer: sees source path, parent archives, extracted evidence, rule result, candidate destination(s), ambiguity; approves/overrides/defers.
- Administrator: maintains approved folder mappings, precedents, security settings, model version, role permissions, data retention and policy versions.
- Auditor: can trace published document to original bytes, issuance, decision evidence, human approval and publication receipt.

## Required MVP stories
1. Import sanitized RFP package as folder or ZIP, preserving original untouched bytes (snapshot/copy and checksums), with safe path handling.
2. Safely recursively inspect/extract ZIPs, count/account for every file/archive entry and record errors/exceptions.
3. Extract text and structured metadata for PDFs, DOCX, XLSX, TXT; acknowledge unsupported/scanned/legacy/CAD via explicit status and later adapters.
4. Classify leaf documents using rule engine and optional locally hosted AI; never use file extension alone to decide complex categories.
5. Maintain source-to-destination lineage across archive nesting, including duplicates and revisions.
6. Show a browsable review UI and editable recommendation with evidence, selection of nine destinations only, and approval audit.
7. Generate local approved nine-folder export with no overwrite; produce JSON/CSV reconciliation and audit records.
8. Keep SharePoint API publishing behind a feature flag and separate least-privilege service until separate approval.

## Out of scope initially
Production SharePoint write integration; full DWG/DGN/other CAD understanding; automatic document splitting; fine-tuning; arbitrary autonomous agents; unsupervised learning from user corrections; legal review; online AI services; Windows installer/executable packaging unless needed after the reproducible Python deployment works.

## Nonfunctional
Security-first archive handling, resource quotas, no network by default, resumable/idempotent processing, atomic outputs, clear failures, scalability to thousands of files, privacy of source/derived documents, versioned rulebook/model/prompts/schema, Windows compatibility, upgrade path to PostgreSQL and authenticated shared server deployment.

## Real-data dependency
The screenshots show a target nine-folder layout and messy CS202 source structure, **not** content-level validated labels. Obtain a sanitized representative complex RFP and at least one verified correctly filed example for acceptance and accuracy benchmarking. Do not hardcode screenshot filenames as ground truth.
