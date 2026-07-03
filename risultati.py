import streamlit as st
import pandas as pd
from analisi import (
    analizza_completezza,
    analizza_errori,
    analizza_governance,
    calcola_score_aggregato
)
from rappresentativita import analizza_rappresentativita, mostra_rappresentativita_con_grafici
from bias import calcola_bias, commento_llm_bias
from rilevanza import calcola_rilevanza
from i18n import (
    t, t_status, status_emoji, sector_label,
    STATUS_COMPLIANT, STATUS_ATTENTION, STATUS_NON_COMPLIANT,
)


def semaforo(stato):
    return status_emoji(stato)


# Thresholds for each dimension, keyed by dimension code
THRESHOLDS = {
    "completeness": ["thr_completeness_compliant", "thr_completeness_attention", "thr_completeness_non_compliant"],
    "errors": ["thr_errors_compliant", "thr_errors_attention", "thr_errors_non_compliant"],
    "bias": ["thr_bias_compliant", "thr_bias_attention", "thr_bias_non_compliant"],
    "relevance": ["thr_relevance_compliant", "thr_relevance_attention", "thr_relevance_non_compliant"],
    "governance": ["thr_governance_compliant", "thr_governance_attention", "thr_governance_non_compliant"],
}

STATUS_ORDER = [STATUS_COMPLIANT, STATUS_ATTENTION, STATUS_NON_COMPLIANT]


def mostra_soglie(dimension_code):
    with st.expander(t("thresholds_expander")):
        for status_code, key in zip(STATUS_ORDER, THRESHOLDS[dimension_code]):
            st.write(f"**{status_emoji(status_code)} {t_status(status_code)}**: {t(key)}")


def mostra_dimensione(dimension_code, risultato, raccomandazione, commento_extra=None):
    stato = risultato["stato"]
    emoji = semaforo(stato)
    titolo = t(f"dim_{dimension_code}")
    riferimento = t(f"ref_{dimension_code}")

    with st.container():
        st.markdown(f"### {emoji} {titolo} — {t_status(stato)}")
        st.caption(f"📖 {riferimento}")

        if stato == STATUS_COMPLIANT:
            st.success(raccomandazione)
        elif stato == STATUS_ATTENTION:
            st.warning(raccomandazione)
        else:
            st.error(raccomandazione)

        if risultato.get("messaggio"):
            st.info(risultato["messaggio"])

        if commento_extra:
            st.info(t("duplicates_llm_comment_label", text=commento_extra))

        if risultato.get("dettaglio"):
            df_det = pd.DataFrame(risultato["dettaglio"])
            st.dataframe(df_det, use_container_width=True, hide_index=True)

        mostra_soglie(dimension_code)

        st.divider()


def mostra_risultati():
    st.title(t("results_title"))
    st.write(t("results_sector_label", sector=sector_label(st.session_state.settore)))

    df = st.session_state.dataset
    governance = st.session_state.governance
    descrizione = st.session_state.descrizione
    settore = st.session_state.settore
    target = st.session_state.get("target")
    attributi_sensibili = st.session_state.get("attributi_sensibili", [])

    # ── Run the analyses ─────────────────────────────────────────────────────
    with st.spinner(t("results_spinner")):
        res_completezza = analizza_completezza(df)
        res_rappresentativita = analizza_rappresentativita(df, settore)
        res_errori = analizza_errori(df, descrizione)
        res_governance = analizza_governance(governance)
        res_rilevanza = calcola_rilevanza(df, descrizione, settore)

        if target and attributi_sensibili:
            res_bias = calcola_bias(df, target, attributi_sensibili)
        else:
            res_bias = {
                "stato": STATUS_ATTENTION,
                "dettaglio": [],
                "messaggio": t("bias_not_evaluated")
            }

    risultati = {
        "completezza": res_completezza,
        "rappresentativita": res_rappresentativita,
        "errori": res_errori,
        "governance": res_governance,
        "bias": res_bias,
        "rilevanza": res_rilevanza,
    }

    # ── Aggregate score ──────────────────────────────────────────────────────
    score = calcola_score_aggregato(risultati)

    # ── Status summary ───────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    col4, col5, col6 = st.columns(3)

    with col1:
        st.metric(t("metric_completeness"), f"{semaforo(res_completezza['stato'])} {t_status(res_completezza['stato'])}")
    with col2:
        st.metric(t("metric_representativeness"), f"{semaforo(res_rappresentativita['stato'])} {t_status(res_rappresentativita['stato'])}")
    with col3:
        st.metric(t("metric_errors"), f"{semaforo(res_errori['stato'])} {t_status(res_errori['stato'])}")
    with col4:
        st.metric(t("metric_governance"), f"{semaforo(res_governance['stato'])} {t_status(res_governance['stato'])}")
    with col5:
        st.metric(t("metric_bias"), f"{semaforo(res_bias['stato'])} {t_status(res_bias['stato'])}")
    with col6:
        st.metric(t("metric_relevance"), f"{semaforo(res_rilevanza['stato'])} {t_status(res_rilevanza['stato'])}")

    st.divider()

    # ── Final score ──────────────────────────────────────────────────────────
    if score >= 70:
        st.success(t("score_title_high", score=score))
    elif score >= 40:
        st.warning(t("score_title_mid", score=score))
    else:
        st.error(t("score_title_low", score=score))

    st.divider()

    # ── Detail per dimension ─────────────────────────────────────────────────
    # Relevance with LLM comment
    with st.container():
        stato_rile = res_rilevanza["stato"]
        emoji_rile = semaforo(stato_rile)
        st.markdown(f"### {emoji_rile} {t('dim_relevance')} — {t_status(stato_rile)}")
        st.caption(f"📖 {t('ref_relevance')}")

        raccomandazione_rile = t("relevance_avg_score", score=res_rilevanza.get('score_medio', 0)) + (
            t("relevance_ok") if stato_rile == STATUS_COMPLIANT
            else t("relevance_low", pct=res_rilevanza.get('pct_irrilevanti', 0))
        )

        if stato_rile == STATUS_COMPLIANT:
            st.success(raccomandazione_rile)
        elif stato_rile == STATUS_ATTENTION:
            st.warning(raccomandazione_rile)
        else:
            st.error(raccomandazione_rile)

        if res_rilevanza.get("messaggio"):
            st.info(res_rilevanza["messaggio"])

        if res_rilevanza.get("commento"):
            st.info(t("llm_comment_label", text=res_rilevanza['commento']))

        if res_rilevanza.get("dettaglio"):
            st.write(t("detail_by_column"))
            df_rile = pd.DataFrame(res_rilevanza["dettaglio"])
            st.dataframe(df_rile, use_container_width=True, hide_index=True)

        mostra_soglie("relevance")

        st.divider()

    mostra_dimensione(
        dimension_code="completeness",
        risultato=res_completezza,
        raccomandazione=(
            t("completeness_recommendation_ok", pct=res_completezza['pct_totale'])
            if res_completezza["stato"] == STATUS_COMPLIANT
            else t("completeness_recommendation_bad", pct=res_completezza['pct_totale'])
        )
    )

    # Representativeness with charts and LLM
    mostra_rappresentativita_con_grafici(res_rappresentativita, descrizione, settore, df)

    # Specific recommendation based on the type of problem
    n_dup = res_errori.get("n_duplicati", 0)
    has_out = res_errori.get("has_outliers", False)
    if n_dup > 0 and has_out:
        raccomandazione_errori = t("errors_recommendation_both", n=n_dup)
    elif n_dup > 0:
        raccomandazione_errori = t("errors_recommendation_dup", n=n_dup)
    elif has_out:
        raccomandazione_errori = t("errors_recommendation_out")
    else:
        raccomandazione_errori = t("errors_recommendation_none")

    mostra_dimensione(
        dimension_code="errors",
        risultato=res_errori,
        raccomandazione=raccomandazione_errori,
        commento_extra=res_errori.get("commento_duplicati")
    )

    # Boxplot for numeric columns with outliers
    colonna_key = t("col_column")
    problema_key = t("col_problem_detected")
    gravita_key = t("col_severity")
    colonne_outlier = [
        d[colonna_key] for d in res_errori.get("dettaglio", [])
        if "outlier" in d.get(problema_key, "") and d[colonna_key] != t("whole_dataset")
    ]
    if colonne_outlier:
        try:
            import plotly.express as px
            st.write(t("outlier_boxplot_label"))
            st.caption(t("outlier_boxplot_caption"))
            for col in colonne_outlier:
                if col in df.columns:
                    gravita = next(
                        (d[gravita_key] for d in res_errori.get("dettaglio", [])
                         if d[colonna_key] == col), "")
                    with st.expander(t("outlier_expander_label", col=col, severity=gravita)):
                        fig = px.box(
                            df, y=col,
                            title=t("outlier_chart_title", col=col),
                            points="outliers",
                            color_discrete_sequence=["#2563EB"]
                        )
                        fig.update_layout(
                            height=350,
                            showlegend=False,
                            yaxis_title=col,
                            xaxis_title=""
                        )
                        st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            st.warning(t("install_plotly_warning"))

    # Messaggio se nessun duplicato
    if n_dup == 0 and res_errori["stato"] != "CONFORME":
        pass  # già gestito dalla raccomandazione

    # Assenza di bias con commento LLM
    # Absence of bias with LLM comment
    with st.container():
        stato_bias = res_bias["stato"]
        emoji_bias = semaforo(stato_bias)
        st.markdown(f"### {emoji_bias} {t('dim_bias')} — {t_status(stato_bias)}")
        st.caption(f"📖 {t('ref_bias')}")

        if stato_bias == STATUS_COMPLIANT:
            st.success(t("bias_none"))
        elif stato_bias == STATUS_ATTENTION:
            st.warning(t("bias_moderate"))
        else:
            st.error(t("bias_high"))

        if res_bias.get("messaggio"):
            st.info(res_bias["messaggio"])

        if res_bias.get("dettaglio"):
            df_bias = pd.DataFrame(res_bias["dettaglio"])
            st.dataframe(df_bias, use_container_width=True, hide_index=True)

            st.write(t("llm_interpretation_label"))
            with st.spinner(t("bias_spinner")):
                commento_bias = commento_llm_bias(
                    res_bias["dettaglio"], descrizione, settore, target or t("not_specified")
                )
            st.info(commento_bias)

        mostra_soglie("bias")

        st.divider()

    mostra_dimensione(
        dimension_code="governance",
        risultato=res_governance,
        raccomandazione=(
            t("governance_ok") if res_governance["stato"] == STATUS_COMPLIANT
            else t("governance_bad")
        )
    )

    st.divider()

    # ── Navigation ───────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        if st.button(t("back_to_start_button"), use_container_width=True):
            st.session_state.pagina = "home"
            st.session_state.dataset = None
            st.session_state.governance = {}
            st.session_state.target = None
            st.session_state.attributi_sensibili = []
            st.rerun()
    with col2:
        st.button(t("download_report_button"), use_container_width=True, disabled=True,
                  help=t("download_report_help"))
