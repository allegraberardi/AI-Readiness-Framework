import pandas as pd
import streamlit as st
from i18n import (
    t, t_level, t_status, lang_name, status_emoji, sector_label_en,
    STATUS_COMPLIANT, STATUS_ATTENTION, STATUS_NON_COMPLIANT,
    LEVEL_HIGH, LEVEL_MEDIUM, LEVEL_LOW,
)
from llm_settings import get_client, get_model

# ── Demographic variables relevant per sector ─────────────────────────────────
VARIABILI_PER_SETTORE = {
    "employment": {
        "keywords": ["gender", "genere", "sex", "sesso", "age", "età", "eta",
                     "education", "istruzione", "nationality", "nazionalità", "country"],
        "focus_key": "sector_focus_employment",
        "reason_key": "sector_reason_employment",
    },
    "essential_services": {
        "keywords": ["gender", "genere", "sex", "sesso", "age", "età", "eta",
                     "income", "reddito", "race", "razza", "ethnicity", "etnia",
                     "education", "istruzione"],
        "focus_key": "sector_focus_essential_services",
        "reason_key": "sector_reason_essential_services",
    },
    "law_enforcement": {
        "keywords": ["race", "razza", "ethnicity", "etnia", "nationality",
                     "nazionalità", "age", "età", "eta", "gender", "genere"],
        "focus_key": "sector_focus_law_enforcement",
        "reason_key": "sector_reason_law_enforcement",
    },
    "education": {
        "keywords": ["country", "paese", "nationality", "nazionalità", "gender",
                     "genere", "sex", "sesso", "age", "età", "eta"],
        "focus_key": "sector_focus_education",
        "reason_key": "sector_reason_education",
    },
    "justice": {
        "keywords": ["race", "razza", "ethnicity", "etnia", "age", "età", "eta",
                     "gender", "genere", "income", "reddito"],
        "focus_key": "sector_focus_justice",
        "reason_key": "sector_reason_justice",
    },
    "migration": {
        "keywords": ["nationality", "nazionalità", "country", "paese",
                     "religion", "religione", "age", "età", "eta", "gender", "genere"],
        "focus_key": "sector_focus_migration",
        "reason_key": "sector_reason_migration",
    },
    "biometrics": {
        "keywords": ["race", "razza", "ethnicity", "etnia", "gender", "genere",
                     "age", "età", "eta", "skin", "pelle"],
        "focus_key": "sector_focus_biometrics",
        "reason_key": "sector_reason_biometrics",
    },
    "critical_infrastructure": {
        "keywords": ["region", "regione", "area", "zone", "zona", "location", "posizione"],
        "focus_key": "sector_focus_critical_infrastructure",
        "reason_key": "sector_reason_critical_infrastructure",
    },
}


def analizza_rappresentativita(df, settore=None):
    """
    Full representativeness analysis with statistics for each column.
    """
    dettaglio_categoriche = []
    dettaglio_numeriche = []
    problemi = []

    # ── Categorical columns ───────────────────────────────────────────────────
    for col in df.select_dtypes(include=["object", "category"]).columns:
        conteggi = df[col].value_counts()
        min_classe = conteggi.min()
        classe_min = conteggi.idxmin()
        pct_min = round(min_classe / df.shape[0] * 100, 2)

        if min_classe < 50:
            gravita = LEVEL_HIGH
        elif min_classe < 100:
            gravita = LEVEL_MEDIUM
        else:
            gravita = LEVEL_LOW

        dettaglio_categoriche.append({
            "colonna": col,
            "conteggi": conteggi,
            "min_classe": min_classe,
            "classe_min": classe_min,
            "pct_min": pct_min,
            "gravita": gravita
        })

        if min_classe < 100:
            problemi.append({
                t("col_column"): col,
                t("col_problem"): t("repr_class_problem", cls=classe_min, n=min_classe, pct=pct_min),
                t("col_severity"): t_level(gravita)
            })

    # ── Numeric columns ───────────────────────────────────────────────────────
    for col in df.select_dtypes(include=["number"]).columns:
        dettaglio_numeriche.append({
            t("col_column"): col,
            t("col_min"): round(df[col].min(), 2),
            t("col_max"): round(df[col].max(), 2),
            t("col_mean"): round(df[col].mean(), 2),
            t("col_median"): round(df[col].median(), 2),
            t("col_unique_values"): df[col].nunique()
        })

    # ── Contextual analysis by sector ────────────────────────────────────────
    contestuale = None
    if settore and settore in VARIABILI_PER_SETTORE:
        config = VARIABILI_PER_SETTORE[settore]
        colonne_rilevanti = []
        for col in df.columns:
            col_lower = col.lower().replace(" ", "_")
            for kw in config["keywords"]:
                if kw in col_lower:
                    colonne_rilevanti.append(col)
                    break

        contestuale = {
            "trovate": len(colonne_rilevanti) > 0,
            "colonne_trovate": colonne_rilevanti,
            "focus": t(config["focus_key"]),
            "motivo": t(config["reason_key"]),
        }

    # ── Final status ─────────────────────────────────────────────────────────
    if any(p[t("col_severity")] == t_level(LEVEL_HIGH) for p in problemi):
        stato = STATUS_NON_COMPLIANT
    elif problemi:
        stato = STATUS_ATTENTION
    else:
        stato = STATUS_COMPLIANT

    return {
        "stato": stato,
        "problemi": problemi,
        "categoriche": dettaglio_categoriche,
        "numeriche": dettaglio_numeriche,
        "contestuale": contestuale
    }


def commento_llm_rappresentativita(df, settore, descrizione, risultato):
    """
    Asks the LLM to interpret the representativeness results.
    """
    riassunto = []
    for cat in risultato["categoriche"]:
        top = cat["conteggi"].head(3).to_dict()
        riassunto.append(
            f"{cat['colonna']}: distribution {top}, "
            f"minimum class '{cat['classe_min']}' with {cat['min_classe']} examples ({cat['pct_min']}%)"
        )

    for num in risultato["numeriche"]:
        values = list(num.values())
        riassunto.append(
            f"{values[0]}: min={values[1]}, max={values[2]}, mean={values[3]}"
        )

    settore_en = sector_label_en(settore)

    prompt = f"""You are an expert in AI fairness and the EU Artificial Intelligence Act (AI Act).

Analyze the representativeness of this dataset in relation to the described use case.

USE CASE: {descrizione}
SECTOR (AI Act, Annex III): {settore_en}

DATA DISTRIBUTION:
{chr(10).join(riassunto)}

Provide:
1. An assessment of the representativeness in relation to the use case
2. Any underrepresented groups that could cause problems
3. A concrete recommendation to improve representativeness

Be concise (5 lines maximum) and refer to Art. 10 of the AI Act where relevant. Reply in {lang_name()}."""

    try:
        client = get_client()
        response = client.chat.completions.create(
            model=get_model(),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.2
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return t("llm_generic_error", error=str(e))


def mostra_rappresentativita_con_grafici(risultato, descrizione, settore, df):
    """
    Shows the representativeness results with charts and an LLM comment.
    """
    stato = risultato["stato"]
    emoji = status_emoji(stato)

    st.markdown(f"### {emoji} {t('dim_representativeness')} — {t_status(stato)}")
    st.caption(f"📖 {t('ref_representativeness')}")

    if stato == STATUS_COMPLIANT:
        st.success(t("representativeness_ok"))
    elif stato == STATUS_ATTENTION:
        st.warning(t("representativeness_attention"))
    else:
        st.error(t("representativeness_bad"))

    # ── Categorical column charts ─────────────────────────────────────────────
    if risultato["categoriche"]:
        st.write(t("categorical_distribution_label"))
        for cat in risultato["categoriche"]:
            with st.expander(t("expander_col", col=cat["colonna"], cls=cat["classe_min"], pct=cat["pct_min"])):
                st.bar_chart(cat["conteggi"])

    # ── Numeric column statistics ─────────────────────────────────────────────
    if risultato["numeriche"]:
        st.write(t("numeric_stats_label"))
        df_num = pd.DataFrame(risultato["numeriche"])
        st.dataframe(df_num, use_container_width=True, hide_index=True)

    # ── Contextual analysis by sector ────────────────────────────────────────
    contestuale = risultato.get("contestuale")
    if contestuale:
        st.write("---")
        st.write(t("contextual_analysis_label"))
        st.info(t("contextual_focus_info", focus=contestuale['focus'], reason=contestuale['motivo']))

        if not contestuale.get("trovate"):
            st.warning(t("contextual_not_found"))
        else:
            st.write(t("contextual_columns_found", cols=", ".join(contestuale.get('colonne_trovate', []))))

    # ── LLM comment ───────────────────────────────────────────────────────────
    st.write("---")
    st.write(t("llm_interpretation_label"))
    with st.spinner(t("representativeness_llm_spinner")):
        commento = commento_llm_rappresentativita(df, settore, descrizione, risultato)
    st.info(commento)

    # ── Thresholds ────────────────────────────────────────────────────────────
    with st.expander(t("thresholds_expander")):
        st.write(f"**{status_emoji(STATUS_COMPLIANT)} {t_status(STATUS_COMPLIANT)}**: {t('thr_representativeness_compliant')}")
        st.write(f"**{status_emoji(STATUS_ATTENTION)} {t_status(STATUS_ATTENTION)}**: {t('thr_representativeness_attention')}")
        st.write(f"**{status_emoji(STATUS_NON_COMPLIANT)} {t_status(STATUS_NON_COMPLIANT)}**: {t('thr_representativeness_non_compliant')}")

    st.divider()
