FROM bde2020/hadoop-namenode:2.0.0-hadoop3.2.1-java8

USER root

ENV DEBIAN_FRONTEND=noninteractive

RUN sed -i 's|http://deb.debian.org/debian|http://archive.debian.org/debian|g' /etc/apt/sources.list \
    && sed -i 's|http://security.debian.org/debian-security|http://archive.debian.org/debian-security|g' /etc/apt/sources.list \
    && sed -i '/stretch-updates/d' /etc/apt/sources.list \
    && printf 'Acquire::Check-Valid-Until \"false\";\nAcquire::AllowInsecureRepositories \"true\";\n' > /etc/apt/apt.conf.d/99archive \
    && apt-get update -o Acquire::Check-Valid-Until=false -o Acquire::AllowInsecureRepositories=true \
    && apt-get install -y --no-install-recommends krb5-user libgssapi-krb5-2 libsasl2-modules-gssapi-mit \
    && HDFS_BIN="$(find / -type f -path '*/bin/hdfs' | head -n 1)" \
    && test -n "${HDFS_BIN}" \
    && HADOOP_BIN_DIR="$(dirname "${HDFS_BIN}")" \
    && HADOOP_HOME_DIR="$(dirname "${HADOOP_BIN_DIR}")" \
    && ln -sf "${HDFS_BIN}" /usr/local/bin/hdfs \
    && if [ -x "${HADOOP_BIN_DIR}/hadoop" ]; then ln -sf "${HADOOP_BIN_DIR}/hadoop" /usr/local/bin/hadoop; fi \
    && printf 'export HADOOP_HOME=%s\nexport PATH=%s:/usr/local/bin:$PATH\n' "${HADOOP_HOME_DIR}" "${HADOOP_BIN_DIR}" > /etc/profile.d/customerdna-hadoop.sh \
    && rm -rf /var/lib/apt/lists/*

CMD ["/bin/bash", "-lc", "while true; do sleep 3600; done"]
