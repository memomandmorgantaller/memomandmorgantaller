Windows desktop release: Python, Tk and runtime libraries are bundled.

Download **RFPRegistry-Setup-0.3.0-x64.exe**, run it, keep the desktop shortcut selected,
and open **RFP Document Registry**. Click **Try the built-in demonstration**, then
**Process package**. No Python installation or PowerShell commands are needed.

A portable **RFPRegistry.exe** is also available. Both include the synthetic demo.
Read **START_HERE.txt** and keep **THIRD_PARTY_NOTICES.txt** with the portable app.
**SHA256SUMS.txt** provides release checksums.

This version retains originals, inventories nested packages, and extracts PDF,
DOCX, XLSX and TXT evidence locally. Classification, approval, export and SharePoint
publishing are still future work. The demo deliberately includes one unsupported
CAD file, shown as needing attention.

The files are **unsigned**. Windows or company policy may require IT approval.
Do not disable security controls. Hosted-runner smoke tests cover the desktop demo,
frozen parser subprocesses and installed executable; they do not replace validation
on your company workstation or provide Windows parser sandboxing.
