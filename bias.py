import pandas as pd
import streamlit as st
from i18n import (
    t, t_level, lang_name, sector_label_en,
    STATUS_COMPLIANT, STATUS_ATTENTION, STATUS_NON_COMPLIANT,
    LEVEL_HIGH, LEVEL_MEDIUM, LEVEL_LOW,
)

# ── Keywords used to automatically identify sensitive attributes ──────────────
# Based on the special categories in Art. 9 GDPR and protected attributes in the AI Act
KEYWORD_SENSIBILI = {
    # Gender and sex
    "genere_sesso": ["gender", "genere", "sex", "sesso"],

    # Age
    "eta": ["age", "età", "eta", "age_group", "birth", "nascita", "dob", "born"],

    # Racial and ethnic origin (Art. 9 GDPR)
    "etnia": ["race", "razza", "ethnicity", "etnia", "ethnic", "origin", "origine"],

    # Nationality and background
    "nazionalita": ["nationality", "nazionalità", "country", "paese", "nation", "nazione"],

    # Religious and philosophical beliefs (Art. 9 GDPR)
    "religione": ["religion", "religione", "faith", "credo", "church", "chiesa",
                  "belief", "credenza", "confession", "confessione"],

    # Political opinions (Art. 9 GDPR)
    "politica": ["political", "politico", "party", "partito", "vote", "voto",
                 "ideology", "ideologia", "opinion", "opinione"],

    # Sexual orientation and sex life (Art. 9 GDPR)
    "orientamento": ["sexual", "sessuale", "orientation", "orientamento",
                     "lgbt", "gay", "lesbian", "bisexual"],

    # Health data (Art. 9 GDPR)
    "salute": ["health", "salute", "medical", "medico", "disease", "malattia",
               "diagnosis", "diagnosi", "illness", "disorder", "condition",
               "patient", "paziente", "hospital", "ospedale", "clinical"],

    # Disability (Art. 9 GDPR)
    "disabilita": ["disability", "disabilità", "disabled", "disabile",
                   "handicap", "impairment", "special_needs"],

    # Genetic data (Art. 9 GDPR)
    "genetica": ["genetic", "genetico", "dna", "gene", "genome", "genoma",
                 "hereditary", "ereditario"],

    # Biometric data (Art. 9 GDPR)
    "biometria": ["biometric", "biometrico", "fingerprint", "impronta",
                  "facial", "facciale", "iris", "retina", "voice", "voce"],

    # Trade union membership (Art. 9 GDPR)
    "sindacato": ["union", "sindacato", "trade_union", "labor", "labour",
                  "sindacale", "membership"],

    # Income and financial status
    "reddito": ["income", "reddito", "salary", "stipendio", "wage", "earning",
                "wealth", "ricchezza", "poverty", "povertà"],

    # Marital and family status
    "stato_civile": ["marital", "stato_civile", "married", "sposato",
                     "divorced", "divorziato", "family", "famiglia"],

    # Education
    "istruzione": ["education", "istruzione", "degree", "laurea",
                   "school", "scuola", "qualification"],
}

# Flat list for fast lookup
KEYWORD_LISTA = [kw for gruppo in KEYWORD_SENSIBILI.values() for kw in gruppo]


def trova_attributi_sensibili(df):
    """Finds columns whose name resembles a GDPR/AI Act sensitive keyword."""
    trovati = []
    for col in df.columns:
        col_lower = col.lower().replace(" ", "_")
        for keyword in KEYWORD_LISTA:
            if keyword in col_lower:
                trovati.append(col)
                break
    return trovati


def categoria_gdpr(col):
    """Returns the GDPR category of a column if it is sensitive."""
    col_lower = col.lower().replace(" ", "_")
    for categoria, keywords in KEYWORD_SENSIBILI.items():
        for kw in keywords:
            if kw in col_lower:
                return categoria
    return None


def calcola_bias(df, target, attributi_sensibili):
    """
    Computes Statistical Parity Difference, Disparate Impact and Class Imbalance
    for each sensitive attribute relative to the target column.
    Aligned with the AIF360 methodology.
    """
    risultati_dettaglio = []
    stati = []

    # Check that the target is binary
    valori_target = df[target].dropna().unique()
    if len(valori_target) != 2:
        return {
            "stato": STATUS_ATTENTION,
            "messaggio": t("bias_target_not_binary", target=target, n=len(valori_target)),
            "dettaglio": []
        }

    # Positive value = 1 if present, otherwise the maximum value
    valore_positivo = 1 if 1 in valori_target else max(valori_target)

    for attr in attributi_sensibili:
        gruppi = df[attr].dropna().unique()

        if len(gruppi) < 2:
            continue

        # ── Class Imbalance ──────────────────────────────────────────────────
        conteggi = df[attr].value_counts()
        pct_min = round(conteggi.min() / len(df) * 100, 1)
        pct_max = round(conteggi.max() / len(df) * 100, 1)
        imbalance = round(pct_max - pct_min, 1)

        if imbalance > 40:
            ci_gravita = LEVEL_HIGH
        elif imbalance > 20:
            ci_gravita = LEVEL_MEDIUM
        else:
            ci_gravita = LEVEL_LOW

        # ── Proportion of positive outcomes for each group ────────────────────
        proporzioni = {}
        for gruppo in gruppi:
            subset = df[df[attr] == gruppo]
            if len(subset) == 0:
                continue
            prop = len(subset[subset[target] == valore_positivo]) / len(subset)
            proporzioni[gruppo] = round(prop, 4)

        if len(proporzioni) < 2:
            continue

        # Privileged group = the one with the highest proportion
        # Disadvantaged group = the one with the lowest proportion
        gruppo_privilegiato = max(proporzioni, key=proporzioni.get)
        gruppo_svantaggiato = min(proporzioni, key=proporzioni.get)
        prop_privilegiato = proporzioni[gruppo_privilegiato]
        prop_svantaggiato = proporzioni[gruppo_svantaggiato]

        # ── Statistical Parity Difference ─────────────────────────────────────
        # Formula: P(positive | disadvantaged) - P(positive | privileged)
        # Ideal value = 0, negative = discrimination
        spd = round(prop_svantaggiato - prop_privilegiato, 4)
        spd_abs = abs(spd)

        if spd_abs > 0.2:
            spd_gravita = LEVEL_HIGH
        elif spd_abs > 0.1:
            spd_gravita = LEVEL_MEDIUM
        else:
            spd_gravita = LEVEL_LOW

        # ── Disparate Impact ────────────────────────────────────────────────────
        # Formula: P(positive | disadvantaged) / P(positive | privileged)
        # Ideal value = 1.0, fair if >= 0.8 and <= 1.25
        if prop_privilegiato > 0:
            di = round(prop_svantaggiato / prop_privilegiato, 4)
        else:
            di = 0

        if di < 0.6 or di > 1.4:
            di_gravita = LEVEL_HIGH
        elif di < 0.8 or di > 1.25:
            di_gravita = LEVEL_MEDIUM
        else:
            di_gravita = LEVEL_LOW

        # ── Overall severity ─────────────────────────────────────────────────
        gravita_valori = {LEVEL_HIGH: 3, LEVEL_MEDIUM: 2, LEVEL_LOW: 1}
        gravita_max = max(
            gravita_valori[spd_gravita],
            gravita_valori[di_gravita],
            gravita_valori[ci_gravita]
        )
        gravita_complessiva = {3: LEVEL_HIGH, 2: LEVEL_MEDIUM, 1: LEVEL_LOW}[gravita_max]

        risultati_dettaglio.append({
            t("col_attribute"): attr,
            t("col_privileged_group"): f"{gruppo_privilegiato} ({round(prop_privilegiato*100,2)}%)",
            t("col_disadvantaged_group"): f"{gruppo_svantaggiato} ({round(prop_svantaggiato*100,2)}%)",
            t("col_spd"): f"{spd} {t('spd_threshold_note')}",
            t("col_di"): f"{di} {t('di_threshold_note')}",
            t("col_class_imbalance"): t("class_imbalance_note", pct=imbalance),
            t("col_severity"): t_level(gravita_complessiva),
        })

        stati.append(gravita_complessiva)

    # ── Final status ─────────────────────────────────────────────────────────
    if not stati:
        return {
            "stato": STATUS_ATTENTION,
            "messaggio": t("bias_cannot_calculate"),
            "dettaglio": []
        }

    if LEVEL_HIGH in stati:
        stato = STATUS_NON_COMPLIANT
    elif LEVEL_MEDIUM in stati:
        stato = STATUS_ATTENTION
    else:
        stato = STATUS_COMPLIANT

    return {
        "stato": stato,
        "dettaglio": risultati_dettaglio
    }


def commento_llm_bias(risultati_dettaglio, descrizione, settore, target):
    """
    Asks the LLM to interpret the bias results in the context of the use case.
    """
    from llm_settings import get_client, get_model

    client = get_client()

    riassunto = []
    for r in risultati_dettaglio:
        values = list(r.values())
        riassunto.append(
            f"Attribute: {values[0]} — "
            f"Privileged group: {values[1]} — "
            f"Disadvantaged group: {values[2]} — "
            f"Statistical Parity Difference: {values[3]} — "
            f"Disparate Impact: {values[4]} — "
            f"Class Imbalance: {values[5]} — "
            f"Severity: {values[6]}"
        )

    settore_en = sector_label_en(settore)

    prompt = f"""You are an expert in AI fairness and the EU Artificial Intelligence Act (AI Act).

Analyze the bias results for this dataset and provide a contextualized assessment.

USE CASE: {descrizione}
SECTOR (AI Act, Annex III): {settore_en}
TARGET VARIABLE: {target}

BIAS ANALYSIS RESULTS:
{chr(10).join(riassunto)}

Provide:
1. An overall assessment of the bias in the dataset in relation to the use case
2. The groups most at risk of discrimination
3. A concrete recommendation to mitigate bias, referring to Art. 10(2)(f) and (g) of the AI Act

Be concise (5 lines maximum) and precise. Reply in {lang_name()}."""

    try:
        response = client.chat.completions.create(
            model=get_model(),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.2
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return t("llm_generic_error", error=str(e))
