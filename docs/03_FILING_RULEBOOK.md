# Filing Rulebook v1.0 — business contract

## Only approved destinations (verbatim names)
| Code | Folder | Content |
|--|--|--|
| 00 | 00 - START HERE | RFP package index, navigation, introduction, general bidder guidance not primarily commercial |
| 01 | 01 - Commercial & Contract | Tender forms, pricing, insurance, contracts, payment/legal/commercial terms |
| 02 | 02 - Scope of Work | Scope descriptions, responsibilities, work boundaries, deliverables, execution requirements |
| 03 | 03 - Specifications | Technical specifications, standards, design criteria, performance/testing requirements |
| 04 | 04 - Drawings | Project-issued engineering drawings, P&IDs, layouts, diagrams, schematics and drawing registers |
| 05 | 05 - Vendor Data | Manufacturer literature, manuals, vendor supporting/reference documents and vendor-origin drawings *when supplied as vendor reference* |
| 06 | 06 - Addenda | ALL files verified to have been issued as part of an official addendum, including updated drawings/specifications |
| 07 | 07 - Clarifications (Q&A) | Formal bidder questions, answers, Q&A registers and clarification correspondence |
| 08 | 08 - Site Access & Safety | Site HSE/access requirements, emergency/site safety plans, permits, induction material |

## Binding policies
- These exact nine folders are the *only* export/publication destinations beneath the selected project. Flat layout: no new subfolders.
- One primary destination per source leaf document. Secondary semantic labels allowed but never imply duplicate publication.
- **Precedence**: verified addendum membership → verified clarification membership → explicit company rule → source issuance context + content/purpose → approved historical precedent → filename/path heuristics.
- Addendum precedence explicitly overrides technical type; extract original addendum ZIP, preserve original separately, route leaf files directly to folder 06.
- Vendor drawing classification based on *purpose* and *issuance context*; if project-issued engineering deliverable → 04; if vendor reference/equipment information → 05; if not distinguishable → review.
- Source folder/ZIP names help establish issuance context but are not automatically conclusive when contradictory.
- Classifier never creates a new folder or forces a low-evidence choice; unresolved → review queue.
- Similar content hash or same document number does not automatically mean duplicate or revision, respectively; record relationship and apply explicit policy.
- Different-content same target filename → block export and human review initially; no silent renaming/overwrite. Identical-content duplicate → preserve both source entries, export once only after approval/policy check.
- Original source untouched; any export copies bytes; verify hash equality.
- Confidential or sensitive documents must not be routed to an unauthorized SharePoint library (later); permissions are independent of classification.

## Ambiguous examples (not ground truth)
- `3.1 CS202 SOW.zip` → extract individually; likely folder 02 for true scope files; do not copy archive as a single output.
- `3.2 CS202 Specifications.zip` → likely 03 for specification leaf files.
- `3.3A CS202 Drawings.zip` → likely 04 for project drawing leaves.
- `CS202 Unit Prices.xls` → 01 if pricing workbook confirmed (legacy parsing may require approved tool).
- `Emergency Plans.pdf` → 08 if site emergency procedure, else review.
- `Project Specific Risk Management Plan.pdf` → potential scope vs site safety; review until purpose established.
- `ES35100-CS02-011000_V2.pdf` → opaque technical code; inspect contents; never decide from filename alone.

## Validation questions not yet confirmed
- Exact filenames for the folder names must be verified against SharePoint, but screenshot and discussion specify the above labels.
- Evidence required to classify official addendum membership and cases with mixed addendum/clarification provenance.
- Policy for compound PDFs containing multiple document types and whether any splitting is allowed (default NO splitting).
- Filename collision resolution/naming convention beyond safe default review.
- Revision and superseded document policy and whether existing SharePoint revisions/metadata are used.
- Formal approval authorities and business-specific security classifications.
