# =============================================================================
# Layer 1 - OS + Python runtime
# =============================================================================
# Current base: python:3.12-slim (official, Debian Bookworm)
#
# Hardened alternative (see issue #29, Florent's comment):
#   FROM cgr.dev/chainguard/python:latest-dev
#   Ref: https://hub.docker.com/hardened-images/catalog/dhi/python
#
# Evaluation result (tested 2026-04-27):
#   [ok] Build succeeds - all packages install cleanly
#   [ok] ser_client_api + ser_client_ftps import and run (Python 3.14 compatible)
#   [ok] OpenSSL 3.6.2 / TLS 1.3 - FTPS egress works (not restricted by the image)
#   [ok] Jupyter starts without --allow-root (image runs as nonroot, which is better)
#   [!]  PATH: scripts install to /home/nonroot/.local/bin - add ENV PATH below
#   [!]  Size: 818 MB vs 299 MB for python:3.12-slim + same layers (2.7x larger)
#   [!]  No pinned 3.12 variant: cgr.dev/chainguard/python:3.12-dev does not exist;
#        latest-dev currently ships Python 3.14 and will change with upstream releases
#
# To use the hardened base, replace the FROM line and add the PATH fix:
#   FROM cgr.dev/chainguard/python:latest-dev
#   ENV PATH="/home/nonroot/.local/bin:$PATH"
#   (and remove --allow-root from CMD)
FROM python:3.12-slim

RUN pip install --no-cache-dir jupyterlab

COPY ser_client-ftps/ ./ser_client-ftps/
RUN pip install --no-cache-dir ./ser_client-ftps

COPY ser-client-api/ ./ser-client-api/
RUN pip install --no-cache-dir ./ser-client-api

EXPOSE 8888

CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
