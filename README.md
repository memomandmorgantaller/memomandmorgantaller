# RFP Document Registry

Working Sprint 0 / first Sprint 1 slice: local intake, nested ZIP decomposition,
retained source snapshots, PDF/DOCX/XLSX/TXT evidence extraction and a durable SQLite
registry. Python 3.12; Windows-first scripts with Linux validation. No AI, classification,
approval, export or SharePoint connector is enabled in this slice.

Start with [operator instructions](baseline/rfp_registry_m1/README.md).
Read [delivery evidence and remaining gates](docs/09_SPRINT_0_1_DELIVERY.md) for exact
coverage and limits. The original handoff specifications remain in `docs/01`–`08`;
they describe the roadmap, not completed integrations.

## Windows quick start

From this checkout in PowerShell, using a restricted Windows account:

```powershell
cd baseline\rfp_registry_m1
.\setup_windows.ps1
.\.venv\Scripts\python.exe examples\create_vertical_slice.py --output "$env:TEMP\rfp-demo.zip"
.\.venv\Scripts\python.exe -m rfp_registry --source "$env:TEMP\rfp-demo.zip" --project "SYNTHETIC-DEMO" --output "$env:TEMP\rfp-demo-result"
```

Use new paths if those already exist. The demonstration exits **2**, intentionally:
four supported documents parse, and one synthetic CAD file is explicitly unsupported.
Inspect `manifest.json`, `manifest.csv`, `extractions.json` and `registry.sqlite3` in
the output directory. No source content leaves the machine during processing.

## Improvement discipline

[Validation and learning log](docs/10_VALIDATION_AND_LEARNING_LOG.md) records findings,
regressions, measured outcomes and open hypotheses. Future work must add a regression
fixture for each confirmed defect, rerun affected checks, and record actual platform
coverage. Real-data accuracy and autonomy require project-level held-out benchmarks;
model confidence or a passing synthetic test is never permission to automate filing.
