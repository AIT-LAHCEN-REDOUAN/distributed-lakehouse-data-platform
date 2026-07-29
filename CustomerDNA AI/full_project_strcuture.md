D:\GITHUB\MASTER_PFE_PROJECT\CUSTOMERDNA AI
│   .gitignore
│   README.md
│   RUNBOOK_local_Acer.md
│   tools_port_local_Acer.txt
│
├───datasets
│   └───client_1
│       ├───Customer_Personality_Analysis
│       │       marketing_campaign.csv
│       │
│       ├───E-commerce_customer_churn
│       │       E-commerce_customer_churn.xlsx
│       │
│       ├───Retailrocket_recommender_system_dataset
│       │       category_tree.csv
│       │       events.csv
│       │       item_properties_part1.csv
│       │       item_properties_part2.csv
│       │
│       └───UCI_Online_Retail_2
│               online_retail_2.xlsx
│
├───project_presentation
│   ├───PFE_presentation
│   ├───PFE_Report
│   │       main.tex
│   │       Master_PFE_Report.docx
│   │       README.md
│   │
│   └───PFE_resources
│       ├───Figures
│       │   │   SAT_values.png
│       │   │
│       │   ├───French_Version
│       │   │       SAT_values_French.png
│       │   │
│       │   └───Tech_logos
│       │           Airflow.png
│       │           Apache_Hive.png
│       │           Apache_Iceberg.png
│       │           apache_kafka.png
│       │           Apache_Parquet.png
│       │           data_build_tool.png
│       │           docker.png
│       │           github.png
│       │           Grafana.png
│       │           great_expectations.png
│       │           hadoop.png
│       │           hadoop_hdfs.png
│       │           kubernetes.png
│       │           OpenVPN.png
│       │           Prometheus.png
│       │           spark.png
│       │           trino.png
│       │
│       └───Logos
│               company_image.png
│               School_image.png
│               University_image.png
│
├───project_requirements
│       BUSINESS_RULES.md
│       BUSINESS_RULES_PFE_REPORT.md
│       initial_project_description.txt
│
└───src
    │   README.md
    │
    ├───airflow
    │   │   .env
    │   │   .env.example
    │   │   docker-compose.yml
    │   │   requirements.txt
    │   │
    │   ├───config
    │   ├───dags
    │   │   └───client_1
    │   │       │   client_1_dag_common.py
    │   │       │   client_1_dbt_spark_transformations_dag.py
    │   │       │   client_1_kafka_hdfs_spark_raw_dag.py
    │   │       │   client_1_lakehouse_readiness_dag.py
    │   │       │   client_1_lakehouse_setup_dag.py
    │   │       │   __init__.py
    │   │       │
    │   │       └───__pycache__
    │   │               client_1_dag_common.cpython-311.pyc
    │   │               client_1_dag_common.cpython-313.pyc
    │   │               client_1_dbt_spark_transformations_dag.cpython-311.pyc
    │   │               client_1_dbt_spark_transformations_dag.cpython-313.pyc
    │   │               client_1_kafka_hdfs_spark_raw_dag.cpython-311.pyc
    │   │               client_1_kafka_hdfs_spark_raw_dag.cpython-313.pyc
    │   │               client_1_lakehouse_readiness_dag.cpython-311.pyc
    │   │               client_1_lakehouse_readiness_dag.cpython-313.pyc
    │   │               client_1_lakehouse_setup_dag.cpython-311.pyc
    │   │               client_1_lakehouse_setup_dag.cpython-313.pyc
    │   │               customerdna_client1_dag_common.cpython-311.pyc
    │   │               customerdna_client1_dag_common.cpython-313.pyc
    │   │               customerdna_client1_dw_setup_dag.cpython-311.pyc
    │   │               customerdna_client1_dw_setup_dag.cpython-313.pyc
    │   │               customerdna_client1_lakehouse_readiness_dag.cpython-311.pyc
    │   │               customerdna_client1_lakehouse_readiness_dag.cpython-313.pyc
    │   │               customerdna_client1_raw_load_dag.cpython-311.pyc
    │   │               customerdna_client1_raw_load_dag.cpython-313.pyc
    │   │               __init__.cpython-311.pyc
    │   │               __init__.cpython-313.pyc
    │   │
    │   ├───logs
    │   │   ├───dag_id=customerdna_client1_dbt_spark_lakehouse_pipeline
    │   │   │   ├───run_id=manual__2026-07-16T134241.857838+0000
    │   │   │   │   ├───task_id=run_dbt_spark_lakehouse_models
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │       attempt=2.log
    │   │   │   │   │
    │   │   │   │   └───task_id=validate_spark_thrift_service
    │   │   │   │           attempt=1.log
    │   │   │   │
    │   │   │   ├───run_id=manual__2026-07-16T135503.203237+0000
    │   │   │   │   ├───task_id=run_dbt_spark_lakehouse_models
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │       attempt=2.log
    │   │   │   │   │
    │   │   │   │   └───task_id=validate_spark_thrift_service
    │   │   │   │           attempt=1.log
    │   │   │   │
    │   │   │   ├───run_id=manual__2026-07-16T142743.964724+0000
    │   │   │   │   ├───task_id=run_dbt_spark_lakehouse_models
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │       attempt=2.log
    │   │   │   │   │
    │   │   │   │   └───task_id=validate_spark_thrift_service
    │   │   │   │           attempt=1.log
    │   │   │   │           attempt=2.log
    │   │   │   │
    │   │   │   ├───run_id=manual__2026-07-16T143057.255533+0000
    │   │   │   │   ├───task_id=run_dbt_spark_lakehouse_models
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │       attempt=2.log
    │   │   │   │   │
    │   │   │   │   └───task_id=validate_spark_thrift_service
    │   │   │   │           attempt=1.log
    │   │   │   │
    │   │   │   ├───run_id=manual__2026-07-16T143840.432803+0000
    │   │   │   │   ├───task_id=run_dbt_spark_lakehouse_models
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │       attempt=2.log
    │   │   │   │   │
    │   │   │   │   └───task_id=validate_spark_thrift_service
    │   │   │   │           attempt=1.log
    │   │   │   │
    │   │   │   ├───run_id=manual__2026-07-16T150502.361656+0000
    │   │   │   │   ├───task_id=run_dbt_spark_lakehouse_models
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │       attempt=2.log
    │   │   │   │   │
    │   │   │   │   └───task_id=validate_spark_thrift_service
    │   │   │   │           attempt=1.log
    │   │   │   │
    │   │   │   ├───run_id=manual__2026-07-16T151025.682197+0000
    │   │   │   │   ├───task_id=run_dbt_spark_lakehouse_models
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │       attempt=2.log
    │   │   │   │   │
    │   │   │   │   └───task_id=validate_spark_thrift_service
    │   │   │   │           attempt=1.log
    │   │   │   │
    │   │   │   ├───run_id=manual__2026-07-16T154403.215373+0000
    │   │   │   │   ├───task_id=run_dbt_spark_lakehouse_models
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │       attempt=2.log
    │   │   │   │   │
    │   │   │   │   └───task_id=validate_spark_thrift_service
    │   │   │   │           attempt=1.log
    │   │   │   │
    │   │   │   ├───run_id=manual__2026-07-16T181249.265753+0000
    │   │   │   │   ├───task_id=run_dbt_spark_lakehouse_models
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   ├───task_id=test_dbt_spark_lakehouse_models
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   ├───task_id=validate_spark_thrift_service
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   └───task_id=validate_trino_query_service
    │   │   │   │           attempt=1.log
    │   │   │   │
    │   │   │   ├───run_id=manual__2026-07-17T142002.503061+0000
    │   │   │   │   ├───task_id=run_dbt_spark_lakehouse_models
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   ├───task_id=test_dbt_spark_lakehouse_models
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   ├───task_id=validate_spark_thrift_service
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   └───task_id=validate_trino_query_service
    │   │   │   │           attempt=1.log
    │   │   │   │
    │   │   │   ├───run_id=manual__2026-07-18T131908.145963+0000
    │   │   │   │   ├───task_id=run_dbt_spark_lakehouse_models
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   ├───task_id=test_dbt_spark_lakehouse_models
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   ├───task_id=validate_spark_thrift_service
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   └───task_id=validate_trino_query_service
    │   │   │   │           attempt=1.log
    │   │   │   │
    │   │   │   ├───run_id=manual__2026-07-20T222954.434302+0000
    │   │   │   │   ├───task_id=run_dbt_spark_lakehouse_models
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │       attempt=2.log
    │   │   │   │   │
    │   │   │   │   └───task_id=validate_spark_thrift_service
    │   │   │   │           attempt=1.log
    │   │   │   │
    │   │   │   ├───run_id=manual__2026-07-21T094821.589661+0000
    │   │   │   │   └───task_id=validate_spark_thrift_service
    │   │   │   │           attempt=1.log
    │   │   │   │
    │   │   │   ├───run_id=manual__2026-07-22T175552.930370+0000
    │   │   │   │   ├───task_id=run_dbt_spark_lakehouse_models
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   ├───task_id=test_dbt_spark_lakehouse_models
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   ├───task_id=validate_spark_thrift_service
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   └───task_id=validate_trino_query_service
    │   │   │   │           attempt=1.log
    │   │   │   │
    │   │   │   └───run_id=manual__2026-07-27T205612.607191+0000
    │   │   │       ├───task_id=run_dbt_spark_lakehouse_models
    │   │   │       │       attempt=1.log
    │   │   │       │
    │   │   │       ├───task_id=test_dbt_spark_lakehouse_models
    │   │   │       │       attempt=1.log
    │   │   │       │
    │   │   │       ├───task_id=validate_spark_thrift_service
    │   │   │       │       attempt=1.log
    │   │   │       │
    │   │   │       └───task_id=validate_trino_query_service
    │   │   │               attempt=1.log
    │   │   │
    │   │   ├───dag_id=customerdna_client1_kafka_hdfs_spark_lakehouse_pipeline
    │   │   │   ├───run_id=manual__2026-07-15T225233.061970+0000
    │   │   │   │   └───task_id=stream_sources_to_hdfs_and_build_iceberg_raw_with_spark
    │   │   │   │           attempt=1.log
    │   │   │   │           attempt=2.log
    │   │   │   │
    │   │   │   ├───run_id=manual__2026-07-15T230221.310499+0000
    │   │   │   │   └───task_id=stream_sources_to_hdfs_and_build_iceberg_raw_with_spark
    │   │   │   │           attempt=1.log
    │   │   │   │
    │   │   │   ├───run_id=manual__2026-07-15T233607.626824+0000
    │   │   │   │   └───task_id=stream_sources_to_hdfs_and_build_iceberg_raw_with_spark
    │   │   │   │           attempt=1.log
    │   │   │   │
    │   │   │   ├───run_id=manual__2026-07-15T235905.017074+0000
    │   │   │   │   └───task_id=stream_sources_to_hdfs_and_build_iceberg_raw_with_spark
    │   │   │   │           attempt=1.log
    │   │   │   │
    │   │   │   ├───run_id=manual__2026-07-16T115451.399830+0000
    │   │   │   │   └───task_id=stream_sources_to_hdfs_and_build_iceberg_raw_with_spark
    │   │   │   │           attempt=1.log
    │   │   │   │           attempt=2.log
    │   │   │   │
    │   │   │   ├───run_id=manual__2026-07-16T122753.397034+0000
    │   │   │   │   ├───task_id=bootstrap_raw_lakehouse_quality_assets
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   ├───task_id=stream_sources_to_hdfs_and_build_iceberg_raw_with_spark
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   └───task_id=validate_raw_lakehouse_quality
    │   │   │   │           attempt=1.log
    │   │   │   │
    │   │   │   ├───run_id=manual__2026-07-16T223552.033849+0000
    │   │   │   │   └───task_id=stream_sources_to_hdfs_and_build_iceberg_raw_with_spark
    │   │   │   │           attempt=1.log
    │   │   │   │
    │   │   │   ├───run_id=manual__2026-07-17T115728.057201+0000
    │   │   │   │   ├───task_id=bootstrap_raw_lakehouse_quality_assets
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   ├───task_id=stream_sources_to_hdfs_and_build_iceberg_raw_with_spark
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   └───task_id=validate_raw_lakehouse_quality
    │   │   │   │           attempt=1.log
    │   │   │   │
    │   │   │   ├───run_id=manual__2026-07-18T121306.365365+0000
    │   │   │   │   ├───task_id=bootstrap_raw_lakehouse_quality_assets
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   ├───task_id=stream_sources_to_hdfs_and_build_iceberg_raw_with_spark
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   └───task_id=validate_raw_lakehouse_quality
    │   │   │   │           attempt=1.log
    │   │   │   │
    │   │   │   ├───run_id=manual__2026-07-20T131915.600958+0000
    │   │   │   │   └───task_id=stream_sources_to_hdfs_and_build_iceberg_raw_with_spark
    │   │   │   │           attempt=1.log
    │   │   │   │           attempt=2.log
    │   │   │   │
    │   │   │   ├───run_id=manual__2026-07-20T190908.143129+0000
    │   │   │   │   └───task_id=stream_sources_to_hdfs_and_build_iceberg_raw_with_spark
    │   │   │   │           attempt=1.log
    │   │   │   │
    │   │   │   ├───run_id=manual__2026-07-20T224412.052383+0000
    │   │   │   │   ├───task_id=bootstrap_raw_lakehouse_quality_assets
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   ├───task_id=stream_sources_to_hdfs_and_build_iceberg_raw_with_spark
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   └───task_id=validate_raw_lakehouse_quality
    │   │   │   │           attempt=1.log
    │   │   │   │
    │   │   │   ├───run_id=manual__2026-07-21T105625.992307+0000
    │   │   │   │   ├───task_id=bootstrap_raw_lakehouse_quality_assets
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   ├───task_id=stream_sources_to_hdfs_and_build_iceberg_raw_with_spark
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   └───task_id=validate_raw_lakehouse_quality
    │   │   │   │           attempt=1.log
    │   │   │   │
    │   │   │   └───run_id=manual__2026-07-27T193556.483248+0000
    │   │   │       ├───task_id=bootstrap_raw_lakehouse_quality_assets
    │   │   │       │       attempt=1.log
    │   │   │       │
    │   │   │       ├───task_id=stream_sources_to_hdfs_and_build_iceberg_raw_with_spark
    │   │   │       │       attempt=1.log
    │   │   │       │
    │   │   │       └───task_id=validate_raw_lakehouse_quality
    │   │   │               attempt=1.log
    │   │   │
    │   │   ├───dag_id=customerdna_client1_lakehouse_readiness_pipeline
    │   │   │   ├───run_id=manual__2026-07-16T183012.597721+0000
    │   │   │   │   ├───task_id=validate_hdfs_bronze_service
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   ├───task_id=validate_hive_metastore_service
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   ├───task_id=validate_spark_cluster_service
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   ├───task_id=validate_spark_thrift_service
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   └───task_id=validate_trino_query_service
    │   │   │   │           attempt=1.log
    │   │   │   │
    │   │   │   ├───run_id=manual__2026-07-17T143606.017401+0000
    │   │   │   │   ├───task_id=validate_hdfs_bronze_service
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   ├───task_id=validate_hive_metastore_service
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   ├───task_id=validate_spark_cluster_service
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   ├───task_id=validate_spark_thrift_service
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   └───task_id=validate_trino_query_service
    │   │   │   │           attempt=1.log
    │   │   │   │
    │   │   │   ├───run_id=manual__2026-07-18T132135.050670+0000
    │   │   │   │   ├───task_id=validate_hdfs_bronze_service
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   ├───task_id=validate_hive_metastore_service
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   ├───task_id=validate_spark_cluster_service
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   ├───task_id=validate_spark_thrift_service
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   └───task_id=validate_trino_query_service
    │   │   │   │           attempt=1.log
    │   │   │   │
    │   │   │   ├───run_id=manual__2026-07-22T181647.154092+0000
    │   │   │   │   ├───task_id=validate_hdfs_bronze_service
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   ├───task_id=validate_hive_metastore_service
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   ├───task_id=validate_spark_cluster_service
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   ├───task_id=validate_spark_thrift_service
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   └───task_id=validate_trino_query_service
    │   │   │   │           attempt=1.log
    │   │   │   │
    │   │   │   └───run_id=manual__2026-07-27T193249.274471+0000
    │   │   │       ├───task_id=validate_hdfs_bronze_service
    │   │   │       │       attempt=1.log
    │   │   │       │
    │   │   │       ├───task_id=validate_hive_metastore_service
    │   │   │       │       attempt=1.log
    │   │   │       │
    │   │   │       ├───task_id=validate_spark_cluster_service
    │   │   │       │       attempt=1.log
    │   │   │       │
    │   │   │       ├───task_id=validate_spark_thrift_service
    │   │   │       │       attempt=1.log
    │   │   │       │
    │   │   │       └───task_id=validate_trino_query_service
    │   │   │               attempt=1.log
    │   │   │
    │   │   ├───dag_id=customerdna_client1_lakehouse_setup_pipeline
    │   │   │   ├───run_id=manual__2026-07-15T224413.132355+0000
    │   │   │   │   ├───task_id=initialize_client1_hdfs_bronze_zone
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   ├───task_id=initialize_client1_iceberg_namespaces
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   └───task_id=validate_trino_query_service
    │   │   │   │           attempt=1.log
    │   │   │   │
    │   │   │   ├───run_id=manual__2026-07-16T223454.665422+0000
    │   │   │   │   ├───task_id=initialize_client1_hdfs_bronze_zone
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   ├───task_id=initialize_client1_iceberg_namespaces
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   └───task_id=validate_trino_query_service
    │   │   │   │           attempt=1.log
    │   │   │   │
    │   │   │   ├───run_id=manual__2026-07-17T115514.231536+0000
    │   │   │   │   ├───task_id=initialize_client1_hdfs_bronze_zone
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   ├───task_id=initialize_client1_iceberg_namespaces
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   └───task_id=validate_trino_query_service
    │   │   │   │           attempt=1.log
    │   │   │   │
    │   │   │   ├───run_id=manual__2026-07-18T121121.172248+0000
    │   │   │   │   ├───task_id=initialize_client1_hdfs_bronze_zone
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   ├───task_id=initialize_client1_iceberg_namespaces
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   └───task_id=validate_trino_query_service
    │   │   │   │           attempt=1.log
    │   │   │   │
    │   │   │   ├───run_id=manual__2026-07-20T131412.350823+0000
    │   │   │   │   ├───task_id=initialize_client1_hdfs_bronze_zone
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   ├───task_id=initialize_client1_iceberg_namespaces
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   └───task_id=validate_trino_query_service
    │   │   │   │           attempt=1.log
    │   │   │   │
    │   │   │   ├───run_id=manual__2026-07-20T190759.254686+0000
    │   │   │   │   ├───task_id=initialize_client1_hdfs_bronze_zone
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   ├───task_id=initialize_client1_iceberg_namespaces
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   └───task_id=validate_trino_query_service
    │   │   │   │           attempt=1.log
    │   │   │   │
    │   │   │   ├───run_id=manual__2026-07-20T222919.255702+0000
    │   │   │   │   ├───task_id=initialize_client1_hdfs_bronze_zone
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   ├───task_id=initialize_client1_iceberg_namespaces
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   └───task_id=validate_trino_query_service
    │   │   │   │           attempt=1.log
    │   │   │   │
    │   │   │   ├───run_id=manual__2026-07-21T105217.044462+0000
    │   │   │   │   ├───task_id=initialize_client1_hdfs_bronze_zone
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   ├───task_id=initialize_client1_iceberg_namespaces
    │   │   │   │   │       attempt=1.log
    │   │   │   │   │
    │   │   │   │   └───task_id=validate_trino_query_service
    │   │   │   │           attempt=1.log
    │   │   │   │
    │   │   │   └───run_id=manual__2026-07-27T193349.176100+0000
    │   │   │       ├───task_id=initialize_client1_hdfs_bronze_zone
    │   │   │       │       attempt=1.log
    │   │   │       │
    │   │   │       ├───task_id=initialize_client1_iceberg_namespaces
    │   │   │       │       attempt=1.log
    │   │   │       │
    │   │   │       └───task_id=validate_trino_query_service
    │   │   │               attempt=1.log
    │   │   │
    │   │   └───dag_processor
    │   │       ├───2026-07-15
    │   │       │   └───dags-folder
    │   │       │       └───client_1
    │   │       │               client_1_dag_common.py.log
    │   │       │               client_1_dbt_spark_transformations_dag.py.log
    │   │       │               client_1_kafka_hdfs_spark_raw_dag.py.log
    │   │       │               client_1_lakehouse_readiness_dag.py.log
    │   │       │               client_1_lakehouse_setup_dag.py.log
    │   │       │               customerdna_client1_dag_common.py.log
    │   │       │               customerdna_client1_dw_setup_dag.py.log
    │   │       │               customerdna_client1_lakehouse_readiness_dag.py.log
    │   │       │               customerdna_client1_raw_load_dag.py.log
    │   │       │               customerdna_client1_transformation_quality_dag.py.log
    │   │       │               __init__.py.log
    │   │       │
    │   │       ├───2026-07-16
    │   │       │   └───dags-folder
    │   │       │       └───client_1
    │   │       │               client_1_dag_common.py.log
    │   │       │               client_1_dbt_spark_transformations_dag.py.log
    │   │       │               client_1_kafka_hdfs_spark_raw_dag.py.log
    │   │       │               client_1_lakehouse_readiness_dag.py.log
    │   │       │               client_1_lakehouse_setup_dag.py.log
    │   │       │               __init__.py.log
    │   │       │
    │   │       ├───2026-07-17
    │   │       │   └───dags-folder
    │   │       │       └───client_1
    │   │       │               client_1_dag_common.py.log
    │   │       │               client_1_dbt_spark_transformations_dag.py.log
    │   │       │               client_1_kafka_hdfs_spark_raw_dag.py.log
    │   │       │               client_1_lakehouse_readiness_dag.py.log
    │   │       │               client_1_lakehouse_setup_dag.py.log
    │   │       │               __init__.py.log
    │   │       │
    │   │       ├───2026-07-18
    │   │       │   └───dags-folder
    │   │       │       └───client_1
    │   │       │               client_1_dag_common.py.log
    │   │       │               client_1_dbt_spark_transformations_dag.py.log
    │   │       │               client_1_kafka_hdfs_spark_raw_dag.py.log
    │   │       │               client_1_lakehouse_readiness_dag.py.log
    │   │       │               client_1_lakehouse_setup_dag.py.log
    │   │       │               __init__.py.log
    │   │       │
    │   │       ├───2026-07-19
    │   │       │   └───dags-folder
    │   │       │       └───client_1
    │   │       │               client_1_dag_common.py.log
    │   │       │               client_1_dbt_spark_transformations_dag.py.log
    │   │       │               client_1_kafka_hdfs_spark_raw_dag.py.log
    │   │       │               client_1_lakehouse_readiness_dag.py.log
    │   │       │               client_1_lakehouse_setup_dag.py.log
    │   │       │               __init__.py.log
    │   │       │
    │   │       ├───2026-07-20
    │   │       │   └───dags-folder
    │   │       │       └───client_1
    │   │       │               client_1_dag_common.py.log
    │   │       │               client_1_dbt_spark_transformations_dag.py.log
    │   │       │               client_1_kafka_hdfs_spark_raw_dag.py.log
    │   │       │               client_1_lakehouse_readiness_dag.py.log
    │   │       │               client_1_lakehouse_setup_dag.py.log
    │   │       │               __init__.py.log
    │   │       │
    │   │       ├───2026-07-21
    │   │       │   └───dags-folder
    │   │       │       └───client_1
    │   │       │               client_1_dag_common.py.log
    │   │       │               client_1_dbt_spark_transformations_dag.py.log
    │   │       │               client_1_kafka_hdfs_spark_raw_dag.py.log
    │   │       │               client_1_lakehouse_readiness_dag.py.log
    │   │       │               client_1_lakehouse_setup_dag.py.log
    │   │       │               __init__.py.log
    │   │       │
    │   │       ├───2026-07-22
    │   │       │   └───dags-folder
    │   │       │       └───client_1
    │   │       │               client_1_dag_common.py.log
    │   │       │               client_1_dbt_spark_transformations_dag.py.log
    │   │       │               client_1_kafka_hdfs_spark_raw_dag.py.log
    │   │       │               client_1_lakehouse_readiness_dag.py.log
    │   │       │               client_1_lakehouse_setup_dag.py.log
    │   │       │               __init__.py.log
    │   │       │
    │   │       ├───2026-07-23
    │   │       │   └───dags-folder
    │   │       │       └───client_1
    │   │       │               client_1_dag_common.py.log
    │   │       │               client_1_dbt_spark_transformations_dag.py.log
    │   │       │               client_1_kafka_hdfs_spark_raw_dag.py.log
    │   │       │               client_1_lakehouse_readiness_dag.py.log
    │   │       │               client_1_lakehouse_setup_dag.py.log
    │   │       │               __init__.py.log
    │   │       │
    │   │       ├───2026-07-24
    │   │       │   └───dags-folder
    │   │       │       └───client_1
    │   │       │               client_1_dag_common.py.log
    │   │       │               client_1_dbt_spark_transformations_dag.py.log
    │   │       │               client_1_kafka_hdfs_spark_raw_dag.py.log
    │   │       │               client_1_lakehouse_readiness_dag.py.log
    │   │       │               client_1_lakehouse_setup_dag.py.log
    │   │       │               __init__.py.log
    │   │       │
    │   │       ├───2026-07-25
    │   │       │   └───dags-folder
    │   │       │       └───client_1
    │   │       │               client_1_dag_common.py.log
    │   │       │               client_1_dbt_spark_transformations_dag.py.log
    │   │       │               client_1_kafka_hdfs_spark_raw_dag.py.log
    │   │       │               client_1_lakehouse_readiness_dag.py.log
    │   │       │               client_1_lakehouse_setup_dag.py.log
    │   │       │               __init__.py.log
    │   │       │
    │   │       ├───2026-07-26
    │   │       │   └───dags-folder
    │   │       │       └───client_1
    │   │       │               client_1_dag_common.py.log
    │   │       │               client_1_dbt_spark_transformations_dag.py.log
    │   │       │               client_1_kafka_hdfs_spark_raw_dag.py.log
    │   │       │               client_1_lakehouse_readiness_dag.py.log
    │   │       │               client_1_lakehouse_setup_dag.py.log
    │   │       │               __init__.py.log
    │   │       │
    │   │       ├───2026-07-27
    │   │       │   └───dags-folder
    │   │       │       └───client_1
    │   │       │               client_1_dag_common.py.log
    │   │       │               client_1_dbt_spark_transformations_dag.py.log
    │   │       │               client_1_kafka_hdfs_spark_raw_dag.py.log
    │   │       │               client_1_lakehouse_readiness_dag.py.log
    │   │       │               client_1_lakehouse_setup_dag.py.log
    │   │       │               __init__.py.log
    │   │       │
    │   │       ├───2026-07-28
    │   │       │   └───dags-folder
    │   │       │       └───client_1
    │   │       │               client_1_dag_common.py.log
    │   │       │               client_1_dbt_spark_transformations_dag.py.log
    │   │       │               client_1_kafka_hdfs_spark_raw_dag.py.log
    │   │       │               client_1_lakehouse_readiness_dag.py.log
    │   │       │               client_1_lakehouse_setup_dag.py.log
    │   │       │               __init__.py.log
    │   │       │
    │   │       ├───2026-07-29
    │   │       │   └───dags-folder
    │   │       │       └───client_1
    │   │       │               client_1_dag_common.py.log
    │   │       │               client_1_dbt_spark_transformations_dag.py.log
    │   │       │               client_1_kafka_hdfs_spark_raw_dag.py.log
    │   │       │               client_1_lakehouse_readiness_dag.py.log
    │   │       │               client_1_lakehouse_setup_dag.py.log
    │   │       │               __init__.py.log
    │   │       │
    │   │       └───latest
    │   └───plugins
    ├───catalog
    │   └───hive
    │       │   .env.example
    │       │   docker-compose.yml
    │       │   README.md
    │       │
    │       ├───client_1
    │       │   ├───external_tables
    │       │   ├───iceberg_catalog
    │       │   └───namespaces
    │       ├───config
    │       │       core-site.xml
    │       │       hdfs-site.xml
    │       │       hive-site.xml
    │       │
    │       └───metastore
    │               Dockerfile
    │
    ├───lake
    │   └───hdfs
    │       │   .env
    │       │   .env.example
    │       │   docker-compose.yml
    │       │   README.md
    │       │
    │       ├───client_1
    │       │   │   .gitignore
    │       │   │   initialize_client1_bronze_zone.py
    │       │   │   list_client1_bronze_objects.py
    │       │   │   reset_client1_bronze.py
    │       │   │
    │       │   ├───bronze
    │       │   │   ├───ecommerce_customer_churn
    │       │   │   ├───marketing_campaign
    │       │   │   ├───online_retail
    │       │   │   ├───retailrocket_category_tree
    │       │   │   ├───retailrocket_events
    │       │   │   └───retailrocket_item_properties
    │       │   ├───common
    │       │   │   │   hdfs_bronze_config.py
    │       │   │   │   hdfs_bronze_utils.py
    │       │   │   │
    │       │   │   └───__pycache__
    │       │   │           hdfs_bronze_config.cpython-311.pyc
    │       │   │           hdfs_bronze_utils.cpython-311.pyc
    │       │   │
    │       │   ├───gold
    │       │   └───silver
    │       └───config
    ├───monitoring
    │   │   README.md
    │   │
    │   ├───exporters
    │   │   │   pipeline_metrics_exporter.py
    │   │   │
    │   │   ├───hdfs_metrics
    │   │   ├───pipeline_metrics
    │   │   ├───spark_metrics
    │   │   └───__pycache__
    │   │           pipeline_metrics_exporter.cpython-313.pyc
    │   │
    │   ├───grafana
    │   │   │   .env.example
    │   │   │   docker-compose.yml
    │   │   │
    │   │   ├───dashboards
    │   │   │       customerdna_infrastructure.dashboard.json
    │   │   │       customerdna_pipeline_health.dashboard.json
    │   │   │       customerdna_postgres.dashboard.json
    │   │   │       README.md
    │   │   │
    │   │   └───provisioning
    │   │       ├───dashboards
    │   │       │       customerdna.yml
    │   │       │
    │   │       └───datasources
    │   │               prometheus.yml
    │   │
    │   ├───prometheus
    │   │       .env
    │   │       .env.example
    │   │       docker-compose.yml
    │   │       prometheus.yml
    │   │       README.md
    │   │
    │   ├───shared
    │   │   │   pipeline_metrics.py
    │   │   │   __init__.py
    │   │   │
    │   │   └───__pycache__
    │   │           pipeline_metrics.cpython-311.pyc
    │   │           pipeline_metrics.cpython-313.pyc
    │   │           __init__.cpython-311.pyc
    │   │
    │   ├───state
    │   │       airflow_pipeline_state.json
    │   │       gx_state.json
    │   │       raw_load_state.json
    │   │
    │   └───tools
    │       │   export_runtime_logs.py
    │       │
    │       └───__pycache__
    │               export_runtime_logs.cpython-313.pyc
    │
    ├───processing
    │   └───spark
    │       │   .env
    │       │   .env.example
    │       │   docker-compose.yml
    │       │   Dockerfile
    │       │   README.md
    │       │
    │       ├───client_1
    │       │   ├───bronze_to_silver
    │       │   ├───common
    │       │   │   │   spark_raw_loader_submitter.py
    │       │   │   │
    │       │   │   └───__pycache__
    │       │   │           spark_raw_loader_submitter.cpython-311.pyc
    │       │   │           spark_raw_loader_submitter.cpython-313.pyc
    │       │   │
    │       │   ├───quality_helpers
    │       │   ├───schemas
    │       │   ├───silver_to_gold
    │       │   └───sql
    │       ├───conf
    │       │       .gitkeep
    │       │
    │       ├───config
    │       │       hive-site.xml
    │       │       spark-defaults.conf
    │       │
    │       └───jobs
    │           │   .gitkeep
    │           │
    │           └───client_1
    │               │   load_hdfs_bronze_to_iceberg.py
    │               │
    │               └───__pycache__
    │                       load_hdfs_bronze_to_iceberg.cpython-313.pyc
    │
    ├───quality
    │   └───great_expectations
    │       ├───client_1
    │       │   │   bootstrap_gx.py
    │       │   │   run_gx_validations.py
    │       │   │
    │       │   ├───artifacts
    │       │   │       raw_lakehouse_quality_checkpoint_latest.json
    │       │   │
    │       │   ├───checkpoints
    │       │   │       checkpoint_manifest.json
    │       │   │
    │       │   ├───data_docs
    │       │   │       index.html
    │       │   │
    │       │   ├───expectations
    │       │   │   ├───bronze
    │       │   │   ├───gold
    │       │   │   └───silver
    │       │   ├───gx_project
    │       │   │   └───gx
    │       │   │       │   .gitignore
    │       │   │       │   great_expectations.yml
    │       │   │       │
    │       │   │       ├───checkpoints
    │       │   │       ├───expectations
    │       │   │       │       .ge_store_backend_id
    │       │   │       │       raw_lakehouse_metrics_suite.json
    │       │   │       │
    │       │   │       ├───plugins
    │       │   │       │   └───custom_data_docs
    │       │   │       │       ├───renderers
    │       │   │       │       ├───styles
    │       │   │       │       │       data_docs_custom_styles.css
    │       │   │       │       │
    │       │   │       │       └───views
    │       │   │       ├───uncommitted
    │       │   │       │   │   config_variables.yml
    │       │   │       │   │
    │       │   │       │   ├───data_docs
    │       │   │       │   │   └───local_site
    │       │   │       │   │       │   index.html
    │       │   │       │   │       │
    │       │   │       │   │       ├───expectations
    │       │   │       │   │       │       raw_lakehouse_metrics_suite.html
    │       │   │       │   │       │
    │       │   │       │   │       ├───static
    │       │   │       │   │       │   ├───fonts
    │       │   │       │   │       │   │   └───HKGrotesk
    │       │   │       │   │       │   │           HKGrotesk-Bold.otf
    │       │   │       │   │       │   │           HKGrotesk-BoldItalic.otf
    │       │   │       │   │       │   │           HKGrotesk-Italic.otf
    │       │   │       │   │       │   │           HKGrotesk-Light.otf
    │       │   │       │   │       │   │           HKGrotesk-LightItalic.otf
    │       │   │       │   │       │   │           HKGrotesk-Medium.otf
    │       │   │       │   │       │   │           HKGrotesk-MediumItalic.otf
    │       │   │       │   │       │   │           HKGrotesk-Regular.otf
    │       │   │       │   │       │   │           HKGrotesk-SemiBold.otf
    │       │   │       │   │       │   │           HKGrotesk-SemiBoldItalic.otf
    │       │   │       │   │       │   │
    │       │   │       │   │       │   ├───images
    │       │   │       │   │       │   │       favicon.ico
    │       │   │       │   │       │   │       glossary_scroller.gif
    │       │   │       │   │       │   │       iterative-dev-loop.png
    │       │   │       │   │       │   │       logo-long-vector.svg
    │       │   │       │   │       │   │       logo-long.png
    │       │   │       │   │       │   │       short-logo-vector.svg
    │       │   │       │   │       │   │       short-logo.png
    │       │   │       │   │       │   │       validation_failed_unexpected_values.gif
    │       │   │       │   │       │   │
    │       │   │       │   │       │   └───styles
    │       │   │       │   │       │           data_docs_custom_styles_template.css
    │       │   │       │   │       │           data_docs_default_styles.css
    │       │   │       │   │       │
    │       │   │       │   │       └───validations
    │       │   │       │   │           └───raw_lakehouse_metrics_suite
    │       │   │       │   │               └───__none__
    │       │   │       │   │                   ├───20260727T204503.230850Z
    │       │   │       │   │                   │       client1_quality_metrics-raw_lakehouse_metrics.html
    │       │   │       │   │                   │
    │       │   │       │   │                   ├───20260727T204504.627428Z
    │       │   │       │   │                   │       client1_quality_metrics-raw_lakehouse_metrics.html
    │       │   │       │   │                   │
    │       │   │       │   │                   ├───20260727T204505.957677Z
    │       │   │       │   │                   │       client1_quality_metrics-raw_lakehouse_metrics.html
    │       │   │       │   │                   │
    │       │   │       │   │                   ├───20260727T204507.275804Z
    │       │   │       │   │                   │       client1_quality_metrics-raw_lakehouse_metrics.html
    │       │   │       │   │                   │
    │       │   │       │   │                   ├───20260727T204508.594090Z
    │       │   │       │   │                   │       client1_quality_metrics-raw_lakehouse_metrics.html
    │       │   │       │   │                   │
    │       │   │       │   │                   └───20260727T204509.925100Z
    │       │   │       │   │                           client1_quality_metrics-raw_lakehouse_metrics.html
    │       │   │       │   │
    │       │   │       │   └───validations
    │       │   │       │       │   .ge_store_backend_id
    │       │   │       │       │
    │       │   │       │       └───raw_lakehouse_metrics_suite
    │       │   │       │           └───__none__
    │       │   │       │               ├───20260727T204503.230850Z
    │       │   │       │               │       client1_quality_metrics-raw_lakehouse_metrics.json
    │       │   │       │               │
    │       │   │       │               ├───20260727T204504.627428Z
    │       │   │       │               │       client1_quality_metrics-raw_lakehouse_metrics.json
    │       │   │       │               │
    │       │   │       │               ├───20260727T204505.957677Z
    │       │   │       │               │       client1_quality_metrics-raw_lakehouse_metrics.json
    │       │   │       │               │
    │       │   │       │               ├───20260727T204507.275804Z
    │       │   │       │               │       client1_quality_metrics-raw_lakehouse_metrics.json
    │       │   │       │               │
    │       │   │       │               ├───20260727T204508.594090Z
    │       │   │       │               │       client1_quality_metrics-raw_lakehouse_metrics.json
    │       │   │       │               │
    │       │   │       │               └───20260727T204509.925100Z
    │       │   │       │                       client1_quality_metrics-raw_lakehouse_metrics.json
    │       │   │       │
    │       │   │       └───validation_definitions
    │       │   │               raw_lakehouse_quality_checkpoint__ecommerce_customer_churn.json
    │       │   │               raw_lakehouse_quality_checkpoint__marketing_campaign.json
    │       │   │               raw_lakehouse_quality_checkpoint__online_retail.json
    │       │   │               raw_lakehouse_quality_checkpoint__retailrocket_category_tree.json
    │       │   │               raw_lakehouse_quality_checkpoint__retailrocket_events.json
    │       │   │               raw_lakehouse_quality_checkpoint__retailrocket_item_properties.json
    │       │   │
    │       │   └───__pycache__
    │       │           bootstrap_gx.cpython-313.pyc
    │       │           run_gx_validations.cpython-313.pyc
    │       │
    │       └───config
    ├───query
    │   └───trino
    │       │   .env.example
    │       │   docker-compose.yml
    │       │   README.md
    │       │
    │       ├───client_1
    │       │   │   initialize_lakehouse_namespace.py
    │       │   │
    │       │   ├───common
    │       │   │   │   trino_rest.py
    │       │   │   │
    │       │   │   └───__pycache__
    │       │   │           trino_rest.cpython-311.pyc
    │       │   │
    │       │   └───__pycache__
    │       │           initialize_lakehouse_namespace.cpython-313.pyc
    │       │
    │       └───etc
    │           │   config.properties
    │           │   core-site.xml
    │           │   hdfs-site.xml
    │           │   jvm.config
    │           │   node.properties
    │           │
    │           └───catalog
    │                   lakehouse.properties
    │
    ├───streaming
    │   └───kafka
    │       │   .gitignore
    │       │   docker-compose.yml
    │       │   requirements.txt
    │       │
    │       ├───client_1
    │       │   │   reset_client1_kafka.py
    │       │   │   run_client1_kafka_raw_pipeline.py
    │       │   │   __init__.py
    │       │   │
    │       │   ├───bronze_writers
    │       │   ├───common
    │       │   │   │   bronze_consumer.py
    │       │   │   │   dataset_producer.py
    │       │   │   │   kafka_config.py
    │       │   │   │   load_event_consumer.py
    │       │   │   │   producer_utils.py
    │       │   │   │   source_row_iterators.py
    │       │   │   │   __init__.py
    │       │   │   │
    │       │   │   └───__pycache__
    │       │   │           bronze_consumer.cpython-311.pyc
    │       │   │           dataset_producer.cpython-311.pyc
    │       │   │           kafka_config.cpython-311.pyc
    │       │   │           load_event_consumer.cpython-311.pyc
    │       │   │           load_event_consumer.cpython-313.pyc
    │       │   │           producer_utils.cpython-311.pyc
    │       │   │           source_row_iterators.cpython-311.pyc
    │       │   │
    │       │   ├───ecommerce_customer_churn
    │       │   │       consume.py
    │       │   │       load.py
    │       │   │       produce.py
    │       │   │       __init__.py
    │       │   │
    │       │   ├───marketing_campaign
    │       │   │       consume.py
    │       │   │       load.py
    │       │   │       produce.py
    │       │   │       __init__.py
    │       │   │
    │       │   ├───online_retail
    │       │   │       consume.py
    │       │   │       load.py
    │       │   │       produce.py
    │       │   │       __init__.py
    │       │   │
    │       │   ├───retailrocket_category_tree
    │       │   │       consume.py
    │       │   │       load.py
    │       │   │       produce.py
    │       │   │       __init__.py
    │       │   │
    │       │   ├───retailrocket_events
    │       │   │       consume.py
    │       │   │       load.py
    │       │   │       produce.py
    │       │   │       __init__.py
    │       │   │
    │       │   ├───retailrocket_item_properties
    │       │   │       consume.py
    │       │   │       load.py
    │       │   │       produce.py
    │       │   │       __init__.py
    │       │   │
    │       │   ├───topic_admin
    │       │   └───__pycache__
    │       │           run_client1_kafka_raw_pipeline.cpython-313.pyc
    │       │
    │       ├───config
    │       ├───docker
    │       └───logs
    │           └───client_1
    └───transformation
        │   README.md
        │
        └───dbt_spark
            └───client_1
                │   .env.example
                │   .user.yml
                │   dbt_project.yml
                │   profiles.yml
                │   README.md
                │   requirements.txt
                │
                ├───dbt_packages
                ├───logs
                │       dbt.log
                │
                ├───macros
                │       lakehouse_schema_management.sql
                │       safe_casts.sql
                │
                ├───models
                │   ├───analytics
                │   │       analytics_customer_overview.sql
                │   │       analytics_retailrocket_engagement.sql
                │   │       analytics_sales_performance.sql
                │   │       schema.yml
                │   │
                │   ├───intermediate
                │   │       int_customer_commercial_360.sql
                │   │       int_customer_profile.sql
                │   │       int_online_retail_customer_sales.sql
                │   │       int_retailrocket_visitor_activity.sql
                │   │       schema.yml
                │   │
                │   └───staging
                │           schema.yml
                │           sources.yml
                │           stg_ecommerce_customer_churn.sql
                │           stg_marketing_campaign.sql
                │           stg_online_retail.sql
                │           stg_retailrocket_category_tree.sql
                │           stg_retailrocket_events.sql
                │           stg_retailrocket_item_properties.sql
                │
                └───target
                    │   graph.gpickle
                    │   graph_summary.json
                    │   manifest.json
                    │   partial_parse.msgpack
                    │   run_results.json
                    │   semantic_manifest.json
                    │
                    ├───compiled
                    │   └───customerdna_client1_lakehouse
                    │       └───models
                    │           ├───analytics
                    │           │   │   analytics_customer_overview.sql
                    │           │   │   analytics_retailrocket_engagement.sql
                    │           │   │   analytics_sales_performance.sql
                    │           │   │
                    │           │   └───schema.yml
                    │           │           not_null_analytics_customer_overview_customer_id.sql
                    │           │           unique_analytics_customer_overview_customer_id.sql
                    │           │
                    │           ├───intermediate
                    │           │   │   int_customer_commercial_360.sql
                    │           │   │   int_customer_profile.sql
                    │           │   │   int_online_retail_customer_sales.sql
                    │           │   │   int_retailrocket_visitor_activity.sql
                    │           │   │
                    │           │   └───schema.yml
                    │           │           not_null_int_customer_commercial_360_customer_id.sql
                    │           │           not_null_int_customer_profile_customer_id.sql
                    │           │           not_null_int_online_retail_customer_sales_customer_id.sql
                    │           │           not_null_int_retailrocket_visitor_activity_visitor_id.sql
                    │           │           unique_int_customer_commercial_360_customer_id.sql
                    │           │           unique_int_customer_profile_customer_id.sql
                    │           │           unique_int_online_retail_customer_sales_customer_id.sql
                    │           │           unique_int_retailrocket_visitor_activity_visitor_id.sql
                    │           │
                    │           └───staging
                    │               │   stg_ecommerce_customer_churn.sql
                    │               │   stg_marketing_campaign.sql
                    │               │   stg_online_retail.sql
                    │               │   stg_retailrocket_category_tree.sql
                    │               │   stg_retailrocket_events.sql
                    │               │   stg_retailrocket_item_properties.sql
                    │               │
                    │               └───schema.yml
                    │                       not_null_stg_ecommerce_customer_churn_customer_id.sql
                    │                       not_null_stg_marketing_campaign_customer_id.sql
                    │                       not_null_stg_retailrocket_category_tree_category_id.sql
                    │                       unique_stg_ecommerce_customer_churn_customer_id.sql
                    │                       unique_stg_marketing_campaign_customer_id.sql
                    │
                    └───run
                        └───customerdna_client1_lakehouse
                            └───models
                                ├───analytics
                                │   │   analytics_customer_overview.sql
                                │   │   analytics_retailrocket_engagement.sql
                                │   │   analytics_sales_performance.sql
                                │   │
                                │   └───schema.yml
                                │           not_null_analytics_customer_overview_customer_id.sql
                                │           unique_analytics_customer_overview_customer_id.sql
                                │
                                ├───intermediate
                                │   │   int_customer_commercial_360.sql
                                │   │   int_customer_profile.sql
                                │   │   int_online_retail_customer_sales.sql
                                │   │   int_retailrocket_visitor_activity.sql
                                │   │
                                │   └───schema.yml
                                │           not_null_int_customer_commercial_360_customer_id.sql
                                │           not_null_int_customer_profile_customer_id.sql
                                │           not_null_int_online_retail_customer_sales_customer_id.sql
                                │           not_null_int_retailrocket_visitor_activity_visitor_id.sql
                                │           unique_int_customer_commercial_360_customer_id.sql
                                │           unique_int_customer_profile_customer_id.sql
                                │           unique_int_online_retail_customer_sales_customer_id.sql
                                │           unique_int_retailrocket_visitor_activity_visitor_id.sql
                                │
                                └───staging
                                    │   stg_ecommerce_customer_churn.sql
                                    │   stg_marketing_campaign.sql
                                    │   stg_online_retail.sql
                                    │   stg_retailrocket_category_tree.sql
                                    │   stg_retailrocket_events.sql
                                    │   stg_retailrocket_item_properties.sql
                                    │
                                    └───schema.yml
                                            not_null_stg_ecommerce_customer_churn_customer_id.sql
                                            not_null_stg_marketing_campaign_customer_id.sql
                                            not_null_stg_retailrocket_category_tree_category_id.sql
                                            unique_stg_ecommerce_customer_churn_customer_id.sql
                                            unique_stg_marketing_campaign_customer_id.sql
