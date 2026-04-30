FROM python:3.12-slim
WORKDIR /app
ENV PYTHONPATH=/app

RUN pip install --no-cache-dir "celery[redis]"

COPY ser_client-ftps/ ./ser_client-ftps/
RUN pip install --no-cache-dir ./ser_client-ftps

COPY ser-client-api/ ./ser-client-api/
RUN pip install --no-cache-dir ./ser-client-api

COPY ser-client-api/docker/worker/*.py ./

CMD ["celery", "-A", "tasks", "worker", "--loglevel=info", "--concurrency=2", "-E"]
