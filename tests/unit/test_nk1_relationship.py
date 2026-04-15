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

from ser_client_api.hl7v2.generator import _V3_ROLE_CODE_SYSTEM, _MATCH_CONFIDENCE_SYSTEM


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


class TestNK1Relationship:
    def test_main_patient_nk1_father_cwe(self, generator, composition):
        """NK1-3 for father in main patient group uses FTH with HL7v3 system."""
        hl7 = _generate(generator, composition)
        nk1s = _nk1_fields(hl7)

        father_nk1 = next(n for n in nk1s if n["pid_set_id"] == "1" and "FTH" in n["nk1_3"])
        expected = (
            f"FTH^father^{_V3_ROLE_CODE_SYSTEM}"
            f"^1.0^match-confidence^{_MATCH_CONFIDENCE_SYSTEM}"
        )
        assert father_nk1["nk1_3"] == expected

    def test_main_patient_nk1_mother_cwe(self, generator, composition):
        """NK1-3 for mother in main patient group uses MTH with HL7v3 system."""
        hl7 = _generate(generator, composition)
        nk1s = _nk1_fields(hl7)

        mother_nk1 = next(n for n in nk1s if n["pid_set_id"] == "1" and "MTH" in n["nk1_3"])
        expected = (
            f"MTH^mother^{_V3_ROLE_CODE_SYSTEM}"
            f"^1.0^match-confidence^{_MATCH_CONFIDENCE_SYSTEM}"
        )
        assert mother_nk1["nk1_3"] == expected

    def test_nok_group_child_code(self, generator, composition):
        """NK1-3 in a NOK's group referencing the main patient uses CHILD (not CHD)."""
        hl7 = _generate(generator, composition)
        nk1s = _nk1_fields(hl7)

        child_nk1s = [n for n in nk1s if "CHILD" in n["nk1_3"]]
        assert len(child_nk1s) >= 1, "Expected at least one CHILD NK1-3 in NOK groups"
        for n in child_nk1s:
            expected = (
                f"CHILD^child^{_V3_ROLE_CODE_SYSTEM}"
                f"^1.0^match-confidence^{_MATCH_CONFIDENCE_SYSTEM}"
            )
            assert n["nk1_3"] == expected

    def test_nok_group_spouse_code(self, generator, composition):
        """NK1-3 in a NOK's group referencing the other parent uses SPS (not SPO)."""
        hl7 = _generate(generator, composition)
        nk1s = _nk1_fields(hl7)

        spouse_nk1s = [n for n in nk1s if "SPS" in n["nk1_3"]]
        assert len(spouse_nk1s) >= 1, "Expected at least one SPS NK1-3 in NOK groups"
        for n in spouse_nk1s:
            expected = (
                f"SPS^spouse^{_V3_ROLE_CODE_SYSTEM}"
                f"^1.0^match-confidence^{_MATCH_CONFIDENCE_SYSTEM}"
            )
            assert n["nk1_3"] == expected
