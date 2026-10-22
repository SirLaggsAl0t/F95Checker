# Rebuild the F95Checker client, then start the Vite dev server. Ctrl+C stops it.
$ErrorActionPreference = 'Stop'
$client = Join-Path $PSScriptRoot 'client'
$vite = Join-Path $client 'node_modules\.bin\vite.cmd'

if (-not (Test-Path $vite)) {
    Write-Error "Missing $vite. Install client deps with: corepack pnpm install --dir client"
    exit 1
}

Set-Location $client
& corepack pnpm 'run' 'build'
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

& $vite --port 5173 --strictPort
