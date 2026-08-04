<#
.SYNOPSIS
    Stops everything started by scripts\dev-up.ps1.

    Uses `taskkill /T /F` (not Stop-Process) on each recorded PID -- uvicorn
    and `npm run dev` both spawn child processes, and killing only the
    parent PID would leave those children running and still holding their
    ports, forcing a manual hunt-and-kill next time. /T kills the whole
    process tree.
#>

$ErrorActionPreference = "SilentlyContinue"
$repoRoot = Split-Path -Parent $PSScriptRoot
$pidFile = Join-Path $repoRoot ".dev-pids.json"

if (-not (Test-Path $pidFile)) {
    Write-Host "No .dev-pids.json found -- nothing to stop (or dev-up.ps1 was never run)." -ForegroundColor Yellow
    exit 0
}

$entries = Get-Content $pidFile | ConvertFrom-Json
foreach ($entry in $entries) {
    $proc = Get-Process -Id $entry.Id -ErrorAction SilentlyContinue
    if ($proc) {
        Write-Host "Stopping $($entry.Title) (PID $($entry.Id))..." -ForegroundColor Cyan
        taskkill /PID $entry.Id /T /F | Out-Null
    } else {
        Write-Host "$($entry.Title) (PID $($entry.Id)) already stopped." -ForegroundColor DarkGray
    }
}

Remove-Item $pidFile -Force
Write-Host "All dev services stopped." -ForegroundColor Green
