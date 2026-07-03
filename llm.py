import json
import streamlit as st
from i18n import t, lang_name, sector_label_en
from llm_settings import get_client, get_model


def identifica_attributi_sensibili(descrizione, settore, colonne):
    """
    Uses an LLM to automatically identify the target column and sensitive
    attributes from the use case description.
    """
    client = get_client()
    settore_en = sector_label_en(settore)

    prompt = f"""You are an expert in AI fairness and the EU Artificial Intelligence Act (AI Act).

You are given:
1. A description of the use case of a high-risk AI system
2. The application sector (AI Act, Annex III)
3. The list of columns present in the dataset

Your task is to identify:
- The TARGET column: the one the AI model will predict (e.g. approved/rejected, hired/not hired)
- The SENSITIVE ATTRIBUTES: columns that represent protected demographic characteristics such as gender, age, ethnicity, nationality, religion, disability, or variables that could be a proxy for these characteristics

USE CASE: {descrizione}
SECTOR: {settore_en}
DATASET COLUMNS: {', '.join(colonne)}

Reply ONLY in this JSON format, with no extra text:
{{
  "target": "target_column_name",
  "attributi_sensibili": ["column1", "column2"],
  "spiegazione": "Brief explanation of the choices made, referring to Art. 10 of the AI Act"
}}

Write the "spiegazione" field in {lang_name()}.

If you cannot identify the target or sensitive attributes with confidence, set target to null and use an empty list for the sensitive attributes."""

    try:
        response = client.chat.completions.create(
            model=get_model(),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.1
        )

        testo = response.choices[0].message.content.strip()
        testo = testo.replace("```json", "").replace("```", "").strip()
        risultato = json.loads(testo)

        # Check that the suggested columns exist in the dataset
        if risultato.get("target") not in colonne:
            risultato["target"] = None
        risultato["attributi_sensibili"] = [
            col for col in risultato.get("attributi_sensibili", [])
            if col in colonne
        ]

        return risultato

    except Exception as e:
        return {
            "target": None,
            "attributi_sensibili": [],
            "spiegazione": t("llm_generic_error", error=str(e))
        }


def mostra_suggerimenti_llm(df, descrizione, settore):
    """
    Shows the LLM suggestions and lets the user confirm or edit them.
    """
    st.subheader(t("llm_auto_analysis_title"))

    with st.spinner(t("llm_spinner_usecase")):
        suggerimenti = identifica_attributi_sensibili(
            descrizione, settore, list(df.columns)
        )

    if suggerimenti.get("spiegazione"):
        st.info(t("llm_analysis_info", text=suggerimenti["spiegazione"]))

    colonne = [None] + list(df.columns)
    target_suggerito = suggerimenti.get("target")
    target_default = target_suggerito if target_suggerito in df.columns else None

    target = st.selectbox(
        t("target_suggested_label"),
        colonne,
        index=colonne.index(target_default) if target_default in colonne else 0,
        format_func=lambda c: t("no_dimension_option") if c is None else c,
        key="bias_target"
    )

    if target is not None:
        attributi_suggeriti = suggerimenti.get("attributi_sensibili", [])
        attributi_validi = [col for col in attributi_suggeriti if col in df.columns and col != target]

        attributi = st.multiselect(
            t("attrs_suggested_label"),
            [col for col in df.columns if col != target],
            default=attributi_validi,
            key="bias_attributi"
        )
    else:
        attributi = []

    return target, attributi
