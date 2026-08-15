[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$composeFile = Join-Path $scriptDir "docker-compose.yml"
$envFile = Join-Path $scriptDir ".env"
$runtimeMonitoring = Join-Path $scriptDir "runtime/monitoring/state"
$runtimeComposeEnv = Join-Path $scriptDir "runtime/compose.generated.env"

Write-Host "============================================================"
Write-Host " CustomerDNA Local Control Plane - Reset Monitoring"
Write-Host "============================================================"
Write-Host "Directory : $scriptDir"
Write-Host "Compose   : $composeFile"
Write-Host "Env file  : $envFile"
Write-Host "============================================================"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker is not installed or not on PATH."
}

Write-Host "[1/4] Stopping control-plane services"
docker compose --env-file $envFile down

Write-Host "[2/4] Clearing isolated monitoring state"
New-Item -ItemType Directory -Force -Path $runtimeMonitoring | Out-Null
Get-ChildItem -Path $runtimeMonitoring -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
if (Test-Path $runtimeComposeEnv) {
    Remove-Item -Force $runtimeComposeEnv
}

Write-Host "[3/4] Removing Prometheus history volume"
$prometheusVolume = "control_plane_pc_prometheus_data"
if (docker volume ls --format '{{.Name}}' | Select-String -Pattern "^${prometheusVolume}$" -Quiet) {
    docker volume rm $prometheusVolume | Out-Null
    Write-Host "[OK] Removed $prometheusVolume"
}
else {
    Write-Host "[INFO] Volume $prometheusVolume not found"
}

Write-Host "[4/4] Monitoring reset complete"
Write-Host "Next step: run .\\start_control_plane_pc.ps1"
