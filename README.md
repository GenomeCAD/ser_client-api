# ser-client-api

[![Unit Tests](https://github.com/GenomeCAD/ser-client-api/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/GenomeCAD/ser-client-api/actions/workflows/unit-tests.yml)
[![ML Integration Tests](https://github.com/GenomeCAD/ser-client-api/actions/workflows/ml-integration-tests.yml/badge.svg)](https://github.com/GenomeCAD/ser-client-api/actions/workflows/ml-integration-tests.yml)

`ser-client-api` is a Python library for converting clinical genomics reports from French sequencing networks (SeqOIA, AuraGen, PériGénoMed) into HL7v2 ORU_R01 messages for the GIP-CAD national data collector. It parses institution-specific JSON reports, generates conformant HL7v2 messages, and processes the ACK responses GIP-CAD returns.

## Installation

Requires Python 3.12 or later.

```bash
pip install ser-client-api
```

If you need ML-based pedigree relationship resolution for free-text inputs, install the optional ML extras:

```bash
pip install "ser-client-api[ml]"
```

See [Optional ML features](#optional-ml-features) for details.

## Quick start

Parse a prescription JSON into a domain model and generate an HL7v2 ORU_R01 message:

```python
import json
from pathlib import Path

import ser_client_api
from ser_client_api import ParserFactory
from ser_client_api.hl7v2 import SEQOIA, HL7v2Generator

# GIP-CAD HL7v2 profile bundled with the package
profiles_dir = Path(ser_client_api.__file__).parent / "hl7v2" / "gipcad" / "profiles" / "v000_compiled"

# Load institution-specific prescription JSON
prescription_json = json.loads(Path("prescription.json").read_text())

# Parse into a shared domain model
parser = ParserFactory(SEQOIA).create()
parser.validate(prescription_json)
composition = parser.parse(prescription_json)

# Generate HL7v2 ORU_R01 message
generator = HL7v2Generator(profiles_dir / "oru_r01_lab36", SEQOIA)
hl7_message = generator.generate(composition)
```

Replace `SEQOIA` with `AURAGEN` or `PERIGENOMED` for other institutions. See [Supported institutions](#supported-institutions) and [Usage](#usage) for more.

## Supported institutions

```python
from ser_client_api.hl7v2 import SEQOIA, AURAGEN, PERIGENOMED
```

| Constant | Facility | Lab FINESS | Parser |
|---|---|---|---|
| `SEQOIA` | GCS SeqOIA | 1750063265 | ✓ implemented |
| `AURAGEN` | GCS AuraGen - Hospices Civils de Lyon | 1690045059 | not yet implemented |
| `PERIGENOMED` | CHU Dijon Bourgogne | 1210987558 | not yet implemented |

Each constant is an `InstitutionConfig` instance holding the identifiers that populate HL7v2 message headers and the parser reference used by `ParserFactory`.

## Usage

### Parsing local data

```python
from ser_client_api import ParserFactory
from ser_client_api.hl7v2 import SEQOIA

parser = ParserFactory(SEQOIA).create()
parser.validate(prescription_json)  # raises ValueError on invalid input
composition = parser.parse(prescription_json)
```

`CompositionData` carries all extracted data: `report_id`, `patient`, `next_of_kin`, `preindication`, `rcp`, `person`, `analysis`, `timing`, `consent`, and `results`.

### Generating HL7v2

```python
from ser_client_api.hl7v2 import generate_sidecars

# Returns the HL7v2 message as a string
hl7_message = generator.generate(composition)

# Production pattern: pre-compute SHA-256 sidecars, then write the sealed HL7v2 file
generate_sidecars(presc_dir)
hl7_file = generator.generate_and_seal(composition, presc_dir, prescription_name)
```

### Processing ACK responses

```python
from pathlib import Path

import ser_client_api
from ser_client_api import analyze_ack_message, determine_transfer_status, parse_hl7_message_robust

profiles_dir = Path(ser_client_api.__file__).parent / "hl7v2" / "gipcad" / "profiles" / "v000_compiled"

ack_msg = parse_hl7_message_robust(ack_content, str(profiles_dir / "ack_r01_ack"))
analysis = analyze_ack_message(ack_msg)
status = determine_transfer_status(analysis)
# 0 = accepted, 2 = failed
```

`analysis.critical_errors`, `analysis.warnings`, and `analysis.infos` contain the detail messages from the ACK.

### Pedigree relationship mapping (SeqOIA)

The SeqOIA parser resolves free-text relationship labels to HL7v3 RoleCode values automatically through a three-level cascade:

1. **Exact lookup** against the SeqOIA-to-HL7v3 ConceptMap
2. **Regex matching** against known free-text patterns
3. **ML similarity** - PII removal followed by cosine similarity against the GIP-CAD pedigree referential (requires `[ml]` extras)

Levels 1 and 2 cover the vast majority of real-world inputs. Level 3 activates automatically when the first two fail and `[ml]` is installed. Without `[ml]`, unresolved labels fall back to `EXT`.

## Optional ML features

The `[ml]` extras enable Level 3 pedigree relationship resolution in the SeqOIA parser, as described in [Pedigree relationship mapping](#pedigree-relationship-mapping-seqoia).

On first use, two models are downloaded from HuggingFace and cached locally (~600 MB total): `nvidia/gliner-pii` for PII detection and `paraphrase-multilingual-MiniLM-L12-v2` for sentence embeddings. In environments without internet access, pre-populate the HuggingFace cache (`~/.cache/huggingface`) before deployment.

If `[ml]` is not installed, the SeqOIA parser silently falls back to `EXT` for unresolved labels - no exception is raised.

## Docker demo environment

`docker/` contains a self-contained Compose stack for running and demonstrating the prescription processing pipeline locally - no GIP-CAD infrastructure required. It supports two independent demo flows:

**Automated processing flow** - drop a JSON prescription into a watched directory; the Celery worker picks it up, generates the HL7v2 message and SHA-256 sidecars, and publishes an audit event. This flow demonstrates automated prescription handling.

**Interactive FTPS flow** - a JupyterLab notebook (`docs/ser_demo_notebook.ipynb`, served by the `jupyter` dev service) walks through the full client-side exchange step by step: parse, generate HL7v2, transfer files to the mock FTPS server via `ser_client-ftps`, and pull back and parse the ACK response. This flow demonstrates the complete transfer handshake with `ser_server-ftps`.

The two flows are independent: the worker does not perform FTPS transfers, and the notebook does not go through Celery.

### Architecture

| Service | Flow | Role |
|---|---|---|
| `rabbitmq-client` | automated | RabbitMQ broker for Celery tasks and audit events (management UI on port 15673) |
| `redis` | automated | Celery result backend |
| `poller` | automated | Watches `docker/seqoia/` for new `.json` files and dispatches a Celery task for each |
| `worker` | automated | Celery worker - parses the prescription, generates HL7v2 + SHA-256 sidecars, publishes an audit event |
| `flower` | automated | Celery task monitor (port 5555) |
| `proftpd` | FTPS | Mock FTPS server (port 9990) |
| `appserver` | FTPS | ser_server-ftps application server - processes received HL7v2 and writes ACK responses |
| `rabbitmq` | FTPS | Dedicated RabbitMQ instance for ser_server-ftps |
| `jupyter` _(dev profile)_ | FTPS | JupyterLab serving the interactive FTPS demo notebook (port 8888) |

### Prerequisites

- Docker with the Compose plugin
- Generated dev TLS certificates (one-time):

```bash
bash docker/certs/generate-certs.sh
```

### Starting the stack

```bash
docker compose -f docker/docker-compose.yml build
docker compose -f docker/docker-compose.yml up
```

To also start JupyterLab for the interactive FTPS demo:

```bash
docker compose -f docker/docker-compose.yml --profile dev up
```

Open http://localhost:8888 (token: `ser-demo`) and run `docs/ser_demo_notebook.ipynb`.

### Processing a prescription

Copy any SeqOIA prescription JSON into the inbox directory:

```bash
cp your-prescription.json docker/seqoia/
```

The poller picks it up within 5 seconds. The worker writes results to `docker/seqoia/<report_id>/`:

```
docker/seqoia/<report_id>/
    <report_id>.hl7          # sealed HL7v2 ORU_R01 message
    <report_id>/             # per-individual subdirectories
        <file>.sha256        # SHA-256 sidecar for each genomic file
```

Processing is idempotent: if `<report_id>.hl7` already exists the task is skipped.

To scale workers horizontally:

```bash
docker compose -f docker/docker-compose.yml up --scale worker=3
```

### Admin UIs

| URL | Service | Credentials |
|---|---|---|
| http://localhost:15673 | RabbitMQ management | `user` / `password` |
| http://localhost:5555 | Flower (Celery monitor) | none |
| http://localhost:8888 | JupyterLab (dev profile) | token: `ser-demo` |

### Audit events

The worker publishes a FHIR R4 `AuditEvent` to the `ser.audit` fanout exchange on `rabbitmq-client` at every processing outcome:

| HTTP code | Meaning |
|---|---|
| `201 Created` | Prescription processed successfully |
| `208 Already Reported` | Skipped - output already exists |
| `500 Internal Server Error` | Failed after all retries exhausted |

Events accumulate in the durable `ser_audit` queue and are visible in the RabbitMQ management UI. A database consumer (`audit-db`) is not yet wired - see the commented-out `audit-db` service in `docker-compose.yml`.

### FTPS configuration

Jupyter and the FTPS-related services read their connection parameters from `docker/.env`:

```
FTPS_HOST=proftpd
FTPS_PORT=990
FTPS_USER=CHU-TEST
FTPS_PASSWORD=ftppassword
REMOTE_PATH=remote/seqoia
CERT_DIR=/certs
```

Edit this file to point at a real FTPS endpoint without touching `docker-compose.yml`.

## Development

### Setup

```bash
pip install ".[dev]"      # core deps + pytest
pip install ".[dev,ml]"   # also install ML extras for integration tests
```

### Running tests

Unit tests have no ML dependencies and run in a few seconds:

```bash
pytest tests/unit
```

Integration tests require `[ml]` and download models on first run (~600 MB):

```bash
pytest tests/integration
```

### Linting

The project uses [ruff](https://docs.astral.sh/ruff/) for linting and formatting, enforced via a pre-commit hook.

```bash
pip install pre-commit
pre-commit install        # installs the hook - runs ruff automatically on each commit
```

To run manually:

```bash
ruff check .
ruff format .
```

## License

MIT License - see [LICENSE](LICENSE) for details.
