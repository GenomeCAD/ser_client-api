# Current base: cgr.dev/chainguard/python:latest-dev (Chainguard hardened image)
# - runs as nonroot; PATH fix required (ENV PATH below)
# - latest-dev ships Python 3.14; no pinned 3.12 variant exists - tag is mutable
# - 818 MB vs 299 MB for python:3.12-slim
#
# To revert to the slim base:
#   FROM python:3.12-slim
#   (remove ENV PATH; add --allow-root to CMD)
FROM cgr.dev/chainguard/python:latest-dev
ENV PATH="/home/nonroot/.local/bin:$PATH"

RUN pip install --no-cache-dir jupyterlab

COPY ser_client-ftps/ ./ser_client-ftps/
RUN pip install --no-cache-dir ./ser_client-ftps

COPY ser-client-api/ ./ser-client-api/
RUN pip install --no-cache-dir ./ser-client-api

EXPOSE 8888

ENTRYPOINT []
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser"]
