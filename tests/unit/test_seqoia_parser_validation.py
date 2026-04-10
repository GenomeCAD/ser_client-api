"""
Tests for SeqoiaParser JSON schema validation.

The SeqOIA parser has two validation layers:
- Layer 1 (schema): jsonschema validates types and structure before parsing
- Layer 2 (parser): _get_required_field enforces required business fields

The schema defines no `required` arrays, so missing fields pass schema
validation and are caught exclusively by layer 2.
"""

import copy
import importlib.resources
import json

import pytest

from ser_client_api.hl7v2.seqoia.parser import SeqoiaParser


@pytest.fixture(autouse=True)
def reset_schema_cache():
    """Reset the class-level schema cache before each test for isolation."""
    SeqoiaParser._schema = None
    yield
    SeqoiaParser._schema = None


class TestSchemaValidation:
    """Layer 1: jsonschema type/structure checks."""

    def test_valid_prescription_passes(self, minimal_prescription_json):
        composition = SeqoiaParser().parse(minimal_prescription_json)
        assert composition.report_id == minimal_prescription_json["_id"]

    def test_root_not_object_raises_schema_error(self):
        with pytest.raises(ValueError, match="schema validation"):
            SeqoiaParser().parse([1, 2, 3])

    def test_patients_not_array_raises_schema_error(self, minimal_prescription_json):
        data = {**minimal_prescription_json, "patients": "not an array"}
        with pytest.raises(ValueError, match="schema validation"):
            SeqoiaParser().parse(data)

    def test_patients_item_not_object_raises_schema_error(self, minimal_prescription_json):
        data = {**minimal_prescription_json, "patients": ["string_instead_of_object"]}
        with pytest.raises(ValueError, match="schema validation"):
            SeqoiaParser().parse(data)

    def test_dateconsent_string_instead_of_number_raises_schema_error(self, minimal_prescription_json):
        data = copy.deepcopy(minimal_prescription_json)
        data["patients"][0]["dateConsent"] = "2024-01-01"
        with pytest.raises(ValueError, match="schema validation"):
            SeqoiaParser().parse(data)

    def test_date_prelevement_string_instead_of_number_raises_schema_error(self, minimal_prescription_json):
        data = copy.deepcopy(minimal_prescription_json)
        data["patients"][0]["date_prelevement"] = "2024-01-01"
        with pytest.raises(ValueError, match="schema validation"):
            SeqoiaParser().parse(data)

    def test_error_message_identifies_seqoia_and_includes_jsonschema_detail(self, minimal_prescription_json):
        data = {**minimal_prescription_json, "patients": 42}
        with pytest.raises(ValueError) as exc_info:
            SeqoiaParser().parse(data)
        msg = str(exc_info.value)
        assert "SeqOIA JSON schema validation failed" in msg
        assert "42" in msg or "patients" in msg


class TestParserValidation:
    """Layer 2: _get_required_field checks for business-required fields."""

    def test_missing_preindication_bypasses_schema_but_fails_parser(self, minimal_prescription_json):
        # Schema has no `required` arrays, so the missing field passes layer 1.
        # Layer 2 (_get_required_field) raises ValueError.
        data = {k: v for k, v in minimal_prescription_json.items() if k != "preindication"}
        with pytest.raises(ValueError):
            SeqoiaParser().parse(data)

    def test_missing_analysis_info_bypasses_schema_but_fails_parser(self, minimal_prescription_json):
        data = {k: v for k, v in minimal_prescription_json.items() if k != "analysis_info"}
        with pytest.raises(ValueError):
            SeqoiaParser().parse(data)


class TestSchemaCaching:

    def test_schema_loaded_after_first_parse(self, minimal_prescription_json):
        assert SeqoiaParser._schema is None
        SeqoiaParser().parse(minimal_prescription_json)
        assert SeqoiaParser._schema is not None

    def test_schema_object_is_reused_across_calls(self, minimal_prescription_json):
        parser = SeqoiaParser()
        parser.parse(minimal_prescription_json)
        schema_after_first = SeqoiaParser._schema
        parser.parse(minimal_prescription_json)
        assert SeqoiaParser._schema is schema_after_first


class TestTrioParsing:
    """id_anon extraction and folder_name resolution for trio prescriptions."""

    def test_main_patient_id_anon_parsed(self, minimal_prescription_json):
        composition = SeqoiaParser().parse(minimal_prescription_json)
        assert composition.patient.id_anon == "TESTID"

    def test_nok_father_id_anon_parsed(self, minimal_prescription_json):
        composition = SeqoiaParser().parse(minimal_prescription_json)
        father = next(n for n in composition.next_of_kin if n.relationship_code == "FTH")
        assert father.id_anon == "TESTID2"

    def test_nok_mother_id_anon_parsed(self, minimal_prescription_json):
        composition = SeqoiaParser().parse(minimal_prescription_json)
        mother = next(n for n in composition.next_of_kin if n.relationship_code == "MTH")
        assert mother.id_anon == "TESTID3"

    def test_patient_folder_name_uses_id_anon(self, minimal_prescription_json):
        composition = SeqoiaParser().parse(minimal_prescription_json)
        assert composition.patient.folder_name == "TESTID"
        assert composition.patient.folder_name != "DUPONT_MARIE"

    def test_nok_folder_name_uses_id_anon(self, minimal_prescription_json):
        composition = SeqoiaParser().parse(minimal_prescription_json)
        father = next(n for n in composition.next_of_kin if n.relationship_code == "FTH")
        assert father.folder_name == "TESTID2"
        assert father.folder_name != "DUPONT_JEAN"

    def test_folder_name_falls_back_to_family_given_when_no_id_anon(self):
        from ser_client_api.hl7v2.domain_models import RelatedPersonData
        nok = RelatedPersonData(set_id=1, relationship_code="FTH", family_name="DUPONT", given_name="JEAN")
        assert nok.folder_name == "DUPONT_JEAN"

    def test_folder_name_returns_none_when_no_id_anon_and_no_names(self):
        from ser_client_api.hl7v2.domain_models import RelatedPersonData
        nok = RelatedPersonData(set_id=1, relationship_code="FTH")
        assert nok.folder_name is None


class TestRealExamples:

    @pytest.mark.parametrize("filename", [
        "6d91642f-40ee-4f8e-afc3-3526101ad1e4.json",
        "ceb02985-8da5-4b7e-87b3-bb55d3d374a8.json",
    ])
    def test_bundled_real_prescription_parses_successfully(self, filename):
        examples = importlib.resources.files("ser_client_api.hl7v2.seqoia") / "examples"
        data = json.loads((examples / filename).read_text(encoding="utf-8"))
        composition = SeqoiaParser().parse(data)
        assert composition.report_id is not None
        assert composition.patient is not None
        assert composition.preindication is not None
