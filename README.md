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
_profiles = Path(ser_client_api.__file__).parent / "hl7v2" / "gipcad" / "profiles" / "v000_compiled"

# Load institution-specific prescription JSON
prescription_json = json.loads(Path("prescription.json").read_text())

# Parse into a shared domain model
parser = ParserFactory(SEQOIA).create()
parser.validate(prescription_json)
composition = parser.parse(prescription_json)

# Generate HL7v2 ORU_R01 message
generator = HL7v2Generator(_profiles / "oru_r01_lab36", SEQOIA)
hl7_message = generator.generate(composition)
```

Replace `SEQOIA` with `AURAGEN` or `PERIGENOMED` for other institutions. See [Supported institutions](#supported-institutions) and [Usage](#usage) for more.
