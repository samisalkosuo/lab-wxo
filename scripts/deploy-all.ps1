# deploy-all.ps1
# Deploys scenarios to a WXO environment non-interactively.
# Reads credentials from env.cfg in the repository root; never reads secrets from other sources.
#
# What gets deployed comes from the scenario manifests (scenarios/<id>/scenario.yaml), read by
# scripts/scenario_manifest.py. Without -Scenario, every manifest with `status: live` is deployed.
#
# Import order (dependency chain):
#   connections -> tools (flat .py, OpenAPI .yaml, package folders) -> knowledge bases -> flows -> agents
#
# Prerequisites:
#   - Copy env.cfg.example to env.cfg and fill in WXO_API_KEY, WXO_URL, WXO_ENV_NAME.
#   - The `orchestrate` CLI must be on PATH (activated venv, or system install).
#   - Python with PyYAML (the one that runs `orchestrate`; ibm-watsonx-orchestrate depends on PyYAML).
#
# Usage:
#   .\scripts\deploy-all.ps1                           # every live scenario
#   .\scripts\deploy-all.ps1 -Scenario incident-triage # one scenario
param([string]$Scenario = "")

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

# ── Resolve the deploy plan from the scenario manifests ────────────────────
# Prefer the python.exe that sits next to the orchestrate CLI (same environment, has PyYAML).
$py = $null
$orchCmd = Get-Command orchestrate -ErrorAction SilentlyContinue
if ($orchCmd -and $orchCmd.Source) {
    $candidate = Join-Path (Split-Path $orchCmd.Source -Parent) "python.exe"
    if (Test-Path $candidate) { $py = $candidate }
}
if (-not $py) {
    $found = Get-Command python -ErrorAction SilentlyContinue
    if ($found) { $py = $found.Source }
}
if (-not $py) {
    Write-Error "ERROR: Python not found. Activate the virtual environment that has ibm-watsonx-orchestrate installed."
    exit 1
}
$planArgs = @((Join-Path $Root "scripts\scenario_manifest.py"), "deploy-plan")
if ($Scenario) { $planArgs += @("--scenario", $Scenario) }
$planLines = @(& $py @planArgs)
if ($LASTEXITCODE -ne 0) {
    Write-Error "ERROR: could not build the deploy plan (see message above). Aborting."
    exit 1
}
$plan = @($planLines | Where-Object { $_ } | ForEach-Object { , ($_ -split "`t") })
function Get-FullPath([string]$RelPath) { [System.IO.Path]::GetFullPath((Join-Path $Root $RelPath)) }
if ($Scenario) { Write-Host "Scenario: $Scenario" } else { Write-Host "Scenarios: all with status 'live'" }

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
$steps = @($plan | Where-Object { $_[0] -like "tool_*" })
if ($steps.Count -eq 0) { Write-Host "  (no tools in the plan, skipping)" }
foreach ($s in $steps) {
    switch ($s[0]) {
        "tool_py" {
            Invoke-Orchestrate @("tools", "import", "-k", "python", "-f", (Get-FullPath $s[1])) `
                "tools import -k python -f $(Split-Path $s[1] -Leaf)"
        }
        "tool_openapi" {
            Invoke-Orchestrate @("tools", "import", "-k", "openapi", "-f", (Get-FullPath $s[1])) `
                "tools import -k openapi -f $(Split-Path $s[1] -Leaf)"
        }
        "tool_pkg" {
            Invoke-Orchestrate @("tools", "import", "-k", "python",
                "-p", (Get-FullPath $s[1]),
                "-f", (Get-FullPath $s[2]),
                "-r", (Get-FullPath $s[3])) `
                "tools import -k python -p $(Split-Path $s[1] -Leaf) -f $(Split-Path $s[2] -Leaf) -r requirements.txt"
        }
    }
}

# ── Knowledge bases ───────────────────────────────────────────────────────────
Write-Host "`n[3/6] Importing knowledge bases..." -ForegroundColor Yellow
$steps = @($plan | Where-Object { $_[0] -eq "kb" })
if ($steps.Count -eq 0) { Write-Host "  (no knowledge bases in the plan, skipping)" }
foreach ($s in $steps) {
    Invoke-Orchestrate @("knowledge-bases", "import", "-f", (Get-FullPath $s[1])) `
        "knowledge-bases import -f $(Split-Path $s[1] -Leaf)"
}

# ── Flows ────────────────────────────────────────────────────────────────────
Write-Host "`n[4/6] Importing flows..." -ForegroundColor Yellow
$steps = @($plan | Where-Object { $_[0] -eq "flow" })
if ($steps.Count -eq 0) { Write-Host "  (no flows in the plan, skipping)" }
foreach ($s in $steps) {
    Invoke-Orchestrate @("tools", "import", "-k", "flow", "-f", (Get-FullPath $s[1])) `
        "tools import -k flow -f $(Split-Path $s[1] -Leaf)"
}

# ── Agents ────────────────────────────────────────────────────────────────────
Write-Host "`n[5/6] Importing agents..." -ForegroundColor Yellow
$steps = @($plan | Where-Object { $_[0] -eq "agent" })
if ($steps.Count -eq 0) { Write-Host "  (no agents in the plan, skipping)" }
foreach ($s in $steps) {
    $agentName = $s[2]
    Invoke-Orchestrate @("agents", "import", "-f", (Get-FullPath $s[1])) `
        "agents import -f $($s[1] -replace '^agents/','')"

    # 'agents import' creates a DRAFT agent. The chat UI lists only LIVE agents,
    # so promote it. This fails on the Developer Edition (draft only); warn and continue.
    Write-Host "    agents deploy --name $agentName"
    & orchestrate agents deploy --name $agentName
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "agents deploy failed for '$agentName' (exit $LASTEXITCODE). The agent exists as a draft; it may not appear in the chat UI."
    }
}

Write-Host "`n=== Deploy complete ===" -ForegroundColor Green
