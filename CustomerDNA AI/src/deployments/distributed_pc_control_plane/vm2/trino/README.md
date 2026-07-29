# VM2 Trino

VM2 hosts the Trino coordinator.

The Trino config here uses the VM2 host IP for discovery and for the Hive-backed Iceberg catalog so VM1 and VM3 workers can join later.
