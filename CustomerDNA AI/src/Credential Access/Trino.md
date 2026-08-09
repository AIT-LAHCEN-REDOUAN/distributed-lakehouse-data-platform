# Trino

- Internal compatibility endpoint: `http://10.10.252.12:8088`
- Encrypted endpoint: `https://10.10.252.12:8443`
- Demo analyst username: `customerdna_analyst`
- Demo analyst password: `CustomerDNA_Trino_Analyst_2026!`
- Demo service username: `customerdna_service`
- Demo service password: `CustomerDNA_Trino_Service_2026!`
- Catalog: `lakehouse`
- Typical schemas:
  - `raw_data`
  - `analytics`
  - `intermediate`
  - `staging`

Notes:

- The public Trino endpoint is protected by the VM2 gateway layer.
- Airflow and monitoring use the `customerdna_service` account.
- The control plane now calls Trino over the encrypted `https://10.10.252.12:8443` path.
- DBeaver can use either port:
  - `8088` for HTTP with username/password
  - `8443` for HTTPS with username/password
- The HTTPS endpoint uses an internal demo certificate authority, so the client may ask you to trust the certificate.
