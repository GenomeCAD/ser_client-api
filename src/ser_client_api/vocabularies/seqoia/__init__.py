"""
SeqOIA vocabulary mappings - CAD standardization layer.

Domain covered:

    FILIERE - maps preindication.key (e.g. "p1-sp49") to a PFMG Filière code and full display
    label, used to populate PV1.14 of the ORU_R01 CAD message.

    RELATIONSHIP — maps pedigree libellés (lien.name free text) to HL7v3 RoleCode, used to
    populate NK1-3 of the ORU_R01 CAD message.  Lookup is case-insensitive.

Unknown keys/libellés are not rejected - a warning is logged and the caller receives None,
allowing the generator to apply a safe fallback rather than fail.
"""

import importlib.resources
import json
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

FILIERE: dict[str, tuple[str, str]] = {
    "p1-sp1":  ("F-45", "Maladies osseuses constitutionnelles [OSCAR]"),
    "p1-sp2":  ("F-09", "Maladies mitochondriales [FILNEMUS]"),
    "p1-sp3":  ("F-10", "Anomalies sévères de la différenciation sexuelle d'origine gonadique et hypothalamo-hypophysaire [FIRENDO]"),
    "p1-sp4":  ("F-66", "Insuffisance ovarienne prématurée et anomalies ovocytaires rares [FIRENDO]"),
    "p1-sp5":  ("F-18", "Maladies héréditaires du métabolisme [G2M]"),
    "p1-sp6":  ("F-29", "Néphropathies chroniques [ORKID]"),
    "p1-sp7":  ("F-30", "Maladies auto-inflammatoires et auto-immunes monogéniques [FAI²R]"),
    "p1-sp8":  ("F-01", "Cardiomyopathies familiales [CARDIOGEN]"),
    "p1-sp9":  ("F-36", "Leucodystrophies [BRAIN-TEAM]"),
    "p1-sp10": ("F-48", "Anomalies du développement, syndromes malformatifs et syndromes dysmorphiques sans déficience intellectuelle [AnDDI-Rares]"),
    "p1-sp11": ("F-51", "Malformations cérébrales [AnDDI-Rares]"),        # also F-52; multi-filière
    "p1-sp12": ("F-51", "Malformations cérébrales [AnDDI-Rares]"),        # also F-52; multi-filière
    "p1-sp13": ("F-58", "Epilepsies pharmacorésistantes à début précoce [DéfiScience]"),
    "p1-sp14": ("F-33", "Ataxies héréditaires du sujet jeune [BRAIN-TEAM]"),
    "p1-sp15": ("F-40", "Paraparésies spastiques héréditaires du sujet jeune [BRAIN-TEAM]"),
    "p1-sp16": ("F-41", "Hypotonies néonatales périphériques suspectes de maladies neuromusculaires [FILNEMUS]"),
    "p1-sp17": ("F-42", "Myopathies [FILNEMUS]"),
    "p1-sp18": ("F-13", "Dysfonction de l'axe thyréotrope et hypothyroïdies congénitales [FIRENDO]"),
    "p1-sp19": ("F-11", "Diabète néonatal [FIRENDO]"),
    "p1-sp20": ("F-68", "Surdités précoces [SENSGENE]"),
    "p1-sp21": ("F-62", "Malformations oculaires [SENSGENE]"),
    "p1-sp22": ("F-35", "Dystonie ou mouvements anormaux rares du sujet jeune [BRAIN-TEAM]"),
    "p1-sp23": ("F-38", "Maladies et troubles cognitifs neurodégénératifs du sujet jeune et/ou familiaux [BRAIN-TEAM]"),
    "p1-sp24": ("F-39", "Neurodégénérescence par accumulation intracérébrale de fer [BRAIN-TEAM]"),
    "p1-sp25": ("F-57", "Malformations cardiaques complexes congénitales [CARDIOGEN]"),
    "p1-sp26": ("F-02", "Troubles du rythme héréditaires [CARDIOGEN]"),
    "p1-sp27": ("F-01", "Cardiomyopathies familiales [CARDIOGEN]"),
    "p1-sp28": ("F-04", "Maladie de Rendu-Osler [FAVA-Multi]"),
    "p1-sp29": ("F-07", "Syndrome de Marfan et pathologies apparentées, formes familiales d'anévrysmes de l'aorte thoracique [FAVA-Multi]"),
    "p1-sp30": ("F-06", "Malformations artérioveineuses superficielles et du SNC à potentiel agressif [FAVA-Multi]"),
    "p1-sp31": ("F-05", "Maladies des artères de moyen calibre [FAVA-Multi]"),
    "p1-sp32": ("F-26", "Pathologies sévères du foie à révélation pédiatrique [FILFOIE]"),
    "p1-sp33": ("F-08", "Génodermatoses [FIMARAD]"),
    "p1-sp34": ("F-27", "Entéropathies congénitales du jeune enfant [FIMATHO]"),
    "p1-sp35": ("F-16", "Hypersécrétions hormonales hypophysaires et lésions endocriniennes multiples (hors NEM2) [FIRENDO]"),
    "p1-sp36": ("F-12", "Diabètes rares du sujet jeune et diabètes lipoatrophiques [FIRENDO]"),
    "p1-sp37": ("F-15", "Déficit hypophysaire combiné ou somatotrope isolé ou corticotrope isolé [FIRENDO]"),
    "p1-sp38": ("F-18", "Maladies héréditaires du métabolisme [G2M]"),
    "p1-sp39": ("F-32", "Déficits immunitaires héréditaires [MaRIH]"),
    "p1-sp40": ("F-24", "Maladies constitutionnelles du globule rouge [MCGRE]"),
    "p1-sp41": ("F-25", "Pathologies de l'hémostase [MHEMO]"),
    "p1-sp42": ("F-47", "Maladies respiratoires rares [RESPIFIL]"),
    "p1-sp43": ("F-67", "Dystrophies rétiniennes héréditaires [SENSGENE]"),
    "p1-sp44": ("F-53", "Troubles Psychiatriques Majeurs [AnDDI-Rares]"),  # also F-54; multi-filière
    "p1-sp45": ("F-61", "Troubles du spectre autistique ou troubles précoces et sévères du neuro-développement- sans déficience intellectuelle, de formes monogéniques [DéfiScience]"),  # corrigé=Y
    "p1-sp46": ("F-22", "Neutropénies chroniques sévères [MaRIH]"),
    "p1-sp47": ("F-55", "Dysraphismes [AnDDI-Rares]"),                    # also F-56; multi-filière
    "p1-sp48": ("F-19", "Pathologies rares du métabolisme phospho-calcique ou de la minéralisation dentaire [OSCAR]"),
    "p1-sp49": ("F-20", "Aplasies et hypoplasies médullaires [MaRIH]"),
    "p1-sp50": ("F-64", "Formes syndromiques de maladies rares à expression bucco-dentaire [TÊTECOU]"),
    "p1-sp51": ("F-61", "Troubles du spectre autistique ou troubles précoces et sévères du neuro-développement- sans déficience intellectuelle, de formes monogéniques [DéfiScience]"),
    "p1-sp52": ("F-17", "Syndrome de Cushing par hyperplasie nodulaire bilatérale des surrénales et Insuffisance Surrénale Primaire [FIRENDO]"),
    "p1-sp53": ("F-34", "Calcifications cérébrales [BRAIN-TEAM]"),
    "p1-sp54": ("F-37", "Maladies cérébrovasculaires rares [BRAIN-TEAM]"),
    "p1-sp55": ("F-03", "Lymphoedèmes primaires [FAVA-Multi]"),
    "p1-sp56": ("F-43", "Neuropathies périphériques héréditaires [FILNEMUS]"),
    "p1-sp57": ("F-44", "Sclérose latérale amyotrophique [FilSLAN]"),
    "p1-sp58": ("F-28", "Pancréatites chroniques d'origine génétique [FIMATHO]"),
    "p1-sp59": ("F-65", "Infertilités masculines rares [FIRENDO]"),
    "p1-sp60": ("F-31", "Angioedèmes bradykiniques héréditaires [MaRIH]"),
    "p1-sp61": ("F-46", "Syndromes avec hyperlaxité articulaire majeure, sans déficit intellectuel [OSCAR]"),
    "p1-sp63": ("F-63", "Neuropathies optiques génétiques (NOG) [SENSGENE]"),
    "p1-sp64": ("F-60", "Obésités génétiques rares [DéfiScience]"),
    "p1-sp65": ("F-23", "Syndromes hyperéosinophiliques clonaux inexpliqués [MaRIH]"),
    "p1-sp68": ("F-89", "Néoplasmes myéloprolifératifs familiaux et thrombocytose héréditaire [FIM]"),  # also F-90; multi-filière
    "p2-sp1":  ("F-85", "Cancers et leucémies pédiatriques en échec de traitement [SFCE]"),
    "p2-sp11": ("F-84", "Cancers et leucémies pédiatriques au diagnostic [SFCE]"),
    "p2-sp13": ("F-69", "Patients adultes atteints de leucémie aiguë au diagnostic, éligibles à un traitement actif [ALFA]"),  # also F-70/71/72; multi-filière
    "p2-sp2":  ("F-73", "Leucémies aiguës réfractaires ou en rechute chez l'adulte [GBMHM]"),
    "p2-sp4":  ("F-74", "Lymphomes B diffus à grandes cellules en rechute ou réfractaires [GBMHM]"),  # also F-75; multi-filière
    "p2-sp5":  ("F-76", "Lymphomes de diagnostic incertain [GBMHM]"),     # also F-77; multi-filière
    "p2-sp6":  ("F-82", "Cancers rares [GFCO]"),                           # also F-83; multi-filière
    "p2-sp7":  ("F-80", "Cancers de primitif inconnu [GFCO]"),             # also F-81; multi-filière
    "p2-sp8":  ("F-78", "Cancers avancés en échec thérapeutique de première ligne [GFCO]"),  # also F-79; multi-filière
    "p3-sp1":  ("F-87", "Cancers avec antécédents familiaux particulièrement sévères [Groupe génétique et cancer]"),
    "p3-sp2":  ("F-88", "Cancers avec phénotypes tumoraux extrêmes et sans antécédents familiaux [Groupe génétique et cancer]"),
    "p3-sp3":  ("F-86", "Leucémies aiguës (LA) de l'adulte avec histoire familiale [CIGAL]"),
}


def translate_filiere(seqoia_key: str) -> Optional[tuple[str, str]]:
    """Return (PFMG filière code, full display label) for a SeqOIA preindication key."""
    result = FILIERE.get(seqoia_key)
    if result is None:
        logger.warning(
            "SeqOIA preindication key %r has no PFMG filière mapping - PV1.14 will be empty",
            seqoia_key,
        )
    return result

_relationship_index: Optional[dict[str, str]] = None


def _get_relationship_index() -> dict[str, str]:
    global _relationship_index
    if _relationship_index is None:
        f = (
            importlib.resources.files("ser_client_api.vocabularies.seqoia")
            / "seqoia-to-v3-relationship.json"
        )
        data = json.loads(f.read_text(encoding="utf-8"))
        index: dict[str, str] = {}
        for group in data.get("group", []):
            for element in group.get("element", []):
                code = element.get("code")
                targets = element.get("target", [])
                if code and targets:
                    index[code.lower()] = targets[0]["code"]
        _relationship_index = index
    return _relationship_index


def translate_relationship(libelle: str) -> Optional[str]:
    """Return HL7v3 RoleCode for a SeqOIA pedigree libellé (case-insensitive).

    :param libelle: Free-text pedigree label from lien.name field.
    :returns: HL7v3 v3-RoleCode string (e.g. "BRO", "SIS"), or None if not found.
    """
    if not libelle:
        return None
    return _get_relationship_index().get(libelle.strip().lower())


_pattern_rules: Optional[list] = None


def _get_pattern_rules() -> list:
    global _pattern_rules
    if _pattern_rules is None:
        f = (
            importlib.resources.files("ser_client_api.vocabularies.seqoia")
            / "seqoia-relationship-patterns.json"
        )
        data = json.loads(f.read_text(encoding="utf-8"))
        _pattern_rules = [(re.compile(row["pattern"]), row["code"]) for row in data]
    return _pattern_rules


def translate_relationship_by_regex(libelle: str) -> Optional[str]:
    """Return HL7v3 RoleCode by matching libellé against ordered regex patterns.

    Patterns are tested in order; the first match wins.  Designed for free-text
    entries that embed PII (e.g. "frère de Lucas") and therefore cannot be exact
    matched via the ConceptMap index.

    :param libelle: Free-text pedigree label from lien.name field.
    :returns: HL7v3 v3-RoleCode string, or None if no pattern matches.
    """
    if not libelle:
        return None
    for pattern, code in _get_pattern_rules():
        if pattern.search(libelle):
            return code
    return None
