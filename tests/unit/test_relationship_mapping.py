"""Unit tests for SeqOIA pedigree relationship mapping."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from ser_client_api.hl7v2.seqoia.parser import SeqoiaParser
from ser_client_api.vocabularies.seqoia import (
    translate_relationship,
    translate_relationship_by_regex,
)

_REGEX_EXAMPLES = json.loads(
    (Path(__file__).parent.parent / "fixtures" / "relationship_regex_examples.json").read_text(encoding="utf-8")
)


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
            "catname": "Cat",
            "catkey": "p1",
            "name": "Test",
            "key": "p1-sp60",
            "rcp_id": "rcp1",
            "rcp_nom": "RCP",
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
    @pytest.mark.parametrize("libelle,expected_code", _REGEX_EXAMPLES)
    def test_regex_resolution(self, libelle, expected_code):
        assert translate_relationship_by_regex(libelle) == expected_code

    def test_grand_pere_does_not_match_fth(self):
        """'grand-père' compound must NOT resolve to FTH via the generic père pattern."""
        assert translate_relationship_by_regex("oncle très éloigné côté grand-père maternel") is None

    def test_grand_mere_does_not_match_mth(self):
        """'grand-mère' compound must NOT resolve to MTH via the generic mère pattern."""
        assert translate_relationship_by_regex("grand-mère de Sophie") is None

    def test_no_match_returns_none(self):
        """A string matching no pattern returns None."""
        assert translate_relationship_by_regex("parenté inconnue XYZ") is None

    def test_empty_string_returns_none(self):
        """Empty input returns None without raising."""
        assert translate_relationship_by_regex("") is None

    def test_sentinel_blocks_unrecognised_multi_hop(self):
        """Two kinship words chained by de/du with no explicit pattern -> None (-> EXT)."""
        assert translate_relationship_by_regex("frère de l'oncle de Paul") is None


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
        data = _make_prescription("autre", "FRÈRE")
        result = SeqoiaParser().parse(data)
        nok = result.next_of_kin[0]
        assert nok.relationship_code == "BRO"

    def test_pere_sets_fth_and_pere_display(self):
        data = _make_prescription("père", "Père")
        result = SeqoiaParser().parse(data)
        nok = result.next_of_kin[0]
        assert nok.relationship_code == "FTH"
        assert nok.relationship_display == "père"

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

    def test_set_id_is_sequential(self, minimal_prescription_json):
        """set_id is assigned sequentially starting at 1."""
        result = SeqoiaParser().parse(minimal_prescription_json)
        set_ids = [nok.set_id for nok in result.next_of_kin]
        assert set_ids == [1, 2]


# A libellé that fails Level 1 (not in ConceptMap) and Level 2 (no regex match) — triggers Level 3
_L3_LIBELLE = "lien familial non précisé par Jean-Pierre Moreau"


class TestParserLevel3Similarity:
    """Parser integration with Level 3 ML similarity — no ML deps, using mocks."""

    def test_level3_fires_when_levels_1_and_2_fail(self):
        """When Level 1 and Level 2 both fail, Level 3 is invoked and its code is used."""
        data = _make_prescription("autre", _L3_LIBELLE)
        with (
            patch("ser_client_api.hl7v2.seqoia.parser._SIMILARITY_AVAILABLE", True),
            patch("ser_client_api.hl7v2.seqoia.parser._translate_by_similarity", return_value="COUSN") as mock_sim,
        ):
            result = SeqoiaParser().parse(data)
            nok = result.next_of_kin[0]

        mock_sim.assert_called_once_with(_L3_LIBELLE)
        assert nok.relationship_code == "COUSN"
        assert nok.relationship_is_exact is False

    def test_level3_none_falls_back_to_ext(self):
        """When Level 3 returns None (below threshold), code falls back to EXT."""
        data = _make_prescription("autre", _L3_LIBELLE)
        with (
            patch("ser_client_api.hl7v2.seqoia.parser._SIMILARITY_AVAILABLE", True),
            patch("ser_client_api.hl7v2.seqoia.parser._translate_by_similarity", return_value=None),
        ):
            result = SeqoiaParser().parse(data)
            nok = result.next_of_kin[0]

        assert nok.relationship_code == "EXT"
        assert nok.relationship_is_exact is False

    def test_level3_skipped_when_unavailable(self):
        """When ML deps are absent (_SIMILARITY_AVAILABLE=False), Level 3 is never called."""
        data = _make_prescription("autre", _L3_LIBELLE)
        with (
            patch("ser_client_api.hl7v2.seqoia.parser._SIMILARITY_AVAILABLE", False),
            patch("ser_client_api.hl7v2.seqoia.parser._translate_by_similarity") as mock_sim,
        ):
            result = SeqoiaParser().parse(data)
            nok = result.next_of_kin[0]

        mock_sim.assert_not_called()
        assert nok.relationship_code == "EXT"

    def test_level3_preserves_original_display(self):
        """relationship_display is always the original lien_name, not the ML output."""
        data = _make_prescription("autre", _L3_LIBELLE)
        with (
            patch("ser_client_api.hl7v2.seqoia.parser._SIMILARITY_AVAILABLE", True),
            patch("ser_client_api.hl7v2.seqoia.parser._translate_by_similarity", return_value="COUSN"),
        ):
            result = SeqoiaParser().parse(data)
            nok = result.next_of_kin[0]

        assert nok.relationship_display == _L3_LIBELLE

    def test_level1_match_skips_level3(self):
        """When Level 1 matches, Level 3 is never invoked."""
        data = _make_prescription("autre", "frère")
        with (
            patch("ser_client_api.hl7v2.seqoia.parser._SIMILARITY_AVAILABLE", True),
            patch("ser_client_api.hl7v2.seqoia.parser._translate_by_similarity") as mock_sim,
        ):
            result = SeqoiaParser().parse(data)
            nok = result.next_of_kin[0]

        mock_sim.assert_not_called()
        assert nok.relationship_code == "BRO"
        assert nok.relationship_is_exact is True

    def test_level2_match_skips_level3(self):
        """When Level 2 (regex) matches, Level 3 is never invoked."""
        data = _make_prescription("autre", "frère de Lucas")
        with (
            patch("ser_client_api.hl7v2.seqoia.parser._SIMILARITY_AVAILABLE", True),
            patch("ser_client_api.hl7v2.seqoia.parser._translate_by_similarity") as mock_sim,
        ):
            result = SeqoiaParser().parse(data)
            nok = result.next_of_kin[0]

        mock_sim.assert_not_called()
        assert nok.relationship_code == "BRO"
