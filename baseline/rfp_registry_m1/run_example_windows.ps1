param(
    [Parameter(Mandatory=$true)][string]$Source,
    [Parameter(Mandatory=$true)][string]$Project,
    [Parameter(Mandatory=$true)][string]$Output
)
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    & .\.venv\Scripts\python.exe -m rfp_registry --source $Source --project $Project --output $Output
    $result = $LASTEXITCODE
    if ($result -eq 2) { Write-Warning 'Completed with exceptions. Review manifest and extraction reports.' }
    elseif ($result -ne 0) { throw 'Registry failed; inspect the reported error.' }
} finally { Pop-Location }
exit $result
