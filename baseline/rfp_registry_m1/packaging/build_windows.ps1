$ErrorActionPreference = 'Stop'
Push-Location (Join-Path $PSScriptRoot '..')
try {
    python -c 'import sys,struct; assert sys.platform == "win32" and struct.calcsize("P") == 8, "Build on 64-bit Windows"'
    if ($LASTEXITCODE -ne 0) { throw 'A 64-bit Windows Python 3.12 build environment is required.' }
    python -m PyInstaller --noconfirm --clean --onefile --windowed --name RFPRegistry --icon packaging/registry.ico --version-file packaging/version_info.txt --add-data 'examples/synthetic_vertical_slice.zip;assets' --collect-all pypdf --copy-metadata pypdf --copy-metadata defusedxml --distpath dist --workpath build --specpath . rfp_registry/desktop_entry.py
    if ($LASTEXITCODE -ne 0) { throw 'Executable build failed. Check PyInstaller output.' }
    python packaging/export_notices.py
    if ($LASTEXITCODE -ne 0) { throw 'Dependency notices could not be exported.' }
    Copy-Item packaging/START_HERE.txt dist/START_HERE.txt
    $compiler = Join-Path ${env:ProgramFiles(x86)} 'Inno Setup 6\ISCC.exe'
    if (-not (Test-Path $compiler)) { throw 'Inno Setup 6 is required on the build machine.' }
    & $compiler packaging/installer.iss
    if ($LASTEXITCODE -ne 0) { throw 'Installer build failed.' }
} catch {
    $message = $_.Exception.Message.Replace('%', '%25').Replace("`r", '%0D').Replace("`n", '%0A')
    Write-Output "::error::$message"
    throw
} finally { Pop-Location }
