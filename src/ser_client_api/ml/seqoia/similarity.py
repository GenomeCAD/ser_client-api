"""
Level 3 relationship resolver - PII removal + cosine similarity fallback.

Requires optional [ml] dependencies:
    pip install "ser-client-api[ml]"

The pipeline:
    1. normalize()              - accent/elision/semantic normalisation (pure Python)
    2. GLiNER.predict_entities  - detect PII spans in the normalized text
    3. remove_entities()        - strip PII while preserving kinship tokens
    4. SentenceTransformer      - embed the cleaned text and all referential entries
    5. cosine similarity        - return the best-matching HL7v3 code, or None if
                                  the best score is below the confidence threshold
"""

import importlib.resources
import json
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# Kinship tokens to preserve during PII removal (all in normalised form:
# lower-case, no accents, no elisions). GLiNER might misclassify some of
# these as proper names.
_KEEP_TOKENS: frozenset = frozenset(
    {
        "pere",
        "mere",
        "frere",
        "soeur",
        "fils",
        "fille",
        "cousin",
        "cousine",
        "niece",
        "neveu",
        "oncle",
        "tante",
        "germain",
        "germains",
        "germaine",
        "germaines",
        "jumeau",
        "jumelle",
        "demi",
        "enfant",
        "foetus",
        "beau",
        "belle",
        "grand",
        "grande",
        "petit",
        "petite",
        "arriere",
        "conjoint",
        "conjointe",
        "epoux",
        "epouse",
    }
)

_GLINER_LABELS: list = ["name", "surname", "phone number", "ethnicity"]

_DEFAULT_GLINER_MODEL = "nvidia/gliner-pii"
_DEFAULT_ST_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

_gliner_model = None
_st_model = None
_ref_index: Optional[list] = None

_ACCENT_TABLE = str.maketrans("àâäéèêëîïôöùûüç", "aaaeeeeiioouuuc")

_DIRECTIONAL_TO_GENERIC: dict = {
    "MUNCLE": "UNCLE",
    "PUNCLE": "UNCLE",
    "MCOUSN": "COUSN",
    "PCOUSN": "COUSN",
    "MAUNT": "AUNT",
    "PAUNT": "AUNT",
    "MGRMTH": "GRMTH",
    "PGRMTH": "GRMTH",
    "MGRFTH": "GRFTH",
    "PGRFTH": "GRFTH",
}


def normalize(text: str) -> str:
    """Normalise a free-text relationship label for embedding comparison."""
    text = text.lower()

    text = text.replace("d'", "de ").replace("d\u2019", "de ")
    text = text.replace("l'", "le ").replace("l\u2019", "le ")

    text = text.replace("\u0153", "oe").replace("\xe6", "ae")

    text = text.translate(_ACCENT_TABLE)

    text = re.sub(r"\bp[eé]re\b", "pere", text)
    text = re.sub(r"\bm[eé]re\b", "mere", text)

    text = re.sub(r"\bmaternel(?:le)?s?\b", "par la mere", text)
    text = re.sub(r"\bpaternel(?:le)?s?\b", "par le pere", text)

    text = re.sub(r"\b(mme|madame|mr|monsieur|dr|docteur)\b", "", text)

    text = re.sub(r"[^a-z ]", " ", text)

    text = re.sub(r"\s+", " ", text)

    tokens = [t for t in text.split() if len(t) > 2]

    return " ".join(tokens).strip()


def remove_entities(text: str, entities: list, keep_tokens: frozenset = _KEEP_TOKENS) -> str:
    """Remove GLiNER-detected PII spans from text.

    Spans whose normalised text appears in keep_tokens are preserved -
    this guards kinship words that GLiNER might misclassify as proper names.

    :param text: Normalised input text.
    :param entities: List of entity dicts from GLiNER (keys: text, start, end, label).
    :param keep_tokens: Set of normalised kinship tokens to never remove.
    :returns: Text with PII spans removed, whitespace collapsed.
    """
    for entity in sorted(entities, key=lambda e: e["start"], reverse=True):
        span_tokens = entity["text"].lower().replace("-", " ").split()
        if any(t in keep_tokens for t in span_tokens):
            continue
        start, end = entity["start"], entity["end"]
        text = text[:start] + text[end:]

    return " ".join(text.split())


def _get_gliner_model(model_name: str = _DEFAULT_GLINER_MODEL):
    global _gliner_model
    if _gliner_model is None:
        try:
            from gliner import GLiNER
        except ImportError as exc:
            raise ImportError(
                "GLiNER is required for Level 3 relationship resolution. Install with: pip install 'ser-client-api[ml]'"
            ) from exc
        logger.info("Loading GLiNER model %r (first call - cached for subsequent calls)", model_name)
        _gliner_model = GLiNER.from_pretrained(model_name)
    return _gliner_model


def _get_st_model(model_name: str = _DEFAULT_ST_MODEL):
    global _st_model
    if _st_model is None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise ImportError(
                "sentence-transformers is required for Level 3 relationship resolution. "
                "Install with: pip install 'ser-client-api[ml]'"
            ) from exc
        logger.info(
            "Loading SentenceTransformer model %r (first call - cached for subsequent calls)",
            model_name,
        )
        _st_model = SentenceTransformer(model_name)
    return _st_model


def _get_ref_index() -> list:
    """Load, normalise, and embed the GIP-CAD pedigree referential."""
    global _ref_index
    if _ref_index is None:
        f = importlib.resources.files("ser_client_api.vocabularies.gipcad") / "Genomic-Pedigree.json"
        data = json.loads(f.read_text(encoding="utf-8"))

        st_model = _get_st_model()

        normalized_displays = [normalize(row["Display"]) for row in data]

        logger.info("Building pedigree referential index (%d entries)...", len(data))
        embeddings = st_model.encode(normalized_displays, normalize_embeddings=True)

        _ref_index = [
            {
                "hl7v3_code": row["hl7v3_code"],
                "display": row["Display"],
                "display_normalized": nd,
                "_embedding": emb,
            }
            for row, nd, emb in zip(data, normalized_displays, embeddings)
        ]
        logger.info("Pedigree referential index ready.")
    return _ref_index


def translate_relationship_by_similarity(
    libelle: str,
    threshold: float = 0.75,
) -> Optional[str]:
    """Return HL7v3 RoleCode by PII removal + cosine similarity (Level 3 fallback).

    Normalises the input, strips PII via GLiNER, then finds the closest entry
    in the GIP-CAD pedigree referential using sentence embeddings. Returns the
    corresponding HL7v3 code if the best similarity score meets the threshold,
    otherwise None (caller should fall back to EXT).

    :param libelle: Free-text pedigree label from lien.name field.
    :param threshold: Minimum cosine similarity score to accept a match [0, 1].
    :returns: HL7v3 RoleCode string, or None if no match above threshold.
    :raises ImportError: If gliner or sentence-transformers are not installed.
    """
    import numpy as np

    if not libelle:
        return None

    ntext = normalize(libelle)
    if not ntext:
        return None

    gliner = _get_gliner_model()
    entities = gliner.predict_entities(ntext, _GLINER_LABELS, threshold=0.5)
    rtext = remove_entities(ntext, entities)

    if not rtext:
        logger.warning("Level 3: text empty after PII removal for libelle %r", libelle)
        return None

    st_model = _get_st_model()
    ref_index = _get_ref_index()

    cleaned_emb = st_model.encode(rtext, normalize_embeddings=True)

    best_score = -1.0
    best_code = None
    best_display = None

    for row in ref_index:
        score = float(np.dot(cleaned_emb, row["_embedding"]))
        if score > best_score:
            best_score = score
            best_code = row["hl7v3_code"]
            best_display = row["display"]

    if best_score >= threshold:
        has_direction = "par mere" in ntext or "par pere" in ntext
        if not has_direction and best_code in _DIRECTIONAL_TO_GENERIC:
            best_code = _DIRECTIONAL_TO_GENERIC[best_code]
        logger.info(
            "Level 3 match: %r -> %s (%r, score=%.4f)",
            libelle,
            best_code,
            best_display,
            best_score,
        )
        return best_code

    logger.warning(
        "Level 3: no match above threshold %.2f for %r (best: %s / %r at %.4f)",
        threshold,
        libelle,
        best_code,
        best_display,
        best_score,
    )
    return None
