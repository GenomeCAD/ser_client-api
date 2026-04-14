"""
SeqOIA local data parser — GLeaves JSON format.
"""

import importlib.resources
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import jsonschema

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
    if field not in data:
        raise ValueError(f"Missing required field: '{field}'")
    value = data[field]
    if not value:
        raise ValueError(f"Required field '{field}' is empty or None")
    return value


def _get_optional_field(data: Dict[str, Any], field: str, default: Any = None) -> Any:
    if field not in data:
        return default
    value = data[field]
    if not value:
        return default
    return value


class SeqoiaParser:
    """Input adapter for GLeaves JSON API (SeqOIA).

    Isolates business models from external JSON structure changes.
    """

    _schema = None  # cached at class level

    @classmethod
    def _get_schema(cls) -> Dict[str, Any]:
        if cls._schema is None:
            schema_file = (
                importlib.resources.files("ser_client_api.hl7v2.seqoia")
                / "schemas"
                / "prescriptions_schema_completed_v2.json"
            )
            cls._schema = json.loads(schema_file.read_text(encoding="utf-8"))
        return cls._schema

    def validate(self, json_data: Dict[str, Any]) -> None:
        """Validate json_data against the SeqOIA JSON schema."""
        try:
            jsonschema.validate(instance=json_data, schema=self._get_schema())
        except jsonschema.ValidationError as e:
            raise ValueError(f"SeqOIA JSON schema validation failed: {e.message}")

    def parse(self, json_data: Dict[str, Any]) -> CompositionData:
        self.validate(json_data)
        try:
            patient = self._parse_patient(json_data)
            rcp_data = self._parse_rcp_data(json_data)
            person_data = self._parse_person_data(json_data)
            analysis_data = self._parse_analysis_data(json_data)
            timing_data = self._parse_timing_data(json_data)
            preindication_data = self._parse_preindication_data(json_data)
            resultat_data = self._parse_resultat_data(json_data)
            consent_data = self._parse_consent(json_data)
            next_of_kin_data = self._parse_next_of_kin(json_data)

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

        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Failed to parse GLeaves JSON: {e}")

    def _parse_patient(self, json_data: Dict[str, Any]) -> PatientData:
        patients_array = _get_required_field(json_data, "patients")
        main_patient_entry = patients_array[0]
        main_patient_info = _get_required_field(main_patient_entry, "patient")

        birth_date = None
        birth_date_str = _get_optional_field(main_patient_info, "date_naissance")
        if birth_date_str:
            try:
                birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                pass

        patient_id_obj = _get_required_field(main_patient_info, "id")
        main_patient_id = _get_required_field(patient_id_obj, "value")
        main_patient_sex = _get_required_field(main_patient_info, "sexe")

        date_prelevement_ms = _get_required_field(main_patient_entry, "date_prelevement")
        date_prelevement = datetime.fromtimestamp(date_prelevement_ms / 1000, tz=timezone.utc)
        id_anon = _get_optional_field(main_patient_entry, "id_anon")

        return PatientData(
            set_id=1,
            patient_id=main_patient_id,
            patient_given_name=_get_required_field(main_patient_info, "prenom"),
            patient_family_name=_get_required_field(main_patient_info, "nom"),
            birth_date=birth_date,
            sex=main_patient_sex,
            date_prelevement=date_prelevement,
            id_anon=id_anon,
        )

    def _parse_rcp_data(self, json_data: Dict[str, Any]) -> CareTeamData:
        preindication = _get_required_field(json_data, "preindication")
        return CareTeamData(
            rcp_id=_get_required_field(preindication, "rcp_id"),
            rcp_nom=_get_required_field(preindication, "rcp_nom"),
        )

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
        if not results:
            return ObservationData(membre_lmg=None)
        membre_lmg = _get_optional_field(results[0], "MembreLMG", None)
        return ObservationData(membre_lmg=membre_lmg)

    def _parse_person_data(self, json_data: Dict[str, Any]) -> PersonData:
        return PersonData(
            prescripteur=_get_required_field(json_data, "prescripteur"),
            membre_rcp=_get_required_field(json_data, "membreRCP"),
        )

    def _parse_analysis_data(self, json_data: Dict[str, Any]) -> ProcedureData:
        analysis_info = _get_required_field(json_data, "analysis_info")
        return ProcedureData(analysis_id=_get_required_field(analysis_info, "analysis_ID"))

    def _parse_timing_data(self, json_data: Dict[str, Any]) -> PeriodData:
        date_creation_ms = _get_required_field(json_data, "date_creation")
        date_cloture_ms = _get_required_field(json_data, "date_cloture")
        return PeriodData(
            start=datetime.fromtimestamp(date_creation_ms / 1000),
            end=datetime.fromtimestamp(date_cloture_ms / 1000),
        )

    def _parse_consent(self, json_data: Dict[str, Any]) -> ConsentData:
        patients_array = _get_required_field(json_data, "patients")
        patient_entry = patients_array[0]

        is_reusable = _get_optional_field(patient_entry, "is_data_reusable_for_research", False)
        date_consent_ms = _get_optional_field(patient_entry, "dateConsent")

        date_consent = None
        if date_consent_ms:
            date_consent = datetime.fromtimestamp(date_consent_ms / 1000, tz=timezone.utc)

        main_patient = _get_required_field(patient_entry, "patient")
        return ConsentData(
            is_data_reusable_for_research=is_reusable,
            date_consent=date_consent,
            consenter_family_name=_get_optional_field(main_patient, "nom"),
            consenter_given_name=_get_optional_field(main_patient, "prenom"),
        )

    def _parse_next_of_kin(self, json_data: Dict[str, Any]) -> Optional[List[RelatedPersonData]]:
        patients_array = _get_optional_field(json_data, "patients", [])
        if len(patients_array) < 2:
            return None

        relationship_map = {
            "père": (1, "FTH", "father"),
            "mère": (2, "MTH", "mother"),
        }
        next_of_kin_list = []

        for idx in range(1, len(patients_array)):
            patient_entry = patients_array[idx]
            lien_data = _get_optional_field(patient_entry, "lien", {})

            if isinstance(lien_data, dict):
                lien_key = lien_data.get("key", "").lower()
            else:
                lien_key = str(lien_data).lower() if lien_data else ""

            patient_info = _get_optional_field(patient_entry, "patient")
            if not patient_info or lien_key not in relationship_map:
                continue

            set_id, rel_code, rel_display = relationship_map[lien_key]

            birth_date = None
            birth_date_str = _get_optional_field(patient_info, "date_naissance")
            if birth_date_str:
                try:
                    birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
                except (ValueError, TypeError):
                    pass

            patient_id = None
            patient_id_obj = _get_optional_field(patient_info, "id")
            if patient_id_obj:
                patient_id = _get_optional_field(patient_id_obj, "value")

            id_anon = _get_optional_field(patient_entry, "id_anon")

            next_of_kin_list.append(RelatedPersonData(
                set_id=set_id,
                relationship_code=rel_code,
                relationship_display=rel_display,
                family_name=_get_optional_field(patient_info, "nom"),
                given_name=_get_optional_field(patient_info, "prenom"),
                birth_date=birth_date,
                sex=_get_optional_field(patient_info, "sexe"),
                patient_id=patient_id,
                id_anon=id_anon,
            ))

        return next_of_kin_list if next_of_kin_list else None

    @classmethod
    def parse_from_file(cls, file_path: str) -> CompositionData:
        with open(file_path, encoding="utf-8") as f:
            json_data = json.load(f)
        return cls().parse(json_data)


def get_parser() -> SeqoiaParser:
    return SeqoiaParser()
