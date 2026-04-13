"""
SeqOIA vocabulary mappings - CAD standardization layer.

Domain covered:

    FILIERE - maps preindication.name to a PFMG Filière code and full display label,
    used to populate PV1.14 of the ORU_R01 CAD message.

Unknown names are not rejected — a warning is logged and the caller receives None,
allowing the generator to leave PV1.14 empty rather than fail.
"""

import logging

logger = logging.getLogger(__name__)

FILIERE: dict[str, tuple[str, str]] = {
    "Cardiomyopathies familiales":                  ("F-01", "Cardiomyopathies familiales [CARDIOGEN]"),
    "Troubles du rythme héréditaires":               ("F-02", "Troubles du rythme héréditaires [CARDIOGEN]"),
    "Lymphoedèmes primaires":                        ("F-03", "Lymphoedèmes primaires [FAVA-Multi]"),
    "Maladie de Rendu-Osler":                        ("F-04", "Maladie de Rendu-Osler [FAVA-Multi]"),
    "Maladies des artères de moyen calibre":         ("F-05", "Maladies des artères de moyen calibre [FAVA-Multi]"),
    "Malformations artérioveineuses superficielles et du SNC à potentiel agressif":
                                                     ("F-06", "Malformations artérioveineuses superficielles et du SNC à potentiel agressif [FAVA-Multi]"),
    "Syndrome de Marfan et pathologies apparentées, formes familiales d'anévrysmes de l'aorte thoracique":
                                                     ("F-07", "Syndrome de Marfan et pathologies apparentées, formes familiales d'anévrysmes de l'aorte thoracique [FAVA-Multi]"),
    "Génodermatoses":                                ("F-08", "Génodermatoses [FIMARAD]"),
    "Maladies mitochondriales":                      ("F-09", "Maladies mitochondriales [FILNEMUS]"),
    "Anomalies sévères de la différenciation sexuelle d'origine gonadique et hypothalamo-hypophysaire":
                                                     ("F-10", "Anomalies sévères de la différenciation sexuelle d'origine gonadique et hypothalamo-hypophysaire [FIRENDO]"),
    "Diabète néonatal":                              ("F-11", "Diabète néonatal [FIRENDO]"),
    "Diabètes rares du sujet jeune et diabètes lipoatrophiques":
                                                     ("F-12", "Diabètes rares du sujet jeune et diabètes lipoatrophiques [FIRENDO]"),
    "Dysfonction de l'axe thyréotrope et hypothyroïdies congénitales":
                                                     ("F-13", "Dysfonction de l'axe thyréotrope et hypothyroïdies congénitales [FIRENDO]"),
    "Dyslipidémies primaires rares":                 ("F-14", "Dyslipidémies primaires rares [FIRENDO]"),
    "Déficit hypophysaire combiné ou somatotrope isolé ou corticotrope isolé":
                                                     ("F-15", "Déficit hypophysaire combiné ou somatotrope isolé ou corticotrope isolé [FIRENDO]"),
    "Hypersécrétions hormonales hypophysaires et lésions endocriniennes multiples (hors NEM2)":
                                                     ("F-16", "Hypersécrétions hormonales hypophysaires et lésions endocriniennes multiples (hors NEM2) [FIRENDO]"),
    "Syndrome de Cushing par hyperplasie nodulaire bilatérale des surrénales et Insuffisance Surrénale Primaire":
                                                     ("F-17", "Syndrome de Cushing par hyperplasie nodulaire bilatérale des surrénales et Insuffisance Surrénale Primaire [FIRENDO]"),
    "Maladies héréditaires du métabolisme":          ("F-18", "Maladies héréditaires du métabolisme [G2M]"),
    "Pathologies rares du métabolisme phospho-calcique ou de la minéralisation dentaire":
                                                     ("F-19", "Pathologies rares du métabolisme phospho-calcique ou de la minéralisation dentaire [OSCAR]"),
    "Aplasies et hypoplasies médullaires":           ("F-20", "Aplasies et hypoplasies médullaires [MaRIH]"),
    "Histiocytoses sans mutation BRAFV600E":         ("F-21", "Histiocytoses sans mutation BRAFV600E [MaRIH]"),
    "Neutropénies chroniques sévères":               ("F-22", "Neutropénies chroniques sévères [MaRIH]"),
    "Syndromes hyperéosinophiliques clonaux inexpliqués":
                                                     ("F-23", "Syndromes hyperéosinophiliques clonaux inexpliqués [MaRIH]"),
    "Maladies constitutionnelles du globule rouge":  ("F-24", "Maladies constitutionnelles du globule rouge [MCGRE]"),
    "Pathologies de l'hémostase":                    ("F-25", "Pathologies de l'hémostase [MHEMO]"),
    "Pathologies sévères du foie à révélation pédiatrique":
                                                     ("F-26", "Pathologies sévères du foie à révélation pédiatrique [FILFOIE]"),
    "Entéropathies congénitales du jeune enfant":    ("F-27", "Entéropathies congénitales du jeune enfant [FIMATHO]"),
    "Pancréatites chroniques d'origine génétique":   ("F-28", "Pancréatites chroniques d'origine génétique [FIMATHO]"),
    "Néphropathies chroniques":                      ("F-29", "Néphropathies chroniques [ORKID]"),
    "Maladies auto-inflammatoires et auto-immunes monogéniques":
                                                     ("F-30", "Maladies auto-inflammatoires et auto-immunes monogéniques [FAI²R]"),
    "Angioedèmes bradykiniques héréditaires":        ("F-31", "Angioedèmes bradykiniques héréditaires [MaRIH]"),
    "Déficits immunitaires héréditaires":            ("F-32", "Déficits immunitaires héréditaires [MaRIH]"),
    "Ataxies héréditaires du sujet jeune":           ("F-33", "Ataxies héréditaires du sujet jeune [BRAIN-TEAM]"),
    "Calcifications cérébrales":                     ("F-34", "Calcifications cérébrales [BRAIN-TEAM]"),
    "Dystonie ou mouvements anormaux rares du sujet jeune":
                                                     ("F-35", "Dystonie ou mouvements anormaux rares du sujet jeune [BRAIN-TEAM]"),
    "Leucodystrophies":                              ("F-36", "Leucodystrophies [BRAIN-TEAM]"),
    "Maladies cérébrovasculaires rares":             ("F-37", "Maladies cérébrovasculaires rares [BRAIN-TEAM]"),
    "Maladies et troubles cognitifs neurodégénératifs du sujet jeune et/ou familiaux":
                                                     ("F-38", "Maladies et troubles cognitifs neurodégénératifs du sujet jeune et/ou familiaux [BRAIN-TEAM]"),
    "Neurodégénérescence par accumulation intracérébrale de fer":
                                                     ("F-39", "Neurodégénérescence par accumulation intracérébrale de fer [BRAIN-TEAM]"),
    "Paraparésies spastiques héréditaires du sujet jeune":
                                                     ("F-40", "Paraparésies spastiques héréditaires du sujet jeune [BRAIN-TEAM]"),
    "Hypotonies néonatales périphériques suspectes de maladies neuromusculaires":
                                                     ("F-41", "Hypotonies néonatales périphériques suspectes de maladies neuromusculaires [FILNEMUS]"),
    "Myopathies":                                    ("F-42", "Myopathies [FILNEMUS]"),
    "Neuropathies périphériques héréditaires":       ("F-43", "Neuropathies périphériques héréditaires [FILNEMUS]"),
    "Sclérose latérale amyotrophique":               ("F-44", "Sclérose latérale amyotrophique [FilSLAN]"),
    "Maladies osseuses constitutionnelles":          ("F-45", "Maladies osseuses constitutionnelles [OSCAR]"),
    "Syndromes avec hyperlaxité articulaire majeure, sans déficit intellectuel":
                                                     ("F-46", "Syndromes avec hyperlaxité articulaire majeure, sans déficit intellectuel [OSCAR]"),
    "Maladies respiratoires rares":                  ("F-47", "Maladies respiratoires rares [RESPIFIL]"),
    "Anomalies du développement, syndromes malformatifs et syndromes dysmorphiques sans déficience intellectuelle":
                                                     ("F-48", "Anomalies du développement, syndromes malformatifs et syndromes dysmorphiques sans déficience intellectuelle [AnDDI-Rares]"),
    "Déficience intellectuelle":                     ("F-49", "Déficience intellectuelle [AnDDI-Rares]"),   # also F-50
    "Malformations cérébrales":                      ("F-51", "Malformations cérébrales [AnDDI-Rares]"),    # also F-52
    "Troubles Psychiatriques Majeurs":               ("F-53", "Troubles Psychiatriques Majeurs [AnDDI-Rares]"),  # also F-54
    "Dysraphismes":                                  ("F-55", "Dysraphismes [AnDDI-Rares]"),                # also F-56
    "Malformations cardiaques complexes congénitales":
                                                     ("F-57", "Malformations cardiaques complexes congénitales [CARDIOGEN]"),
    "Epilepsies pharmacorésistantes à début précoce":
                                                     ("F-58", "Epilepsies pharmacorésistantes à début précoce [DéfiScience]"),
    "Malformations et maladies congénitales et très précoces du cervelet et du tronc cérébral":
                                                     ("F-59", "Malformations et maladies congénitales et très précoces du cervelet et du tronc cérébral [DéfiScience]"),
    "Obésités génétiques rares":                     ("F-60", "Obésités génétiques rares [DéfiScience]"),
    "Troubles du spectre autistique ou troubles précoces et sévères du neuro-développement- sans déficience intellectuelle, de formes monogéniques":
                                                     ("F-61", "Troubles du spectre autistique ou troubles précoces et sévères du neuro-développement- sans déficience intellectuelle, de formes monogéniques [DéfiScience]"),
    "Malformations oculaires":                       ("F-62", "Malformations oculaires [SENSGENE]"),
    "Neuropathies optiques génétiques (NOG)":        ("F-63", "Neuropathies optiques génétiques (NOG) [SENSGENE]"),
    "Formes syndromiques de maladies rares à expression bucco-dentaire":
                                                     ("F-64", "Formes syndromiques de maladies rares à expression bucco-dentaire [TÊTECOU]"),
    "Infertilités masculines rares":                 ("F-65", "Infertilités masculines rares [FIRENDO]"),
    "Insuffisance ovarienne prématurée et anomalies ovocytaires rares":
                                                     ("F-66", "Insuffisance ovarienne prématurée et anomalies ovocytaires rares [FIRENDO]"),
    "Dystrophies rétiniennes héréditaires":          ("F-67", "Dystrophies rétiniennes héréditaires [SENSGENE]"),
    "Surdités précoces":                             ("F-68", "Surdités précoces [SENSGENE]"),
    "Patients adultes atteints de leucémie aiguë au diagnostic, éligibles à un traitement actif":
                                                     ("F-69", "Patients adultes atteints de leucémie aiguë au diagnostic, éligibles à un traitement actif [ALFA]"),  # also F-70/71/72
    "Leucémies aiguës réfractaires ou en rechute chez l'adulte":
                                                     ("F-73", "Leucémies aiguës réfractaires ou en rechute chez l'adulte [GBMHM]"),
    "Lymphomes B diffus à grandes cellules en rechute ou réfractaires":
                                                     ("F-74", "Lymphomes B diffus à grandes cellules en rechute ou réfractaires [GBMHM]"),  # also F-75
    "Lymphomes de diagnostic incertain":             ("F-76", "Lymphomes de diagnostic incertain [GBMHM]"),  # also F-77
    "Cancers avancés en échec thérapeutique de première ligne":
                                                     ("F-78", "Cancers avancés en échec thérapeutique de première ligne [GFCO]"),  # also F-79
    "Cancers de primitif inconnu":                   ("F-80", "Cancers de primitif inconnu [GFCO]"),        # also F-81
    "Cancers rares":                                 ("F-82", "Cancers rares [GFCO]"),                      # also F-83
    "Cancers et leucémies pédiatriques au diagnostic":
                                                     ("F-84", "Cancers et leucémies pédiatriques au diagnostic [SFCE]"),
    "Cancers et leucémies pédiatriques en échec de traitement":
                                                     ("F-85", "Cancers et leucémies pédiatriques en échec de traitement [SFCE]"),
    "Leucémies aiguës (LA) de l'adulte avec histoire familiale":
                                                     ("F-86", "Leucémies aiguës (LA) de l'adulte avec histoire familiale [CIGAL]"),
    "Cancers avec antécédents familiaux particulièrement sévères":
                                                     ("F-87", "Cancers avec antécédents familiaux particulièrement sévères [Groupe génétique et cancer]"),
    "Cancers avec phénotypes tumoraux extrêmes et sans antécédents familiaux":
                                                     ("F-88", "Cancers avec phénotypes tumoraux extrêmes et sans antécédents familiaux [Groupe génétique et cancer]"),
    "Néoplasmes myéloprolifératifs familiaux et thrombocytose héréditaire":
                                                     ("F-89", "Néoplasmes myéloprolifératifs familiaux et thrombocytose héréditaire [FIM]"),  # also F-90
    "Hypertension artérielle monogénique du sujet jeune":
                                                     ("F-91", "Hypertension artérielle monogénique du sujet jeune [ORKID / FIRENDO]"),
    "Migraine hémiplégique familiale":               ("F-92", "Migraine hémiplégique familiale [BRAIN-TEAM]"),
    "Myélome multiple au diagnostic chez des patients non fragiles":
                                                     ("F-93", "Myélome multiple au diagnostic chez des patients non fragiles [Intergroupe Francophone du Myélome]"),
    "Lymphomes B cutanés primitifs réfractaires ou récidivants":
                                                     ("F-94", "Lymphomes B cutanés primitifs réfractaires ou récidivants [GFELC]"),
    "Prédisposition aux hémopathies malignes de l'enfant et de l'adolescent":
                                                     ("F-95", "Prédisposition aux hémopathies malignes de l'enfant et de l'adolescent [SFCE]"),
}


def translate_filiere(preindication_name: str) -> tuple[str, str] | None:
    """Return (PFMG filière code, full display label) for a SeqOIA preindication name."""
    result = FILIERE.get(preindication_name)
    if result is None:
        logger.warning(
            "SeqOIA preindication name %r has no PFMG filière mapping - PV1.14 will be empty",
            preindication_name,
        )
    return result
