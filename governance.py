import streamlit as st
from i18n import t

YES_NO_UNKNOWN = ["yes", "no", "unknown"]
YES_NO_UNKNOWN_NA = ["yes", "no", "unknown", "not_applicable"]

ANSWER_KEYS = {
    "yes": "answer_yes",
    "no": "answer_no",
    "unknown": "answer_unknown",
    "not_applicable": "answer_not_applicable",
}


def _answer_label(code):
    return t(ANSWER_KEYS[code])


ORIGIN_OPTIONS = ["__select__", "internal", "external_vendor", "open_source", "web_scraping", "unknown", "other"]
METHOD_OPTIONS = ["__select__", "surveys", "sensors", "system_logs", "manual_entry", "automated_process", "unknown", "other"]
LABELER_OPTIONS = ["__select__", "domain_experts", "crowdsourcing", "automatic_process", "combination", "unknown", "other"]


def _select_label(prefix, code):
    if code == "__select__":
        return t("select_placeholder")
    return t(f"{prefix}_{code}")


def mostra_governance():
    st.title(t("gov_title"))
    st.write(t("gov_intro"))
    st.info(t("gov_unknown_hint"))

    st.divider()
    risposte = {}

    # ── Data origin ───────────────────────────────────────────────────────────
    st.subheader(t("section_data_origin"))

    risposte["origine"] = st.selectbox(
        t("q_origin"),
        ORIGIN_OPTIONS,
        format_func=lambda c: _select_label("origin", c)
    )

    risposte["anno"] = st.number_input(
        t("q_year"),
        min_value=1990, max_value=2025, value=2023
    )

    risposte["dati_personali"] = st.radio(
        t("q_personal_data"),
        YES_NO_UNKNOWN,
        format_func=_answer_label
    )

    st.divider()

    # ── Collection process ───────────────────────────────────────────────────
    st.subheader(t("section_collection_process"))

    risposte["metodo_raccolta"] = st.selectbox(
        t("q_collection_method"),
        METHOD_OPTIONS,
        format_func=lambda c: _select_label("method", c)
    )

    risposte["doc_raccolta"] = st.radio(
        t("q_collection_doc"),
        YES_NO_UNKNOWN,
        format_func=_answer_label
    )

    risposte["consenso"] = st.radio(
        t("q_consent"),
        YES_NO_UNKNOWN_NA,
        format_func=_answer_label
    )

    st.divider()

    # ── Labeling and annotation ──────────────────────────────────────────────
    st.subheader(t("section_labeling"))

    risposte["etichettati"] = st.radio(
        t("q_labeled"),
        YES_NO_UNKNOWN,
        format_func=_answer_label
    )

    if risposte["etichettati"] == "yes":
        risposte["chi_etichetta"] = st.selectbox(
            t("q_who_labeled"),
            LABELER_OPTIONS,
            format_func=lambda c: _select_label("labeler", c)
        )
        risposte["doc_etichettatura"] = st.radio(
            t("q_labeling_doc"),
            YES_NO_UNKNOWN,
            format_func=_answer_label
        )

    st.divider()

    # ── Cleaning and pre-processing ──────────────────────────────────────────
    st.subheader(t("section_cleaning"))

    risposte["pulizia"] = st.radio(
        t("q_cleaned"),
        YES_NO_UNKNOWN,
        format_func=_answer_label
    )

    if risposte["pulizia"] == "yes":
        risposte["doc_pulizia"] = st.radio(
            t("q_cleaning_doc"),
            YES_NO_UNKNOWN,
            format_func=_answer_label
        )

    st.divider()

    # ── Data card ────────────────────────────────────────────────────────────
    st.subheader(t("section_data_card"))

    risposte["data_card"] = st.radio(
        t("q_data_card"),
        YES_NO_UNKNOWN,
        format_func=_answer_label
    )

    if risposte["data_card"] == "yes":
        risposte["data_card_aggiornata"] = st.radio(
            t("q_data_card_updated"),
            YES_NO_UNKNOWN,
            format_func=_answer_label
        )
        file_data_card = st.file_uploader(
            t("q_data_card_upload"),
            type=["pdf", "docx", "txt"],
            help=t("data_card_upload_help")
        )
        if file_data_card is not None:
            st.success(t("data_card_uploaded_success"))
            risposte["data_card_file"] = file_data_card.name

    st.divider()

    # ── Conformità GDPR ──────────────────────────────────────────────────────
    st.subheader("Conformità GDPR")
    st.write("Domande relative al Regolamento Generale sulla Protezione dei Dati — Reg. UE 2016/679.")
    st.info("💡 Queste informazioni sono necessarie per valutare la conformità del dataset anche rispetto al GDPR, che si applica insieme all'AI Act per i sistemi ad alto rischio.")

    risposte["base_giuridica"] = st.selectbox(
        "15. Il trattamento dei dati ha una base giuridica documentata? (Art. 6 GDPR)",
        ["Seleziona...", "Consenso", "Contratto", "Obbligo legale",
         "Interesse vitale", "Interesse pubblico", "Interesse legittimo",
         "Non lo so", "Non applicabile"]
    )

    risposte["categorie_speciali"] = st.radio(
        "16. Il dataset contiene categorie speciali di dati (Art. 9 GDPR)? Es. salute, etnia, religione, dati biometrici, orientamento sessuale.",
        ["Sì", "No", "Non lo so"]
    )

    if risposte["categorie_speciali"] == "Sì":
        risposte["consenso_esplicito"] = st.radio(
            "17. È stato ottenuto il consenso esplicito per il trattamento di queste categorie speciali? (Art. 9 GDPR)",
            ["Sì", "No", "Non lo so"]
        )

    risposte["informativa_ai"] = st.radio(
        "18. Le persone sono state informate che i loro dati sarebbero stati usati per addestrare un sistema AI? (Art. 13 GDPR)",
        ["Sì", "No", "Non lo so", "Non applicabile"]
    )

    st.divider()

    # ── Conformità GDPR ──────────────────────────────────────────────────────
    st.subheader("Conformità GDPR")
    st.write("Domande relative al Regolamento Generale sulla Protezione dei Dati — Reg. UE 2016/679.")
    st.info("💡 Queste informazioni sono necessarie per valutare la conformità del dataset anche rispetto al GDPR, che si applica insieme all'AI Act per i sistemi ad alto rischio.")

    risposte["base_giuridica"] = st.selectbox(
        "15. Il trattamento dei dati ha una base giuridica documentata? (Art. 6 GDPR)",
        ["Seleziona...", "Consenso", "Contratto", "Obbligo legale",
         "Interesse vitale", "Interesse pubblico", "Interesse legittimo",
         "Non lo so", "Non applicabile"]
    )

    risposte["categorie_speciali"] = st.radio(
        "16. Il dataset contiene categorie speciali di dati (Art. 9 GDPR)? Es. salute, etnia, religione, dati biometrici, orientamento sessuale.",
        ["Sì", "No", "Non lo so"]
    )

    if risposte["categorie_speciali"] == "Sì":
        risposte["consenso_esplicito"] = st.radio(
            "17. È stato ottenuto il consenso esplicito per il trattamento di queste categorie speciali? (Art. 9 GDPR)",
            ["Sì", "No", "Non lo so"]
        )

    risposte["informativa_ai"] = st.radio(
        "18. Le persone sono state informate che i loro dati sarebbero stati usati per addestrare un sistema AI? (Art. 13 GDPR)",
        ["Sì", "No", "Non lo so", "Non applicabile"]
    )

    st.divider()

    # ── Navigation ───────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        if st.button(t("back_button"), use_container_width=True):
            st.session_state.pagina = "home"
            st.rerun()

    with col2:
        if st.button(t("analyze_button"), type="primary", use_container_width=True):
            st.session_state.governance = risposte
            st.session_state.pagina = "risultati"
            st.rerun()
