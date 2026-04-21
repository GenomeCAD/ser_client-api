"""
SeqOIA vocabulary mappings - CAD standardization layer.

Domain covered:

    FILIERE - maps preindication.key (e.g. "p1-sp49") to a PFMG Filière code and full display
    label, used to populate PV1.14 of the ORU_R01 CAD message.

    RELATIONSHIP — maps pedigree libellés (lien.name free text) to HL7v3 RoleCode, used to
    populate NK1-3 of the ORU_R01 CAD message.  Lookup is case-insensitive.

Unknown keys/libellés are not rejected - a warning is logged and the caller receives None,
allowing the generator to apply a safe fallback rather than fail.
"""

import importlib.resources
import json
import logging
import re
from typing import Optional

from ser_client_api.vocabularies.gipcad import pfmg_display

logger = logging.getLogger(__name__)

_concept_map: Optional[dict] = None


def _get_concept_map() -> dict:
    global _concept_map
    if _concept_map is None:
        map_file = importlib.resources.files("ser_client_api.vocabularies.seqoia") / "seqoia-to-pfmg-filiere.json"
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


_relationship_index: Optional[dict[str, str]] = None


def _get_relationship_index() -> dict[str, str]:
    global _relationship_index
    if _relationship_index is None:
        f = importlib.resources.files("ser_client_api.vocabularies.seqoia") / "seqoia-to-v3-relationship.json"
        data = json.loads(f.read_text(encoding="utf-8"))
        index: dict[str, str] = {}
        for group in data.get("group", []):
            for element in group.get("element", []):
                code = element.get("code")
                targets = element.get("target", [])
                if code and targets:
                    index[code.lower()] = targets[0]["code"]
        _relationship_index = index
    return _relationship_index


def translate_relationship(libelle: str) -> Optional[str]:
    """Return HL7v3 RoleCode for a SeqOIA pedigree libellé (case-insensitive).

    :param libelle: Free-text pedigree label from lien.name field.
    :returns: HL7v3 v3-RoleCode string (e.g. "BRO", "SIS"), or None if not found.
    """
    if not libelle:
        return None
    return _get_relationship_index().get(libelle.strip().lower())


_pattern_rules: Optional[list] = None


def _get_pattern_rules() -> list:
    global _pattern_rules
    if _pattern_rules is None:
        f = importlib.resources.files("ser_client_api.vocabularies.seqoia") / "seqoia-relationship-patterns.json"
        data = json.loads(f.read_text(encoding="utf-8"))
        _pattern_rules = [(re.compile(row["pattern"]), row["code"]) for row in data]
    return _pattern_rules


def translate_relationship_by_regex(libelle: str) -> Optional[str]:
    """Return HL7v3 RoleCode by matching libellé against ordered regex patterns.

    Patterns are tested in order; the first match wins.  Designed for free-text
    entries that embed PII (e.g. "frère de Lucas") and therefore cannot be exact
    matched via the ConceptMap index.

    :param libelle: Free-text pedigree label from lien.name field.
    :returns: HL7v3 v3-RoleCode string, or None if no pattern matches.
    """
    if not libelle:
        return None
    for pattern, code in _get_pattern_rules():
        if pattern.search(libelle):
            return code
    return None
