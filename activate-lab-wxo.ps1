# activate-lab-wxo.ps1
# Convenience bootstrap script for lab-wxo.
#
# What it does:
#   1. Creates Python virtual environment (.venv) if missing.
#   2. Activates the virtual environment.
#   3. Installs dependencies from requirements.txt.
#   4. Checks for env.cfg; prompts for credentials or API key if not configured.
#   5. Runs activate-wxo.ps1 to register and activate the WXO environment.
#
# Usage:
#   .\activate-lab-wxo.ps1        # Run script
#   . .\activate-lab-wxo.ps1      # Dot-source to keep .venv active in current shell

param(
    [string]$ApiKey = ""
)

$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

$Root = $PSScriptRoot
$VenvDir = Join-Path $Root ".venv"
$ReqFile = Join-Path $Root "requirements.txt"
$EnvFile = Join-Path $Root "env.cfg"
$EnvExample = Join-Path $Root "env.cfg.example"
$ActivateWxoScript = Join-Path $Root "activate-wxo.ps1"

Write-Host "`n=== lab-wxo Environment Activation ===" -ForegroundColor Cyan

# ── 1. Python & Virtual Environment ──────────────────────────────────────────
$pyCmd = $null
foreach ($cand in @("python", "py", "python3")) {
    if (Get-Command $cand -ErrorAction SilentlyContinue) {
        $pyCmd = $cand
        break
    }
}

if (-not $pyCmd) {
    Write-Error "ERROR: Python is not found on PATH. Please install Python 3.11+ and try again."
    exit 1
}

if (-not (Test-Path $VenvDir)) {
    Write-Host "[1/4] Creating virtual environment (.venv)..." -ForegroundColor Yellow
    & $pyCmd -m venv $VenvDir
    if ($LASTEXITCODE -ne 0 -and -not (Test-Path $VenvDir)) {
        Write-Error "ERROR: Failed to create virtual environment in '$VenvDir'."
        exit 1
    }
} else {
    Write-Host "[1/4] Virtual environment (.venv) found." -ForegroundColor Green
}

# Activate virtual environment in current session / process
$venvActivate = Join-Path $VenvDir "Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    . $venvActivate
} else {
    # Fallback path adjustment
    $venvScripts = Join-Path $VenvDir "Scripts"
    $env:PATH = "$venvScripts;$env:PATH"
    $env:VIRTUAL_ENV = $VenvDir
}

# ── 2. Install Requirements ──────────────────────────────────────────────────
Write-Host "[2/4] Checking / installing dependencies from requirements.txt..." -ForegroundColor Yellow
$pyVenv = Join-Path $VenvDir "Scripts\python.exe"
if (-not (Test-Path $pyVenv)) { $pyVenv = "python" }

if (Test-Path $ReqFile) {
    & $pyVenv -m pip install --quiet --upgrade pip
    & $pyVenv -m pip install --quiet -r $ReqFile
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "pip install returned exit code $LASTEXITCODE. Retrying with verbose output..."
        & $pyVenv -m pip install -r $ReqFile
    }
} else {
    Write-Host "  (requirements.txt not found, skipping pip install)"
}

# ── 3. Configuration & API Key ──────────────────────────────────────────────
Write-Host "[3/4] Checking environment configuration (env.cfg)..." -ForegroundColor Yellow

$resolvedApiKey = $ApiKey

if (-not (Test-Path $EnvFile)) {
    Write-Host "  env.cfg not found." -ForegroundColor DarkYellow
    $createCfg = Read-Host "  Would you like to create env.cfg now? (Y/n)"
    if ($createCfg -eq "" -or $createCfg -match "^[Yy]") {
        $inputUrl = Read-Host "  Enter WXO instance URL"
        $inputEnvName = Read-Host "  Enter WXO environment name [my-env]"
        if (-not $inputEnvName) { $inputEnvName = "my-env" }
        $inputApiKey = Read-Host "  Enter WXO API key (press Enter to skip/prompt later)"
        $inputType = Read-Host "  Enter WXO environment type (ibm_iam/mcsp) [ibm_iam]"
        if (-not $inputType) { $inputType = "ibm_iam" }

        $cfgContent = @"
WXO_API_KEY=$inputApiKey
WXO_URL=$inputUrl
WXO_ENV_NAME=$inputEnvName
WXO_ENV_TYPE=$inputType
"@
        Set-Content -Path $EnvFile -Value $cfgContent -Encoding utf8
        Write-Host "  Created env.cfg." -ForegroundColor Green
        if ($inputApiKey) { $resolvedApiKey = $inputApiKey }
    }
} else {
    # Parse existing env.cfg to check if API key is present
    $cfgLines = Get-Content $EnvFile
    $existingKey = ""
    foreach ($line in $cfgLines) {
        $line = $line.Trim()
        if ($line -eq "" -or $line.StartsWith("#")) { continue }
        $idx = $line.IndexOf("=")
        if ($idx -lt 1) { continue }
        $k = $line.Substring(0, $idx).Trim()
        $v = $line.Substring($idx + 1).Trim()
        if ($k -eq "WXO_API_KEY") { $existingKey = $v }
    }

    if (-not $resolvedApiKey) {
        if ($existingKey -and $existingKey -ne "your-api-key-here") {
            $resolvedApiKey = $existingKey
        } else {
            Write-Host "  WXO_API_KEY is not set in env.cfg." -ForegroundColor DarkYellow
            $inputKey = Read-Host "  Enter WXO API key (press Enter to activate interactively)"
            if ($inputKey) {
                $resolvedApiKey = $inputKey
                $saveKey = Read-Host "  Save this API key to env.cfg? (y/N)"
                if ($saveKey -match "^[Yy]") {
                    $newLines = @()
                    $updated = $false
                    foreach ($line in $cfgLines) {
                        if ($line.Trim().StartsWith("WXO_API_KEY=")) {
                            $newLines += "WXO_API_KEY=$inputKey"
                            $updated = $true
                        } else {
                            $newLines += $line
                        }
                    }
                    if (-not $updated) { $newLines = @("WXO_API_KEY=$inputKey") + $newLines }
                    Set-Content -Path $EnvFile -Value $newLines -Encoding utf8
                    Write-Host "  Updated env.cfg with API key." -ForegroundColor Green
                }
            }
        }
    }
}

# ── 4. Execute activate-wxo.ps1 ──────────────────────────────────────────────
Write-Host "[4/4] Activating WXO environment..." -ForegroundColor Yellow
if (Test-Path $ActivateWxoScript) {
    if ($resolvedApiKey) {
        & $ActivateWxoScript -ApiKey $resolvedApiKey
    } else {
        & $ActivateWxoScript
    }
} else {
    Write-Error "ERROR: $ActivateWxoScript not found."
    exit 1
}

Write-Host "`n=== lab-wxo activation complete! ===" -ForegroundColor Green
Write-Host "To deploy scenarios, run:" -ForegroundColor Cyan
Write-Host "  .\scripts\deploy-all.ps1"
Write-Host "`nTip: Dot-source this script (. .\activate-lab-wxo.ps1) to keep .venv active in your PowerShell shell.`n" -ForegroundColor DarkGray
