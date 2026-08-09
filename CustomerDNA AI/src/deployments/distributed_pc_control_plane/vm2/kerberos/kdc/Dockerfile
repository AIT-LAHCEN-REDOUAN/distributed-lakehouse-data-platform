FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y krb5-kdc krb5-admin-server krb5-user \
    && rm -rf /var/lib/apt/lists/*

COPY entrypoint.sh /opt/customerdna/kerberos/entrypoint.sh

RUN chmod +x /opt/customerdna/kerberos/entrypoint.sh

ENTRYPOINT ["/opt/customerdna/kerberos/entrypoint.sh"]
