"""Unit tests for OBX sidecar hash logic in _populate_obx_files.

Three scenarios are tested:
  1. File + sidecar both exist  → hash read from sidecar (no recomputation)
  2. File exists, no sidecar    → hash computed directly from file
  3. Orphaned sidecar           → RP(data) + RP(sidecar) + ED emitted using sidecar hash
"""

import base64
import hashlib
import tempfile
from pathlib import Path


def _obx_segments(hl7_message: str) -> list[list[str]]:
    return [s.split("|") for s in hl7_message.split("\r") if s.startswith("OBX|")]


def _decode_ed_hash(obx5: str) -> str:
    return base64.b64decode(obx5.split("^")[4]).decode()


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sidecar_content(filepath: Path) -> str:
    return filepath.read_text().strip().split("  ")[0]


class TestObxSidecarLogic:
    def test_file_and_sidecar_exist_reads_hash_from_sidecar(self, generator, composition):
        """When both file and sidecar exist, the ED hash must come from the sidecar,
        not be recomputed. We verify this by writing a deliberately wrong hash to
        the sidecar and asserting the ED reflects it."""
        with tempfile.TemporaryDirectory() as tmp:
            patient_dir = Path(tmp) / "TESTID"
            patient_dir.mkdir()

            bam = patient_dir / "test.bam"
            bam.write_bytes(b"BAM\x01" + b"\x00" * 100)

            fake_hash = "a" * 64
            (patient_dir / "test.bam.sha256").write_text(f"{fake_hash}  test.bam\n")

            hl7 = generator.generate(composition, files_directory=tmp)
            obx = _obx_segments(hl7)

            bam_obx = [s for s in obx if "test.bam" in s[5] and s[2] == "RP" and not s[5].endswith(".sha256")]
            ed_obx = [s for s in obx if s[2] == "ED" and "SHA256" in s[3]]

            assert len(bam_obx) == 1, "Expected one RP for test.bam"
            assert len(ed_obx) >= 1, "Expected at least one ED segment"

            decoded = _decode_ed_hash(ed_obx[0][5])
            assert decoded == fake_hash, f"ED hash should come from sidecar ({fake_hash!r}), got {decoded!r}"
            assert decoded != _sha256_hex(bam.read_bytes()), (
                "ED hash must NOT be recomputed from file when sidecar exists"
            )

    def test_file_without_sidecar_computes_hash_from_file(self, generator, composition):
        """When no sidecar exists, the ED hash must be computed directly from the file."""
        with tempfile.TemporaryDirectory() as tmp:
            patient_dir = Path(tmp) / "TESTID"
            patient_dir.mkdir()

            bam_content = b"BAM\x01" + b"\x00" * 100
            bam = patient_dir / "test.bam"
            bam.write_bytes(bam_content)

            hl7 = generator.generate(composition, files_directory=tmp)
            obx = _obx_segments(hl7)

            rp_obx = [s for s in obx if s[2] == "RP"]
            ed_obx = [s for s in obx if s[2] == "ED"]

            sidecar_rp = [s for s in rp_obx if s[5].endswith(".sha256")]
            assert len(sidecar_rp) == 0, "No sidecar RP expected when sidecar does not exist"

            assert len(ed_obx) == 1, "Expected exactly one ED segment"
            decoded = _decode_ed_hash(ed_obx[0][5])
            assert decoded == _sha256_hex(bam_content), "ED hash must match the SHA256 computed directly from the file"

    def test_obx_ordering_is_rp_data_rp_sidecar_ed(self, generator, composition):
        """For each data file the OBX sequence must be RP(data) -> RP(sidecar) -> ED."""
        with tempfile.TemporaryDirectory() as tmp:
            patient_dir = Path(tmp) / "TESTID"
            patient_dir.mkdir()

            bam_content = b"BAM\x01" + b"\x00" * 100
            bam = patient_dir / "test.bam"
            bam.write_bytes(bam_content)
            digest = _sha256_hex(bam_content)
            (patient_dir / "test.bam.sha256").write_text(f"{digest}  test.bam\n")

            hl7 = generator.generate(composition, files_directory=tmp)
            obx = _obx_segments(hl7)

            rp_data_idx = next(
                i
                for i, s in enumerate(obx)
                if s[2] == "RP" and s[5].endswith("test.bam") and not s[5].endswith(".sha256")
            )
            rp_sidecar_idx = next(i for i, s in enumerate(obx) if s[2] == "RP" and s[5].endswith("test.bam.sha256"))
            ed_idx = next(i for i, s in enumerate(obx) if s[2] == "ED")

            assert rp_data_idx < rp_sidecar_idx < ed_idx, (
                f"Expected RP(data) → RP(sidecar) → ED, got indices {rp_data_idx}, {rp_sidecar_idx}, {ed_idx}"
            )

    def test_orphaned_sidecar_emits_full_triple(self, generator, composition):
        """When only the sidecar exists (file previously pushed), the generator must
        still emit RP(data) + RP(sidecar) + ED using the hash from the sidecar."""
        with tempfile.TemporaryDirectory() as tmp:
            patient_dir = Path(tmp) / "TESTID"
            patient_dir.mkdir()

            sidecar_hash = "b" * 64
            (patient_dir / "test.bam.sha256").write_text(f"{sidecar_hash}  test.bam\n")

            hl7 = generator.generate(composition, files_directory=tmp)
            obx = _obx_segments(hl7)

            rp_obx = [s for s in obx if s[2] == "RP"]
            ed_obx = [s for s in obx if s[2] == "ED"]

            data_rp = [s for s in rp_obx if s[5].endswith("test.bam")]
            sidecar_rp = [s for s in rp_obx if s[5].endswith("test.bam.sha256")]

            assert len(data_rp) == 1, "Expected RP for orphaned data file reference"
            assert len(sidecar_rp) == 1, "Expected RP for the sidecar"
            assert len(ed_obx) == 1, "Expected ED with embedded hash"

            decoded = _decode_ed_hash(ed_obx[0][5])
            assert decoded == sidecar_hash, (
                f"ED hash must come from orphaned sidecar ({sidecar_hash!r}), got {decoded!r}"
            )
