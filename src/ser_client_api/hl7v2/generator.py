"""
HL7v2 Generator - Output Adapter
Transforms business models into HL7v2 format using hl7apy
"""

import base64
import hashlib
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from hl7apy import load_message_profile
from hl7apy.consts import VALIDATION_LEVEL
from hl7apy.core import Message
from ser_client_api.hl7v2.institution_config import InstitutionConfig
from ser_client_api.hl7v2.domain_models import (
    CareTeamData,
    CompositionData,
    ConditionData,
    ConsentData,
    ObservationData,
    PatientData,
    PeriodData,
    PersonData,
    ProcedureData,
    RelatedPersonData,
)

# GIP-CPS OID for "type_identifiant_structure"
OID_GIPCPS_TYPE_IDENTIFIANT_STRUCTURE = "1.2.250.1.71.4.2.2"


class HL7v2Generator:
    """Output adapter for HL7v2 generation.

    Transforms business models into HL7v2 messages using hl7apy library.
    Uses basic HL7v2 structure without profile constraints for POC.
    All fields conform to HL7v2 profile requirements.
    """

    # Format mapping for file extensions to HL7v2 codes
    FORMAT_MAPPING = {
        "json": {
            "code": "60591-5",
            "description": "Synthèse médicale",
            "system": "LN",
        },
        "vcf": {
            "code": "format_3016",
            "description": "VCF",
            "system": "http://edamontology.org",
        },
        "bam": {
            "code": "format_2572",
            "description": "BAM",
            "system": "http://edamontology.org",
        },
        "bai": {
            "code": "format_3327",
            "description": "BAM Index",
            "system": "http://edamontology.org",
        },
        "cram": {
            "code": "format_3462",
            "description": "CRAM",
            "system": "http://edamontology.org",
        },
        "crai": {
            "code": "C192224",
            "description": "CRAI File",
            "system": "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl",
        },
        "tar.gz": {
            "code": "format_3981",
            "description": "TAR",
            "system": "http://edamontology.org",
        },
        "sha256": {
            "code": "C48049",
            "description": "SHA256 Checksum",
            "system": "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl",
        },
    }

    def __init__(self, profile_path: str, institution: InstitutionConfig):
        """Initialize HL7v2 generator with mandatory GIPCAD profile.

        :param profile_path: Path to the compiled GIPCAD ORU_R01 profile directory
        :type profile_path: str
        :param institution: Sending institution identifiers for HL7v2 message headers
        :type institution: InstitutionConfig
        """
        self.message_profile = load_message_profile(profile_path)
        self.institution = institution

    def generate(
        self, parsed_report_data: CompositionData, files_directory: str = None
    ) -> str:
        """Generate HL7v2 ORU_R01 message from GenomicsReport.

        :param parsed_report_data: Business model containing all parsed report data
        :type parsed_report_data: CompositionData
        :param files_directory: Directory path containing files to list in OBX segments
        :type files_directory: str

        :return: HL7v2 message in ER7 pipe-delimited format
        :rtype: str

        """
        # Create HL7v2 message with mandatory GIPCAD profile (STRICT validation)
        msg = Message(
            "ORU_R01",
            reference=self.message_profile,
            validation_level=VALIDATION_LEVEL.STRICT,
        )

        # Populate MSH segment
        self._populate_msh(msg)

        self._populate_sft(msg)

        # Populate PID segment
        self._populate_pid(
            msg, parsed_report_data.patient, parsed_report_data.report_id
        )

        # Populate CON segment (only if consent for research )
        if (
            parsed_report_data.consent
            and parsed_report_data.consent.is_data_reusable_for_research
        ):
            self._populate_con(msg, parsed_report_data.consent)

        # Populate NK1 segments (Next of Kin: father/mother)
        if parsed_report_data.next_of_kin:
            self._populate_nk1(msg, parsed_report_data.next_of_kin)

        # preindication
        self._populate_pv1(
            msg,
            parsed_report_data.analysis,
            parsed_report_data.preindication,
            parsed_report_data.patient,
            parsed_report_data.results,
        )

        # Populate OBX segments with file references (grouped by individual)
        self._populate_obx_files(
            msg,
            files_directory,
            parsed_report_data.timing.end,
            parsed_report_data.patient,
            parsed_report_data.next_of_kin,
        )

        # # Populate PRT segment
        self._populate_prt(
            msg,
            parsed_report_data.rcp,
            parsed_report_data.person,
            parsed_report_data.analysis,
            parsed_report_data.timing,
        )
        self.validate_with_profile(msg)
        return msg.to_er7()

    def validate_with_profile(self, msg: Message):
        """Force validation against GIPCAD profile.

        :param msg: HL7v2 message to validate
        :raises ValidationError: If message violates profile constraints
        """
        try:
            msg.validate()  # Force validation against loaded profile
        except Exception as e:
            raise ValueError(f"GIPCAD Profile validation failed: {e}")

    def _populate_pv1(
        self,
        msg: Message,
        analysis_data: ProcedureData,
        preindication_data: ConditionData,
        patient: PatientData,
        results: ObservationData,
    ) -> None:
        """Populate PV1 segment with patient visit information.

        :param msg: HL7v2 message to populate
        :type msg: Message
        :param analysis_data: Analysis information from business model
        :type analysis_data: ProcedureData
        :param preindication_data: Preindication information from business model
        :type preindication_data: ConditionData
        :param patient: Patient information from business model
        :type patient: PatientData
        :param results: Results information from business model
        :type results: ObservationData
        :return: None
        :rtype: None
        """
        membre_lmg = results.membre_lmg or "UNKNOWN"
        preindication_data.name
        preindication_data.key
        analysis_id = analysis_data.analysis_id
        date_prelevement = patient.date_prelevement

        # Navigate to correct HL7v2 hierarchy for PV1 segment
        visit_group = msg.oru_r01_patient_result.oru_r01_patient.oru_r01_visit

        visit_group.pv1.set_id_pv1 = "1"
        visit_group.pv1.patient_class = "I"
        visit_group.pv1.admission_type = "C"
        visit_group.pv1.referring_doctor = (
            f"{membre_lmg}^^^^^^^^{self.institution.lab_name}"
            f"&{self.institution.lab_finess}&{OID_GIPCPS_TYPE_IDENTIFIANT_STRUCTURE}^D^^^EI"
        )
        visit_group.pv1.consulting_doctor = (
            f"{membre_lmg}^^^^^^^^{self.institution.lab_name}"
            f"&{self.institution.lab_finess}&{OID_GIPCPS_TYPE_IDENTIFIANT_STRUCTURE}^D^^^EI"
        )
        # TODO fix this admit_source, specification was incorrect
        # visit_group.pv1.admit_source = f"{preindication_name}^{preindication_key}^1.2.250.1.710.1.2.10.3^ISO"
        visit_group.pv1.visit_number = (
            f"{analysis_id}^^^{self.institution.lab_name}"
            f"&{self.institution.lab_finess}&{OID_GIPCPS_TYPE_IDENTIFIANT_STRUCTURE}^VN"
        )
        visit_group.pv1.admit_date_time = self._format_to_hl7_timestamp(
            date_prelevement
        )
        visit_group.pv1.discharge_date_time = visit_group.pv1.admit_date_time

    def _populate_sft(self, msg: Message) -> None:
        # SFT.1	Software Vendor Organization
        msg.sft.software_vendor_organization = (
            f"{self.institution.facility_name}^L^^^^ASIP-SANTE-ST&{OID_GIPCPS_TYPE_IDENTIFIANT_STRUCTURE}&ISO^FINEJ^^^{self.institution.facility_finess_ej}"
        )
        # SFT.3	Software Product Name
        msg.sft.software_product_name = self.institution.software_name

        # SFT.5	Software Product Information
        msg.sft.software_product_information = self.institution.software_product_information

    def _populate_msh(self, msg: Message) -> None:
        """Populate MSH segment with all mandatory fields per IHE ILW profile.
        :param msg: HL7v2 message to populate
        :type msg: Message
        :return: None
        :rtype: None
        """
        # MSH-1: Field Separator
        msg.msh.field_separator = "|"
        # MSH-2: Encoding Characters
        msg.msh.encoding_characters = "^~\\&"

        # MSH-3: Sending Application
        msg.msh.sending_application = (
            f"{self.institution.lab_name}^{self.institution.lab_finess}^{OID_GIPCPS_TYPE_IDENTIFIANT_STRUCTURE}"
        )
        # MSH-4: Sending Facility
        msg.msh.sending_facility = (
            f"{self.institution.facility_name}^{self.institution.facility_finess}^{OID_GIPCPS_TYPE_IDENTIFIANT_STRUCTURE}"
        )
        # MSH-5: Receiving Application
        msg.msh.receiving_application = self.institution.receiving_application
        # MSH-6: Receiving Facility
        msg.msh.receiving_facility = self.institution.receiving_facility

        # MSH-7: Date/Time of Message
        # Format now datetime as HL7v2 timestamp (YYYYMMDDHHMMSS.mmm+ZZZZ)
        msg.msh.date_time_of_message = self._format_to_hl7_timestamp(
            datetime.now().astimezone()
        )

        # MSH-9: Message Type
        msg.msh.message_type = "ORU^R01^ORU_R01"
        # MSH-10: Message Control ID
        msg.msh.message_control_id = str(uuid.uuid4())
        # MSH-11: Processing ID
        msg.msh.processing_id = "P"

        # MSH-12: Version ID
        msg.msh.version_id = "2.5^FRA"

        # MSH-15 and MSH-16 must NOT be populated.
        # In all IHE HL7 profiles, these fields are marked as Usage="X" (forbidden).
        # ACK behaviour is fixed to the "HL7 original mode", so these fields must be omitted.
        # MSH-15: Accept Acknowledgment Type
        # msg.msh.accept_acknowledgment_type = 'AL'
        # MSH-16: Application Acknowledgment Type
        # msg.msh.application_acknowledgment_type = 'AL'

        # MSH-17: Application Acknowledgment Type
        msg.msh.country_code = "FRA"
        msg.msh.character_set = "UNICODE UTF-8"
        msg.msh.principal_language_of_message = "fr^français^ISO6391^FR^France^ISO3166"
        msg.msh.message_profile_identifier = (
            f"{self.institution.message_profile_name}"
            f"^{self.institution.message_profile_oid}"
            f"^1.2.250.1.710.1.2.1^ISO"
        )

    def _populate_pid(self, msg: Message, patient: PatientData, report_id: str) -> None:
        """Populate PID segment conforming to oru_r01_lab36.xml profile constraints.

        PID fields according to oru_r01_lab36.xml profile specification:
        PID-1: Set ID (Optional)
        PID-2: Patient ID (External ID) - Not used
        PID-3: Patient Identifier List - REQUIRED (Usage="R")
        PID-4: Alternate Patient ID - Not used
        PID-5: Patient Name - REQUIRED (Usage="R")
        PID-6: Mother's Maiden Name - Not used
        PID-7: Date/Time of Birth - Required but may be Empty (Usage="RE")
        PID-8: Administrative Sex - REQUIRED (Usage="R")

        :param msg: HL7v2 message to populate
        :type msg: Message
        :param patient: Business model patient data
        :type patient: PatientData
        :return: None
        :rtype: None
        :raises ValueError: If required fields are missing
        """

        # Navigate to correct HL7v2 hierarchy for PID segment
        patient_group = msg.oru_r01_patient_result.oru_r01_patient

        # PID-1: Set ID
        patient_group.pid.set_id_pid = str(patient.set_id)
        # PID.3 - Patient Identifier List
        patient_group.pid.patient_identifier_list = (
            f"{patient.patient_id}^^^{self.institution.lab_name}"
            f"&{self.institution.lab_finess}&{OID_GIPCPS_TYPE_IDENTIFIANT_STRUCTURE}^PI"
        )
        # PID.5 - Patient Name
        patient_group.pid.patient_name = (
            f"{patient.patient_given_name}" f"^{patient.patient_family_name}^^^^^L"
        )
        # PID-7: Date/Time of Birth
        patient_group.pid.date_time_of_birth = patient.hl7_birth_date
        # PID-8: Administrative Sex
        patient_group.pid.administrative_sex = patient.sex
        # PID.18 - Patient Account Number
        patient_group.pid.patient_account_number = (
            f"{report_id}^^^{self.institution.lab_name}"
            f"&{self.institution.lab_finess}&{OID_GIPCPS_TYPE_IDENTIFIANT_STRUCTURE}^AN"
        )
        # PID.24 - Multiple Birth Indicator
        patient_group.pid.multiple_birth_indicator = "Y"
        # PID.25 - Birth Order
        patient_group.pid.birth_order = "2"
        # PID.30 - Patient Death Indicator#
        patient_group.pid.patient_death_indicator = "N"
        # PID.32 - Identity Reliability Code
        patient_group.pid.identity_reliability_code = "PROV"

    def _populate_con(self, msg: Message, consent: ConsentData) -> None:
        """Populate CON segment

        Only called when is_data_reusable_for_research == True.
        CON segment follows PID in the patient group hierarchy.

        :param msg: HL7v2 message to populate
        :type msg: Message
        :param consent: Consent data from business model
        :type consent: ConsentData
        :return: None
        :rtype: None
        """
        # Navigate to patient group (CON is after PID in profile)
        patient_group = msg.oru_r01_patient_result.oru_r01_patient

        # Add CON segment
        con = patient_group.add_segment("CON")

        # CON.1 - Set ID (R)
        con.con_1 = "1"

        # CON.2 - Consent Type (O) - CWE
        con.con_2 = (
            "1^Release of Information / MR / "
            "Authorization to Disclosure Protected Health Information"
        )

        # CON.3 - Consent Form ID (O)
        con.con_3 = "*"

        # CON.4 - Consent Form Number (O)
        con.con_4 = "00000"

        # CON.5 - Consent Text (RE)
        con.con_5 = "*"

        # CON.6-9 - Empty (subject specific texts)

        # CON.10 - Consent Mode (O) - W = Written
        con.con_10 = "W"

        # CON.11 - Consent Status (R) - A = Active
        con.con_11 = "A"

        # CON.12, 13, 14 - Dates (O) - format YYYYMMDD
        if consent.date_consent:
            date_str = consent.date_consent.strftime("%Y%m%d")
            con.con_12 = date_str  # Discussion Date
            con.con_13 = date_str  # Decision Date
            con.con_14 = date_str  # Effective Date

        # CON.15 - End Date (O) - Empty

        # CON.16 - Subject Competence Indicator (O) - Y
        con.con_16 = "Y"

        # CON.17-23 - Empty

        # CON.24 - Consenter ID (R) - XPN datatype
        # Format: family_name^given_name^^^^^L
        con.con_24 = (
            f"{consent.consenter_family_name}^{consent.consenter_given_name}^^^^^L"
        )

        # CON.25 - Relationship to Subject (R) - 7 = Self
        con.con_25 = "7"

    def _populate_nk1(
        self, msg: Message, next_of_kin_list: List[RelatedPersonData]
    ) -> None:
        """Populate NK1 segments for father/mother.

        NK1 segments come after PID/CON in the patient group hierarchy.
        Creates one NK1 segment per next of kin entry.

        :param msg: HL7v2 message to populate
        :type msg: Message
        :param next_of_kin_list: List of next of kin data (father/mother)
        :type next_of_kin_list: List[RelatedPersonData]
        :return: None
        :rtype: None
        """
        patient_group = msg.oru_r01_patient_result.oru_r01_patient

        for nok in next_of_kin_list:
            nk1 = patient_group.add_segment("NK1")

            # NK1-1: Set ID (1=father, 2=mother)
            nk1.nk1_1 = str(nok.set_id)

            # NK1-2: Name (XPN format: family^given^^^^^L)
            if nok.family_name and nok.given_name:
                nk1.nk1_2 = f"{nok.family_name}^{nok.given_name}^^^^^L"

            # NK1-3: Relationship (FTH=Father, MTH=Mother)
            nk1.nk1_3 = nok.relationship_code

            # NK1-15: Sex
            if nok.sex:
                nk1.nk1_15 = nok.sex

            # NK1-16: Date of Birth (YYYYMMDD)
            if nok.birth_date:
                nk1.nk1_16 = nok.hl7_birth_date

    def _populate_obx_files(
        self,
        msg: Message,
        directory_path: str,
        date_cloture: datetime,
        patient_data: PatientData,
        next_of_kin: Optional[List[RelatedPersonData]] = None,
    ) -> None:
        """Populate OBX segments with file references, grouped by individual.

        Scans the prescription directory recursively and creates OBX segments
        for each file found. Files are grouped by individual:
        - OBX-1 = "1" : main patient files + root-level files (VCF, tar.gz)
        - OBX-1 = "2" : father files
        - OBX-1 = "3" : mother files

        OBX-4 is the index within each individual's group (restarts at 1).

        :param msg: HL7v2 message to populate
        :type msg: Message
        :param directory_path: Directory path to scan for files
        :type directory_path: str
        :param date_cloture: Date de clôture for OBX-14 field
        :type date_cloture: datetime
        :param patient_data: Main patient data for folder identification
        :type patient_data: PatientData
        :param next_of_kin: List of next of kin data (father/mother)
        :type next_of_kin: Optional[List[RelatedPersonData]]
        :return: None
        :rtype: None
        :raises ValueError: If unsupported file extension is found
        """
        if not os.path.exists(directory_path):
            return

        # Build mapping: folder_name → OBX-1 value
        # OBX-1 = "1" for main patient, "2" for father, "3" for mother
        patient_folder = (
            f"{patient_data.patient_family_name}_{patient_data.patient_given_name}"
        )
        folder_to_obx1: Dict[str, str] = {
            patient_folder: "1",  # Main patient
        }

        if next_of_kin:
            for nok in next_of_kin:
                if nok.folder_name:
                    # set_id=1 for father → OBX-1="2", set_id=2 for mother → OBX-1="3"
                    folder_to_obx1[nok.folder_name] = str(nok.set_id + 1)

        # Scan files and group by OBX-1
        files_by_obx1: Dict[str, List[str]] = {"1": [], "2": [], "3": []}

        for root, dirs, filenames in os.walk(directory_path):
            rel_path = os.path.relpath(root, directory_path)

            for filename in filenames:
                # Skip .hl7 files to avoid self-reference
                if filename.endswith(".hl7"):
                    continue

                # Determine OBX-1 based on directory
                if rel_path == ".":
                    # Root-level files → main patient (OBX-1 = "1")
                    obx1 = "1"
                    # Root files: just the filename
                    file_ref = filename
                else:
                    # Files in subdirectory → lookup by folder name
                    top_folder = rel_path.split(os.sep)[0]
                    obx1 = folder_to_obx1.get(top_folder, "1")
                    # Subdirectory files: relative path (folder/filename)
                    file_ref = os.path.join(rel_path, filename)

                files_by_obx1[obx1].append(file_ref)

        # Create ORDER_OBSERVATION group and OBR segment
        order_observation = msg.oru_r01_patient_result.add_group(
            "ORU_R01_ORDER_OBSERVATION"
        )

        obr = order_observation.add_segment("OBR")
        obr.obr_1 = "1"  # Set ID
        obr.obr_2 = "11"  # Placer Order Number
        obr.obr_3 = "11"  # Filler Order Number
        obr.obr_4 = "GenomicsReport^Genomic Analysis Report"

        # Create OBX segments grouped by individual
        for obx1_value in ["1", "2", "3"]:
            files = sorted(files_by_obx1.get(obx1_value, []))
            obx4_index = 1  # OBX-4 counter (increments for each OBX segment)
            files_set = set(files)

            for file_ref in files:
                # Extract filename for format detection (file_ref may include path)
                filename = os.path.basename(file_ref)
                # Two cases: normal data file, or orphaned sidecar
                if filename.endswith(".sha256"):
                    data_ref = file_ref[: -len(".sha256")]
                    if data_ref in files_set:
                        continue
                    sidecar_ref = file_ref
                    hash_b64 = self._read_sha256_b64_from_sidecar(
                        os.path.join(directory_path, file_ref)
                    )
                else:
                    data_ref = file_ref
                    sidecar_ref = file_ref + ".sha256"
                    if sidecar_ref in files_set:
                        hash_b64 = self._read_sha256_b64_from_sidecar(
                            os.path.join(directory_path, sidecar_ref)
                        )
                    else:
                        sidecar_ref = None
                        hash_b64 = self._compute_sha256_b64(
                            os.path.join(directory_path, file_ref)
                        )

                data_filename = os.path.basename(data_ref)
                code, description, system = self._get_file_format_info(data_filename)

                # 1. RP OBX: reference pointer to data file
                observation_group = order_observation.add_group("ORU_R01_OBSERVATION")
                obx = observation_group.add_segment("OBX")
                # OBX-1: Individual number (1=patient, 2=father, 3=mother)
                obx.obx_1 = obx1_value
                # OBX-2: Value Type
                obx.obx_2 = "RP"
                # OBX-3: Observation Identifier (format code)
                obx.obx_3 = f"{code}^{description}^{system}"
                # OBX-4: File index within this individual's group
                obx.obx_4 = str(obx4_index)
                obx4_index += 1
                obx.obx_5 = data_ref
                obx.obx_11 = "F"
                obx.obx_14 = date_cloture.strftime("%Y%m%d%H%M%S")

                # 2. RP OBX: reference pointer to .sha256 sidecar (if present)
                if sidecar_ref is not None:
                    sidecar_filename = os.path.basename(sidecar_ref)
                    s_code, s_desc, s_system = self._get_file_format_info(sidecar_filename)
                    observation_group_s = order_observation.add_group("ORU_R01_OBSERVATION")
                    obx_s = observation_group_s.add_segment("OBX")
                    obx_s.obx_1 = obx1_value
                    obx_s.obx_2 = "RP"
                    obx_s.obx_3 = f"{s_code}^{s_desc}^{s_system}"
                    obx_s.obx_4 = str(obx4_index)
                    obx4_index += 1
                    obx_s.obx_5 = sidecar_ref
                    obx_s.obx_11 = "F"
                    obx_s.obx_14 = date_cloture.strftime("%Y%m%d%H%M%S")

                # 3. ED OBX: embedded SHA-256 hash of the data file
                observation_group_ed = order_observation.add_group("ORU_R01_OBSERVATION")
                obx_ed = observation_group_ed.add_segment("OBX")
                obx_ed.obx_1 = obx1_value
                obx_ed.obx_2 = "ED"
                obx_ed.obx_3 = "operation_3098^SHA256 Checksum^http://edamontology.org"
                obx_ed.obx_4 = str(obx4_index)
                obx4_index += 1
                obx_ed.obx_5 = f"^TXT^SHA256^Base64^{hash_b64}"
                obx_ed.obx_11 = "F"
                obx_ed.obx_14 = date_cloture.strftime("%Y%m%d%H%M%S")

    def _populate_prt(
        self,
        msg: Message,
        rcp: CareTeamData,
        person: PersonData,
        analysis: ProcedureData,
        timing: PeriodData,
    ) -> None:
        """Populate complete PRT segment using hl7apy according to Excel specifications.

        :param msg: HL7v2 message to populate
        :type msg: Message
        :param rcp: RCP data from business model
        :type rcp: CareTeamData
        :param person: Person data from business model
        :type person: PersonData
        :param analysis: Analysis data from business model
        :type analysis: ProcedureData
        :param timing: Timing data from business model
        :type timing: PeriodData
        :return: None
        :rtype: None
        """
        try:
            # Navigate to correct HL7v2 hierarchy for PRT segment
            order_observation = msg.oru_r01_patient_result.oru_r01_order_observation
            observation_group = order_observation.oru_r01_observation

            # PRT-1: Participation Instance Id (EI) - Complete format with authority
            if rcp and rcp.rcp_nom and rcp.rcp_id:
                observation_group.prt.prt_1 = (
                    f"{rcp.rcp_nom}^{rcp.rcp_id}^1.2.250.1.710.1.2.5.3^ISO"
                )

            # PRT-2: Action Code (ID) - Fixed value from specs
            observation_group.prt.prt_2 = "AD"

            # PRT-3: Action Reason (CWE) - Empty per specs
            # Intentionally left empty

            # PRT-4: Role of Participation (CWE) - Fixed hardcoded values per Excel specs
            observation_group.prt.prt_4 = "MDIR^Responsable médical^HL70912"

            # PRT-5: Person (XCN) - Multiple persons using hl7apy native repetitions
            if person:
                person_entries = []
                if person.prescripteur:
                    person_entries.append(
                        f"{person.prescripteur}^^^^^^MD^1.2.250.1.710.1.5.1"
                    )
                if person.membre_rcp:
                    person_entries.append(
                        f"{person.membre_rcp}^^^^^^MD^1.2.250.1.710.1.5.1"
                    )

                # Add each person entry as a separate PRT-5 repetition
                for xcn_value in person_entries:
                    prt_5_field = observation_group.prt.add_field(
                        "PRT_5"
                    )  # Add repetition
                    prt_5_field.value = xcn_value  # Set ER7 value

            # PRT-6: Person Provider Type (CWE) - Empty per specs
            # Intentionally left empty

            # PRT-7: Organization Unit Type (CWE) - Empty per specs
            # Intentionally left empty

            # PRT-8: Organization (XON) - Sending institution
            observation_group.prt.participation_organization = (
                f"{self.institution.lab_name}^^^^^{self.institution.lab_finess}&{OID_GIPCPS_TYPE_IDENTIFIANT_STRUCTURE}"
            )

            # PRT-9: Location (PL) - Empty per specs
            # Intentionally left empty

            # PRT-10: Device (EI) - analysis_ID using hl7apy native EI structure
            if analysis and analysis.analysis_id:
                observation_group.prt.prt_10 = analysis.analysis_id

            # PRT-11: Begin Date/Time (DTM) - Using hl7apy native DTM handling
            if timing and timing.start:
                observation_group.prt.prt_11.value = timing.start.strftime("%Y%m%d%H%M")

            # PRT-12: End Date/Time (DTM) - Using hl7apy native DTM handling
            if timing and timing.end:
                observation_group.prt.prt_12.value = timing.end.strftime("%Y%m%d%H%M")

        except Exception as e:
            # If adding PRT fails, print debug info and continue
            print(f"DEBUG: Failed to add PRT segment with hl7apy: {e}")
            print(
                f"DEBUG: Available segments in message: {[s.name for s in msg.children]}"
            )
            raise

    def _compute_sha256_b64(self, filepath: str) -> str:
        """Compute SHA-256 of a file and return its hex digest Base64-encoded.

        :param filepath: Full path to the file
        :type filepath: str
        :return: Base64-encoded hex digest
        :rtype: str
        """
        digest = hashlib.sha256(open(filepath, "rb").read()).hexdigest()
        return base64.b64encode(digest.encode()).decode()

    def _read_sha256_b64_from_sidecar(self, sidecar_path: str) -> str:
        """Read SHA-256 hex digest from a .sha256 sidecar file and return Base64-encoded.

        :param sidecar_path: Full path to the .sha256 sidecar file
        :type sidecar_path: str
        :return: Base64-encoded hex digest
        :rtype: str
        """
        with open(sidecar_path, encoding="utf-8") as f:
            content = f.read().strip()
        hash_value = content.split("  ")[0]
        return base64.b64encode(hash_value.encode()).decode()

    def _get_file_format_info(self, filename: str) -> Tuple[str, str, str]:
        """Get format code, description and system for a given filename.

        :param filename: The filename to get format info for
        :type filename: str
        :return: Tuple of (code, description, system)
        :rtype: Tuple[str, str, str]
        :raises ValueError: If file extension is not supported
        """
        # Handle compound extension .tar.gz first
        if filename.lower().endswith(".tar.gz"):
            extension = "tar.gz"
        else:
            # Get single extension
            parts = filename.lower().split(".")
            if len(parts) < 2:
                raise ValueError(
                    f"Unsupported file extension: {filename} (no extension)"
                )
            extension = parts[-1]

        # Look up format info
        format_info = self.FORMAT_MAPPING.get(extension)
        if not format_info:
            raise ValueError(f"Unsupported file extension: .{extension}")

        return format_info["code"], format_info["description"], format_info["system"]

    def generate_and_seal(
        self,
        parsed_report_data: CompositionData,
        directory: "Path",
        name: str,
    ) -> "Path":
        """Generate an HL7v2 message, write it to disk, and "seal" it
        with a .hl7.sha256 checksum file.

        :param parsed_report_data: Business model containing all parsed report data
        :type parsed_report_data: CompositionData
        :param directory: Directory where the .hl7 and .hl7.sha256 files will be written
        :type directory: Path
        :param name: Prescription name used as the file stem (e.g. "DEMO-PRESCRIPTION-001")
        :type name: str
        :return: Path to the written .hl7 file
        :rtype: Path
        """
        from pathlib import Path as _Path

        directory = _Path(directory)
        hl7_message = self.generate(parsed_report_data, files_directory=str(directory))

        hl7_file = directory / f"{name}.hl7"
        hl7_file.write_text(hl7_message, encoding="utf-8")

        # Always force-recalculate the .hl7.sha256
        digest = hashlib.sha256(hl7_file.read_bytes()).hexdigest()
        (directory / f"{name}.hl7.sha256").write_text(f"{digest}  {hl7_file.name}\n", encoding="utf-8")

        return hl7_file

    def validate_message(self, hl7_message: str) -> bool:
        """Basic validation of generated HL7v2 message.

        IMPORTANT: This is just basic manual validation for POC.
        In production, this should use the profile file oru_r01_lab36.xml
        to validate conformance against the actual profile constraints
        via hl7apy's native validation: msg.validate(profile).

        :param hl7_message: HL7v2 message string
        :type hl7_message: str
        :return: True if message appears valid
        :rtype: bool
        """
        try:
            # Check basic structure
            lines = hl7_message.split("\r")

            # Should have at least MSH and PID segments
            if len(lines) < 2:
                return False

            # First line should be MSH
            if not lines[0].startswith("MSH|"):
                return False

            # Second line should be PID
            if not lines[1].startswith("PID|"):
                return False

            return True

        except Exception:
            return False

    @staticmethod
    def _format_to_hl7_timestamp(dt: datetime) -> str:
        """
        Format : YYYYMMDDHHMMSS.mmm+ZZZZ
        Exemple : 20240712153123.456+0200

        :param dt: datetime with timezone (aware)
        :raises ValueError: if dt is not timezone-aware (tzinfo=None)
        """
        if dt.tzinfo is None or dt.utcoffset() is None:
            raise ValueError("datetime must be timezone-aware (tzinfo is required)")

        base = dt.strftime("%Y%m%d%H%M%S")
        millis = f".{round(dt.microsecond / 1000):03d}"
        offset = dt.strftime("%z")

        return f"{base}{millis}{offset}"
