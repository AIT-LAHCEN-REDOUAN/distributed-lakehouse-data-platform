$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupRoot = Join-Path $scriptDir "runtime\\backups\\control_plane"
$targetDir = Join-Path $backupRoot $timestamp

New-Item -ItemType Directory -Force -Path $targetDir | Out-Null

$envPath = Join-Path $scriptDir ".env"
if (Test-Path $envPath) {
    Get-Content $envPath | ForEach-Object {
        if ($_ -match '^\s*#' -or $_ -notmatch '=') { return }
        $parts = $_ -split '=', 2
        [System.Environment]::SetEnvironmentVariable($parts[0], $parts[1], "Process")
    }
}

Write-Host "============================================================"
Write-Host " CustomerDNA Control Plane - Backup State"
Write-Host "============================================================"
Write-Host "Target directory: $targetDir"

Copy-Item (Join-Path $scriptDir ".env") $targetDir -ErrorAction SilentlyContinue
Copy-Item (Join-Path $scriptDir "docker-compose.yml") $targetDir
Copy-Item (Join-Path $scriptDir "prometheus.yml") $targetDir
Copy-Item (Join-Path $scriptDir "README.md") $targetDir -ErrorAction SilentlyContinue
Copy-Item (Join-Path $scriptDir "grafana") (Join-Path $targetDir "grafana") -Recurse -Force
Copy-Item (Join-Path $scriptDir "ssh") (Join-Path $targetDir "ssh") -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item (Join-Path $scriptDir "runtime\\monitoring") (Join-Path $targetDir "monitoring_state") -Recurse -Force -ErrorAction SilentlyContinue

$airflowDumpPath = Join-Path $targetDir "airflow_postgres.sql"
$airflowUser = if ($env:AIRFLOW_POSTGRES_USER) { $env:AIRFLOW_POSTGRES_USER } else { "airflow" }
$airflowDb = if ($env:AIRFLOW_POSTGRES_DB) { $env:AIRFLOW_POSTGRES_DB } else { "airflow" }

docker exec control_plane_airflow_postgres pg_dump -U $airflowUser $airflowDb | Out-File -Encoding utf8 $airflowDumpPath

Write-Host "[OK] Backup completed."
Write-Host "Airflow metadata dump: $airflowDumpPath"
