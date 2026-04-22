"""Integration tests for Level 3 ML similarity - require [ml] extras.

Run with:
    pip install "ser-client-api[ml]"
    pytest tests/integration/test_similarity_ml.py -v

Skipped automatically when gliner, sentence-transformers, or numpy are absent.
"""

import pytest

gliner = pytest.importorskip("gliner", reason="gliner not installed - skipping ML integration tests")
sentence_transformers = pytest.importorskip(
    "sentence_transformers", reason="sentence-transformers not installed - skipping ML integration tests"
)
numpy = pytest.importorskip("numpy", reason="numpy not installed - skipping ML integration tests")

from ser_client_api.hl7v2.seqoia.parser import SeqoiaParser  # noqa: E402
from ser_client_api.ml.seqoia.similarity import (  # noqa: E402
    _get_ref_index,
    normalize,
    remove_entities,
    translate_relationship_by_similarity,
)


def _make_prescription(lien_name: str) -> dict:
    """Minimal prescription with one 'autre' related person."""
    return {
        "_id": "test-id",
        "preindication": {
            "catname": "Cat",
            "catkey": "p1",
            "name": "Test",
            "key": "p1-sp60",
            "rcp_id": "r1",
            "rcp_nom": "RCP",
        },
        "patients": [
            {
                "patient": {
                    "id": {"type": "IPP", "value": "IPP-001"},
                    "date_naissance": "1990-01-01",
                    "sexe": "F",
                    "nom": "TEST",
                    "nom_naissance": "TEST",
                    "prenom": "PATIENT",
                },
                "lien": {"key": "patient", "name": "Patient"},
                "is_data_reusable_for_research": False,
                "date_prelevement": 1741651200000,
                "id_anon": "IDMAIN",
            },
            {
                "patient": {
                    "id": {"type": "IPP", "value": "IPP-002"},
                    "date_naissance": "1965-06-15",
                    "sexe": "M",
                    "nom": "AUTRE",
                    "nom_naissance": "AUTRE",
                    "prenom": "PERSON",
                },
                "lien": {"key": "autre", "name": lien_name},
                "is_data_reusable_for_research": False,
                "date_prelevement": 1741651200000,
                "id_anon": "IDNOK",
            },
        ],
        "prescripteur": "123",
        "membreRCP": "456",
        "analysis_info": {"analysis_ID": "9999", "date_fin_analyse": "01042026"},
        "date_creation": 1741606397865,
        "date_cloture": 1745498322775,
        "resultats": [],
    }


class TestReferentialIndex:
    def test_index_loads_and_has_expected_size(self):
        ref = _get_ref_index()
        assert len(ref) == 101

    def test_index_entries_have_required_keys(self):
        ref = _get_ref_index()
        for entry in ref:
            assert "hl7v3_code" in entry
            assert "display" in entry
            assert "display_normalized" in entry
            assert "_embedding" in entry

    def test_embeddings_are_unit_vectors(self):
        import numpy as np

        ref = _get_ref_index()
        for entry in ref[:10]:
            norm = float(np.linalg.norm(entry["_embedding"]))
            assert abs(norm - 1.0) < 1e-4


class TestTranslateRelationshipBySimilarity:
    """End-to-end tests against real models - cases that should always exceed the 0.75 threshold."""

    @pytest.mark.parametrize(
        "libelle,expected_code",
        [
            ("frère", "BRO"),
            ("soeur", "SIS"),
            ("père", "FTH"),
            ("mère", "MTH"),
            ("fils", "SON"),
            ("fille", "DAU"),
            # hyphens -> spaces in normalize(), so these hit the same referential entries
            ("grand-père", "GRFTH"),
            ("grand-mère", "GRMTH"),
            ("arrière-grand-père", "GGRFTH"),
            ("demi-frère", "HBRO"),
            ("demi-sœur", "HSIS"),
            # belle-mere/beau-pere map to in-law codes (stepparent codes have no French Display entry)
            ("belle-mère", "MTHINLAW"),
            ("beau-père", "FTHINLAW"),
        ],
    )
    def test_clear_kinship_terms(self, libelle, expected_code):
        result = translate_relationship_by_similarity(libelle)
        assert result == expected_code, f"Expected {expected_code} for {libelle!r}, got {result!r}"

    def test_with_pii_noise(self):
        result = translate_relationship_by_similarity("frère de Jean-Pierre Dupont")
        assert result == "BRO"

    def test_maternelle_suffix_resolves(self):
        """'maternelle' expands to 'par la mere' in normalize(), pushing the embedding toward MUNCLE."""
        result = translate_relationship_by_similarity("oncle maternel")
        assert result is not None
        assert result in {"UNCLE", "MUNCLE"}

    # ------------------------------------------------------------------
    # Real-world L3 cases - strings that fall through L1 and L2 in the
    # SeqOIA cascade and are expected to reach the ML similarity layer.
    # ------------------------------------------------------------------

    def test_masculine_cousin_with_pii(self):
        """'cousin de X' - L2 only has a feminine 'cousine de' pattern; masculine reaches L3."""
        result = translate_relationship_by_similarity("cousin de Paul Dupont")
        assert result == "COUSN"

    def test_cousin_issu_de_germains(self):
        """French legal term for second cousin - no L1/L2 entry."""
        result = translate_relationship_by_similarity("cousin issu de germains")
        assert result == "COUSN"

    def test_cousin_germain_with_directional_prose(self):
        """'cousin germain par le côté maternel' - normalize expands 'maternel' -> 'par mere'."""
        result = translate_relationship_by_similarity("cousin germain par le côté maternel")
        assert result == "MCOUSN"

    def test_grand_oncle_with_pii(self):
        """'grand-oncle de Jean' - PII removed, no direction -> downgraded to generic UNCLE."""
        result = translate_relationship_by_similarity("grand-oncle de Jean")
        assert result == "UNCLE"

    def test_cousine_germaine_with_family_name(self):
        """'cousine germaine de la famille Martin' - no direction -> downgraded to generic COUSN."""
        result = translate_relationship_by_similarity("cousine germaine de la famille Martin")
        assert result == "COUSN"

    def test_niece_par_alliance_below_threshold(self):
        """'nièce par alliance' - 'alliance' adds enough noise that similarity falls below threshold."""
        result = translate_relationship_by_similarity("nièce par alliance")
        assert result is None

    def test_unrelated_text_returns_none(self):
        result = translate_relationship_by_similarity("xkcd zazdzy plouf", threshold=0.75)
        assert result is None

    def test_empty_string_returns_none(self):
        assert translate_relationship_by_similarity("") is None

    def test_custom_threshold_low_accepts_weak_match(self):
        result = translate_relationship_by_similarity("lien familial", threshold=0.0)
        assert result is not None

    def test_custom_threshold_rejects_weak_match(self):
        result = translate_relationship_by_similarity("lien familial", threshold=0.95)
        assert result is None


class TestPIIRemovalPipeline:
    def test_name_is_stripped_from_normalised_text(self):
        from ser_client_api.ml.seqoia.similarity import _GLINER_LABELS, _get_gliner_model

        model = _get_gliner_model()
        text = normalize("frère de Jean-Pierre Dupont")
        entities = model.predict_entities(text, _GLINER_LABELS, threshold=0.5)
        result = remove_entities(text, entities)
        assert "frere" in result
        assert "dupont" not in result or "jean" not in result

    def test_kinship_token_germain_preserved(self):
        from ser_client_api.ml.seqoia.similarity import _GLINER_LABELS, _get_gliner_model

        model = _get_gliner_model()
        text = normalize("cousin germain")
        entities = model.predict_entities(text, _GLINER_LABELS, threshold=0.5)
        result = remove_entities(text, entities)
        assert "germain" in result


class TestParserCascadeL3:
    """Full SeqoiaParser cascade reaching Level 3 - requires real ML models."""

    def test_masculine_cousin_with_pii_resolves_via_l3(self):
        """'cousin de X' fails L1 (no exact entry) and L2 (only feminine pattern exists) - reaches L3."""
        data = _make_prescription("cousin de Paul Dupont")
        result = SeqoiaParser().parse(data)
        nok = result.next_of_kin[0]
        assert nok.relationship_code == "COUSN"
        assert nok.relationship_is_exact is False
        assert nok.relationship_display == "cousin de Paul Dupont"

    def test_cousin_issu_de_germains_resolves_via_l3(self):
        """French legal term for second cousin - no L1/L2 entry; 'germains' guard prevents PII removal."""
        data = _make_prescription("cousin issu de germains")
        result = SeqoiaParser().parse(data)
        nok = result.next_of_kin[0]
        assert nok.relationship_code == "COUSN"
        assert nok.relationship_is_exact is False
        assert nok.relationship_display == "cousin issu de germains"
