# ser_client-api

Core genomics domain models for CAD forwarding connectors.

Provides the shared `ParsedReportData` model and related dataclasses used by
laboratory-specific forwarding connectors (e.g. `seqoia-fwd`, `auragen-fwd`).

## Usage

```python
from ser_client_api.hl7v2 import ParsedReportData, PatientData
```

## License

MIT
