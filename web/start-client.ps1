# Start the F95Checker Vite client in the foreground. Ctrl+C stops it.
$ErrorActionPreference = 'Stop'
$client = Join-Path $PSScriptRoot 'client'
$vite = Join-Path $client 'node_modules\.bin\vite.cmd'

if (-not (Test-Path $vite)) {
    Write-Error "Missing $vite. Install client deps with: corepack pnpm install --dir client"
    exit 1
}

Set-Location $client
& $vite --port 5173 --strictPort
