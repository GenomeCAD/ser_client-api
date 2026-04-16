"""Unit tests for NK1-3 relationship coding using HL7v3 FamilyMember ValueSet.

NK1-3 is encoded as CWE with 6 components:
  CWE.1: HL7v3 code (e.g. FTH, MTH, CHILD, SPS)
  CWE.2: display text (e.g. "father")
  CWE.3: system URI (http://terminology.hl7.org/CodeSystem/v3-RoleCode)
  CWE.4: match confidence score ("1.0" for exact matches)
  CWE.5: label "match-confidence"
  CWE.6: confidence system URI (http://www.genomecad.fr/CodeSystem/MatchConfidence)
"""

import tempfile
from pathlib import Path

import pytest

from ser_client_api.hl7v2.generator import (
    _V3_ROLE_CODE_SYSTEM,
    _MATCH_CONFIDENCE_SYSTEM,
    _resolve_inverse_code,
)


def _generate(generator, composition):
    with tempfile.TemporaryDirectory() as tmp:
        for folder in ("TESTID", "TESTID2", "TESTID3"):
            d = Path(tmp) / folder
            d.mkdir()
            (d / "test.bam").write_bytes(b"BAM\x01" + b"\x00" * 100)
        return generator.generate(composition, files_directory=tmp)


def _nk1_fields(hl7_message: str) -> list[dict]:
    """Return list of parsed NK1 segments as dicts."""
    result = []
    current_pid = None

    for segment in hl7_message.split("\r"):
        if not segment:
            continue
        fields = segment.split("|")
        if fields[0] == "PID":
            current_pid = fields[1] if len(fields) > 1 else None
        elif fields[0] == "NK1":
            nk1_3 = fields[3] if len(fields) > 3 else ""
            result.append({"pid_set_id": current_pid, "nk1_3": nk1_3})

    return result


class TestResolveInverseCode:
    def test_parent_inverse_is_child(self):
        assert _resolve_inverse_code("FTH", "F") == "CHILD"
        assert _resolve_inverse_code("MTH", "M") == "CHILD"

    def test_brother_of_female_patient_sees_sister(self):
        assert _resolve_inverse_code("BRO", "F") == "SIS"

    def test_brother_of_male_patient_sees_brother(self):
        assert _resolve_inverse_code("BRO", "M") == "BRO"

    def test_sister_of_male_patient_sees_brother(self):
        assert _resolve_inverse_code("SIS", "M") == "BRO"

    def test_grandparent_of_female_patient_sees_granddaughter(self):
        assert _resolve_inverse_code("GRFTH", "F") == "GRNDDAU"

    def test_grandparent_of_male_patient_sees_grandson(self):
        assert _resolve_inverse_code("MGRMTH", "M") == "GRNDSON"

    def test_uncle_sees_nephew_or_niece(self):
        assert _resolve_inverse_code("PUNCLE", "M") == "NEPHEW"
        assert _resolve_inverse_code("MAUNT", "F") == "NIECE"

    def test_cousin_is_symmetric(self):
        assert _resolve_inverse_code("COUSN", "M") == "COUSN"
        assert _resolve_inverse_code("MCOUSN", "F") == "COUSN"
        assert _resolve_inverse_code("PCOUSN", None) == "COUSN"

    def test_unknown_code_returns_none(self):
        assert _resolve_inverse_code("FTHINLAW", "M") is None
        assert _resolve_inverse_code("NOTACODE", "F") is None

    def test_unknown_sex_returns_none_for_sex_dependent_codes(self):
        assert _resolve_inverse_code("BRO", None) is None
        assert _resolve_inverse_code("SIS", "") is None

    def test_unknown_sex_still_resolves_sex_neutral_codes(self):
        assert _resolve_inverse_code("FTH", None) == "CHILD"
        assert _resolve_inverse_code("SPS", "") == "SPS"

    def test_spouse(self):
        assert _resolve_inverse_code("HUSB", "F") == "WIFE"
        assert _resolve_inverse_code("WIFE", "M") == "HUSB"


class TestNK1Relationship:
    def test_main_patient_nk1_father_cwe(self, generator, composition):
        hl7 = _generate(generator, composition)
        nk1s = _nk1_fields(hl7)

        father_nk1 = next(n for n in nk1s if n["pid_set_id"] == "1" and "FTH" in n["nk1_3"])
        expected = (
            f"FTH^père^{_V3_ROLE_CODE_SYSTEM}"
            f"^1.0^match-confidence^{_MATCH_CONFIDENCE_SYSTEM}"
        )
        assert father_nk1["nk1_3"] == expected

    def test_main_patient_nk1_mother_cwe(self, generator, composition):
        hl7 = _generate(generator, composition)
        nk1s = _nk1_fields(hl7)

        mother_nk1 = next(n for n in nk1s if n["pid_set_id"] == "1" and "MTH" in n["nk1_3"])
        expected = (
            f"MTH^mère^{_V3_ROLE_CODE_SYSTEM}"
            f"^1.0^match-confidence^{_MATCH_CONFIDENCE_SYSTEM}"
        )
        assert mother_nk1["nk1_3"] == expected

    def test_nok_group_child_code(self, generator, composition):
        hl7 = _generate(generator, composition)
        nk1s = _nk1_fields(hl7)

        child_nk1s = [n for n in nk1s if "CHILD" in n["nk1_3"]]
        assert len(child_nk1s) >= 1, "Expected at least one CHILD NK1-3 in NOK groups"
        for n in child_nk1s:
            expected = (
                f"CHILD^enfant^{_V3_ROLE_CODE_SYSTEM}"
                f"^1.0^match-confidence^{_MATCH_CONFIDENCE_SYSTEM}"
            )
            assert n["nk1_3"] == expected

    def test_nok_group_no_sps_segment(self, generator, composition):
        hl7 = _generate(generator, composition)
        nk1s = _nk1_fields(hl7)
        assert not any("SPS" in n["nk1_3"] for n in nk1s)

    def test_non_exact_nok_has_no_inverse_nk1(self, generator, composition):
        import tempfile
        from ser_client_api.hl7v2.seqoia.parser import SeqoiaParser
        prescription = {
            "_id": "test-non-exact",
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
                        "sexe": "M",
                        "nom": "DUPONT", "nom_naissance": "DUPONT", "prenom": "PAUL",
                    },
                    "lien": {"key": "patient", "name": "Patient"},
                    "is_data_reusable_for_research": False,
                    "date_prelevement": 1741651200000,
                    "id_anon": "MAIN",
                },
                {
                    "patient": {
                        "id": {"type": "IPP", "value": "IPP-002"},
                        "date_naissance": "1988-05-10",
                        "sexe": "M",
                        "nom": "DUPONT", "nom_naissance": "DUPONT", "prenom": "NICOLAS",
                    },
                    "lien": {"key": "autre", "name": "frère de Paul"},  # Level 2 regex
                    "is_data_reusable_for_research": False,
                    "date_prelevement": 1741651200000,
                    "id_anon": "NOK1",
                },
            ],
            "prescripteur": "123", "membreRCP": "456",
            "analysis_info": {"analysis_ID": "9999", "date_fin_analyse": "01042026"},
            "date_creation": 1741606397865,
            "date_cloture": 1745498322775,
            "resultats": [],
        }
        comp = SeqoiaParser().parse(prescription)
        with tempfile.TemporaryDirectory() as tmp:
            for folder in ("MAIN", "NOK1"):
                d = Path(tmp) / folder
                d.mkdir()
                (d / "test.bam").write_bytes(b"BAM\x01" + b"\x00" * 100)
            hl7 = generator.generate(comp, files_directory=tmp)

        nk1s = _nk1_fields(hl7)
        nok_nk1s = [n for n in nk1s if n["pid_set_id"] == "2"]
        assert nok_nk1s == [], (
            "Non-exact NOK should produce no inverse NK1, "
            f"but got: {nok_nk1s}"
        )
