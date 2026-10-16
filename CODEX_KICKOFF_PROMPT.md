# Paste this as the first prompt to Codex

You are the lead engineer for the RFP Document Registry. The repository contains an existing Python ZIP intake baseline plus an engineering handoff. Read `AGENTS.md`, `START_HERE.md`, and all `docs/*.md` before coding, with special attention to the nine-folder filing rulebook and `docs/07_EXISTING_CODE_AUDIT.md`.

Mission: deliver incremental runnable code for a secure Windows-first local application that processes large messy industrial RFP packages, preserves original source/archive lineage, extracts individual documents, classifies them into exactly nine existing flat folders using deterministic policy plus optional locally hosted agents, offers human approval, and eventually supports narrowly scoped SharePoint Online publication. Source documents must never be sent to cloud AI. No unattended publication in the MVP.

First implement and demonstrate **Sprint 0 and a focused Sprint 1 vertical slice**: audit/harden current archive processor, add reliable manifest reconciliation and immutable source snapshot, support PDF/DOCX/XLSX/TXT local extraction with source-linked evidence, introduce typed storage and versioned results, upgrade tests, and provide Windows setup/run/test instructions. If time is limited, finish a smaller working slice rather than scaffolding everything incompletely.

Start by executing baseline tests. Provide a concise gap analysis. Then implement changes and rerun tests. Provide output files, working commands, limitations, and proposed Sprint 2 work. Do not assert Windows testing unless executed on Windows. Do not request access to SharePoint yet. Use synthetic fixtures until I provide a sanitized RFP and a curated correctly filed example.
