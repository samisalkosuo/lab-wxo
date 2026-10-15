# activate-wxo.ps1
# Reads env.cfg, registers the WXO environment (if needed), and activates it.

$EnvFile = Join-Path $PSScriptRoot "env.cfg"

if (-not (Test-Path $EnvFile)) {
    Write-Error "env.cfg not found. Copy env.cfg.example to env.cfg and fill in your credentials."
    exit 1
}

# Parse key=value pairs from env.cfg (skip blank lines and comments)
foreach ($line in Get-Content $EnvFile) {
    $line = $line.Trim()
    if ($line -eq "" -or $line.StartsWith("#")) { continue }
    $parts = $line -split "=", 2
    [System.Environment]::SetEnvironmentVariable($parts[0].Trim(), $parts[1].Trim(), "Process")
}

$apiKey  = $env:WXO_API_KEY
$url     = $env:WXO_URL
$envName = $env:WXO_ENV_NAME

if (-not $apiKey -or -not $url -or -not $envName) {
    Write-Error "env.cfg must define WXO_API_KEY, WXO_URL, and WXO_ENV_NAME."
    exit 1
}

Write-Host "Registering WXO environment '$envName' ..."
orchestrate env add -n $envName -u $url --type ibm_iam --activate 

Write-Host "Activating WXO environment '$envName' ..."
orchestrate env activate $envName

Write-Host "Done. Active environment: $envName"
