import streamlit as st
import pandas as pd
from dotenv import load_dotenv
import os
from llm import mostra_suggerimenti_llm
from bias import trova_attributi_sensibili
from i18n import t, sector_label, sector_options, SECTOR_PLACEHOLDER

load_dotenv()

def mostra_home():
    st.title(t("home_title"))
    st.write(t("home_intro"))

    st.divider()

    # ── Sector selection ─────────────────────────────────────────────────────
    st.subheader(t("sector_section_title"))
    settore = st.selectbox(
        t("sector_question"),
        sector_options(),
        format_func=sector_label,
    )

    # ── Use case description ─────────────────────────────────────────────────
    st.subheader(t("usecase_section_title"))
    descrizione = st.text_area(
        t("usecase_label"),
        placeholder=t("usecase_placeholder"),
        height=120
    )

    # ── CSV upload ────────────────────────────────────────────────────────────
    st.subheader(t("upload_section_title"))
    file = st.file_uploader(
        t("upload_label"),
        type=["csv"],
        help=t("upload_help")
    )

    df = None
    if file is not None:
        try:
            df = pd.read_csv(file, sep=None, engine="python")
            st.success(t("upload_success", rows=df.shape[0], cols=df.shape[1]))
            st.dataframe(df.head(5), use_container_width=True)
            st.session_state.dataset = df
        except Exception as e:
            st.error(t("upload_error", error=e))

    # ── Target and sensitive attribute selection ─────────────────────────────
    if df is not None and settore != SECTOR_PLACEHOLDER and descrizione.strip():
        st.subheader(t("bias_config_title"))

        modalita = st.radio(
            t("bias_mode_question"),
            ["auto_llm", "manual"],
            format_func=lambda m: t("mode_auto_llm") if m == "auto_llm" else t("mode_manual"),
            horizontal=True
        )

        if modalita == "auto_llm":
            target, attributi = mostra_suggerimenti_llm(df, descrizione, settore)
        else:
            suggeriti = trova_attributi_sensibili(df)
            if suggeriti:
                st.info(t("detected_sensitive_info", cols=", ".join(suggeriti)))

            colonne = [None] + list(df.columns)
            target = st.selectbox(
                t("target_column_label"), colonne,
                format_func=lambda c: t("no_dimension_option") if c is None else c,
                key="bias_target"
            )

            if target:
                attributi = st.multiselect(
                    t("sensitive_attrs_label"),
                    [col for col in df.columns if col != target],
                    default=[col for col in suggeriti if col != target],
                    key="bias_attributi"
                )
            else:
                attributi = []

        st.session_state.target = target
        st.session_state.attributi_sensibili = attributi

    elif df is not None:
        st.info(t("complete_fields_info"))
        st.session_state.target = None
        st.session_state.attributi_sensibili = []

    st.divider()

    # ── Next button ───────────────────────────────────────────────────────────
    if st.button(t("next_button"), type="primary", use_container_width=True):
        if settore == SECTOR_PLACEHOLDER:
            st.warning(t("warn_select_sector"))
        elif not descrizione.strip():
            st.warning(t("warn_enter_description"))
        elif st.session_state.get("dataset") is None:
            st.warning(t("warn_upload_dataset"))
        else:
            st.session_state.settore = settore
            st.session_state.descrizione = descrizione
            st.session_state.pagina = "governance"
            st.rerun()
