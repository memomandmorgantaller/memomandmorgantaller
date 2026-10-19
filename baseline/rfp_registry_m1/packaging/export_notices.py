"""Retain installed third-party license texts with the Windows distribution."""

import sys
from importlib.metadata import distribution
from pathlib import Path

names = [
    "pypdf",
    "defusedxml",
    "pyinstaller",
    "pyinstaller-hooks-contrib",
    "altgraph",
    "packaging",
    "setuptools",
    "pefile",
    "pywin32-ctypes",
]
parts = [
    "RFP Document Registry — third-party notices",
    "Python: PSF license. Tcl/Tk: BSD-style licenses. PyInstaller includes its bootloader distribution exception.",
    "Source: https://github.com/memomandmorgantaller/memomandmorgantaller",
    "This distribution is unsigned. No claim of organizational security approval is made.",
]
for name in names:
    package = distribution(name)
    parts.append(f"\n=== {package.metadata['Name']} {package.version} ===")
    parts.append(
        str(
            package.metadata.get("License-Expression")
            or package.metadata.get("License")
            or "See license text."
        )
    )
    for item in package.files or []:
        if "license" in str(item).lower() or "copying" in str(item).lower():
            path = Path(str(package.locate_file(item)))
            if path.is_file() and path.suffix not in {".pyc", ".py"}:
                parts.append(path.read_text(encoding="utf-8", errors="replace"))
for relative in ["LICENSE.txt", "tcl/tcl8.6/license.terms", "tcl/tk8.6/license.terms"]:
    path = Path(sys.base_prefix) / relative
    if path.is_file():
        parts.append(f"\n=== {relative} ===\n" + path.read_text(encoding="utf-8", errors="replace"))
Path("dist/THIRD_PARTY_NOTICES.txt").write_text("\n\n".join(parts), encoding="utf-8")
