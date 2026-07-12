# SHIELD one-command demo reset (Sprint 6 T8).
#
# Tears the stack down INCLUDING volumes (a clean slate), rebuilds, waits for the
# full-matrix /ready probe (T3) to go all-green, reseeds the coherent Atlas demo
# story (4 services + a synthesized Risk Register, all released + downloadable),
# and prints the URLs + logins.
#
#   powershell -ExecutionPolicy Bypass -File scripts/demo-reset.ps1
#
# WARNING: `docker compose down -v` DELETES all demo data (Postgres, MinIO,
# Redis). That is the point of a reset — do not run this against anything you
# want to keep. Live AI is optional: put ANTHROPIC_API_KEY in .env first.

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

function Write-Step($m) { Write-Host "`n>> $m" -ForegroundColor Cyan }
function Test-DockerUp {
  docker info 1>$null 2>$null
  return ($LASTEXITCODE -eq 0)
}

Write-Host "============================================================" -ForegroundColor DarkCyan
Write-Host "  SHIELD by Kentro - resetting the demo stack (down -v)" -ForegroundColor DarkCyan
Write-Host "============================================================" -ForegroundColor DarkCyan

if (-not (Test-DockerUp)) {
  Write-Host "Docker daemon not running. Start Docker Desktop, then re-run." -ForegroundColor Red
  exit 1
}

# 1) Full teardown INCLUDING volumes (clean slate).
Write-Step "Tearing down (docker compose down -v)..."
docker compose down -v
if ($LASTEXITCODE -ne 0) { Write-Host "docker compose down -v failed." -ForegroundColor Red; exit 1 }

# 2) Rebuild + start the full stack.
Write-Step "Building + starting containers (docker compose up -d --build)..."
docker compose up -d --build
if ($LASTEXITCODE -ne 0) { Write-Host "docker compose up failed - see output above." -ForegroundColor Red; exit 1 }

# 3) Wait for the FULL-MATRIX readiness probe to go all-green (T3): every
#    required dependency (db, redis, minio, keycloak, llm) must report ok.
Write-Step "Waiting for /ready (full dependency matrix) to be all-green..."
$ready = $false
$offenders = ""
for ($i = 0; $i -lt 80; $i++) {
  try {
    $r = Invoke-WebRequest -UseBasicParsing "http://localhost:8000/ready" -TimeoutSec 3
    $body = $r.Content | ConvertFrom-Json
    if ($body.ready -eq $true) { $ready = $true; break }
    $offenders = ($body.offenders -join ", ")
  } catch {}
  Start-Sleep -Seconds 3
}
if (-not $ready) {
  Write-Host "Stack not ready in time. Offenders: $offenders" -ForegroundColor Red
  Write-Host "Inspect: docker compose logs api" -ForegroundColor Yellow
  exit 1
}
Write-Host "All dependencies ready." -ForegroundColor Green

# 4) Seed the coherent Atlas demo (idempotent, but the DB is fresh here).
Write-Step "Seeding the Atlas demo story..."
docker compose exec -T api python scripts/seed_demo.py
if ($LASTEXITCODE -ne 0) { Write-Host "Seed failed - see output above." -ForegroundColor Red; exit 1 }

# 5) Give the web app a moment (first build is slow; non-fatal if not ready yet).
Write-Step "Waiting for the web app..."
for ($i = 0; $i -lt 40; $i++) {
  try {
    $r = Invoke-WebRequest -UseBasicParsing "http://localhost:3000" -TimeoutSec 3
    if ($r.StatusCode -lt 500) { break }
  } catch {}
  Start-Sleep -Seconds 3
}

# 6) Print the banner.
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  SHIELD by Kentro - demo reset complete" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  Web app:     " -NoNewline; Write-Host "http://localhost:3000" -ForegroundColor White
Write-Host "  API + docs:  " -NoNewline; Write-Host "http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Readiness:   " -NoNewline; Write-Host "http://localhost:8000/ready" -ForegroundColor White
Write-Host "  MailHog:     " -NoNewline; Write-Host "http://localhost:8025" -ForegroundColor White
Write-Host ""
Write-Host "  ADMIN  login: " -NoNewline -ForegroundColor Cyan
Write-Host "admin@kentro.example   /  DemoPass!2026" -ForegroundColor White
Write-Host "  CLIENT login: " -NoNewline -ForegroundColor Cyan
Write-Host "client@atlas.example   /  DemoPass!2026" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  Demo story: 4 services + Risk Register, released + downloadable" -ForegroundColor DarkGray
Write-Host "  See it on:  /home and /documents (client) - reports download" -ForegroundColor DarkGray
Write-Host "  Live AI (optional): put ANTHROPIC_API_KEY in .env, then re-run." -ForegroundColor DarkGray
Write-Host ""
