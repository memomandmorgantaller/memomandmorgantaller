"""Run frozen GUI + parsers without developer Python on PATH, then install/uninstall."""

from __future__ import annotations

import hashlib
import json
import ntpath
import os
import subprocess
import tempfile
from collections.abc import Mapping
from pathlib import Path


def runtime_environment(environ: Mapping[str, str]) -> dict[str, str]:
    # Windows environment names are case-insensitive, unlike a plain dict copy.
    environment = {name.upper(): value for name, value in environ.items()}
    root = environment.get("SYSTEMROOT")
    if not root:
        raise ValueError("Windows SYSTEMROOT is missing from the build environment")
    for name in ("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV", "TCL_LIBRARY", "TK_LIBRARY"):
        environment.pop(name, None)
    environment["PATH"] = ntpath.join(root, "System32") + ";" + root
    return environment


def smoke(executable: Path, root: Path) -> Path:
    report = root / "smoke-result.json"
    environment = runtime_environment(os.environ)
    process = subprocess.run(
        [
            str(executable),
            "--smoke-test",
            "--output",
            str(root / "results"),
            "--result",
            str(report),
        ],
        cwd=root,
        env=environment,
        timeout=240,
        capture_output=True,
        check=False,
    )
    if not report.is_file():
        raise RuntimeError(
            f"Packaged GUI did not save a smoke report (exit {process.returncode}): {process.stderr.decode(errors='replace')}"
        )
    result = json.loads(report.read_text(encoding="utf-8"))
    if process.returncode or not result["ok"]:
        raise RuntimeError(f"Packaged GUI demo failed: {result}")
    output = Path(result["output"])
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    for entry in manifest["entries"]:
        for field in ("extracted_relative_path", "snapshot_relative_path"):
            if entry.get(field):
                digest = hashlib.sha256((output / entry[field]).read_bytes()).hexdigest()
                assert digest == entry["sha256"], "Frozen output hash mismatch"
    return output


def main() -> None:
    distribution = Path("dist").resolve(strict=True)
    installer = distribution / "RFPRegistry-Setup-0.3.0-x64.exe"
    assert installer.read_bytes()[:2] == b"MZ", "Missing Windows installer"
    executable = distribution / "RFPRegistry.exe"
    assert executable.read_bytes()[:2] == b"MZ", "Missing Windows executable"
    with tempfile.TemporaryDirectory(prefix="RFP packaged smoke ") as temporary:
        root = Path(temporary)
        portable = root / "portable test"
        portable.mkdir()
        smoke(executable, portable)
        installed = root / "installed application"
        subprocess.run(
            [str(installer), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", f"/DIR={installed}"],
            timeout=180,
            check=True,
        )
        installed_exe = installed / "RFPRegistry.exe"
        assert installed_exe.is_file(), "Installer did not deploy the executable"
        installed_test = root / "installed test"
        installed_test.mkdir()
        results = smoke(installed_exe, installed_test)
        subprocess.run(
            [str(installed / "unins000.exe"), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"],
            timeout=180,
            check=True,
        )
        assert not installed_exe.exists(), "Uninstaller did not remove the executable"
        assert (results / "manifest.json").exists(), "Uninstall removed user results"
    names = ["RFPRegistry.exe", installer.name, "START_HERE.txt", "THIRD_PARTY_NOTICES.txt"]
    lines = [
        hashlib.sha256((distribution / name).read_bytes()).hexdigest() + "  " + name
        for name in names
    ]
    (distribution / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        "Windows portable GUI, installed GUI, parser subprocesses, hashes and uninstall preservation passed."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        message = str(error).replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        print(f"::error::{message}")
        raise
