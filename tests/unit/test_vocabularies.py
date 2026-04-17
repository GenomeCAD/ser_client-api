"""Unit tests for the gipcad and seqoia vocabulary modules."""

import logging

from ser_client_api.vocabularies.gipcad import pfmg_display, v3_display
from ser_client_api.vocabularies.seqoia import FILIERE, translate_filiere


class TestV3Display:

    def test_known_code_returns_display(self):
        assert v3_display("FTH") == "father"

    def test_unknown_code_returns_none(self):
        assert v3_display("NOTACODE") is None


class TestPfmgDisplay:

    def test_known_code_returns_french_label(self):
        assert pfmg_display("F-01") == "Cardiomyopathies familiales [CARDIOGEN]"


class TestTranslateFiliere:

    def test_multi_target_key_returns_first_target(self):
        # p1-sp11 maps to F-51, F-52, F-59 — first wins
        code, display = translate_filiere("p1-sp11")
        assert code == "F-51"
        assert "Malformations cérébrales" in display

    def test_unknown_key_returns_none_and_warns(self, caplog):
        with caplog.at_level(logging.WARNING, logger="ser_client_api.vocabularies.seqoia"):
            result = translate_filiere("p1-sp999")
        assert result is None
        assert "p1-sp999" in caplog.text

    def test_filiere_index_fully_loaded(self):
        assert len(FILIERE) == 77
