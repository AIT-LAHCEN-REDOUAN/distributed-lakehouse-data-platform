FROM bde2020/hadoop-namenode:2.0.0-hadoop3.2.1-java8

USER root

ENV DEBIAN_FRONTEND=noninteractive

RUN sed -i 's|http://deb.debian.org/debian|http://archive.debian.org/debian|g' /etc/apt/sources.list \
    && sed -i 's|http://security.debian.org/debian-security|http://archive.debian.org/debian-security|g' /etc/apt/sources.list \
    && sed -i '/stretch-updates/d' /etc/apt/sources.list \
    && printf 'Acquire::Check-Valid-Until \"false\";\nAcquire::AllowInsecureRepositories \"true\";\n' > /etc/apt/apt.conf.d/99archive \
    && apt-get update -o Acquire::Check-Valid-Until=false -o Acquire::AllowInsecureRepositories=true \
    && apt-get install -y --no-install-recommends krb5-user \
    && rm -rf /var/lib/apt/lists/*

CMD ["/bin/bash", "-lc", "while true; do sleep 3600; done"]
