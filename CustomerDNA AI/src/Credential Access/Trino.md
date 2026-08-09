# Trino

- Endpoint: `http://10.10.252.12:8088`
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
- DBeaver should use the public endpoint on port `8088`.
