"""Unit tests for SeqOIA pedigree relationship mapping (issue #33)."""

import pytest

from ser_client_api.vocabularies.seqoia import translate_relationship, translate_relationship_by_regex
from ser_client_api.hl7v2.seqoia.parser import SeqoiaParser

class TestTranslateRelationship:
    def test_known_lowercase_entry(self):
        """Exact lowercase match returns the correct HL7v3 code."""
        assert translate_relationship("frère") == "BRO"

    def test_case_insensitive_lookup(self):
        """Lookup is case-insensitive: 'Frère' and 'FRERE' both resolve to BRO."""
        assert translate_relationship("Frère") == "BRO"
        assert translate_relationship("FRERE") == "BRO"

    def test_known_entry_with_accent_variant(self):
        """Entries with typographic variants (é/è) from real data are covered."""
        assert translate_relationship("soeur") == "SIS"
        assert translate_relationship("Sœur") == "SIS"

    def test_unknown_libelle_returns_none(self):
        """A libellé not in the table returns None (caller decides the fallback)."""
        assert translate_relationship("xyz_not_a_relation") is None

    def test_empty_string_returns_none(self):
        """Empty input returns None without raising."""
        assert translate_relationship("") is None

def _make_prescription(lien_key, lien_name):
    """Return a minimal prescription JSON with one related person."""
    return {
        "_id": "test-id",
        "preindication": {
            "catname": "Cat", "catkey": "p1",
            "name": "Test", "key": "p1-sp60",
            "rcp_id": "rcp1", "rcp_nom": "RCP",
        },
        "patients": [
            {
                "patient": {
                    "id": {"type": "IPP", "value": "IPP-001"},
                    "date_naissance": "1990-01-01",
                    "sexe": "F",
                    "nom": "TEST",
                    "nom_naissance": "TEST",
                    "prenom": "PATIENT",
                },
                "lien": {"key": "patient", "name": "Patient"},
                "is_data_reusable_for_research": False,
                "date_prelevement": 1741651200000,
                "id_anon": "IDMAIN",
            },
            {
                "patient": {
                    "id": {"type": "IPP", "value": "IPP-002"},
                    "date_naissance": "1965-06-15",
                    "sexe": "M",
                    "nom": "AUTRE",
                    "nom_naissance": "AUTRE",
                    "prenom": "PERSON",
                },
                "lien": {"key": lien_key, "name": lien_name},
                "is_data_reusable_for_research": False,
                "date_prelevement": 1741651200000,
                "id_anon": "IDNOK",
            },
        ],
        "prescripteur": "123",
        "membreRCP": "456",
        "analysis_info": {"analysis_ID": "9999", "date_fin_analyse": "01042026"},
        "date_creation": 1741606397865,
        "date_cloture": 1745498322775,
        "resultats": [],
    }


class TestTranslateRelationshipByRegex:
    def test_pii_pattern_brother(self):
        """'Frère de Lucas' (PII) matches BRO via regex."""
        assert translate_relationship_by_regex("Frère de Lucas") == "BRO"

    def test_pii_pattern_paternal_uncle(self):
        """'frère du père de Lucas' matches PUNCLE, not the generic BRO."""
        assert translate_relationship_by_regex("frère du père de Lucas") == "PUNCLE"

    def test_ordering_puncle_before_uncle(self):
        """'Frère du père Xavier' matches UNCLE (not PUNCLE, not BRO)."""
        assert translate_relationship_by_regex("Frère du père Xavier") == "UNCLE"

    def test_pii_pattern_mother(self):
        """'mère de Sophie' matches MTH via regex."""
        assert translate_relationship_by_regex("mère de Sophie") == "MTH"

    def test_no_match_returns_none(self):
        """A string matching no pattern returns None."""
        assert translate_relationship_by_regex("parenté inconnue XYZ") is None

    def test_empty_string_returns_none(self):
        """Empty input returns None without raising."""
        assert translate_relationship_by_regex("") is None


class TestParserAutreLogic:
    def test_autre_with_matched_libelle_uses_table_code(self):
        """When lien.key='autre' and lien.name matches the table, use the table code."""
        data = _make_prescription("autre", "frère")
        result = SeqoiaParser().parse(data)
        nok = result.next_of_kin[0]
        assert nok.relationship_code == "BRO"
        assert nok.relationship_display == "frère"  # original French text preserved

    def test_autre_with_unmatched_libelle_uses_ext(self):
        """When lien.key='autre' and lien.name is not in the table, fall back to EXT."""
        data = _make_prescription("autre", "parenté inconnue")
        result = SeqoiaParser().parse(data)
        nok = result.next_of_kin[0]
        assert nok.relationship_code == "EXT"
        assert nok.relationship_display == "parenté inconnue"

    def test_autre_case_insensitive_match(self):
        """Matching lien.name against the table is case-insensitive."""
        data = _make_prescription("autre", "FRÈRE")
        result = SeqoiaParser().parse(data)
        nok = result.next_of_kin[0]
        assert nok.relationship_code == "BRO"

    def test_pere_sets_fth_and_father_display(self):
        """lien.key='père' → FTH with 'father' display, regardless of lien.name."""
        data = _make_prescription("père", "Père")
        result = SeqoiaParser().parse(data)
        nok = result.next_of_kin[0]
        assert nok.relationship_code == "FTH"
        assert nok.relationship_display == "father"

    def test_patient_key_is_skipped(self):
        """lien.key='patient' entries are skipped (not added to next_of_kin)."""
        data = _make_prescription("patient", "Patient")
        result = SeqoiaParser().parse(data)
        assert result.next_of_kin is None

    def test_autre_with_pii_pattern_uses_regex_code(self):
        """When lien.key='autre' and lien.name contains PII matching a regex, use that code."""
        data = _make_prescription("autre", "frère de Lucas")
        result = SeqoiaParser().parse(data)
        nok = result.next_of_kin[0]
        assert nok.relationship_code == "BRO"
        assert nok.relationship_display == "frère de Lucas"  # original text preserved (may contain PII)

    def test_set_id_is_sequential(self):
        """set_id is assigned sequentially starting at 1."""
        from tests.conftest import MINIMAL_PRESCRIPTION_JSON
        result = SeqoiaParser().parse(MINIMAL_PRESCRIPTION_JSON)
        set_ids = [nok.set_id for nok in result.next_of_kin]
        assert set_ids == [1, 2]

