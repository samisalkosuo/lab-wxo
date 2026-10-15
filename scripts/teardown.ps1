# teardown.ps1
# Removes all agents and tools from the active WXO environment.
# Use for dev cleanup before re-deploying a fresh state.
# Prerequisites: run .\activate-wxo.ps1 first.

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot | Split-Path -Parent

Write-Host "=== WXO Teardown ===" -ForegroundColor Cyan

# ── Agents ───────────────────────────────────────────────────────────────────
Write-Host "`n[1/2] Removing agents..." -ForegroundColor Yellow

$agentsDir = Join-Path $Root "agents"

foreach ($agentDir in Get-ChildItem -Path $agentsDir -Directory) {
    $agentYaml = Join-Path $agentDir.FullName "agent.yaml"
    if (Test-Path $agentYaml) {
        $agentName = (Get-Content $agentYaml | Select-String "^name:" | ForEach-Object { $_ -replace "^name:\s*", "" }).Trim()
        if ($agentName) {
            Write-Host "  -> Removing agent: $agentName"
            orchestrate agents remove --agent-name $agentName 2>&1 | Out-Null
        }
    }
}

# ── Tools ────────────────────────────────────────────────────────────────────
Write-Host "`n[2/2] Removing tools..." -ForegroundColor Yellow

$toolsDir = Join-Path $Root "tools"

foreach ($file in Get-ChildItem -Path $toolsDir -Filter "*.py") {
    $toolName = $file.BaseName
    Write-Host "  -> Removing tool: $toolName"
    orchestrate tools remove --tool-name $toolName 2>&1 | Out-Null
}

Write-Host "`n=== Teardown complete ===" -ForegroundColor Green
