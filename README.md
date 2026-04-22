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
