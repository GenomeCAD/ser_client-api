"""
Notebook demo helpers - scaffolding utilities for the ser_demo_notebook.
Not intended for production use.
"""

import tempfile
from pathlib import Path
from typing import Any, Dict, Tuple

from ser_client_api.hl7v2.domain_models import CompositionData
from ser_client_api.hl7v2.ack_service import AckAnalysisResult, analyze_ack_message, determine_transfer_status
from ser_client_api.hl7v2.institution_config import InstitutionConfig
from ser_client_api.parser_factory import ParserFactory


def get_prescription_directory(prescription_name: str) -> Tuple[Path, Path]:
    """Create a temporary directory for a demo prescription transfer.
    Returns (tmp_dir, presc_dir) where presc_dir = tmp_dir / prescription_name.
    """
    tmp_dir = Path(tempfile.mkdtemp(prefix="ser_demo_"))
    presc_dir = tmp_dir / prescription_name
    return tmp_dir, presc_dir


def populate_temporary_presc_dir(presc_dir: Path, prescription_name: str, composition: CompositionData) -> None:
    """Populate a prescription directory with minimal dummy data files.

    - Root-level shared files (VCF, tar.gz) attributed to the main patient (OBX-1=1)
    - One subdirectory per individual named by id_anon, each containing stub BAM/BAI files
    - Next-of-kin subdirectories created for each entry in composition.next_of_kin

    The resulting structure is sufficient to exercise the full
    generate → sidecar → seal → transfer pipeline.
    """
    presc_dir.mkdir(parents=True, exist_ok=True)

    # Root-level shared files (OBX-1="1", main patient)
    (presc_dir / f"{prescription_name}_final.vcf").write_text("##fileformat=VCFv4.2\n#CHROM\tPOS\tID\tREF\tALT\n")
    (presc_dir / f"{prescription_name}_final.tar.gz").write_bytes(b"\x1f\x8b" + b"\x00" * 20)

    # One subdirectory per individual
    individuals = [composition.patient]
    if composition.next_of_kin:
        individuals += composition.next_of_kin

    for individual in individuals:
        folder = individual.folder_name
        if not folder:
            continue
        ind_dir = presc_dir / folder
        ind_dir.mkdir(parents=True, exist_ok=True)
        (ind_dir / f"{prescription_name}_chr1_markdup.bam").write_bytes(b"BAM\x01" + b"\x00" * 100)
        (ind_dir / f"{prescription_name}_chr1_markdup.bam.bai").write_bytes(b"BAI\x01" + b"\x00" * 20)


def get_composition(institution: InstitutionConfig, prescription_json: Dict[str, Any]) -> CompositionData:
    """Parse a prescription JSON dict into a CompositionData using the institution's parser."""
    return ParserFactory(institution).create().parse(prescription_json)


def print_composition(composition: CompositionData) -> None:
    """Print a human-readable summary of a parsed CompositionData."""
    print(f"Report ID    : {composition.report_id}")
    print(f"Patient      : {composition.patient.patient_family_name} {composition.patient.patient_given_name}")
    print(f"DOB          : {composition.patient.birth_date}  sex={composition.patient.sex}")
    print(f"Preindication: {composition.preindication.name} ({composition.preindication.key})")
    print(f"RCP          : {composition.rcp.rcp_nom} (id={composition.rcp.rcp_id})")
    print(f"Analysis ID  : {composition.analysis.analysis_id}")
    print(f"Period       : {composition.timing.start} > {composition.timing.end}")
    print(f"Prescripteur : {composition.person.prescripteur}")
    print(f"MembreLMG    : {composition.results.membre_lmg}")
    print(f"Consent      : reusable={composition.consent.is_data_reusable_for_research}")
    if composition.next_of_kin:
        for nok in composition.next_of_kin:
            print(f"Next of kin  : [{nok.relationship_code}] {nok.family_name} {nok.given_name} (DOB: {nok.birth_date})")


def print_transfer_directory(presc_dir: Path) -> None:
    """Print the contents of a prescription transfer directory with file sizes."""
    all_files = [f for f in sorted(presc_dir.rglob("*")) if f.is_file()]
    print(f"Transfer directory: {presc_dir}")
    print(f"Files to transfer ({len(all_files)}):")
    for f in all_files:
        print(f"  {f.relative_to(presc_dir)}  ({f.stat().st_size} bytes)")


def print_hl7_file(hl7_file: Path) -> None:
    """Print a summary and first few segments of a generated HL7v2 file."""
    segments = hl7_file.read_bytes().decode("utf-8").split("\r")
    print(f"HL7v2 file: {hl7_file.name}  ({hl7_file.stat().st_size} bytes, {len(segments)} segments)")
    print()
    for seg in segments[:6]:
        print(seg[:100] + ("..." if len(seg) > 100 else ""))


def print_ack(ack_msg, ack_filename: str = None) -> None:
    """Analyze an ACK message and print a human-readable summary."""
    analysis = analyze_ack_message(ack_msg)
    status = determine_transfer_status(analysis)
    status_label = {0: "OK", 1: "ERROR (retry)", 2: "FAILED"}.get(status, "UNKNOWN")
    if ack_filename:
        print(f"ACK file   : {ack_filename}")
    print(f"MSA status : {analysis.msa_status}")
    print(f"Control ID : {analysis.message_control_id}")
    print(f"Errors     : {len(analysis.critical_errors)}")
    print(f"Warnings   : {len(analysis.warnings)}")
    print(f"Infos      : {len(analysis.infos)}")
    print(f"Result     : {status_label}")
    if analysis.critical_errors:
        print()
        for e in analysis.critical_errors:
            print(f"  error: {e}")
    if analysis.warnings:
        print()
        for w in analysis.warnings:
            print(f"  warning: {w}")
