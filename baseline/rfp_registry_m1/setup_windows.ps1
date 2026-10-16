$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path '.venv\Scripts\python.exe')) {
    py -3.12 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Install Python 3.12 from an approved source.' }
}
& .\.venv\Scripts\python.exe -c 'import sys; assert sys.version_info[:2] == (3,12), "Python 3.12 required"'
if ($LASTEXITCODE -ne 0) { throw 'Existing .venv uses the wrong Python version.' }
& .\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements.lock
if ($LASTEXITCODE -ne 0) { throw 'Verified dependency installation failed.' }
& .\.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e .
if ($LASTEXITCODE -ne 0) { throw 'Project installation failed.' }
& "$PSScriptRoot\test_windows.ps1"
