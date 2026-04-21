"""Unit tests for similarity.normalize() and remove_entities() - no ML deps required."""

from ser_client_api.ml.seqoia.similarity import normalize, remove_entities


class TestNormalize:
    def test_lowercase(self):
        assert normalize("FRÈRE") == "frere"

    def test_accents_removed(self):
        assert normalize("père mère") == "pere mere"

    def test_ligature_oe(self):
        assert normalize("sœur") == "soeur"

    def test_ligature_ae(self):
        assert normalize("æ") == ""  # single char -> dropped by the <=2 token filter

    def test_elision_apostrophe_straight(self):
        assert normalize("frère d'un inconnu") == "frere inconnu"

    def test_elision_apostrophe_curly(self):
        assert normalize("frère d\u2019un inconnu") == "frere inconnu"

    def test_elision_l_straight(self):
        assert normalize("fils de l'oncle") == "fils oncle"

    def test_elision_l_curly(self):
        assert normalize("fils de l\u2019oncle") == "fils oncle"

    def test_semantic_maternelle(self):
        assert normalize("cousine maternelle") == "cousine par mere"

    def test_semantic_maternel(self):
        assert normalize("oncle maternel") == "oncle par mere"

    def test_semantic_paternelle(self):
        assert normalize("cousine paternelle") == "cousine par pere"

    def test_semantic_paternel(self):
        assert normalize("oncle paternel") == "oncle par pere"

    def test_removes_mme(self):
        assert "mme" not in normalize("frère de Mme Dupont")

    def test_removes_madame(self):
        assert "madame" not in normalize("soeur de Madame Durand")

    def test_removes_monsieur(self):
        assert "monsieur" not in normalize("fils de Monsieur Martin")

    def test_removes_mr(self):
        assert "mr" not in normalize("neveu de Mr Leblanc")

    def test_removes_short_tokens(self):
        # "de", "du", "la", "le", "et" are all <=2 chars -> dropped
        result = normalize("frère de la mère du père")
        assert "de" not in result.split()
        assert "la" not in result.split()
        assert "du" not in result.split()

    def test_par_kept(self):
        # "par" is 3 chars -> kept after semantic expansion
        assert "par" in normalize("cousine paternelle")

    def test_removes_digits(self):
        assert "01" not in normalize("soeur de Jeanne (01 12 34 56 78)")
        assert "12" not in normalize("soeur de Jeanne (01 12 34 56 78)")

    def test_removes_parentheses(self):
        result = normalize("soeur (demi)")
        assert "(" not in result
        assert ")" not in result

    def test_collapses_whitespace(self):
        assert "  " not in normalize("frère   de   Paul")

    def test_empty_string(self):
        assert normalize("") == ""

    def test_whitespace_only(self):
        assert normalize("   ") == ""

    def test_full_pr_example(self):
        text = "cousine paternelle du père de Mme Sarrault Claude et soeur de Jeanne (01 12 34 56 78)"
        result = normalize(text)
        assert "cousine" in result
        assert "par" in result
        assert "pere" in result
        assert "soeur" in result
        assert "sarrault" in result
        assert "claude" in result
        assert "mme" not in result
        assert "01" not in result

    def test_referential_entry_pere(self):
        assert normalize("père") == "pere"

    def test_referential_entry_grand_pere_par_le_pere(self):
        result = normalize("grand père par le père")
        assert "grand" in result
        assert "pere" in result
        assert "par" in result

    def test_hyphen_becomes_space(self):
        # hyphens -> spaces so "grand-pere" and "grand pere" get identical embeddings
        assert normalize("grand-père") == normalize("grand père")

    def test_hyphenated_compound_tokens_consistent(self):
        assert normalize("demi-frère") == normalize("demi frère")
        assert normalize("belle-mère") == normalize("belle mère")
        assert normalize("beau-père") == normalize("beau père")
        assert normalize("arrière-grand-père") == normalize("arrière grand père")


class TestRemoveEntities:
    def test_removes_detected_name(self):
        text = "cousine par pere sarrault claude soeur jeanne"
        entities = [
            {
                "text": "sarrault",
                "start": text.index("sarrault"),
                "end": text.index("sarrault") + 8,
                "label": "surname",
            },  # noqa: E501
            {"text": "claude", "start": text.index("claude"), "end": text.index("claude") + 6, "label": "name"},
            {"text": "jeanne", "start": text.index("jeanne"), "end": text.index("jeanne") + 6, "label": "name"},
        ]
        result = remove_entities(text, entities)
        assert "sarrault" not in result
        assert "claude" not in result
        assert "jeanne" not in result

    def test_preserves_kinship_tokens(self):
        text = "fils germain soeur"
        entities = [
            {"text": "germain", "start": text.index("germain"), "end": text.index("germain") + 7, "label": "name"},
        ]
        result = remove_entities(text, entities)
        assert "germain" in result

    def test_preserves_cousine(self):
        text = "cousine par pere"
        entities = [
            {"text": "cousine", "start": 0, "end": 7, "label": "name"},
        ]
        result = remove_entities(text, entities)
        assert "cousine" in result

    def test_empty_entities(self):
        text = "cousine par pere soeur"
        assert remove_entities(text, []) == text

    def test_multiple_removals_preserve_offsets(self):
        text = "aaa bbb ccc"
        entities = [
            {"text": "aaa", "start": 0, "end": 3, "label": "name"},
            {"text": "ccc", "start": 8, "end": 11, "label": "name"},
        ]
        result = remove_entities(text, entities)
        assert "aaa" not in result
        assert "ccc" not in result
        assert "bbb" in result

    def test_collapses_whitespace_after_removal(self):
        text = "cousine paul soeur"
        entities = [{"text": "paul", "start": 8, "end": 12, "label": "name"}]
        result = remove_entities(text, entities)
        assert "  " not in result

    def test_full_pr_example(self):
        text = normalize("cousine paternelle du père de Mme Sarrault Claude et soeur de Jeanne (01 12 34 56 78)")
        entities = [
            {
                "text": "sarrault",
                "start": text.index("sarrault"),
                "end": text.index("sarrault") + 8,
                "label": "surname",
            },
            {"text": "claude", "start": text.index("claude"), "end": text.index("claude") + 6, "label": "name"},
            {"text": "jeanne", "start": text.index("jeanne"), "end": text.index("jeanne") + 6, "label": "name"},
        ]
        result = remove_entities(text, entities)
        assert result == "cousine par pere pere soeur"

    def test_preserves_compound_kinship_span(self):
        text = "grand pere par le pere"
        entities = [{"text": "grand pere", "start": 0, "end": 10, "label": "name"}]
        result = remove_entities(text, entities)
        assert "grand" in result
        assert "pere" in result

    def test_preserves_hyphenated_compound_kinship_span(self):
        text = "grand-pere par le pere"
        entities = [{"text": "grand-pere", "start": 0, "end": 10, "label": "ethnicity"}]
        result = remove_entities(text, entities)
        assert "grand" in result or "pere" in result

    def test_pii_name_with_hyphen_is_removed(self):
        text = "frere jean-pierre dupont"
        entities = [{"text": "jean-pierre", "start": 6, "end": 17, "label": "name"}]
        result = remove_entities(text, entities)
        assert "jean" not in result
        assert "pierre" not in result
        assert "frere" in result
