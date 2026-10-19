# Windows desktop application 0.3.0

## Click-and-go use

Open this repository's **Releases** page and select the desktop release. Download
**RFPRegistry-Setup-0.3.0-x64.exe**, run it, and keep **Create a desktop shortcut**
selected. The installer installs under your Windows account without requesting
administrator privileges. Open **RFP Document Registry** from the desktop or Start menu.
You do not need Python, PowerShell, Git, Excel, a model server or internet to process files.

1. Click **Try the built-in demonstration**.
2. Click **Process package** and wait for the completion message.
3. Expect four parsed documents and one intentionally unsupported CAD document needing
   attention. No intake failures are expected.
4. Click **Open results folder**. The summary and local manifests account for every
   inventoried occurrence, including unsupported files and archive relationships.
5. For approved sanitized input, choose a ZIP/document or folder, explicitly enter
   its project name, choose the results location if needed, and click **Process package**.

Each run creates a new results subfolder under `RFPRegistryResults` in your user
folder by default. Originals stay in place and are retained separately. A running
job keeps the interface responsive; controls prevent concurrent submissions and closing
while records are being saved. Progress indicates stages rather than an invented percentage.

**RFPRegistry.exe** is the portable alternative: double-click it without installing.
Both executable forms include Python, Tcl/Tk, pypdf, defusedxml, SQLite support, and
the synthetic demo. First launch may take a moment while the one-file bundle starts.
Keep the release's `THIRD_PARTY_NOTICES.txt` with a redistributed portable executable.
Uninstalling the application leaves result folders intact.

The Windows x64 build targets Windows 10/11. The files are currently **unsigned**:
SmartScreen or company policy may require IT approval. Do not disable security
controls. Hosted-runner validation does not establish restricted-workstation approval
or Windows parser sandboxing. Continue with synthetic/approved sanitized files.

## Scope retained

The GUI runs the same deterministic intake/extraction engine as the CLI. It does not
classify, approve, export or upload documents. The exact nine flat destinations,
addendum/clarification precedence, contextual vendor drawings, source traceability,
local processing and progressive-autonomy requirements remain unchanged for later work.
No network listener, cloud AI service, upload identity or self-updater is introduced.

## Maintainer build and validation

Use 64-bit Python 3.12 on Windows and Inno Setup 6. The GitHub Windows runner supplies
the compiler. From `baseline/rfp_registry_m1`:

```powershell
python -m pip install --require-hashes -r packaging/requirements-windows.lock
python -m pip install --no-deps --no-build-isolation -e .
.\packaging\build_windows.ps1
python ci/verify_windows_distribution.py
```

For source development, run `python -m rfp_registry.desktop_entry`. The CLI remains
available. App version is 0.3.0; manifest/extraction/database versions are unchanged.
There are no migrations or changes to approval/filing policy.

The parser's Python `-m` launch path cannot be used inside a frozen windowed executable.
Frozen children re-enter an explicit worker dispatch and return bounded versioned JSON
through a temporary file, including when stdout is absent. Source CLI behavior is retained.

CI gates the distribution on Linux/Windows tests and static checks. The Windows package
job builds a one-file windowed executable, builds a per-user installer, then:

- Exercises the real demo and Process buttons using native Tk event handling.
- Runs PDF/DOCX/XLSX/TXT parsers inside the frozen app with developer Python removed
  from the child PATH, from a different working directory and paths containing spaces.
- Checks expected counts and original/staged content hashes.
- Silently installs, repeats the GUI smoke test using the installed app, uninstalls,
  and verifies that user results remain.
- Generates SHA-256 checksums and uploads only tested distribution files.

A `desktop-v*` Git tag runs those gates again and publishes the tested assets to a
GitHub Release. Only that release job has repository write permission; PR/main builds
cannot publish releases. Never tag a failed or unreviewed build as a release.

Python/Tk and installed third-party license texts are exported with the package.
The Windows build lock pins PyInstaller 6.22.3, hooks 2026.8, altgraph 0.17.5,
pefile 2024.8.26 and pywin32-ctypes 0.2.3, in addition to the runtime lock.
PyInstaller uses GPL licensing with the bootloader distribution exception; other
license metadata/notices are retained. Inno Setup is the build compiler and is not
installed on user PCs. The combined lock advisory check on 2026-10-19 found no known
vulnerabilities; repeat it before subsequent releases.
