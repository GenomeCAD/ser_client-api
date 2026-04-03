"""
Pre-defined InstitutionConfig instances for the three SeqOIA network members.
"""

from .institution_config import InstitutionConfig

# Common CAD receiving-end identifiers (same for all institutions)
_RECEIVING_APPLICATION = "GIP COLLECTEUR ANALYSEUR DE DONNEES^313003057000027^1.2.250.1.71.4.2.2"
_RECEIVING_FACILITY = "GIP COLLECTEUR ANALYSEUR DE DONNEES^2130030570^1.2.250.1.71.4.2.2"
_MESSAGE_PROFILE_NAME = "Message au format CAD ORU_R01 v1"
_MESSAGE_PROFILE_OID = "1.2.250.1.710.1.15.9.1.1.1"

SEQOIA = InstitutionConfig(
    lab_name="GCS LBM SEQOIA SITE BROUSSAIS",
    lab_finess="1750063265",
    facility_name="GCS SEQOIA",
    facility_finess="1750059800",
    facility_finess_ej="750059800",
    software_name="gleaves",
    software_product_information="variantannotator^1.2.250.1.710.1.7.3.2.9^1.2.250.1.710.1.2.1",
    receiving_application=_RECEIVING_APPLICATION,
    receiving_facility=_RECEIVING_FACILITY,
    message_profile_name=_MESSAGE_PROFILE_NAME,
    message_profile_oid=_MESSAGE_PROFILE_OID,
    local_data_parser="ser_client_api.hl7v2.seqoia.parser",
)

AURAGEN = InstitutionConfig(
    lab_name="GCS AURAGEN - CENTRE LEON BERARD",
    lab_finess="1690045059",
    facility_name="GCS AURAGEN - HOPICES CIVILS DE LYON",  # NB: typo intentional (official registry)
    facility_finess="1690043534",
    facility_finess_ej="690043534",
    software_name="Auragen variant caller",
    software_product_information="variantannotator^1.2.250.1.710.1.7.3.2.9^1.2.250.1.710.1.2.1",
    receiving_application=_RECEIVING_APPLICATION,
    receiving_facility=_RECEIVING_FACILITY,
    message_profile_name=_MESSAGE_PROFILE_NAME,
    message_profile_oid=_MESSAGE_PROFILE_OID,
    local_data_parser="ser_client_api.hl7v2.auragen.parser",
)

PERIGENOMED = InstitutionConfig(
    lab_name="HOPITAL LE BOCAGE CHRU DIJON",
    lab_finess="1210987558",
    facility_name="CHU DIJON BOURGOGNE",
    facility_finess="1210780581",
    facility_finess_ej="210780581",
    software_name="lims",
    software_product_information="variantannotator^1.2.250.1.710.1.7.3.2.9^1.2.250.1.710.1.2.1",
    receiving_application="GIP CAD Zone Périgénomed^1.2.250.1.710.1.7.3.6.1^1.2.250.1.710.1",
    receiving_facility=_RECEIVING_FACILITY,
    message_profile_name=_MESSAGE_PROFILE_NAME,
    message_profile_oid=_MESSAGE_PROFILE_OID,
    local_data_parser="ser_client_api.hl7v2.perigenomed.parser",
)
