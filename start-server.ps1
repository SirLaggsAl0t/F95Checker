# Start the F95Checker API server in the foreground. Ctrl+C stops it.
$ErrorActionPreference = 'Stop'
$server = Join-Path $PSScriptRoot 'server'
$python = Join-Path $server '.venv\Scripts\python.exe'

if (-not (Test-Path $python)) {
    Write-Error "Missing $python. Create it with: python -m venv server/.venv; server/.venv/Scripts/pip install -r server/requirements-dev.txt"
    exit 1
}

Set-Location $server
& $python 'run.py'
