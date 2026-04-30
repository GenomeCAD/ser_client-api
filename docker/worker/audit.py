import logging
import os
import uuid
from datetime import datetime, timezone

from kombu import Connection, Exchange, Producer, Queue

logger = logging.getLogger(__name__)

_BROKER_URL = os.environ.get("BROKER_URL", "amqp://user:password@rabbitmq-client:5672//")
_EXCHANGE = Exchange("ser.audit", type="fanout", durable=True)
_QUEUE = Queue("ser_audit", exchange=_EXCHANGE, durable=True)

_DEVICE = {
    "resourceType": "Device",
    "id": "device_ser_client_api",
    "identifier": [{"system": "urn:ietf:rfc:3986", "value": "ser_client_api"}],
    "type": {"text": "SER client API worker"},
}


def emit(report_id: str, subtype: str, severity: str, outcome_code: str, outcome_display: str) -> None:
    event = {
        "resourceType": "AuditEvent",
        "id": str(uuid.uuid4()),
        "meta": {
            "security": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-Confidentiality",
                    "code": "R",
                    "display": "Restricted",
                }
            ]
        },
        "type": {
            "coding": [
                {
                    "system": "http://www.perigenomed.fr/ontology/operations",
                    "code": "ser_client_api",
                    "display": "SER client API",
                }
            ]
        },
        "subtype": {
            "coding": [
                {
                    "system": "http://www.perigenomed.fr/ontology/operations/ser_client_api",
                    "code": subtype,
                    "display": subtype,
                }
            ]
        },
        "action": "C",
        "recorded": datetime.now(timezone.utc).isoformat(),
        "severity": severity,
        "outcome": {
            "code": {
                "system": "https://www.iana.org/assignments/http-status-codes",
                "code": outcome_code,
                "display": outcome_display,
            }
        },
        "agent": [{"who": {"reference": "#device_ser_client_api"}, "requestor": True}],
        "source": {"observer": {"reference": "#device_ser_client_api"}},
        "entity": [
            {
                "what": {
                    "identifier": {
                        "type": {
                            "coding": [
                                {
                                    "system": "http://www.perigenomed.fr/identifier",
                                    "code": "prescription",
                                }
                            ],
                            "text": "Identifiant prescription SER",
                        },
                        "value": report_id,
                    }
                },
                "role": "report",
            }
        ],
        "contained": [_DEVICE],
    }
    try:
        with Connection(_BROKER_URL) as conn:
            with Producer(conn) as producer:
                producer.publish(
                    event,
                    exchange=_EXCHANGE,
                    serializer="json",
                    declare=[_EXCHANGE, _QUEUE],
                )
    except Exception:
        logger.warning("Failed to publish audit event for %s", report_id)
