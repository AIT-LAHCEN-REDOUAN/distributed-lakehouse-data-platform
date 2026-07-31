[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$runtimeLogs = Join-Path $scriptDir "runtime/airflow/logs"
$runtimeDir = Join-Path $scriptDir "runtime"
$runtimeComposeEnv = Join-Path $runtimeDir "compose.generated.env"
$envFile = Join-Path $scriptDir ".env"
$composeFile = Join-Path $scriptDir "docker-compose.yml"

function Get-EnvMap {
    param(
        [Parameter(Mandatory = $true)][string]$Path
    )

    $values = @{}
    Get-Content $Path | ForEach-Object {
        if ($_ -match '^\s*([^#=]+?)=(.*)$') {
            $values[$matches[1].Trim()] = $matches[2].Trim()
        }
    }
    return $values
}

function Test-PortInUse {
    param(
        [Parameter(Mandatory = $true)][int]$Port
    )

    try {
        $null = Get-NetTCPConnection -LocalPort $Port -ErrorAction Stop
        return $true
    }
    catch {
        return $false
    }
}

function Resolve-FreePort {
    param(
        [Parameter(Mandatory = $true)][int]$PreferredPort
    )

    $candidate = $PreferredPort
    while (Test-PortInUse -Port $candidate) {
        $candidate++
    }
    return $candidate
}

function Get-ExistingPublishedPort {
    param(
        [Parameter(Mandatory = $true)][string]$ContainerName,
        [Parameter(Mandatory = $true)][int]$ContainerPort
    )

    try {
        $inspectJson = docker inspect $ContainerName 2>$null
        if (-not $inspectJson) {
            return $null
        }

        $inspect = $inspectJson | ConvertFrom-Json
        if (-not $inspect[0].State.Running) {
            return $null
        }

        $portKey = "$ContainerPort/tcp"
        $bindings = $inspect[0].NetworkSettings.Ports.$portKey
        if ($bindings -and $bindings[0].HostPort) {
            return [int]$bindings[0].HostPort
        }
    }
    catch {
        return $null
    }

    return $null
}

function Invoke-Compose {
    param(
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )

    & docker compose --env-file $envFile --env-file $runtimeComposeEnv @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose $($Arguments -join ' ') failed with exit code $LASTEXITCODE"
    }
}

function Set-RuntimeComposeEnv {
    param(
        [Parameter(Mandatory = $true)][int]$AirflowPort,
        [Parameter(Mandatory = $true)][int]$PrometheusPort,
        [Parameter(Mandatory = $true)][int]$GrafanaPort,
        [Parameter(Mandatory = $true)][int]$KafkaUiPort
    )

    @(
        "CUSTOMERDNA_CONTROL_PLANE_AIRFLOW_PORT=$AirflowPort"
        "CUSTOMERDNA_CONTROL_PLANE_PROMETHEUS_PORT=$PrometheusPort"
        "CUSTOMERDNA_CONTROL_PLANE_GRAFANA_PORT=$GrafanaPort"
        "CUSTOMERDNA_CONTROL_PLANE_KAFKA_UI_PORT=$KafkaUiPort"
        "AIRFLOW__API__BASE_URL=http://localhost:$AirflowPort"
    ) | Set-Content -Path $runtimeComposeEnv -Encoding ascii
}

function Wait-ForContainerHealth {
    param(
        [Parameter(Mandatory = $true)][string]$ContainerName,
        [Parameter(Mandatory = $true)][int]$TimeoutSeconds,
        [Parameter(Mandatory = $true)][string]$Label
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)

    while ((Get-Date) -lt $deadline) {
        $inspectJson = docker inspect $ContainerName 2>$null
        if (-not $inspectJson) {
            Start-Sleep -Seconds 2
            continue
        }

        $inspect = $inspectJson | ConvertFrom-Json
        $state = $inspect[0].State

        if (-not $state.Running) {
            docker logs --tail 200 $ContainerName
            throw "$Label is not running."
        }

        if ($state.Health) {
            $healthStatus = $state.Health.Status
            if ($healthStatus -eq "healthy") {
                Write-Host "[OK] $Label is healthy"
                return
            }
            if ($healthStatus -eq "unhealthy") {
                docker logs --tail 200 $ContainerName
                throw "$Label became unhealthy."
            }
        }
        else {
            Write-Host "[OK] $Label is running"
            return
        }

        Start-Sleep -Seconds 5
    }

    docker logs --tail 200 $ContainerName
    throw "$Label did not become healthy within $TimeoutSeconds seconds."
}

Write-Host "============================================================"
Write-Host " CustomerDNA Local Control Plane - Start Stack"
Write-Host "============================================================"
Write-Host "Directory : $scriptDir"
Write-Host "Compose   : $composeFile"
Write-Host "Env file  : $envFile"
Write-Host "============================================================"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker is not installed or not on PATH."
}

docker compose version | Out-Null

if (-not (Test-Path $envFile)) {
    throw "Missing required env file: $envFile"
}

$envValues = Get-EnvMap -Path $envFile
$preferredAirflowPort = "18080"
if ($envValues.ContainsKey("CUSTOMERDNA_CONTROL_PLANE_AIRFLOW_PORT") -and $envValues["CUSTOMERDNA_CONTROL_PLANE_AIRFLOW_PORT"]) {
    $preferredAirflowPort = $envValues["CUSTOMERDNA_CONTROL_PLANE_AIRFLOW_PORT"]
}
$preferredPrometheusPort = "19090"
if ($envValues.ContainsKey("CUSTOMERDNA_CONTROL_PLANE_PROMETHEUS_PORT") -and $envValues["CUSTOMERDNA_CONTROL_PLANE_PROMETHEUS_PORT"]) {
    $preferredPrometheusPort = $envValues["CUSTOMERDNA_CONTROL_PLANE_PROMETHEUS_PORT"]
}
$preferredGrafanaPort = "13001"
if ($envValues.ContainsKey("CUSTOMERDNA_CONTROL_PLANE_GRAFANA_PORT") -and $envValues["CUSTOMERDNA_CONTROL_PLANE_GRAFANA_PORT"]) {
    $preferredGrafanaPort = $envValues["CUSTOMERDNA_CONTROL_PLANE_GRAFANA_PORT"]
}
$preferredKafkaUiPort = "18085"
if ($envValues.ContainsKey("CUSTOMERDNA_CONTROL_PLANE_KAFKA_UI_PORT") -and $envValues["CUSTOMERDNA_CONTROL_PLANE_KAFKA_UI_PORT"]) {
    $preferredKafkaUiPort = $envValues["CUSTOMERDNA_CONTROL_PLANE_KAFKA_UI_PORT"]
}

$preferredAirflowPort = [int]$preferredAirflowPort
$preferredPrometheusPort = [int]$preferredPrometheusPort
$preferredGrafanaPort = [int]$preferredGrafanaPort
$preferredKafkaUiPort = [int]$preferredKafkaUiPort

$resolvedAirflowPort = Get-ExistingPublishedPort -ContainerName "control_plane_airflow_api_server" -ContainerPort 8080
if (-not $resolvedAirflowPort) {
    $resolvedAirflowPort = Resolve-FreePort -PreferredPort $preferredAirflowPort
}

$resolvedPrometheusPort = Get-ExistingPublishedPort -ContainerName "control_plane_prometheus" -ContainerPort 9090
if (-not $resolvedPrometheusPort) {
    $resolvedPrometheusPort = Resolve-FreePort -PreferredPort $preferredPrometheusPort
}

$resolvedGrafanaPort = Get-ExistingPublishedPort -ContainerName "control_plane_grafana" -ContainerPort 3000
if (-not $resolvedGrafanaPort) {
    $resolvedGrafanaPort = Resolve-FreePort -PreferredPort $preferredGrafanaPort
}

$resolvedKafkaUiPort = Get-ExistingPublishedPort -ContainerName "control_plane_kafka_ui" -ContainerPort 8080
if (-not $resolvedKafkaUiPort) {
    $resolvedKafkaUiPort = Resolve-FreePort -PreferredPort $preferredKafkaUiPort
}

if ($resolvedAirflowPort -ne $preferredAirflowPort) {
    Write-Host "[INFO] Airflow port $preferredAirflowPort is busy. Using $resolvedAirflowPort."
}
if ($resolvedPrometheusPort -ne $preferredPrometheusPort) {
    Write-Host "[INFO] Prometheus port $preferredPrometheusPort is busy. Using $resolvedPrometheusPort."
}
if ($resolvedGrafanaPort -ne $preferredGrafanaPort) {
    Write-Host "[INFO] Grafana port $preferredGrafanaPort is busy. Using $resolvedGrafanaPort."
}
if ($resolvedKafkaUiPort -ne $preferredKafkaUiPort) {
    Write-Host "[INFO] Kafka UI port $preferredKafkaUiPort is busy. Using $resolvedKafkaUiPort."
}

$env:CUSTOMERDNA_CONTROL_PLANE_AIRFLOW_PORT = "$resolvedAirflowPort"
$env:CUSTOMERDNA_CONTROL_PLANE_PROMETHEUS_PORT = "$resolvedPrometheusPort"
$env:CUSTOMERDNA_CONTROL_PLANE_GRAFANA_PORT = "$resolvedGrafanaPort"
$env:CUSTOMERDNA_CONTROL_PLANE_KAFKA_UI_PORT = "$resolvedKafkaUiPort"
$env:AIRFLOW__API__BASE_URL = "http://localhost:$resolvedAirflowPort"

New-Item -ItemType Directory -Force -Path $runtimeLogs | Out-Null
New-Item -ItemType Directory -Force -Path $runtimeDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $runtimeDir "spark/.ivy2") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $runtimeDir "monitoring/state") | Out-Null
Set-RuntimeComposeEnv -AirflowPort $resolvedAirflowPort -PrometheusPort $resolvedPrometheusPort -GrafanaPort $resolvedGrafanaPort -KafkaUiPort $resolvedKafkaUiPort

Write-Host "[1/5] Building and starting base services"
Invoke-Compose -Arguments @(
    "up", "-d", "--build",
    "spark-submit-client",
    "airflow-postgres",
    "postgres-exporter",
    "pipeline-metrics-exporter",
    "prometheus",
    "kafka-ui",
    "grafana"
)

Write-Host "[2/5] Waiting for Airflow PostgreSQL"
Wait-ForContainerHealth -ContainerName "control_plane_airflow_postgres" -TimeoutSeconds 90 -Label "Airflow PostgreSQL"

Write-Host "[3/5] Running airflow-init"
Invoke-Compose -Arguments @(
    "up",
    "--build",
    "--abort-on-container-exit",
    "--exit-code-from", "airflow-init",
    "airflow-init"
)

Write-Host "[4/5] Starting Airflow API server and waiting for health"
Invoke-Compose -Arguments @("up", "-d", "airflow-api-server")
Wait-ForContainerHealth -ContainerName "control_plane_airflow_api_server" -TimeoutSeconds 180 -Label "Airflow API server"

Write-Host "[5/5] Starting remaining Airflow services"
Invoke-Compose -Arguments @("up", "-d", "airflow-scheduler", "airflow-dag-processor", "airflow-triggerer")

Write-Host "[6/7] Listing running services"
Invoke-Compose -Arguments @("ps")

Write-Host "[7/7] Access points"
Write-Host "Airflow   : http://localhost:$resolvedAirflowPort"
Write-Host "Prometheus: http://localhost:$resolvedPrometheusPort"
Write-Host "Grafana   : http://localhost:$resolvedGrafanaPort"
Write-Host "Kafka UI  : http://localhost:$resolvedKafkaUiPort"
Write-Host "Compose env override: $runtimeComposeEnv"
