"""Shared fixtures for ser_client_api tests."""

import pytest
from pathlib import Path

import ser_client_api
from ser_client_api.hl7v2 import HL7v2Generator, InstitutionConfig
from ser_client_api.hl7v2.gleaves import GleavesJSONParser

# Minimal valid prescription JSON : trio case (patient + father + mother)
MINIMAL_PRESCRIPTION_JSON = {
    "_id": "67cecdfdb4cffa55e8707002",
    "preindication": {
        "catname": "Maladie rare",
        "catkey": "p1",
        "name": "Angiodèmes bradykiniques héréditaires",
        "key": "p1-sp60",
        "rcp_id": "5e71f8b3efaa9b6f5a729fa6",
        "rcp_nom": "MaRIH-NEUTROPENIES",
    },
    "patients": [
        {
            "patient": {
                "id": {"type": "IPP", "value": "IPP-TEST-001"},
                "date_naissance": "1980-06-15",
                "sexe": "F",
                "nom": "DUPONT",
                "nom_naissance": "DUPONT",
                "prenom": "MARIE",
                "date_prelevement": 1741651200000,
            },
            "lien": {"key": "patient", "name": "Patient"},
            "is_data_reusable_for_research": True,
            "dateConsent": 1741940668351,
            "id_anon": "TESTID",
            "resultat_compte_rendu_gleaves": {},
        },
        {
            "patient": {
                "id": {"type": "IPP", "value": "IPP-TEST-002"},
                "date_naissance": "1955-03-22",
                "sexe": "M",
                "nom": "DUPONT",
                "nom_naissance": "DUPONT",
                "prenom": "JEAN",
            },
            "lien": {"key": "père", "name": "Père"},
            "is_data_reusable_for_research": False,
            "date_prelevement": 1741651200000,
            "id_anon": "TESTID2",
        },
        {
            "patient": {
                "id": {"type": "IPP", "value": "IPP-TEST-003"},
                "date_naissance": "1958-11-04",
                "sexe": "F",
                "nom": "MARTIN",
                "nom_naissance": "MARTIN",
                "prenom": "CLAIRE",
            },
            "lien": {"key": "mère", "name": "Mère"},
            "is_data_reusable_for_research": False,
            "date_prelevement": 1741651200000,
            "id_anon": "TESTID3",
        },
    ],
    "prescripteur": "4031575",
    "membreRCP": "541351",
    "analysis_info": {
        "analysis_ID": "55014",
        "date_fin_analyse": "08042025",
    },
    "date_creation": 1741606397865,
    "date_cloture": 1745498322775,
    "resultats": [
        {
            "type": "cr_biologique",
            "MembreLMG": "541351",
            "filename": "CR_Test.pdf",
        }
    ],
}


@pytest.fixture(scope="session")
def institution():
    return InstitutionConfig(
        lab_name="TEST LAB",
        lab_finess="1000000001",
        facility_name="TEST FACILITY",
        facility_finess="1000000002",
        facility_finess_ej="000000002",
        software_name="test",
        software_product_information="test^1.0^1.0",
        receiving_application="TEST APP^123^1.2.3",
        receiving_facility="TEST FACILITY^456^1.2.3",
        message_profile_name="Message au format CAD ORU_R01 v1",
        message_profile_oid="1.2.250.1.710.1.15.9.1.1.1",
        local_data_parser="ser_client_api.hl7v2.seqoia.parser",
    )


@pytest.fixture(scope="session")
def generator(institution):
    profiles_dir = (
        Path(ser_client_api.__file__).parent
        / "hl7v2" / "profiles" / "gipcad" / "v000_compiled"
    )
    return HL7v2Generator(
        profile_path=str(profiles_dir / "oru_r01_lab36"),
        institution=institution,
    )


@pytest.fixture(scope="session")
def composition():
    parser = GleavesJSONParser()
    return parser.parse(MINIMAL_PRESCRIPTION_JSON)
