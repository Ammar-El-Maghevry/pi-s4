#!/bin/sh
set -e

CERT_DIR=/etc/nginx/certs
mkdir -p "$CERT_DIR"

SAN_IP="${TLS_SAN_IP:-127.0.0.1}"

if [ ! -f "$CERT_DIR/selfsigned.crt" ]; then
  echo "Generating self-signed TLS certificate for $SAN_IP ..."
  openssl req -x509 -nodes -newkey rsa:2048 \
    -keyout "$CERT_DIR/selfsigned.key" \
    -out "$CERT_DIR/selfsigned.crt" \
    -days 825 \
    -subj "/CN=${SAN_IP}" \
    -addext "subjectAltName=IP:${SAN_IP},DNS:localhost,IP:127.0.0.1"
fi

exec nginx -g "daemon off;"
