"""
Polls INBOX_DIR for new .json prescription files and dispatches a Celery task
for each one. Uses send_task() so the full ser_client_api stack is not loaded
in this process.

Note: the 'seen' set is in-memory only. On restart, all files in the inbox are
redispatched. Acceptable for demo use.
"""

import logging
import os
import time
from pathlib import Path

from celery_app import app

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

INBOX_DIR = Path(os.environ.get("INBOX_DIR", "/data/seqoia"))
RESULTS_DIR = Path(os.environ.get("RESULTS_DIR", "/data/seqoia"))
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "5"))

INBOX_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

logger.info("Polling %s every %ds", INBOX_DIR, POLL_INTERVAL)

seen: set[str] = set()

while True:
    for json_file in sorted(INBOX_DIR.glob("*.json")):
        if json_file.name not in seen:
            seen.add(json_file.name)
            app.send_task(
                "tasks.process_prescription",
                args=[str(json_file), str(RESULTS_DIR)],
            )
            logger.info("Dispatched: %s", json_file.name)
    time.sleep(POLL_INTERVAL)
