<#
.SYNOPSIS
    Starts all five MediBridge AI local-dev processes (speech-pipeline,
    clinical-nlp, orchestrator, gateway, web) each in its own window, so a
    full local session is one command instead of five manually-juggled
    terminals. See README.md's "Local development" section for what each
    command does individually and why.

.PARAMETER Real
    Run speech-pipeline/clinical-nlp against the real ASR/MT/TTS/
    diarization/similarity models instead of the deterministic fixture
    providers. Requires requirements-full.txt already installed in
    speech-pipeline's venv (see README.md). Slower to start (model loads)
    and needs a real microphone-capable browser session -- fixture mode
    (the default) is enough to see the UI working end-to-end.

.EXAMPLE
    scripts\dev-up.ps1
    scripts\dev-up.ps1 -Real
#>
param(
    [switch]$Real
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$pidFile = Join-Path $repoRoot ".dev-pids.json"

if (Test-Path $pidFile) {
    Write-Host "A previous dev session's PID file already exists: $pidFile" -ForegroundColor Yellow
    Write-Host "Run scripts\dev-down.ps1 first (those processes may still be running)." -ForegroundColor Yellow
    exit 1
}

function Assert-Venv([string]$ServiceDir) {
    $python = Join-Path $repoRoot "services\$ServiceDir\.venv\Scripts\python.exe"
    if (-not (Test-Path $python)) {
        Write-Host "Missing venv: services\$ServiceDir\.venv" -ForegroundColor Red
        Write-Host "Run: cd services\$ServiceDir; python -m venv .venv; .venv\Scripts\Activate.ps1; pip install -r requirements-dev.txt" -ForegroundColor Red
        exit 1
    }
    return $python
}

$speechPython = Assert-Venv "speech-pipeline"
$clinicalPython = Assert-Venv "clinical-nlp"
$orchestratorPython = Assert-Venv "orchestrator"

if (-not (Test-Path (Join-Path $repoRoot "node_modules"))) {
    Write-Host "Missing root node_modules -- run 'npm install' first." -ForegroundColor Red
    exit 1
}

$fixtureMode = if ($Real) { "" } else { "1" }
if ($Real) {
    Write-Host "Starting in REAL model mode -- expect slower startup (model downloads/loads)." -ForegroundColor Cyan
} else {
    Write-Host "Starting in FIXTURE mode (deterministic, no model downloads) -- pass -Real for the actual ML pipeline." -ForegroundColor Cyan
}

$launched = @()

function Start-DevProcess([string]$Title, [string]$WorkDir, [string]$Command) {
    # cmd /k (not /c) keeps the window open if the command crashes on
    # startup, so a stack trace stays readable instead of flashing shut.
    $proc = Start-Process cmd.exe -ArgumentList "/k", "title $Title && $Command" `
        -WorkingDirectory $WorkDir -PassThru
    Write-Host "Started $Title (PID $($proc.Id))" -ForegroundColor Green
    return [PSCustomObject]@{ Title = $Title; Id = $proc.Id }
}

# Each service's env vars are set on this parent process right before it's
# launched -- Start-Process children inherit the parent's environment block
# at creation time, so later mutations here don't leak backward into
# already-started processes.
$env:MEDIBRIDGE_FIXTURE_MODE = $fixtureMode
$env:PYTHONPATH = "."
$env:CLINICAL_NLP_URL = "http://localhost:8002"
$env:ORCHESTRATOR_URL = "http://localhost:8004"
$launched += Start-DevProcess "speech-pipeline" (Join-Path $repoRoot "services\speech-pipeline") `
    "`"$speechPython`" -m uvicorn app.main:app --port 8001"

$env:MEDIBRIDGE_FIXTURE_MODE = $fixtureMode
$env:PYTHONPATH = "."
$launched += Start-DevProcess "clinical-nlp" (Join-Path $repoRoot "services\clinical-nlp") `
    "`"$clinicalPython`" -m uvicorn app.main:app --port 8002"

Remove-Item Env:\MEDIBRIDGE_FIXTURE_MODE -ErrorAction SilentlyContinue
$env:PYTHONPATH = "."
$launched += Start-DevProcess "orchestrator" (Join-Path $repoRoot "services\orchestrator") `
    "`"$orchestratorPython`" -m uvicorn app.main:app --port 8004"

Remove-Item Env:\PYTHONPATH -ErrorAction SilentlyContinue
$env:SPEECH_PIPELINE_WS_URL = "ws://localhost:8001/ws/transcribe"
$env:ORCHESTRATOR_URL = "http://localhost:8004"
$launched += Start-DevProcess "gateway" (Join-Path $repoRoot "services\gateway") "npm run dev"

Remove-Item Env:\SPEECH_PIPELINE_WS_URL -ErrorAction SilentlyContinue
$launched += Start-DevProcess "web" (Join-Path $repoRoot "apps\web") "npm run dev"

$launched | ConvertTo-Json | Set-Content -Path $pidFile

Write-Host ""
Write-Host "All five services are launching in separate windows -- give them ~5-10s to come up." -ForegroundColor Cyan
Write-Host "Check the 'web' window for the URL Vite prints (usually http://localhost:5173)." -ForegroundColor Cyan
Write-Host "Run scripts\dev-down.ps1 when you're done to stop everything." -ForegroundColor Cyan
