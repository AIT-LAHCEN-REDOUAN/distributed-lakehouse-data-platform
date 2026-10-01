ARG SPARK_BASE_IMAGE=spark:4.1.2-python3
FROM ${SPARK_BASE_IMAGE}

ARG ICEBERG_VERSION=1.11.0
ARG POSTGRES_JDBC_VERSION=42.7.4

USER root

ADD https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-4.1_2.13/${ICEBERG_VERSION}/iceberg-spark-runtime-4.1_2.13-${ICEBERG_VERSION}.jar /opt/spark/jars/
ADD https://repo1.maven.org/maven2/org/postgresql/postgresql/${POSTGRES_JDBC_VERSION}/postgresql-${POSTGRES_JDBC_VERSION}.jar /opt/spark/jars/

RUN mkdir -p /opt/spark/custom-conf /opt/spark/logs /opt/spark/work-dir/.ivy2/cache \
    && chmod 644 /opt/spark/jars/iceberg-spark-runtime-4.1_2.13-${ICEBERG_VERSION}.jar \
    && chmod 644 /opt/spark/jars/postgresql-${POSTGRES_JDBC_VERSION}.jar \
    && chown spark:spark /opt/spark/jars/iceberg-spark-runtime-4.1_2.13-${ICEBERG_VERSION}.jar \
    && chown spark:spark /opt/spark/jars/postgresql-${POSTGRES_JDBC_VERSION}.jar

USER spark
