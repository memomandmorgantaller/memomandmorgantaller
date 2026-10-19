# RFP Document Registry

Working Sprint 0 / first Sprint 1 slice: local intake, nested ZIP decomposition,
retained source snapshots, PDF/DOCX/XLSX/TXT evidence extraction and a durable SQLite
registry. Python 3.12; Windows and Linux CI validated. No AI, classification,
approval, export or SharePoint connector is enabled in this slice.

Windows tests, Linux tests and static checks passed for `3ad2d1e` in
[GitHub Actions](https://github.com/memomandmorgantaller/memomandmorgantaller/actions/runs/38917255658). Production workstation deployment and parser containment
remain separate validation gates.

Start with [operator instructions](baseline/rfp_registry_m1/README.md).
Read [delivery evidence and remaining gates](docs/09_SPRINT_0_1_DELIVERY.md) for exact
coverage and limits. The original handoff specifications remain in `docs/01`–`08`;
they describe the roadmap, not completed integrations.

## Windows: install and click

Download **RFPRegistry-Setup-0.3.0-x64.exe** from the
[desktop releases](https://github.com/memomandmorgantaller/memomandmorgantaller/releases),
run it, and keep the desktop shortcut selected. Open **RFP Document Registry**, click
**Try the built-in demonstration**, then **Process package**. No Python installation
or PowerShell commands are required. The portable **RFPRegistry.exe** is also available.

The demonstration parses four documents and flags one deliberately unsupported CAD
file. Click **Open results folder** to view the saved inventory and evidence.
For your own approved sanitized input, choose the source, enter the project explicitly,
and click **Process package**. Every run creates a new results folder.

The builds are unsigned; Windows/company policy may require IT approval. Keep security
controls enabled. See [desktop instructions and build gates](docs/13_WINDOWS_DESKTOP.md).
The [source developer instructions](baseline/rfp_registry_m1/README.md) still apply
when running or building from Python.

## Improvement discipline

[Validation and learning log](docs/10_VALIDATION_AND_LEARNING_LOG.md) records findings,
regressions, measured outcomes and open hypotheses. Future work must add a regression
fixture for each confirmed defect, rerun affected checks, and record actual platform
coverage. Real-data accuracy and autonomy require project-level held-out benchmarks;
model confidence or a passing synthetic test is never permission to automate filing.
