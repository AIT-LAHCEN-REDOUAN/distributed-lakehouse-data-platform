# LUKS Encrypted Runtime Storage

Purpose:

- Protect VM runtime service data at rest for the distributed demo deployment.
- Encrypt the mounted runtime areas used by Kafka, HDFS, Hive Metastore PostgreSQL, Spark, and Trino.

Deployment scope:

- VM1 encrypted runtime mount: `/mnt/customerdna_secure`
- VM2 encrypted runtime mount: `/mnt/customerdna_secure`
- VM3 encrypted runtime mount: `/mnt/customerdna_secure`

Demo passphrases:

- VM1: `CustomerDNA_LUKS_VM1_2026!`
- VM2: `CustomerDNA_LUKS_VM2_2026!`
- VM3: `CustomerDNA_LUKS_VM3_2026!`

Backing image paths:

- VM1: `/var/lib/customerdna-secure/customerdna-vm1.img`
- VM2: `/var/lib/customerdna-secure/customerdna-vm2.img`
- VM3: `/var/lib/customerdna-secure/customerdna-vm3.img`

Notes:

- These passphrases are for the demo only and are intentionally documented here for fast redeployment.
- The encrypted storage setup is applied by `setup_encrypted_storage_vm1.sh`, `setup_encrypted_storage_vm2.sh`, and `setup_encrypted_storage_vm3.sh`.
- Containers do not open the LUKS devices themselves. The host VM opens and mounts the encrypted filesystem first, then Docker bind-mounts the decrypted runtime paths.
