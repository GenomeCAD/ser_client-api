"""
GIPCAD / CAD output-side vocabulary loaders.

Exposes two lookup functions backed by static FHIR ValueSet JSON files:

    v3_display(code)   – HL7v3 RoleCode display label (e.g. "FTH" → "father")
    pfmg_display(code) – PFMG Filière display label   (e.g. "F-20" → "Aplasies …")

Unknown codes return None; callers are responsible for deciding whether to raise
or fall back to the bare code.
"""

import importlib.resources
import json
from typing import Optional

_v3_index: Optional[dict[str, str]] = None
_pfmg_index: Optional[dict[str, str]] = None


def _load_expansion(filename: str) -> dict[str, str]:
    """Return {code: display} from a ValueSet JSON expansion."""
    f = importlib.resources.files("ser_client_api.vocabularies.gipcad") / filename
    data = json.loads(f.read_text(encoding="utf-8"))
    return {entry["code"]: entry["display"] for entry in data.get("expansion", {}).get("contains", [])}


def v3_display(code: str) -> Optional[str]:
    """Return the HL7v3 RoleCode display label for *code*, or None if unknown."""
    global _v3_index
    if _v3_index is None:
        _v3_index = _load_expansion("v3-FamilyMember.json")
    return _v3_index.get(code)


def pfmg_display(code: str) -> Optional[str]:
    """Return the PFMG Filière display label for *code*, or None if unknown."""
    global _pfmg_index
    if _pfmg_index is None:
        _pfmg_index = _load_expansion("PFMG-Filiere.json")
    return _pfmg_index.get(code)
