# Client 1 dbt-spark Transformation Layer

This project materializes the structured lakehouse layers that sit on top of the Iceberg raw zone:

- `raw_data`: Kafka + HDFS + Spark generated raw Iceberg tables
- `staging`: standardized, typed views
- `intermediate`: reusable business-ready tables
- `analytics`: final reporting marts

## Local Installation

Install dbt-spark in your active virtual environment:

```powershell
pip install -r "D:\github\Master_PFE_Project\CustomerDNA AI\src\transformation\dbt_spark\client_1\requirements.txt"
```

## Local Execution

Make sure the Spark Thrift Server is running, then:

```powershell
$env:DBT_PROFILES_DIR="D:\github\Master_PFE_Project\CustomerDNA AI\src\transformation\dbt_spark\client_1"
$env:CUSTOMERDNA_DBT_SPARK_HOST="localhost"
$env:CUSTOMERDNA_DBT_SPARK_PORT="10000"
dbt debug
dbt run
dbt test
```
