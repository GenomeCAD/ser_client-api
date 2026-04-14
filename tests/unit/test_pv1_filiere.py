"""Tests for PV1.14 (Admit Source) PFMG filière population."""

import copy
import tempfile
from pathlib import Path

import pytest

from ser_client_api.hl7v2.seqoia.parser import SeqoiaParser
from ser_client_api.hl7v2.generator import _PFMG_FILIERE_SYSTEM


def _pv1_14(hl7_message: str) -> str:
    for segment in hl7_message.split("\r"):
        if segment.startswith("PV1|"):
            fields = segment.split("|")
            return fields[14] if len(fields) > 14 else ""
    return ""


def _generate(generator, composition):
    with tempfile.TemporaryDirectory() as tmp:
        for folder in ("TESTID", "TESTID2", "TESTID3"):
            d = Path(tmp) / folder
            d.mkdir()
            (d / "test.bam").write_bytes(b"BAM\x01" + b"\x00" * 100)
        return generator.generate(composition, files_directory=tmp)


class TestPV1Filiere:

    def test_pv1_14_full_cwe_value(self, generator, composition):
        hl7 = _generate(generator, composition)
        pv1_14 = _pv1_14(hl7)
        expected = (
            "F-31"
            "^Angioedèmes bradykiniques héréditaires [MaRIH]"
            f"^{_PFMG_FILIERE_SYSTEM}"
        )
        assert pv1_14 == expected

    def test_pv1_14_absent_for_unknown_filiere_key(
        self, generator, institution, minimal_prescription_json
    ):
        data = copy.deepcopy(minimal_prescription_json)
        data["preindication"]["key"] = "p1-sp99"  # not in the mapping table
        composition = SeqoiaParser().parse(data)

        hl7 = _generate(generator, composition)
        assert _pv1_14(hl7) == ""
