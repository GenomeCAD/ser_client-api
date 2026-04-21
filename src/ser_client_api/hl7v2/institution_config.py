from dataclasses import dataclass


@dataclass
class InstitutionConfig:
    """Sending-institution identifiers for HL7v2 message headers."""

    lab_name: str  # MSH-3, PID-3/18, PV1, PRT-8
    lab_finess: str  # FINESS-ET of the sending lab
    facility_name: str  # MSH-4, SFT-1
    facility_finess: str  # FINESS-ET of the facility (MSH-4)
    facility_finess_ej: str  # FINESS-EJ of the facility (SFT-1)
    software_name: str  # SFT-3: EHR/software product name
    software_product_information: str  # SFT-5: software product information
    receiving_application: str  # MSH-5: target CAD receiving application
    receiving_facility: str  # MSH-6: target CAD receiving facility
    message_profile_name: str  # MSH-21: human-readable profile label
    message_profile_oid: str  # MSH-21: profile version OID
    local_data_parser: str  # dotted module path to the institution's local data parser
