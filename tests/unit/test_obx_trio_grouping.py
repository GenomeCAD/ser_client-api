"""Unit tests for OBX-1 grouping in trio prescriptions.

Verifies that files in id_anon-named subdirectories are attributed to the
correct individual:
  - TESTID/   → OBX-1="1" (main patient)
  - TESTID2/  → OBX-1="2" (father)
  - TESTID3/  → OBX-1="3" (mother)

Root-level files always go to OBX-1="1".
"""

import tempfile
from pathlib import Path

import pytest


def _obx_segments(hl7_message: str) -> list[list[str]]:
    return [s.split("|") for s in hl7_message.split("\r") if s.startswith("OBX|")]


def _obx1_values_for_folder(obx_segments, folder: str) -> set[str]:
    return {s[1] for s in obx_segments if s[5].startswith(folder + "/")}


class TestObxTrioGrouping:

    def test_main_patient_subdir_is_obx1_1(self, generator, composition):
        with tempfile.TemporaryDirectory() as tmp:
            patient_dir = Path(tmp) / "TESTID"
            patient_dir.mkdir()
            (patient_dir / "test.bam").write_bytes(b"BAM\x01" + b"\x00" * 100)

            hl7 = generator.generate(composition, files_directory=tmp)
            obx = _obx_segments(hl7)

            assert _obx1_values_for_folder(obx, "TESTID") == {"1"}

    def test_father_subdir_is_obx1_2(self, generator, composition):
        with tempfile.TemporaryDirectory() as tmp:
            father_dir = Path(tmp) / "TESTID2"
            father_dir.mkdir()
            (father_dir / "test.bam").write_bytes(b"BAM\x01" + b"\x00" * 100)

            hl7 = generator.generate(composition, files_directory=tmp)
            obx = _obx_segments(hl7)

            assert _obx1_values_for_folder(obx, "TESTID2") == {"2"}

    def test_mother_subdir_is_obx1_3(self, generator, composition):
        with tempfile.TemporaryDirectory() as tmp:
            mother_dir = Path(tmp) / "TESTID3"
            mother_dir.mkdir()
            (mother_dir / "test.bam").write_bytes(b"BAM\x01" + b"\x00" * 100)

            hl7 = generator.generate(composition, files_directory=tmp)
            obx = _obx_segments(hl7)

            assert _obx1_values_for_folder(obx, "TESTID3") == {"3"}

    def test_root_level_files_are_obx1_1(self, generator, composition):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "shared.vcf").write_text("##fileformat=VCFv4.2\n")

            hl7 = generator.generate(composition, files_directory=tmp)
            obx = _obx_segments(hl7)

            root_obx = [s for s in obx if s[5] == "shared.vcf"]
            assert len(root_obx) >= 1
            assert all(s[1] == "1" for s in root_obx)

    def test_full_trio_all_groups_correct(self, generator, composition):
        with tempfile.TemporaryDirectory() as tmp:
            for folder in ("TESTID", "TESTID2", "TESTID3"):
                d = Path(tmp) / folder
                d.mkdir()
                (d / "test.bam").write_bytes(b"BAM\x01" + b"\x00" * 100)

            hl7 = generator.generate(composition, files_directory=tmp)
            obx = _obx_segments(hl7)

            assert _obx1_values_for_folder(obx, "TESTID") == {"1"}
            assert _obx1_values_for_folder(obx, "TESTID2") == {"2"}
            assert _obx1_values_for_folder(obx, "TESTID3") == {"3"}
