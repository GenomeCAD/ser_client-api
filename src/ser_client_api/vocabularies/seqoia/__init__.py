"""
SeqOIA vocabulary mappings - CAD standardization layer.

Domain covered:

    FILIERE - maps preindication.key (e.g. "p1-sp49") to a PFMG Filière code and full display label,
    used to populate PV1.14 of the ORU_R01 CAD message.

Unknown keys are not rejected - a warning is logged and the caller receives None,
allowing the generator to leave PV1.14 empty rather than fail.
"""

import importlib.resources
import json
import logging
from typing import Optional

from ser_client_api.vocabularies.gipcad import pfmg_display

logger = logging.getLogger(__name__)

_concept_map: Optional[dict] = None


def _get_concept_map() -> dict:
    global _concept_map
    if _concept_map is None:
        map_file = (
            importlib.resources.files("ser_client_api.vocabularies.seqoia")
            / "seqoia-to-pfmg-filiere.json"
        )
        _concept_map = json.loads(map_file.read_text(encoding="utf-8"))
    return _concept_map


def _build_filiere_index() -> dict[str, tuple[str, str]]:
    index: dict[str, tuple[str, str]] = {}
    for group in _get_concept_map().get("group", []):
        for element in group.get("element", []):
            seqoia_code = element.get("code")
            targets = element.get("target", [])
            if seqoia_code and targets:
                pfmg_code = targets[0]["code"]
                display = pfmg_display(pfmg_code) or pfmg_code
                index[seqoia_code] = (pfmg_code, display)
    return index


FILIERE: dict[str, tuple[str, str]] = _build_filiere_index()


def translate_filiere(seqoia_key: str) -> Optional[tuple[str, str]]:
    """Return (PFMG filière code, full display label) for a SeqOIA preindication key."""
    result = FILIERE.get(seqoia_key)
    if result is None:
        logger.warning(
            "SeqOIA preindication key %r has no PFMG filière mapping - PV1.14 will be empty",
            seqoia_key,
        )
    return result
