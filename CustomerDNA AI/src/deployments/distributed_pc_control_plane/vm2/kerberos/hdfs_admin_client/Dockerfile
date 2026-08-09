FROM bde2020/hadoop-namenode:2.0.0-hadoop3.2.1-java8

USER root

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y krb5-user \
    && rm -rf /var/lib/apt/lists/*

CMD ["/bin/bash", "-lc", "while true; do sleep 3600; done"]
