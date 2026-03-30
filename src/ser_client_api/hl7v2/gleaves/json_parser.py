"""
JSON Parser - Input Adapter
Transforms external GLeaves JSON format into business models
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

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


def _get_required_field(data: Dict[str, Any], field: str) -> Any:
    """Get required field and raise KeyError if missing or empty.

    :param data: Dictionary to check
    :param field: Field name to get
    :return: Field value
    :raises KeyError: If field is missing, None, or empty
    """
    if field not in data:
        raise KeyError(f"Missing required field: '{field}'")

    value = data[field]
    if not value:
        raise KeyError(f"Required field '{field}' is empty or None")

    return value


def _get_optional_field(data: Dict[str, Any], field: str, default: Any = None) -> Any:
    """Get optional field with default value if missing or empty.

    :param data: Dictionary to check
    :param field: Field name to get
    :param default: Default value if field is missing or empty
    :return: Field value or default
    """
    if field not in data:
        return default

    value = data[field]
    if not value:
        return default

    return value


class GleavesJSONParser:
    """Input adapter for GLeaves JSON API.

    Isolates business models from external JSON structure changes.
    """

    def parse(self, json_data: Dict[str, Any]) -> CompositionData:
        """Parse GLeaves JSON into business models.

        :param json_data: Raw JSON from GLeaves API
        :type json_data: Dict[str, Any]
        :return: Business model
        :rtype: CompositionData
        :raises ValueError: If required fields are missing
        """
        try:
            # Parse patient information
            patient = self._parse_patient(json_data)

            # Parse RCP information
            rcp_data = self._parse_rcp_data(json_data)

            # Parse Person information
            person_data = self._parse_person_data(json_data)

            # Parse Analysis information
            analysis_data = self._parse_analysis_data(json_data)

            # Parse Timing information
            timing_data = self._parse_timing_data(json_data)

            # Parse pre-indication information
            preindication_data = self._parse_preindication_data(json_data)

            # Parse result information
            resultat_data = self._parse_resultat_data(json_data)

            # Parse consent information
            consent_data = self._parse_consent(json_data)

            # Parse next of kin information (father/mother)
            next_of_kin_data = self._parse_next_of_kin(json_data)

            # Create aggregate root
            return CompositionData(
                report_id=json_data["_id"],
                patient=patient,
                person=person_data,
                analysis=analysis_data,
                timing=timing_data,
                rcp=rcp_data,
                preindication=preindication_data,
                results=resultat_data,
                consent=consent_data,
                next_of_kin=next_of_kin_data,
            )

        except KeyError as e:
            raise ValueError(f"Missing required JSON field: {e}")
        except Exception as e:
            raise ValueError(f"Failed to parse GLeaves JSON: {e}")

    def _parse_patient(self, json_data: Dict[str, Any]) -> PatientData:
        """Extract and transform patient information from JSON.

        :param json_data: Raw JSON from GLeaves API
        :type json_data: Dict[str, Any]
        :return: Parsed patient data
        :rtype: PatientData
        :raises ValueError: If no patient data found
        """

        # Patient data is nested in patients array
        patients_array = _get_required_field(json_data, "patients")

        # Get main patient (index 0)
        # Next of kin (father/mother) are handled in _parse_next_of_kin()
        main_patient_info = _get_required_field(patients_array[0], "patient")

        # Parse birth date (format: "YYYY-MM-DD")
        birth_date = datetime.strptime(
            _get_required_field(main_patient_info, "date_naissance"), "%Y-%m-%d"
        ).date()

        patient_id_obj = _get_required_field(main_patient_info, "id")
        main_patient_id = _get_required_field(patient_id_obj, "value")

        main_patient_sex = _get_required_field(main_patient_info, "sexe")

        date_prelevement_ms = _get_required_field(main_patient_info, "date_prelevement")
        date_prelevement = datetime.fromtimestamp(
            date_prelevement_ms / 1000, tz=timezone.utc
        )

        return PatientData(
            set_id=1,  # Force 1 for single patient
            patient_id=main_patient_id,
            patient_given_name=_get_required_field(main_patient_info, "prenom"),
            patient_family_name=_get_required_field(main_patient_info, "nom"),
            birth_date=birth_date,
            sex=main_patient_sex,
            date_prelevement=date_prelevement,
        )

    def _parse_rcp_data(self, json_data: Dict[str, Any]) -> CareTeamData:
        """Extract RCP information from JSON.

        :param json_data: Raw JSON from GLeaves API
        :type json_data: Dict[str, Any]
        :return: Parsed RCP data or None if not available
        :rtype: CareTeamData
        """
        preindication = _get_required_field(json_data, "preindication")

        rcp_id = _get_required_field(preindication, "rcp_id")
        rcp_nom = _get_required_field(preindication, "rcp_nom")

        return CareTeamData(rcp_id=rcp_id, rcp_nom=rcp_nom)

    def _parse_preindication_data(self, json_data: Dict[str, Any]) -> ConditionData:
        preindication = _get_required_field(json_data, "preindication")
        return ConditionData(
            name=_get_required_field(preindication, "name"),
            key=_get_required_field(preindication, "key"),
            cat_name=_get_required_field(preindication, "catname"),
            cat_key=_get_required_field(preindication, "catkey"),
        )

    def _parse_resultat_data(self, json_data: Dict[str, Any]) -> ObservationData:
        results = _get_optional_field(json_data, "resultats", [])

        # Handle missing resultats array (6.7% of prescriptions)
        if not results:
            return ObservationData(membre_lmg=None)

        # Handle missing MembreLMG in first result (20% of prescriptions)
        membre_lmg = _get_optional_field(results[0], "MembreLMG", None)
        return ObservationData(membre_lmg=membre_lmg)

    def _parse_person_data(self, json_data: Dict[str, Any]) -> PersonData:
        """Extract Person information from JSON.

        :param json_data: Raw JSON from GLeaves API
        :type json_data: Dict[str, Any]
        :return: Parsed Person data or None if no person fields available
        :rtype: PersonData
        """
        prescripteur = _get_required_field(json_data, "prescripteur")
        membre_rcp = _get_required_field(json_data, "membreRCP")

        return PersonData(prescripteur=prescripteur, membre_rcp=membre_rcp)

    def _parse_analysis_data(self, json_data: Dict[str, Any]) -> ProcedureData:
        """Extract Analysis information from JSON.

        :param json_data: Raw JSON from GLeaves API
        :type json_data: Dict[str, Any]
        :return: Parsed Analysis data or None if not available
        :rtype: ProcedureData
        """
        analysis_info = _get_required_field(json_data, "analysis_info")
        analysis_id = _get_required_field(analysis_info, "analysis_ID")

        return ProcedureData(analysis_id=analysis_id)

    def _parse_timing_data(self, json_data: Dict[str, Any]) -> PeriodData:
        """Extract Timing information from JSON.

        :param json_data: Raw JSON from GLeaves API
        :type json_data: Dict[str, Any]
        :return: Parsed Timing data or None if no timing fields available
        :rtype: PeriodData
        """
        # date_creation treated as required until proven otherwise in production
        date_creation_ms = _get_required_field(json_data, "date_creation")

        # date_cloture is required (100% presence confirmed)
        date_cloture_ms = _get_required_field(json_data, "date_cloture")

        # Convert timestamps from milliseconds to datetime
        date_creation = datetime.fromtimestamp(date_creation_ms / 1000)
        date_cloture = datetime.fromtimestamp(date_cloture_ms / 1000)

        return PeriodData(start=date_creation, end=date_cloture)

    def _parse_consent(self, json_data: Dict[str, Any]) -> ConsentData:
        """Extract consent information from JSON.

        CON segment only generated when is_data_reusable_for_research=True.

        :param json_data: Raw JSON from GLeaves API
        :type json_data: Dict[str, Any]
        :return: Parsed Consent data
        :rtype: ConsentData
        """
        patients_array = _get_required_field(json_data, "patients")
        patient_entry = patients_array[0]

        # Consent fields are at patient_entry level, not nested in "patient"
        is_reusable = _get_optional_field(
            patient_entry, "is_data_reusable_for_research", False
        )
        date_consent_ms = _get_optional_field(patient_entry, "dateConsent")

        date_consent = None
        if date_consent_ms:
            date_consent = datetime.fromtimestamp(
                date_consent_ms / 1000, tz=timezone.utc
            )

        # Get patient name for CON.24 (Consenter ID) - patient consents for self
        main_patient = _get_required_field(patient_entry, "patient")
        family_name = _get_optional_field(main_patient, "nom")
        given_name = _get_optional_field(main_patient, "prenom")

        return ConsentData(
            is_data_reusable_for_research=is_reusable,
            date_consent=date_consent,
            consenter_family_name=family_name,
            consenter_given_name=given_name,
        )

    def _parse_next_of_kin(
        self, json_data: Dict[str, Any]
    ) -> Optional[List[RelatedPersonData]]:
        """Extract Next of Kin information from patients array.

        Parses patients[1] (father) and patients[2] (mother) if present.
        Returns None if only main patient exists (backwards compatible).

        :param json_data: Raw JSON from GLeaves API
        :type json_data: Dict[str, Any]
        :return: List of RelatedPersonData or None if no next of kin
        :rtype: Optional[List[RelatedPersonData]]
        """
        patients_array = _get_optional_field(json_data, "patients", [])

        # No next of kin if only main patient
        if len(patients_array) < 2:
            return None

        # Mapping lien key → (set_id, relationship_code)
        relationship_map = {
            "père": (1, "FTH"),
            "mère": (2, "MTH"),
        }

        next_of_kin_list = []

        # Process patients[1:] (skip main patient at index 0)
        for idx in range(1, len(patients_array)):
            patient_entry = patients_array[idx]
            lien_data = _get_optional_field(patient_entry, "lien", {})

            # Handle object format: {"key": "father", "name": "pere"}
            if isinstance(lien_data, dict):
                lien_key = lien_data.get("key", "").lower()
            else:
                # Backwards compatibility: string format
                lien_key = str(lien_data).lower() if lien_data else ""

            patient_info = _get_optional_field(patient_entry, "patient")

            if not patient_info or lien_key not in relationship_map:
                continue

            set_id, rel_code = relationship_map[lien_key]

            # Parse optional birth date
            birth_date = None
            birth_date_str = _get_optional_field(patient_info, "date_naissance")
            if birth_date_str:
                try:
                    birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
                except (ValueError, TypeError):
                    pass

            # Get patient ID if available
            patient_id = None
            patient_id_obj = _get_optional_field(patient_info, "id")
            if patient_id_obj:
                patient_id = _get_optional_field(patient_id_obj, "value")

            nok = RelatedPersonData(
                set_id=set_id,
                relationship_code=rel_code,
                family_name=_get_optional_field(patient_info, "nom"),
                given_name=_get_optional_field(patient_info, "prenom"),
                birth_date=birth_date,
                sex=_get_optional_field(patient_info, "sexe"),
                patient_id=patient_id,
            )
            next_of_kin_list.append(nok)

        return next_of_kin_list if next_of_kin_list else None

    @classmethod
    def parse_from_file(cls, file_path: str) -> CompositionData:
        """Convenience method to parse JSON directly from file.

        :param file_path: Path to JSON file
        :type file_path: str
        :return: Parsed business model
        :rtype: CompositionData
        """
        parser = cls()

        with open(file_path, encoding="utf-8") as f:
            json_data = json.load(f)

        return parser.parse(json_data)


# Convenience function for tests
def parse_json_to_genomics_report(json_data: Dict[str, Any]) -> CompositionData:
    """Parse JSON data to GenomicsReport (convenience function for tests).

    :param json_data: JSON dictionary
    :type json_data: Dict[str, Any]
    :return: Parsed business model
    :rtype: CompositionData
    """
    parser = GleavesJSONParser()
    return parser.parse(json_data)
