import importlib.resources
import json
import logging
from pathlib import Path

from celery_app import app

from ser_client_api.demo.helpers import get_composition, populate_temporary_presc_dir
from ser_client_api.hl7v2 import SEQOIA, HL7v2Generator, generate_sidecars

logger = logging.getLogger(__name__)

_profile_path = str(importlib.resources.files("ser_client_api.hl7v2.gipcad.profiles.v000_compiled") / "oru_r01_lab36")
_generator = HL7v2Generator(profile_path=_profile_path, institution=SEQOIA)


@app.task(bind=True, max_retries=3, default_retry_delay=10)
def process_prescription(self, json_path: str, results_dir: str) -> dict:
    json_file = Path(json_path)
    results = Path(results_dir)

    try:
        json_data = json.loads(json_file.read_text(encoding="utf-8"))
        composition = get_composition(SEQOIA, json_data)

        presc_dir = results / composition.report_id
        if (presc_dir / f"{composition.report_id}.hl7").exists():
            logger.info("Skipping %s - already processed", composition.report_id)
            return {"report_id": composition.report_id, "status": "skipped"}

        populate_temporary_presc_dir(presc_dir, composition.report_id, composition)

        _generator.generate_and_seal(composition, presc_dir, composition.report_id)

        n_sidecars = generate_sidecars(presc_dir)

        logger.info("Processed %s: %d sidecar(s) written", composition.report_id, n_sidecars)
        return {
            "report_id": composition.report_id,
            "sidecars_written": n_sidecars,
            "presc_dir": str(presc_dir),
        }
    except Exception as exc:
        raise self.retry(exc=exc)
