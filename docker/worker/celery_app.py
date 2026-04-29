import os

from celery import Celery

BROKER_URL = os.environ.get("BROKER_URL", "amqp://user:password@rabbitmq-client:5672//")
BACKEND_URL = os.environ.get("BACKEND_URL", "redis://redis:6379/0")

app = Celery("ser_worker", broker=BROKER_URL, backend=BACKEND_URL)
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
