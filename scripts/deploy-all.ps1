# deploy-all.ps1
# Deploys all tools and agents to the active WXO environment.
# Run this against any fresh WXO instance to reproduce the full setup.
# Prerequisites: run .\activate-wxo.ps1 first.

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot | Split-Path -Parent

Write-Host "=== WXO Deploy All ===" -ForegroundColor Cyan
Write-Host "Root: $Root"

# ── Tools ────────────────────────────────────────────────────────────────────
Write-Host "`n[1/2] Importing tools..." -ForegroundColor Yellow

$toolsDir = Join-Path $Root "tools"

foreach ($file in Get-ChildItem -Path $toolsDir -Filter "*.py") {
    Write-Host "  -> Python tool: $($file.Name)"
    orchestrate tools import -k python -f $file.FullName
}

foreach ($file in Get-ChildItem -Path $toolsDir -Filter "*.yaml") {
    Write-Host "  -> OpenAPI tool: $($file.Name)"
    orchestrate tools import -k openapi -f $file.FullName
}

# ── Agents ───────────────────────────────────────────────────────────────────
Write-Host "`n[2/2] Importing agents..." -ForegroundColor Yellow

$agentsDir = Join-Path $Root "agents"

foreach ($agentDir in Get-ChildItem -Path $agentsDir -Directory) {
    $agentYaml = Join-Path $agentDir.FullName "agent.yaml"
    if (Test-Path $agentYaml) {
        Write-Host "  -> Agent: $($agentDir.Name)"
        orchestrate agents import -f $agentYaml
    }
}

Write-Host "`n=== Deploy complete ===" -ForegroundColor Green
