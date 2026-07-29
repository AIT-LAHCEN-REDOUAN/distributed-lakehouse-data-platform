[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

function Test-TcpEndpoint {
    param(
        [Parameter(Mandatory = $true)][string]$HostName,
        [Parameter(Mandatory = $true)][int]$Port,
        [Parameter(Mandatory = $true)][string]$Label
    )

    try {
        $result = Test-NetConnection -ComputerName $HostName -Port $Port -InformationLevel Quiet -WarningAction SilentlyContinue
        if ($result) {
            Write-Host "[OK] $Label -> ${HostName}:$Port"
        }
        else {
            Write-Host "[WARN] $Label -> ${HostName}:$Port not reachable"
        }
    }
    catch {
        Write-Host "[WARN] $Label -> ${HostName}:$Port check failed: $($_.Exception.Message)"
    }
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptDir "../../../..")).Path

Write-Host "============================================================"
Write-Host " CustomerDNA Local Control Plane - Preflight Checks"
Write-Host "============================================================"

Write-Host "[Local tools]"
if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Host "[OK] docker"
}
else {
    Write-Host "[WARN] docker missing"
}

try {
    docker compose version | Out-Null
    Write-Host "[OK] docker compose"
}
catch {
    Write-Host "[WARN] docker compose missing"
}

if (Get-Command git -ErrorAction SilentlyContinue) {
    Write-Host "[OK] git"
}
else {
    Write-Host "[WARN] git missing"
}

Write-Host ""
Write-Host "[Required paths]"
$requiredPaths = @(
    (Join-Path $repoRoot "src/airflow/dags/client_1"),
    (Join-Path $repoRoot "src/processing/spark"),
    (Join-Path $repoRoot "src/monitoring"),
    (Join-Path $repoRoot "src/transformation/dbt_spark/client_1"),
    (Join-Path $repoRoot "src/quality/great_expectations/client_1")
)

foreach ($path in $requiredPaths) {
    if (Test-Path $path) {
        Write-Host "[OK] $path"
    }
    else {
        Write-Host "[WARN] Missing path: $path"
    }
}

Write-Host ""
Write-Host "[Remote dependencies]"
Test-TcpEndpoint -HostName "10.10.252.11" -Port 9092 -Label "Kafka broker on VM1"
Test-TcpEndpoint -HostName "10.10.252.12" -Port 9092 -Label "Kafka broker on VM2"
Test-TcpEndpoint -HostName "10.10.252.13" -Port 9092 -Label "Kafka broker on VM3"
Test-TcpEndpoint -HostName "10.10.252.12" -Port 9000 -Label "HDFS NameNode RPC on VM2"
Test-TcpEndpoint -HostName "10.10.252.12" -Port 9870 -Label "HDFS NameNode web on VM2"
Test-TcpEndpoint -HostName "10.10.252.12" -Port 9083 -Label "Hive Metastore on VM2"
Test-TcpEndpoint -HostName "10.10.252.12" -Port 7077 -Label "Spark master on VM2"
Test-TcpEndpoint -HostName "10.10.252.12" -Port 10000 -Label "Spark Thrift on VM2"
Test-TcpEndpoint -HostName "10.10.252.12" -Port 8088 -Label "Trino coordinator on VM2"
Test-TcpEndpoint -HostName "10.10.252.12" -Port 5435 -Label "Hive Metastore PostgreSQL on VM2"
Test-TcpEndpoint -HostName "10.10.252.11" -Port 8081 -Label "cAdvisor on VM1"
Test-TcpEndpoint -HostName "10.10.252.12" -Port 8081 -Label "cAdvisor on VM2"
Test-TcpEndpoint -HostName "10.10.252.13" -Port 8081 -Label "cAdvisor on VM3"
