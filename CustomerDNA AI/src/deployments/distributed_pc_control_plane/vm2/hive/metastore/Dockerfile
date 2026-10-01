ARG HIVE_METASTORE_VERSION=3.1.3
FROM apache/hive:${HIVE_METASTORE_VERSION}

ARG POSTGRES_JDBC_VERSION=42.7.4

USER root
ADD https://jdbc.postgresql.org/download/postgresql-${POSTGRES_JDBC_VERSION}.jar /opt/hive/lib/postgresql.jar
COPY start-metastore.sh /opt/customerdna/start-metastore.sh
RUN chmod +x /opt/customerdna/start-metastore.sh
RUN chown hive:hive /opt/hive/lib/postgresql.jar
USER hive
ENTRYPOINT ["/opt/customerdna/start-metastore.sh"]
