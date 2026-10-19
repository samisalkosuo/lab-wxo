# activate-wxo.ps1
# Reads env.cfg, registers the WXO environment (if needed), and activates it.
# If an API key is present in env.cfg or passed via -ApiKey, it activates non-interactively;
# otherwise, it activates interactively and prompts for the API key.
# For full non-interactive deploy, run scripts/deploy-all.ps1 instead.
param(
    [string]$ApiKey = ""
)

$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

$EnvFile = Join-Path $PSScriptRoot "env.cfg"

if (Test-Path $EnvFile) {
    # Parse key=value pairs from env.cfg (skip blank lines and comments; split on first '=' only)
    foreach ($line in Get-Content $EnvFile) {
        $line = $line.Trim()
        if ($line -eq "" -or $line.StartsWith("#")) { continue }
        $idx = $line.IndexOf("=")
        if ($idx -lt 1) { continue }
        $key   = $line.Substring(0, $idx).Trim()
        $value = $line.Substring($idx + 1).Trim()
        [System.Environment]::SetEnvironmentVariable($key, $value, "Process")
    }
}

if ($ApiKey) {
    $apiKey = $ApiKey
} else {
    $apiKey = $env:WXO_API_KEY
}

if ($apiKey -eq "your-api-key-here") {
    $apiKey = ""
}

$url     = $env:WXO_URL
$envName = $env:WXO_ENV_NAME
$envType = if ($env:WXO_ENV_TYPE) { $env:WXO_ENV_TYPE } else { "ibm_iam" }

if (-not $url -or -not $envName) {
    Write-Error "env.cfg (or environment variables) must define WXO_URL and WXO_ENV_NAME."
    exit 1
}

Write-Host "Registering WXO environment '$envName' ..."
# 'env add' asks "update the environment?" when the name already exists; answer Y so re-runs are non-interactive.
"Y" | orchestrate env add -n $envName -u $url --type $envType

if ($apiKey) {
    Write-Host "Activating WXO environment '$envName' with API key..."
    orchestrate env activate $envName --api-key $apiKey
} else {
    Write-Host "Activating WXO environment '$envName' (interactive)..."
    orchestrate env activate $envName
}

Write-Host "Done. Active environment: $envName" -ForegroundColor Green
