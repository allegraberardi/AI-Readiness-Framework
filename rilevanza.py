import pandas as pd
import json
from i18n import (
    t, t_level, lang_name, sector_label_en,
    STATUS_COMPLIANT, STATUS_ATTENTION, STATUS_NON_COMPLIANT,
    LEVEL_HIGH, LEVEL_MEDIUM, LEVEL_LOW,
)
from llm_settings import get_client, get_model


def pulisci_testo(testo):
    """Removes special characters that could break the JSON."""
    return str(testo).replace('"', "'").replace('\\', '').replace('\n', ' ').strip()


def descrivi_colonna(df, col):
    """
    Generates an automatic description of a column based on
    its data type and the values present.
    """
    dtype = df[col].dtype
    n_unici = df[col].nunique()

    if dtype == "object":
        valori = df[col].dropna().unique()[:5]
        valori_puliti = [pulisci_testo(v) for v in valori]
        return t("desc_categorical", n=n_unici, examples=", ".join(valori_puliti))
    elif dtype in ["int64", "float64"]:
        min_val = round(df[col].min(), 2)
        max_val = round(df[col].max(), 2)
        media = round(df[col].mean(), 2)
        return t("desc_numeric", min=min_val, max=max_val, mean=media)
    else:
        return t("desc_type", dtype=dtype, n=n_unici)


def calcola_rilevanza(df, descrizione, settore):
    """
    Uses the LLM to assess the relevance of each dataset column
    with respect to the use case description and sector.
    """
    if not descrizione or not descrizione.strip():
        return {
            "stato": STATUS_ATTENTION,
            "messaggio": t("no_description_provided"),
            "dettaglio": [],
            "score_medio": 0
        }

    colonne_info = {}
    for col in df.columns:
        colonne_info[col] = descrivi_colonna(df, col)

    colonne_testo = "\n".join([f"- {col}: {desc}" for col, desc in colonne_info.items()])
    settore_en = sector_label_en(settore)

    prompt = f"""You are an expert in AI and the EU Artificial Intelligence Act (AI Act).

You must assess the relevance of each dataset column with respect to the use case described by the user.

USE CASE: {descrizione}
AI ACT SECTOR (Annex III): {settore_en}

DATASET COLUMNS:
{colonne_testo}

For each column assign:
- a score from 0 to 100 indicating how relevant it is to the use case (0 = completely irrelevant, 100 = essential)
- a brief explanation of why

Reply ONLY in this JSON format, with no extra text:
{{
  "valutazioni": [
    {{
      "colonna": "column_name",
      "score": 85,
      "spiegazione": "Brief explanation of why it is or isn't relevant"
    }}
  ],
  "commento_generale": "Overall assessment of the dataset's relevance to the use case"
}}

Write the "spiegazione" and "commento_generale" text in {lang_name()}."""

    try:
        client = get_client()
        response = client.chat.completions.create(
            model=get_model(),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.1
        )

        testo = response.choices[0].message.content.strip()
        testo = testo.replace("```json", "").replace("```", "").strip()
        risultato_llm = json.loads(testo)

        dettaglio = []
        scores = []

        for val in risultato_llm.get("valutazioni", []):
            score = val.get("score", 0)
            scores.append(score)

            if score >= 60:
                rilevanza_level = LEVEL_HIGH
                gravita = LEVEL_LOW
            elif score >= 30:
                rilevanza_level = LEVEL_MEDIUM
                gravita = LEVEL_MEDIUM
            else:
                rilevanza_level = LEVEL_LOW
                gravita = LEVEL_HIGH

            dettaglio.append({
                t("col_column"): val.get("colonna", ""),
                t("col_description"): colonne_info.get(val.get("colonna", ""), ""),
                t("col_relevance_score"): f"{score}/100",
                t("col_relevance"): t_level(rilevanza_level),
                t("col_llm_explanation"): val.get("spiegazione", ""),
                t("col_severity"): t_level(gravita)
            })

        dettaglio = sorted(dettaglio, key=lambda x: int(x[t("col_relevance_score")].split("/")[0]), reverse=True)

        score_medio = round(sum(scores) / len(scores), 1) if scores else 0
        n_irrilevanti = sum(1 for s in scores if s < 30)
        pct_irrilevanti = round(n_irrilevanti / len(scores) * 100, 1) if scores else 0

        commento = risultato_llm.get("commento_generale", "")

        if pct_irrilevanti > 50:
            stato = STATUS_NON_COMPLIANT
        elif pct_irrilevanti > 25 or score_medio < 50:
            stato = STATUS_ATTENTION
        else:
            stato = STATUS_COMPLIANT

        return {
            "stato": stato,
            "score_medio": score_medio,
            "pct_irrilevanti": pct_irrilevanti,
            "commento": commento,
            "dettaglio": dettaglio,
            "messaggio": None
        }

    except Exception as e:
        return {
            "stato": STATUS_ATTENTION,
            "score_medio": 0,
            "pct_irrilevanti": 0,
            "commento": "",
            "dettaglio": [],
            "messaggio": t("llm_generic_error", error=str(e))
        }
