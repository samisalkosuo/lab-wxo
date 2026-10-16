# activate-wxo.ps1
# Reads env.cfg, registers the WXO environment (if needed), and activates it interactively.
# For non-interactive/scripted use, run scripts/deploy-all.ps1 instead.

$EnvFile = Join-Path $PSScriptRoot "env.cfg"

if (-not (Test-Path $EnvFile)) {
    Write-Error "env.cfg not found. Copy env.cfg.example to env.cfg and fill in your credentials."
    exit 1
}

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

$apiKey  = $env:WXO_API_KEY
$url     = $env:WXO_URL
$envName = $env:WXO_ENV_NAME
$envType = if ($env:WXO_ENV_TYPE) { $env:WXO_ENV_TYPE } else { "ibm_iam" }

if (-not $apiKey -or -not $url -or -not $envName) {
    Write-Error "env.cfg must define WXO_API_KEY, WXO_URL, and WXO_ENV_NAME."
    exit 1
}

Write-Host "Registering WXO environment '$envName' ..."
orchestrate env add -n $envName -u $url --type $envType

Write-Host "Activating WXO environment '$envName' ..."
orchestrate env activate $envName

Write-Host "Done. Active environment: $envName"
