"""
Notebook demo helpers - scaffolding utilities for the ser_demo_notebook.
Not intended for production use.
"""

import tempfile
from pathlib import Path
from typing import Any, Dict, Tuple

from ser_client_api.hl7v2.domain_models import CompositionData
from ser_client_api.hl7v2.institution_config import InstitutionConfig
from ser_client_api.parser_factory import ParserFactory


def get_prescription_directory(prescription_name: str) -> Tuple[Path, Path]:
    """Create a temporary directory for a demo prescription transfer.
    Returns (tmp_dir, presc_dir) where presc_dir = tmp_dir / prescription_name.
    """
    tmp_dir = Path(tempfile.mkdtemp(prefix="ser_demo_"))
    presc_dir = tmp_dir / prescription_name
    return tmp_dir, presc_dir


def populate_temporary_presc_dir(presc_dir: Path, prescription_name: str, id_anon: str) -> None:
    """Populate a prescription directory with minimal dummy data files.
    Creates a patient subdirectory (named by id_anon) containing stub
    BAM, BAI, VCF and tar.gz files sufficient to exercise the full
    generate → sidecar → seal → transfer pipeline.
    #TODO: add next of kin files
    """
    patient_dir = presc_dir / id_anon
    patient_dir.mkdir(parents=True)
    (patient_dir / f"{prescription_name}_final.vcf").write_text("##fileformat=VCFv4.2\n#CHROM\tPOS\tID\tREF\tALT\n")
    (patient_dir / f"{prescription_name}_final.tar.gz").write_bytes(b"\x1f\x8b" + b"\x00" * 20)
    (patient_dir / f"{prescription_name}_chr1_markdup.bam").write_bytes(b"BAM\x01" + b"\x00" * 100)
    (patient_dir / f"{prescription_name}_chr1_markdup.bam.bai").write_bytes(b"BAI\x01" + b"\x00" * 20)


def get_composition(institution: InstitutionConfig, prescription_json: Dict[str, Any]) -> CompositionData:
    """Parse a prescription JSON dict into a CompositionData using the institution's parser."""
    return ParserFactory(institution).create().parse(prescription_json)
