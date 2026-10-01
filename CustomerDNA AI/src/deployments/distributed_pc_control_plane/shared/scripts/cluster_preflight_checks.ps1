[CmdletBinding()]
param(
    [string]$Label = "CustomerDNA Distributed Cluster",
    [string]$Vm1Ip = "10.10.252.11",
    [string]$Vm2Ip = "10.10.252.12",
    [string]$Vm3Ip = "10.10.252.13"
)

$ErrorActionPreference = "Stop"

function Test-TcpEndpoint {
    param(
        [Parameter(Mandatory = $true)][string]$HostName,
        [Parameter(Mandatory = $true)][int]$Port,
        [Parameter(Mandatory = $true)][string]$ServiceLabel
    )

    try {
        $ok = Test-NetConnection -ComputerName $HostName -Port $Port -InformationLevel Quiet -WarningAction SilentlyContinue
        if ($ok) {
            Write-Host "[OK] $ServiceLabel -> ${HostName}:$Port"
        }
        else {
            Write-Host "[WARN] $ServiceLabel -> ${HostName}:$Port not reachable"
        }
    }
    catch {
        Write-Host "[WARN] $ServiceLabel -> ${HostName}:$Port check failed: $($_.Exception.Message)"
    }
}

Write-Host "============================================================"
Write-Host " $Label - Shared Preflight Checks"
Write-Host "============================================================"

Test-TcpEndpoint -HostName $Vm1Ip -Port 9092 -ServiceLabel "Kafka broker on VM1"
Test-TcpEndpoint -HostName $Vm2Ip -Port 9092 -ServiceLabel "Kafka broker on VM2"
Test-TcpEndpoint -HostName $Vm3Ip -Port 9092 -ServiceLabel "Kafka broker on VM3"

Test-TcpEndpoint -HostName $Vm2Ip -Port 9000 -ServiceLabel "HDFS NameNode RPC on VM2"
Test-TcpEndpoint -HostName $Vm2Ip -Port 9871 -ServiceLabel "HDFS NameNode web on VM2"
Test-TcpEndpoint -HostName $Vm2Ip -Port 9083 -ServiceLabel "Hive Metastore on VM2"
Test-TcpEndpoint -HostName $Vm2Ip -Port 5435 -ServiceLabel "Hive Metastore PostgreSQL on VM2"

Test-TcpEndpoint -HostName $Vm2Ip -Port 7077 -ServiceLabel "Spark master on VM2"
Test-TcpEndpoint -HostName $Vm2Ip -Port 8086 -ServiceLabel "Spark master UI on VM2"
Test-TcpEndpoint -HostName $Vm2Ip -Port 10000 -ServiceLabel "Spark Thrift on VM2"
Test-TcpEndpoint -HostName $Vm2Ip -Port 4040 -ServiceLabel "Spark Thrift UI on VM2"

Test-TcpEndpoint -HostName $Vm2Ip -Port 8088 -ServiceLabel "Trino coordinator on VM2"

Test-TcpEndpoint -HostName $Vm1Ip -Port 8081 -ServiceLabel "cAdvisor on VM1"
Test-TcpEndpoint -HostName $Vm2Ip -Port 8081 -ServiceLabel "cAdvisor on VM2"
Test-TcpEndpoint -HostName $Vm3Ip -Port 8081 -ServiceLabel "cAdvisor on VM3"
