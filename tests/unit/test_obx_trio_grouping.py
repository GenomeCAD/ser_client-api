"""Unit tests for file OBX attribution in trio prescriptions (multi-PID structure).

In the multi-PID architecture each individual (main_patient, father, mother) has their
own PATIENT_RESULT group:
  - PATIENT_RESULT 1 (PID set_id="1"): main_patient files + root-level files
  - PATIENT_RESULT 2 (PID set_id="2"): father files
  - PATIENT_RESULT 3 (PID set_id="3"): mother files

This module verifies that files found in id_anon-named subdirectories end up in
the correct PATIENT_RESULT group and that their OBX-5 paths are correct.
"""

import tempfile
from pathlib import Path


def _parse_patient_result_obx_refs(hl7_message: str) -> dict[str, list[str]]:
    """Return a dict mapping PID set_id → list of OBX-5 file references.

    Iterates through segments in ER7 order and groups OBX-5 values by the
    most-recently-seen PID set_id.
    """
    result: dict[str, list[str]] = {}
    current_pid = None

    for segment in hl7_message.split("\r"):
        if not segment:
            continue
        fields = segment.split("|")
        if fields[0] == "PID":
            current_pid = fields[1] if len(fields) > 1 else None
            result.setdefault(current_pid, [])
        elif fields[0] == "OBX" and current_pid is not None:
            obx5 = fields[5] if len(fields) > 5 else ""
            result[current_pid].append(obx5)

    return result


class TestMultiPidTrioGrouping:
    def test_main_patient_subdir_in_main_patient_group(self, generator, composition):
        """Files in the main_patient's id_anon folder appear in PID set_id=1 group."""
        with tempfile.TemporaryDirectory() as tmp:
            # Must have at least one file per individual to satisfy profile validation
            for folder in ("TESTID", "TESTID2", "TESTID3"):
                d = Path(tmp) / folder
                d.mkdir()
                (d / "test.bam").write_bytes(b"BAM\x01" + b"\x00" * 100)

            hl7 = generator.generate(composition, files_directory=tmp)
            groups = _parse_patient_result_obx_refs(hl7)

            main_patient_refs = groups.get("1", [])
            assert any("TESTID/" in ref for ref in main_patient_refs)

    def test_father_subdir_in_father_group(self, generator, composition):
        """Files in the father's id_anon folder appear in PID set_id=2 group."""
        with tempfile.TemporaryDirectory() as tmp:
            for folder in ("TESTID", "TESTID2", "TESTID3"):
                d = Path(tmp) / folder
                d.mkdir()
                (d / "test.bam").write_bytes(b"BAM\x01" + b"\x00" * 100)

            hl7 = generator.generate(composition, files_directory=tmp)
            groups = _parse_patient_result_obx_refs(hl7)

            father_refs = groups.get("2", [])
            assert any("TESTID2/" in ref for ref in father_refs)

    def test_mother_subdir_in_mother_group(self, generator, composition):
        """Files in the mother's id_anon folder appear in PID set_id=3 group."""
        with tempfile.TemporaryDirectory() as tmp:
            for folder in ("TESTID", "TESTID2", "TESTID3"):
                d = Path(tmp) / folder
                d.mkdir()
                (d / "test.bam").write_bytes(b"BAM\x01" + b"\x00" * 100)

            hl7 = generator.generate(composition, files_directory=tmp)
            groups = _parse_patient_result_obx_refs(hl7)

            mother_refs = groups.get("3", [])
            assert any("TESTID3/" in ref for ref in mother_refs)

    def test_root_level_files_in_main_patient_group(self, generator, composition):
        """Root-level files (VCF, tar.gz) appear in the main_patient's PID group."""
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "shared.vcf").write_text("##fileformat=VCFv4.2\n")
            for folder in ("TESTID", "TESTID2", "TESTID3"):
                d = Path(tmp) / folder
                d.mkdir()
                (d / "test.bam").write_bytes(b"BAM\x01" + b"\x00" * 100)

            hl7 = generator.generate(composition, files_directory=tmp)
            groups = _parse_patient_result_obx_refs(hl7)

            main_patient_refs = groups.get("1", [])
            assert "shared.vcf" in main_patient_refs

    def test_father_files_not_in_main_patient_or_mother_group(self, generator, composition):
        """Father's files must not appear in the main_patient or mother groups."""
        with tempfile.TemporaryDirectory() as tmp:
            for folder in ("TESTID", "TESTID2", "TESTID3"):
                d = Path(tmp) / folder
                d.mkdir()
                (d / "test.bam").write_bytes(b"BAM\x01" + b"\x00" * 100)

            hl7 = generator.generate(composition, files_directory=tmp)
            groups = _parse_patient_result_obx_refs(hl7)

            main_patient_refs = groups.get("1", [])
            mother_refs = groups.get("3", [])
            assert not any("TESTID2/" in ref for ref in main_patient_refs)
            assert not any("TESTID2/" in ref for ref in mother_refs)

    def test_message_has_three_pid_groups_for_trio(self, generator, composition):
        """A trio prescription generates exactly three PATIENT_RESULT groups (three PIDs)."""
        with tempfile.TemporaryDirectory() as tmp:
            for folder in ("TESTID", "TESTID2", "TESTID3"):
                d = Path(tmp) / folder
                d.mkdir()
                (d / "test.bam").write_bytes(b"BAM\x01" + b"\x00" * 100)

            hl7 = generator.generate(composition, files_directory=tmp)
            pid_segments = [s for s in hl7.split("\r") if s.startswith("PID|")]
            assert len(pid_segments) == 3
