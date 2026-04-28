#!/usr/bin/env bash
# Generates self-signed dev certs for the ser-demo environment.
# Cert names match the convention expected by ser_demo_notebook.ipynb.
#
# Output (client-side, mounted into the Jupyter container at /certs):
#   ca-cert.pem      CA certificate
#   client-cert.pem  client certificate (O=CHU-TEST -> mapped to FTP username by ProFTPD)
#   client-key.pem   client private key
#
# Output (server-side, mounted into the ProFTPD container):
#   server.crt       server certificate (CN=proftpd -> required by ser_client-ftps check_hostname)
#   server.key       server private key
#
# Requirements: openssl 3.x

set -euo pipefail
cd "$(dirname "$0")"

rm -f ca.key ca-cert.pem server.key server.csr server.crt client.key client.csr client-cert.pem client-key.pem

openssl genrsa -out ca.key 4096
openssl req -x509 -new -nodes -key ca.key -sha256 -days 3650 \
    -subj "/CN=ser-demo-CA/O=GenomeCAD" \
    -addext "basicConstraints=critical,CA:TRUE" \
    -addext "keyUsage=critical,keyCertSign,cRLSign" \
    -addext "subjectKeyIdentifier=hash" \
    -out ca-cert.pem

openssl genrsa -out server.key 2048
openssl req -new -key server.key -subj "/CN=proftpd/O=GenomeCAD" -out server.csr
openssl x509 -req -in server.csr -CA ca-cert.pem -CAkey ca.key \
    -CAcreateserial -out server.crt -days 3650 -sha256 \
    -extfile <(printf "subjectAltName=DNS:proftpd,DNS:localhost\nextendedKeyUsage=serverAuth\nbasicConstraints=CA:FALSE")

openssl genrsa -out client-key.pem 2048
openssl req -new -key client-key.pem -subj "/CN=ser-demo-client/O=CHU-TEST" -out client.csr
openssl x509 -req -in client.csr -CA ca-cert.pem -CAkey ca.key \
    -CAcreateserial -out client-cert.pem -days 3650 -sha256 \
    -extfile <(printf "extendedKeyUsage=clientAuth\nbasicConstraints=CA:FALSE")

rm -f ca.key ca-cert.pem.srl server.csr client.csr

echo "Certs generated:"
ls -lh ca-cert.pem server.crt server.key client-cert.pem client-key.pem
