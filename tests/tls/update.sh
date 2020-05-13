#!/bin/bash

# source:
# https://github.com/scoriacorp/docker-tls-memcached
# courtesy Moisés Guimarães

# extracting client credentials
docker run --rm scoriacorp/tls_memcached cat /opt/certs/key/client.key > client.key
docker run --rm scoriacorp/tls_memcached cat /opt/certs/crt/client.crt > client.crt

# extracting client CA certificate
docker run --rm scoriacorp/tls_memcached cat /opt/certs/crt/client-ca-root.crt > client-ca-root.crt

# extracting server credentials
docker run --rm scoriacorp/tls_memcached cat /opt/certs/key/server-rsa2048.key > server.key
docker run --rm scoriacorp/tls_memcached cat /opt/certs/chain/server-rsa2048.pem > server_chain.pem

# extracting CA certificate
docker run --rm scoriacorp/tls_memcached cat /opt/certs/crt/ca-root.crt > ca-root.crt
