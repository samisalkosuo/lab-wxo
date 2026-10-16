# teardown.ps1
# Removes all resources created by deploy-all.ps1 from the active WXO environment.
# Resources are removed in reverse dependency order: agents first, then flows, then tools,
# then knowledge bases, because agents reference tools and knowledge bases.
#
# REAL RESOURCE NAMES (not file names) are used here.  The tool package
# tools/incident_triage/incident_triage.py exports several @tool functions, each of which
# becomes an individual named tool in WXO; file-name discovery does not work for packages.
#
# SAFETY: Use -DryRun to print every command without executing it.
#   .\scripts\teardown.ps1 -DryRun
#
# IMPORTANT — UNTESTED FOR REAL DELETION:
#   Real deletion was NEVER executed against a live instance during development.
#   The demo resources on instance 'techzone1' were preserved intentionally.
#   The -DryRun output shows the exact commands that would run, but their actual
#   behaviour (including any confirmation prompts, errors when an agent still
#   references a tool, or partial-delete side effects) is unknown.
#
#   If `orchestrate agents remove` / `orchestrate tools remove` /
#   `orchestrate knowledge-bases remove` require a --yes / --force flag to be
#   non-interactive, the commands below will hang waiting for input.  Check each
#   subcommand's --help output and add the flag if needed before running for real.
#
# Prerequisites:
#   - Copy env.cfg.example to env.cfg and fill in WXO_API_KEY, WXO_URL, WXO_ENV_NAME.
#   - The `orchestrate` CLI must be on PATH (activated venv, or system install).
#
# Usage:
#   .\scripts\teardown.ps1           # real deletion (UNTESTED — see warning above)
#   .\scripts\teardown.ps1 -DryRun  # print commands without running them

param(
    [switch]$DryRun
)

$ErrorActionPreference = "Continue"   # errors are non-fatal; script continues after each failure
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$Root = $PSScriptRoot | Split-Path -Parent

# ── Dry-run helper ────────────────────────────────────────────────────────────
function Invoke-Remove {
    param([string[]]$ArgList, [string]$Description)
    if ($DryRun) {
        Write-Host "  [DRY-RUN] orchestrate $($ArgList -join ' ')" -ForegroundColor DarkCyan
    } else {
        Write-Host "  -> $Description"
        & orchestrate @ArgList
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "  WARNING: orchestrate $($ArgList -join ' ') exited with code $LASTEXITCODE (continuing)"
        }
    }
}

# ── Banner ────────────────────────────────────────────────────────────────────
if ($DryRun) {
    Write-Host "=== WXO Teardown (DRY-RUN -- no changes will be made) ===" -ForegroundColor Cyan
} else {
    Write-Host "=== WXO Teardown ===" -ForegroundColor Cyan
    Write-Warning "Real deletion mode.  This will remove resources from the active WXO environment."
    Write-Warning "NOTE: real deletion has never been tested.  Check --help for each subcommand if prompts appear."
}
Write-Host "Root: $Root"

# ── Prerequisite: orchestrate on PATH ────────────────────────────────────────
if (-not (Get-Command orchestrate -ErrorAction SilentlyContinue)) {
    Write-Error "ERROR: 'orchestrate' not found on PATH. Activate your virtual environment first."
    exit 1
}

# ── Read env.cfg and activate environment ────────────────────────────────────
# Same parsing logic as deploy-all.ps1: split on the first '=' only.
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

# Activate the environment so subsequent commands target the right instance.
Write-Host "`n[0/5] Registering and activating environment '$envName' ..." -ForegroundColor Yellow
if ($DryRun) {
    Write-Host "  [DRY-RUN] orchestrate env add -n $envName -u (url) --type $envType" -ForegroundColor DarkCyan
    Write-Host "  [DRY-RUN] orchestrate env activate $envName --api-key (api-key)" -ForegroundColor DarkCyan
} else {
    "Y" | & orchestrate env add -n $envName -u $url --type $envType
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "WARNING: env add exited $LASTEXITCODE (may be expected if env already exists)"
    }
    & orchestrate env activate $envName --api-key $apiKey
    if ($LASTEXITCODE -ne 0) {
        Write-Error "ERROR: env activate failed. Cannot proceed."
        exit $LASTEXITCODE
    }
}

# ── Step 1: Remove agents ─────────────────────────────────────────────────────
# Agents must be removed first because they reference tools and knowledge bases.
# Both agents are kind=native (from agent.yaml).
#
# CLI: orchestrate agents remove --name <name> --kind native
# NOTE: --kind is required per 'orchestrate agents remove --help'.
Write-Host "`n[1/5] Removing agents..." -ForegroundColor Yellow

foreach ($agentName in @("incident_triage", "hello_world")) {
    Invoke-Remove @("agents", "remove", "--name", $agentName, "--kind", "native") `
        "agents remove --name $agentName --kind native"
}

# ── Step 2: Remove flow tool ──────────────────────────────────────────────────
# The remediation approval flow is imported as a tool (kind=flow).
# It must be removed before the Python tools it calls (execute_remediation).
# CLI: orchestrate tools remove --name <name>
Write-Host "`n[2/5] Removing flow tool..." -ForegroundColor Yellow

Invoke-Remove @("tools", "remove", "--name", "request_remediation") `
    "tools remove --name request_remediation"

# ── Step 3: Remove Python tools ───────────────────────────────────────────────
# These are the @tool-decorated functions from tools/incident_triage/incident_triage.py
# and tools/greetings.py.  WXO registers each function as a separate named tool.
# The names are the function names exactly as written in the source.
# CLI: orchestrate tools remove --name <name>
Write-Host "`n[3/5] Removing Python tools..." -ForegroundColor Yellow

# tools/incident_triage/incident_triage.py — 8 @tool functions
foreach ($toolName in @(
    "list_open_incidents",
    "get_incident",
    "get_service_health",
    "query_logs",
    "get_metrics",
    "list_recent_deployments",
    "open_ticket",
    "execute_remediation"
)) {
    Invoke-Remove @("tools", "remove", "--name", $toolName) `
        "tools remove --name $toolName"
}

# tools/greetings.py — single @tool function
Invoke-Remove @("tools", "remove", "--name", "greeting") `
    "tools remove --name greeting"

# ── Step 4: Remove knowledge bases ────────────────────────────────────────────
# Knowledge bases can be removed after tools because nothing references them at
# the CLI level (the reference is inside agent.yaml only, and the agent is gone).
# CLI: orchestrate knowledge-bases remove --name <name>
# NOTE: --name is optional but --id is the alternative; --name is cleaner here.
# NOTE: removing a built-in Milvus KB deletes the ingested document data too.
Write-Host "`n[4/5] Removing knowledge bases..." -ForegroundColor Yellow

Invoke-Remove @("knowledge-bases", "remove", "--name", "incident_triage_runbooks") `
    "knowledge-bases remove --name incident_triage_runbooks"

# ── Done ──────────────────────────────────────────────────────────────────────
Write-Host "`n[5/5] Done." -ForegroundColor Yellow
if ($DryRun) {
    Write-Host "`n=== Dry run complete -- no changes were made ===" -ForegroundColor Cyan
    Write-Host "Review the commands above, then run without -DryRun to perform real deletion."
    Write-Host "REMINDER: real deletion has never been tested.  Check each subcommand's --help"
    Write-Host "          output for confirmation-prompt flags before executing for real."
} else {
    Write-Host "`n=== Teardown complete ===" -ForegroundColor Green
}
