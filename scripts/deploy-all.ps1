# deploy-all.ps1
# Deploys all resource types to a WXO environment non-interactively.
# Reads credentials from env.cfg in the repository root; never reads secrets from other sources.
#
# Import order (dependency chain):
#   connections -> tools (flat .py, OpenAPI .yaml, package folders) -> knowledge bases -> flows -> agents
#
# Prerequisites:
#   - Copy env.cfg.example to env.cfg and fill in WXO_API_KEY, WXO_URL, WXO_ENV_NAME.
#   - The `orchestrate` CLI must be on PATH (activated venv, or system install).
#
# Usage:
#   .\scripts\deploy-all.ps1

$ErrorActionPreference = "Continue"   # Do NOT use Stop; native commands don't throw.
# The orchestrate CLI prints Unicode symbols (e.g. a check mark) after knowledge-base import. With redirected
# output Python on Windows defaults to cp1252 and crashes with UnicodeEncodeError (exit code 1) even though the
# import itself succeeded. Force UTF-8.
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$Root = $PSScriptRoot | Split-Path -Parent

# ── Helper: run an orchestrate command and stop on failure ──────────────────
function Invoke-Orchestrate {
    param([string[]]$ArgList, [string]$Description, [string]$StdIn = $null)
    Write-Host "    $Description"
    if ($null -ne $StdIn) {
        $StdIn | & orchestrate @ArgList
    } else {
        & orchestrate @ArgList
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Error "ERROR: orchestrate $($ArgList -join ' ') exited with code $LASTEXITCODE. Aborting."
        exit $LASTEXITCODE
    }
}

Write-Host "=== WXO Deploy All ===" -ForegroundColor Cyan
Write-Host "Root: $Root"

# ── Prerequisite: orchestrate on PATH ──────────────────────────────────────
if (-not (Get-Command orchestrate -ErrorAction SilentlyContinue)) {
    Write-Error "ERROR: 'orchestrate' not found on PATH. Activate your virtual environment first."
    exit 1
}

# ── Read env.cfg ────────────────────────────────────────────────────────────
$EnvFile = Join-Path $Root "env.cfg"
if (-not (Test-Path $EnvFile)) {
    Write-Error "ERROR: env.cfg not found at '$EnvFile'. Copy env.cfg.example and fill in your credentials."
    exit 1
}

foreach ($line in Get-Content $EnvFile) {
    $line = $line.Trim()
    if ($line -eq "" -or $line.StartsWith("#")) { continue }
    $idx = $line.IndexOf("=")
    if ($idx -lt 1) { continue }
    $key   = $line.Substring(0, $idx).Trim()
    $value = $line.Substring($idx + 1).Trim()
    [System.Environment]::SetEnvironmentVariable($key, $value, "Process")
}

$apiKey  = $env:WXO_API_KEY
$url     = $env:WXO_URL
$envName = $env:WXO_ENV_NAME
$envType = if ($env:WXO_ENV_TYPE) { $env:WXO_ENV_TYPE } else { "ibm_iam" }

if (-not $apiKey -or -not $url -or -not $envName) {
    Write-Error "ERROR: env.cfg must define WXO_API_KEY, WXO_URL, and WXO_ENV_NAME."
    exit 1
}

# ── Register and activate environment ───────────────────────────────────────
Write-Host "`n[0/6] Registering and activating environment '$envName' ..." -ForegroundColor Yellow
# 'env add' asks "update the environment?" when the name already exists; answer Y so re-runs are non-interactive.
Invoke-Orchestrate @("env", "add", "-n", $envName, "-u", $url, "--type", $envType) `
    "orchestrate env add -n $envName -u <url> --type $envType" "Y"
Invoke-Orchestrate @("env", "activate", $envName, "--api-key", $apiKey) `
    "orchestrate env activate $envName --api-key ***"

# ── Connections ──────────────────────────────────────────────────────────────
Write-Host "`n[1/6] Importing connections..." -ForegroundColor Yellow
$connectionsDir = Join-Path $Root "connections"
if (Test-Path $connectionsDir) {
    foreach ($file in Get-ChildItem -Path $connectionsDir -Filter "*.yaml" -Recurse) {
        Invoke-Orchestrate @("connections", "import", "-f", $file.FullName) `
            "connections import -f $($file.Name)"
    }
} else {
    Write-Host "  (no connections/ directory, skipping)"
}

# ── Tools ────────────────────────────────────────────────────────────────────
Write-Host "`n[2/6] Importing tools..." -ForegroundColor Yellow
$toolsDir = Join-Path $Root "tools"

if (Test-Path $toolsDir) {
    # Single-file Python tools: tools/*.py
    foreach ($file in Get-ChildItem -Path $toolsDir -Filter "*.py") {
        Invoke-Orchestrate @("tools", "import", "-k", "python", "-f", $file.FullName) `
            "tools import -k python -f $($file.Name)"
    }

    # OpenAPI tools: tools/*.yaml
    foreach ($file in Get-ChildItem -Path $toolsDir -Filter "*.yaml") {
        Invoke-Orchestrate @("tools", "import", "-k", "openapi", "-f", $file.FullName) `
            "tools import -k openapi -f $($file.Name)"
    }

    # Multi-file Python package tools: tools/<name>/ with requirements.txt
    foreach ($pkgDir in Get-ChildItem -Path $toolsDir -Directory) {
        $reqFile = Join-Path $pkgDir.FullName "requirements.txt"
        if (-not (Test-Path $reqFile)) { continue }
        # Find the single .py entry file directly inside the package folder
        $entryFiles = Get-ChildItem -Path $pkgDir.FullName -Filter "*.py" -Depth 0 | Where-Object { $_.Name -ne "__init__.py" }
        if ($entryFiles.Count -eq 0) {
            Write-Host "  WARNING: package '$($pkgDir.Name)' has requirements.txt but no top-level .py entry file; skipping."
            continue
        }
        foreach ($entry in $entryFiles) {
            Invoke-Orchestrate @("tools", "import", "-k", "python",
                "-p", $pkgDir.FullName,
                "-f", $entry.FullName,
                "-r", $reqFile) `
                "tools import -k python -p $($pkgDir.Name) -f $($entry.Name) -r requirements.txt"
        }
    }
} else {
    Write-Host "  (no tools/ directory, skipping)"
}

# ── Knowledge bases ───────────────────────────────────────────────────────────
Write-Host "`n[3/6] Importing knowledge bases..." -ForegroundColor Yellow
$knowledgeDir = Join-Path $Root "knowledge"
if (Test-Path $knowledgeDir) {
    foreach ($file in Get-ChildItem -Path $knowledgeDir -Filter "*.yaml" -Recurse) {
        Invoke-Orchestrate @("knowledge-bases", "import", "-f", $file.FullName) `
            "knowledge-bases import -f $($file.Name)"
    }
} else {
    Write-Host "  (no knowledge/ directory, skipping)"
}

# ── Flows ────────────────────────────────────────────────────────────────────
Write-Host "`n[4/6] Importing flows..." -ForegroundColor Yellow
$flowsDir = Join-Path $Root "flows"
if (Test-Path $flowsDir) {
    foreach ($file in Get-ChildItem -Path $flowsDir -Filter "*.py" -Recurse) {
        Invoke-Orchestrate @("tools", "import", "-k", "flow", "-f", $file.FullName) `
            "tools import -k flow -f $($file.Name)"
    }
} else {
    Write-Host "  (no flows/ directory, skipping)"
}

# ── Agents ────────────────────────────────────────────────────────────────────
Write-Host "`n[5/6] Importing agents..." -ForegroundColor Yellow
$agentsDir = Join-Path $Root "agents"
if (Test-Path $agentsDir) {
    foreach ($agentDir in Get-ChildItem -Path $agentsDir -Directory) {
        $agentYaml = Join-Path $agentDir.FullName "agent.yaml"
        if (Test-Path $agentYaml) {
            Invoke-Orchestrate @("agents", "import", "-f", $agentYaml) `
                "agents import -f $($agentDir.Name)/agent.yaml"

            # 'agents import' creates a DRAFT agent. The chat UI lists only LIVE agents,
            # so promote it. This fails on the Developer Edition (draft only); warn and continue.
            $nameLine = Get-Content $agentYaml | Where-Object { $_ -match '^name:\s*(\S+)' } | Select-Object -First 1
            if ($nameLine -match '^name:\s*(\S+)') {
                $agentName = $Matches[1]
                Write-Host "    agents deploy --name $agentName"
                & orchestrate agents deploy --name $agentName
                if ($LASTEXITCODE -ne 0) {
                    Write-Warning "agents deploy failed for '$agentName' (exit $LASTEXITCODE). The agent exists as a draft; it may not appear in the chat UI."
                }
            }
        }
    }
} else {
    Write-Host "  (no agents/ directory, skipping)"
}

Write-Host "`n=== Deploy complete ===" -ForegroundColor Green
