import pandas as pd
from rappresentativita import analizza_rappresentativita
import json
from i18n import (
    t, t_level, lang_name,
    STATUS_COMPLIANT, STATUS_ATTENTION, STATUS_NON_COMPLIANT,
    LEVEL_HIGH, LEVEL_MEDIUM, LEVEL_LOW,
)
from llm_settings import get_client, get_model


def analizza_completezza(df):
    totale_celle = df.shape[0] * df.shape[1]
    totale_mancanti = df.isnull().sum().sum()
    pct_totale = round(totale_mancanti / totale_celle * 100, 2)

    dettaglio = []
    for col in df.columns:
        n_mancanti = df[col].isnull().sum()
        pct = round(n_mancanti / df.shape[0] * 100, 2)
        if n_mancanti > 0:
            gravita = LEVEL_HIGH if pct > 15 else LEVEL_MEDIUM if pct > 5 else LEVEL_LOW
            dettaglio.append({
                t("col_column"): col,
                t("col_missing_values"): n_mancanti,
                "%": f"{pct}%",
                t("col_severity"): t_level(gravita)
            })

    if pct_totale < 5:
        stato = STATUS_COMPLIANT
    elif pct_totale < 15:
        stato = STATUS_ATTENTION
    else:
        stato = STATUS_NON_COMPLIANT

    return {"stato": stato, "pct_totale": pct_totale, "dettaglio": dettaglio}


def valuta_duplicati_llm(df, descrizione, n_duplicati, pct_duplicati):
    """
    Asks the LLM whether the duplicates found are legitimate in the context of the use case.
    """
    duplicati_df = df[df.duplicated(keep=False)]
    esempio = duplicati_df.head(2).to_dict(orient="records") if len(duplicati_df) > 0 else []

    prompt = f"""You are a data quality expert for high-risk AI systems (AI Act, Art. 10).

{n_duplicati} duplicate rows were found in the dataset ({pct_duplicati}% of the total).

DATASET USE CASE: {descrizione}

EXAMPLE OF DUPLICATE ROWS:
{json.dumps(esempio, indent=2, default=str)}

Answer this question: in the context of this use case, are the duplicates a problem, or could they be legitimate?

Reply concisely (2-3 lines) explaining whether the duplicates should be removed or can be kept, and why. Reply in {lang_name()}."""

    try:
        client = get_client()
        response = client.chat.completions.create(
            model=get_model(),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.2
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return t("llm_generic_error", error=str(e))


def controlla_formato_llm(df, descrizione):
    """
    Asks the LLM to check whether the column formats are consistent.
    """
    campioni = {}
    for col in df.columns:
        valori = df[col].dropna().unique()[:8]
        campioni[col] = [str(v) for v in valori]

    prompt = f"""You are a data quality expert for AI systems.

Check whether the data formats in the following columns are consistent and correct.

USE CASE: {descrizione}

SAMPLE VALUES PER COLUMN:
{json.dumps(campioni, indent=2)}

Identify any format issues such as:
- Dates written in different formats
- Numbers with inconsistent formatting
- Text with mixed uppercase/lowercase
- Values that seem impossible or out of range
- Codes or IDs with different formats

Reply ONLY in this JSON format:
{{
  "problemi": [
    {{
      "colonna": "column_name",
      "problema": "description of the problem",
      "gravita": "HIGH|MEDIUM|LOW"
    }}
  ]
}}

Write the "problema" text in {lang_name()}.

If there are no format issues, reply with an empty list: {{"problemi": []}}"""

    try:
        client = get_client()
        response = client.chat.completions.create(
            model=get_model(),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.1
        )
        testo = response.choices[0].message.content.strip()
        testo = testo.replace("```json", "").replace("```", "").strip()
        risultato = json.loads(testo)
        return risultato.get("problemi", [])
    except Exception:
        return []


_SEVERITY_CODE_MAP = {"high": LEVEL_HIGH, "medium": LEVEL_MEDIUM, "low": LEVEL_LOW,
                       "alta": LEVEL_HIGH, "media": LEVEL_MEDIUM, "bassa": LEVEL_LOW}


def _normalizza_gravita(valore):
    return _SEVERITY_CODE_MAP.get(str(valore).strip().lower(), LEVEL_MEDIUM)


def analizza_errori(df, descrizione=""):
    dettaglio = []
    severita_rilevate = []
    commento_duplicati = None
    has_outliers = False

    # ── Duplicates ────────────────────────────────────────────────────────────
    n_duplicati = df.duplicated().sum()
    pct_duplicati = round(n_duplicati / df.shape[0] * 100, 2)
    if n_duplicati > 0:
        gravita = LEVEL_HIGH if pct_duplicati > 10 else LEVEL_MEDIUM if pct_duplicati > 5 else LEVEL_LOW
        severita_rilevate.append(gravita)
        dettaglio.append({
            t("col_column"): t("whole_dataset"),
            t("col_problem_detected"): t("duplicates_detected", n=n_duplicati, pct=pct_duplicati),
            t("col_severity"): t_level(gravita)
        })
        if descrizione:
            commento_duplicati = valuta_duplicati_llm(df, descrizione, n_duplicati, pct_duplicati)

    # ── Outliers via IQR — excludes binary columns ───────────────────────────
    for col in df.select_dtypes(include=["number"]).columns:
        # Skip binary columns (only 2 unique values, e.g. 0/1)
        if df[col].nunique() <= 2:
            continue
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        outliers = df[(df[col] < Q1 - 1.5 * IQR) | (df[col] > Q3 + 1.5 * IQR)]
        n_outlier = len(outliers)
        if n_outlier > 0:
            pct_out = round(n_outlier / df.shape[0] * 100, 2)
            gravita = LEVEL_HIGH if pct_out > 5 else LEVEL_MEDIUM if pct_out > 1 else LEVEL_LOW
            severita_rilevate.append(gravita)
            has_outliers = True
            dettaglio.append({
                t("col_column"): col,
                t("col_problem_detected"): t("outliers_detected", n=n_outlier, pct=pct_out),
                t("col_severity"): t_level(gravita)
            })

    # ── Data format check with LLM ────────────────────────────────────────────
    if descrizione:
        problemi_formato = controlla_formato_llm(df, descrizione)
        for p in problemi_formato:
            gravita = _normalizza_gravita(p.get("gravita", "medium"))
            severita_rilevate.append(gravita)
            dettaglio.append({
                t("col_column"): p.get("colonna", ""),
                t("col_problem_detected"): t("format_problem_prefix", text=p.get("problema", "")),
                t("col_severity"): t_level(gravita)
            })

    # ── Final status ──────────────────────────────────────────────────────────
    if LEVEL_HIGH in severita_rilevate:
        stato = STATUS_NON_COMPLIANT
    elif dettaglio:
        stato = STATUS_ATTENTION
    else:
        stato = STATUS_COMPLIANT

    return {
        "stato": stato,
        "dettaglio": dettaglio,
        "commento_duplicati": commento_duplicati,
        "n_duplicati": n_duplicati,
        "has_outliers": has_outliers
    }


def analizza_governance(risposte):
    """
    Computes the governance score from the questionnaire answers.
    - "no" → high-severity problem (NON-COMPLIANT)
    - "unknown" → medium-severity problem (ATTENTION)
    - "yes" → no problem
    """
    problemi = []

    # Collection documentation
    if risposte.get("doc_raccolta") == "no":
        problemi.append({t("col_problem"): t("gov_doc_collection_missing"), t("col_detail"): t("gov_doc_collection_missing_detail"), t("col_severity"): t_level(LEVEL_HIGH)})
    elif risposte.get("doc_raccolta") == "unknown":
        problemi.append({t("col_problem"): t("gov_doc_collection_unknown"), t("col_detail"): t("gov_doc_collection_unknown_detail"), t("col_severity"): t_level(LEVEL_MEDIUM)})

    # Consent
    if risposte.get("consenso") == "no":
        problemi.append({t("col_problem"): t("gov_consent_missing"), t("col_detail"): t("gov_consent_missing_detail"), t("col_severity"): t_level(LEVEL_HIGH)})
    elif risposte.get("consenso") == "unknown":
        problemi.append({t("col_problem"): t("gov_consent_unknown"), t("col_detail"): t("gov_consent_unknown_detail"), t("col_severity"): t_level(LEVEL_MEDIUM)})

    # Labeling
    if risposte.get("etichettati") == "yes":
        if risposte.get("doc_etichettatura") == "no":
            problemi.append({t("col_problem"): t("gov_labeling_criteria_missing"), t("col_detail"): t("gov_labeling_criteria_missing_detail"), t("col_severity"): t_level(LEVEL_HIGH)})
        elif risposte.get("doc_etichettatura") == "unknown":
            problemi.append({t("col_problem"): t("gov_labeling_criteria_unknown"), t("col_detail"): t("gov_labeling_criteria_unknown_detail"), t("col_severity"): t_level(LEVEL_MEDIUM)})

    # Cleaning
    if risposte.get("pulizia") == "yes":
        if risposte.get("doc_pulizia") == "no":
            problemi.append({t("col_problem"): t("gov_cleaning_undocumented"), t("col_detail"): t("gov_cleaning_undocumented_detail"), t("col_severity"): t_level(LEVEL_HIGH)})
        elif risposte.get("doc_pulizia") == "unknown":
            problemi.append({t("col_problem"): t("gov_cleaning_unknown"), t("col_detail"): t("gov_cleaning_unknown_detail"), t("col_severity"): t_level(LEVEL_MEDIUM)})

    # Data card
    if risposte.get("data_card") == "no":
        problemi.append({t("col_problem"): t("gov_data_card_missing"), t("col_detail"): t("gov_data_card_missing_detail"), t("col_severity"): t_level(LEVEL_HIGH)})
    elif risposte.get("data_card") == "unknown":
        problemi.append({t("col_problem"): t("gov_data_card_unknown"), t("col_detail"): t("gov_data_card_unknown_detail"), t("col_severity"): t_level(LEVEL_MEDIUM)})

    # ── Sezione GDPR ─────────────────────────────────────────────────────────
    if risposte.get("base_giuridica") == "Non lo so":
        problemi.append({"Problema": "Base giuridica GDPR non documentata", "Dettaglio": "Non è nota la base giuridica per il trattamento dei dati (Art. 6 GDPR)", "Gravità": "ALTA"})

    if risposte.get("categorie_speciali") == "Sì":
        if risposte.get("consenso_esplicito") == "No":
            problemi.append({"Problema": "Consenso esplicito assente — categorie speciali", "Dettaglio": "Il dataset contiene categorie speciali (Art. 9 GDPR) ma non è stato ottenuto consenso esplicito", "Gravità": "ALTA"})
        elif risposte.get("consenso_esplicito") == "Non lo so":
            problemi.append({"Problema": "Consenso esplicito — informazione non disponibile", "Dettaglio": "Non è noto se il consenso esplicito per le categorie speciali è stato ottenuto (Art. 9 GDPR)", "Gravità": "MEDIA"})

    if risposte.get("informativa_ai") == "No":
        problemi.append({"Problema": "Informativa sull'uso AI assente", "Dettaglio": "Le persone non sono state informate che i dati sarebbero stati usati per addestrare un sistema AI (Art. 13 GDPR)", "Gravità": "ALTA"})
    elif risposte.get("informativa_ai") == "Non lo so":
        problemi.append({"Problema": "Informativa sull'uso AI — informazione non disponibile", "Dettaglio": "Non è noto se le persone sono state informate dell'uso AI dei loro dati (Art. 13 GDPR)", "Gravità": "MEDIA"})

    gravita_alta_label = t_level(LEVEL_HIGH)
    
    if any(p[t("col_severity")] == gravita_alta_label for p in problemi):
        stato = STATUS_NON_COMPLIANT
    elif problemi:
        stato = STATUS_ATTENTION
    else:
        stato = STATUS_COMPLIANT

    return {"stato": stato, "dettaglio": problemi}


def calcola_score_aggregato(risultati):
    pesi = {
        "bias":              0.25,
        "rappresentativita": 0.20,
        "governance":        0.20,
        "completezza":       0.15,
        "errori":            0.10,
        "rilevanza":         0.10,
    }

    punteggi = {
        STATUS_COMPLIANT:     1.0,
        STATUS_ATTENTION:     0.5,
        STATUS_NON_COMPLIANT: 0.0
    }

    score = 0
    peso_totale = 0
    for dim, peso in pesi.items():
        if dim in risultati:
            score += punteggi.get(risultati[dim]["stato"], 0) * peso
            peso_totale += peso

    if peso_totale > 0:
        score = score / peso_totale

    return round(score * 100, 1)
