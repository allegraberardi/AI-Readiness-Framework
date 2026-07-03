"""Internationalization helpers: string catalog, status/severity labels and
sector labels for the AI Readiness Framework, with English and Italian support.
"""
import streamlit as st

LANGUAGES = {"en": "English", "it": "Italiano"}
DEFAULT_LANG = "en"


def get_lang():
    return st.session_state.get("lang", DEFAULT_LANG)


def set_lang(lang):
    st.session_state.lang = lang


def lang_name(lang=None):
    """Full language name, used to instruct the LLM which language to reply in."""
    lang = lang or get_lang()
    return "Italian" if lang == "it" else "English"


def language_selector():
    if "lang" not in st.session_state:
        st.session_state.lang = DEFAULT_LANG
    codes = list(LANGUAGES.keys())
    col1, col2 = st.columns([5, 1])
    with col2:
        selected = st.selectbox(
            t("lang_label"),
            codes,
            index=codes.index(st.session_state.lang),
            format_func=lambda c: LANGUAGES[c],
            key="lang_selector",
            label_visibility="collapsed",
        )
    if selected != st.session_state.lang:
        st.session_state.lang = selected
        st.rerun()


# ── String catalog ────────────────────────────────────────────────────────────
STRINGS = {
    "lang_label": {"en": "Language", "it": "Lingua"},

    # Navigation
    "nav_step1": {"en": "1. Information", "it": "1. Informazioni"},
    "nav_step2": {"en": "2. Governance", "it": "2. Governance"},
    "nav_step3": {"en": "3. Results", "it": "3. Risultati"},

    # Sectors
    "sector_placeholder": {"en": "Select...", "it": "Seleziona..."},
    "sector_biometrics": {"en": "Biometrics", "it": "Biometria"},
    "sector_critical_infrastructure": {"en": "Critical infrastructure", "it": "Infrastrutture critiche"},
    "sector_education": {"en": "Education and training", "it": "Istruzione e formazione"},
    "sector_employment": {"en": "Employment and worker management", "it": "Occupazione e selezione del personale"},
    "sector_essential_services": {"en": "Essential services (credit, welfare, insurance)", "it": "Servizi essenziali (credito, welfare, assicurazioni)"},
    "sector_law_enforcement": {"en": "Law enforcement", "it": "Forze dell'ordine"},
    "sector_migration": {"en": "Migration and border management", "it": "Migrazione e gestione delle frontiere"},
    "sector_justice": {"en": "Justice and democratic processes", "it": "Giustizia e processi democratici"},

    # home.py
    "home_title": {"en": "NORMA", "it": "NORMA"},
    "home_intro": {
        "en": "Check whether your dataset meets the AI Act requirements for high-risk systems (Annex III).",
        "it": "Verifica se il tuo dataset rispetta i requisiti dell'AI Act per i sistemi ad alto rischio (Allegato III).",
    },
    "sector_section_title": {"en": "1. Select the application sector", "it": "1. Seleziona il settore di applicazione"},
    "sector_question": {"en": "Which sector does your AI system belong to?", "it": "A quale settore appartiene il tuo sistema AI?"},
    "usecase_section_title": {"en": "2. Describe how you will use this dataset", "it": "2. Descrivi come utilizzerai questo dataset"},
    "usecase_label": {"en": "Use case description", "it": "Descrizione del caso d'uso"},
    "usecase_placeholder": {
        "en": "E.g. This dataset will be used to train a classifier that predicts...",
        "it": "Es. Questo dataset verrà usato per addestrare un classificatore che predice...",
    },
    "upload_section_title": {"en": "3. Upload your dataset", "it": "3. Carica il tuo dataset"},
    "upload_label": {"en": "Drag and drop your CSV file here, or click to browse", "it": "Trascina qui il tuo file CSV oppure clicca per sfogliare"},
    "upload_help": {"en": "Supported format: .csv — Max 200 MB", "it": "Formato supportato: .csv — Max 200 MB"},
    "upload_success": {"en": "File uploaded successfully — {rows} rows × {cols} columns", "it": "File caricato correttamente — {rows} righe × {cols} colonne"},
    "upload_error": {"en": "Error reading file: {error}", "it": "Errore nella lettura del file: {error}"},
    "bias_config_title": {"en": "4. Bias analysis configuration", "it": "4. Configurazione analisi bias"},
    "bias_mode_question": {"en": "How do you want to identify sensitive attributes?", "it": "Come vuoi identificare gli attributi sensibili?"},
    "mode_auto_llm": {"en": "🤖 Automatic with LLM", "it": "🤖 Automatico con LLM"},
    "mode_manual": {"en": "✋ Manual", "it": "✋ Manuale"},
    "detected_sensitive_info": {
        "en": "I automatically detected these possible sensitive attributes: **{cols}**",
        "it": "Ho rilevato automaticamente questi possibili attributi sensibili: **{cols}**",
    },
    "target_column_label": {"en": "Target column", "it": "Colonna target"},
    "no_dimension_option": {"en": "None — skip this dimension", "it": "Nessuna — salta questa dimensione"},
    "sensitive_attrs_label": {"en": "Sensitive attributes", "it": "Attributi sensibili"},
    "complete_fields_info": {
        "en": "Complete the sector and description to configure the bias analysis.",
        "it": "Completa settore e descrizione per configurare l'analisi del bias.",
    },
    "next_button": {"en": "Next →", "it": "Avanti →"},
    "warn_select_sector": {"en": "Select the application sector before continuing.", "it": "Seleziona il settore di applicazione prima di continuare."},
    "warn_enter_description": {"en": "Enter a use case description before continuing.", "it": "Inserisci una descrizione del caso d'uso prima di continuare."},
    "warn_upload_dataset": {"en": "Upload the CSV dataset before continuing.", "it": "Carica il dataset CSV prima di continuare."},

    # llm.py
    "llm_auto_analysis_title": {"en": "🤖 Automatic LLM analysis", "it": "🤖 Analisi automatica con LLM"},
    "llm_spinner_usecase": {"en": "The LLM is analyzing the use case...", "it": "L'LLM sta analizzando il caso d'uso..."},
    "llm_analysis_info": {"en": "**LLM analysis:** {text}", "it": "**Analisi LLM:** {text}"},
    "target_suggested_label": {"en": "Target column — suggested by the LLM (you can edit it)", "it": "Colonna target — suggerita dall'LLM (puoi modificarla)"},
    "attrs_suggested_label": {"en": "Sensitive attributes — suggested by the LLM (you can edit them)", "it": "Attributi sensibili — suggeriti dall'LLM (puoi modificarli)"},
    "llm_generic_error": {"en": "Error during LLM analysis: {error}", "it": "Errore durante l'analisi LLM: {error}"},

    # governance.py
    "gov_title": {"en": "Dataset governance", "it": "Governance del dataset"},
    "gov_intro": {
        "en": "Fill in the information about your dataset. The answers will be used to assess the Governance dimension.",
        "it": "Compila le informazioni sul tuo dataset. Le risposte verranno usate per valutare la dimensione Governance.",
    },
    "gov_unknown_hint": {
        "en": "💡 If you don't know the answer to a question, select 'I don't know' — it will be treated as a warning signal in the assessment.",
        "it": "💡 Se non conosci la risposta a una domanda seleziona 'Non lo so' — verrà considerato come un segnale di attenzione nella valutazione.",
    },
    "select_placeholder": {"en": "Select...", "it": "Seleziona..."},

    "section_data_origin": {"en": "Data origin", "it": "Origine dei dati"},
    "q_origin": {"en": "1. Where does the data come from?", "it": "1. Da dove provengono i dati?"},
    "origin_internal": {"en": "Collected internally", "it": "Raccolti internamente"},
    "origin_external_vendor": {"en": "Purchased from an external vendor", "it": "Acquistati da fornitore esterno"},
    "origin_open_source": {"en": "Open source / public", "it": "Open source / pubblici"},
    "origin_web_scraping": {"en": "Web scraping", "it": "Web scraping"},
    "origin_unknown": {"en": "I don't know", "it": "Non lo so"},
    "origin_other": {"en": "Other", "it": "Altro"},

    "q_year": {"en": "2. What year was it collected?", "it": "2. In che anno sono stati raccolti?"},
    "q_personal_data": {"en": "3. Does the data contain personal data?", "it": "3. I dati contengono dati personali?"},

    "answer_yes": {"en": "Yes", "it": "Sì"},
    "answer_no": {"en": "No", "it": "No"},
    "answer_unknown": {"en": "I don't know", "it": "Non lo so"},
    "answer_not_applicable": {"en": "Not applicable", "it": "Non applicabile"},

    "section_collection_process": {"en": "Collection process", "it": "Processo di raccolta"},
    "q_collection_method": {"en": "4. How was it collected?", "it": "4. Come sono stati raccolti?"},
    "method_surveys": {"en": "Surveys or questionnaires", "it": "Sondaggi o questionari"},
    "method_sensors": {"en": "Sensors or automatic devices", "it": "Sensori o dispositivi automatici"},
    "method_system_logs": {"en": "System logs", "it": "Log di sistema"},
    "method_manual_entry": {"en": "Manual entry", "it": "Inserimento manuale"},
    "method_automated_process": {"en": "Automated process", "it": "Processo automatizzato"},
    "method_unknown": {"en": "I don't know", "it": "Non lo so"},
    "method_other": {"en": "Other", "it": "Altro"},

    "q_collection_doc": {"en": "5. Does documentation of the collection process exist?", "it": "5. Esiste documentazione del processo di raccolta?"},
    "q_consent": {
        "en": "6. Were the people whose data was collected aware of it and did they give consent?",
        "it": "6. Le persone i cui dati sono stati raccolti erano consapevoli e hanno dato il consenso?",
    },

    "section_labeling": {"en": "Labeling and annotation", "it": "Etichettatura e annotazione"},
    "q_labeled": {"en": "7. Is the data labeled?", "it": "7. I dati sono etichettati?"},
    "q_who_labeled": {"en": "8. Who labeled the data?", "it": "8. Chi ha etichettato i dati?"},
    "labeler_domain_experts": {"en": "Domain experts (e.g. doctors, lawyers)", "it": "Esperti del dominio (es. medici, giuristi)"},
    "labeler_crowdsourcing": {"en": "Crowdsourcing", "it": "Crowdsourcing"},
    "labeler_automatic_process": {"en": "Automatic process", "it": "Processo automatico"},
    "labeler_combination": {"en": "Combination of methods", "it": "Combinazione di metodi"},
    "labeler_unknown": {"en": "I don't know", "it": "Non lo so"},
    "labeler_other": {"en": "Other", "it": "Altro"},
    "q_labeling_doc": {"en": "9. Does documentation on the labeling criteria exist?", "it": "9. Esiste documentazione sui criteri di etichettatura?"},

    "section_cleaning": {"en": "Cleaning and pre-processing", "it": "Pulizia e pre-processing"},
    "q_cleaned": {"en": "10. Was the dataset cleaned or pre-processed?", "it": "10. Il dataset è stato pulito o pre-processato?"},
    "q_cleaning_doc": {"en": "11. Are the cleaning operations documented?", "it": "11. Le operazioni di pulizia sono documentate?"},

    "section_data_card": {"en": "Data card", "it": "Data card"},
    "q_data_card": {"en": "12. Does a data card or datasheet for datasets exist for this dataset?", "it": "12. Esiste una data card o datasheet for datasets per questo dataset?"},
    "q_data_card_updated": {"en": "13. Is the data card up to date?", "it": "13. La data card è aggiornata?"},
    "q_data_card_upload": {"en": "14. Upload the data card", "it": "14. Carica la data card"},
    "data_card_upload_help": {"en": "Optional — upload the file if available", "it": "Opzionale — carica il file se disponibile"},
    "data_card_uploaded_success": {"en": "✅ Data card uploaded!", "it": "✅ Data card caricata!"},

    "back_button": {"en": "← Back", "it": "← Indietro"},
    "analyze_button": {"en": "Analyze dataset →", "it": "Analizza dataset →"},

    # risultati.py
    "results_title": {"en": "Results — AI Readiness Report", "it": "Risultati — Report AI Readiness"},
    "results_sector_label": {"en": "**Sector:** {sector}", "it": "**Settore:** {sector}"},
    "results_spinner": {"en": "Analyzing dataset...", "it": "Analisi del dataset in corso..."},

    "dim_relevance": {"en": "Relevance", "it": "Rilevanza"},
    "dim_completeness": {"en": "Completeness", "it": "Completezza"},
    "dim_representativeness": {"en": "Representativeness", "it": "Rappresentatività"},
    "dim_errors": {"en": "Absence of errors", "it": "Assenza di errori"},
    "dim_bias": {"en": "Absence of bias", "it": "Assenza di bias"},
    "dim_governance": {"en": "Governance and Consent", "it": "Governance e Consenso"},

    "ref_relevance": {
        "en": "Art. 10(3) AI Act — data must be relevant to the intended purpose",
        "it": "Art. 10, par. 3 AI Act — i dati devono essere pertinenti rispetto alle finalità previste",
    },
    "ref_completeness": {
        "en": "Art. 10(3) AI Act — data must be complete as far as possible",
        "it": "Art. 10, par. 3 AI Act — i dati devono essere completi nella misura del possibile",
    },
    "ref_representativeness": {
        "en": "Art. 10(3)-(4) AI Act — data must be sufficiently representative and take into account the characteristics of the context of use",
        "it": "Art. 10, par. 3 e par. 4 AI Act — i dati devono essere sufficientemente rappresentativi e tenere conto delle caratteristiche del contesto di utilizzo",
    },
    "ref_errors": {
        "en": "Art. 10(3) AI Act — data must be free of errors as far as possible",
        "it": "Art. 10, par. 3 AI Act — i dati devono essere esenti da errori nella misura del possibile",
    },
    "ref_bias": {
        "en": "Art. 10(2)(f)-(g) AI Act — examine possible biases and adopt appropriate measures",
        "it": "Art. 10, par. 2(f) e 2(g) AI Act — esaminare le possibili distorsioni e adottare misure adeguate",
    },
    "ref_governance": {
        "en": "Art. 10(2) AI Act — data must be subject to appropriate governance practices",
        "it": "Art. 10, par. 2 AI Act — i dati devono essere soggetti a pratiche di governance adeguate",
    },

    "metric_completeness": {"en": "Completeness", "it": "Completezza"},
    "metric_representativeness": {"en": "Representativeness", "it": "Rappresentatività"},
    "metric_errors": {"en": "Absence of errors", "it": "Assenza di errori"},
    "metric_governance": {"en": "Governance", "it": "Governance"},
    "metric_bias": {"en": "Absence of bias", "it": "Assenza di bias"},
    "metric_relevance": {"en": "Relevance", "it": "Rilevanza"},

    "score_title_high": {"en": "### AI Readiness Score: {score}/100 — Dataset sufficiently compliant", "it": "### AI Readiness Score: {score}/100 — Dataset sufficientemente conforme"},
    "score_title_mid": {"en": "### AI Readiness Score: {score}/100 — Improvements needed", "it": "### AI Readiness Score: {score}/100 — Miglioramenti necessari"},
    "score_title_low": {"en": "### AI Readiness Score: {score}/100 — Dataset not compliant with the AI Act", "it": "### AI Readiness Score: {score}/100 — Dataset non conforme all'AI Act"},

    "relevance_avg_score": {"en": "Average relevance score: {score}/100. ", "it": "Score medio di rilevanza: {score}/100. "},
    "relevance_ok": {"en": "The dataset columns are relevant to the described use case.", "it": "Le colonne del dataset sono pertinenti al caso d'uso descritto."},
    "relevance_low": {"en": "{pct}% of the columns are of low relevance to the use case.", "it": "Il {pct}% delle colonne risulta poco pertinente al caso d'uso."},
    "detail_by_column": {"en": "**Detail by column:**", "it": "**Dettaglio per colonna:**"},
    "llm_comment_label": {"en": "**LLM comment:** {text}", "it": "**Commento LLM:** {text}"},

    "thresholds_expander": {"en": "📏 Thresholds used for this dimension", "it": "📏 Soglie utilizzate per questa dimensione"},

    "completeness_recommendation_ok": {
        "en": "The dataset has {pct}% missing values. No corrective action required.",
        "it": "Il dataset presenta il {pct}% di valori mancanti. Nessuna azione correttiva richiesta.",
    },
    "completeness_recommendation_bad": {
        "en": "The dataset has {pct}% missing values. We recommend checking and filling in the missing values in the critical columns.",
        "it": "Il dataset presenta il {pct}% di valori mancanti. Si raccomanda di verificare e integrare i valori mancanti nelle colonne critiche.",
    },

    "errors_recommendation_both": {
        "en": "Found {n} duplicates and anomalous values in the indicated columns — check and correct before proceeding.",
        "it": "Rilevati {n} duplicati e valori anomali nelle colonne indicate — verificare e correggere prima di procedere.",
    },
    "errors_recommendation_dup": {
        "en": "Found {n} duplicates in the dataset — assess whether to remove them based on the use case.",
        "it": "Rilevati {n} duplicati nel dataset — valutare se rimuoverli in base al caso d'uso.",
    },
    "errors_recommendation_out": {
        "en": "Anomalous values found in the indicated columns — check whether they are errors or legitimate values.",
        "it": "Rilevati valori anomali nelle colonne indicate — verificare se sono errori o valori legittimi.",
    },
    "errors_recommendation_none": {"en": "No significant errors detected.", "it": "Nessun errore significativo rilevato."},

    "duplicates_llm_comment_label": {"en": "**LLM assessment on duplicates:** {text}", "it": "**Valutazione LLM sui duplicati:** {text}"},

    "bias_none": {"en": "No significant bias detected.", "it": "Nessun bias significativo rilevato."},
    "bias_moderate": {
        "en": "Moderate bias detected — apply mitigation techniques on the critical attributes.",
        "it": "Bias moderato rilevato — applicare tecniche di mitigazione sugli attributi critici.",
    },
    "bias_high": {
        "en": "Apply bias mitigation techniques (re-sampling, re-weighting) on the critical attributes.",
        "it": "Applicare tecniche di mitigazione del bias (re-sampling, re-weighting) sugli attributi critici.",
    },
    "llm_interpretation_label": {"en": "**LLM interpretation:**", "it": "**Interpretazione LLM:**"},
    "bias_spinner": {"en": "The LLM is analyzing the bias...", "it": "L'LLM sta analizzando il bias..."},
    "bias_not_evaluated": {
        "en": "Dimension not evaluated — target or sensitive attributes not selected.",
        "it": "Dimensione non valutata — target o attributi sensibili non selezionati.",
    },

    "governance_ok": {"en": "The dataset governance is adequate.", "it": "La governance del dataset è adeguata."},
    "governance_bad": {"en": "Document the missing information and update the dataset's data card.", "it": "Documentare le informazioni mancanti e aggiornare la data card del dataset."},

    "back_to_start_button": {"en": "← Back to start", "it": "← Torna all'inizio"},
    "download_report_button": {"en": "📄 Download PDF Report", "it": "📄 Scarica Report PDF"},
    "download_report_help": {"en": "Feature in development", "it": "Funzionalità in sviluppo"},

    "not_specified": {"en": "not specified", "it": "non specificato"},

    # thresholds table
    "thr_completeness_compliant": {"en": "Missing values < 5%", "it": "Valori mancanti < 5%"},
    "thr_completeness_attention": {"en": "Missing values between 5% and 15%", "it": "Valori mancanti tra 5% e 15%"},
    "thr_completeness_non_compliant": {"en": "Missing values > 15%", "it": "Valori mancanti > 15%"},
    "thr_representativeness_compliant": {"en": "All classes have more than 100 examples", "it": "Tutte le classi hanno più di 100 esempi"},
    "thr_representativeness_attention": {"en": "At least one class has between 50 and 100 examples", "it": "Almeno una classe ha tra 50 e 100 esempi"},
    "thr_representativeness_non_compliant": {"en": "At least one class has fewer than 50 examples", "it": "Almeno una classe ha meno di 50 esempi"},
    "thr_errors_compliant": {"en": "No significant duplicates or outliers", "it": "Nessun duplicato o outlier significativo"},
    "thr_errors_attention": {"en": "Duplicates between 5% and 10%, or outliers between 1% and 5%", "it": "Duplicati tra 5% e 10% oppure outlier tra 1% e 5%"},
    "thr_errors_non_compliant": {"en": "Duplicates > 10%, or outliers > 5%", "it": "Duplicati > 10% oppure outlier > 5%"},
    "thr_bias_compliant": {
        "en": "Statistical Parity Difference < 0.1 and Disparate Impact between 0.8 and 1.25 and Class Imbalance < 20%",
        "it": "Statistical Parity Difference < 0.1 e Disparate Impact tra 0.8 e 1.25 e Class Imbalance < 20%",
    },
    "thr_bias_attention": {
        "en": "Statistical Parity Difference between 0.1 and 0.2, or Disparate Impact between 0.6 and 0.8, or Class Imbalance between 20% and 40%",
        "it": "Statistical Parity Difference tra 0.1 e 0.2 oppure Disparate Impact tra 0.6 e 0.8 oppure Class Imbalance tra 20% e 40%",
    },
    "thr_bias_non_compliant": {
        "en": "Statistical Parity Difference > 0.2, or Disparate Impact < 0.6, or Class Imbalance > 40%",
        "it": "Statistical Parity Difference > 0.2 oppure Disparate Impact < 0.6 oppure Class Imbalance > 40%",
    },
    "thr_relevance_compliant": {"en": "Average LLM score > 60/100 and irrelevant columns < 25%", "it": "Score medio LLM > 60/100 e colonne irrilevanti < 25%"},
    "thr_relevance_attention": {
        "en": "Average LLM score between 30 and 60, or irrelevant columns between 25% and 50%",
        "it": "Score medio LLM tra 30 e 60 oppure colonne irrilevanti tra 25% e 50%",
    },
    "thr_relevance_non_compliant": {"en": "Average LLM score < 30, or irrelevant columns > 50%", "it": "Score medio LLM < 30 oppure colonne irrilevanti > 50%"},
    "thr_governance_compliant": {"en": "All information documented", "it": "Tutte le informazioni documentate"},
    "thr_governance_attention": {"en": "Some information not available (I don't know)", "it": "Alcune informazioni non disponibili (Non lo so)"},
    "thr_governance_non_compliant": {
        "en": "Key information missing (consent, data card, collection documentation)",
        "it": "Informazioni chiave assenti (consenso, data card, documentazione raccolta)",
    },

    # rappresentativita.py
    "representativeness_ok": {"en": "Balanced class distribution.", "it": "Distribuzione delle classi bilanciata."},
    "representativeness_attention": {"en": "Some classes are underrepresented.", "it": "Alcune classi sono sottorappresentate."},
    "representativeness_bad": {"en": "Significant imbalances detected — apply balancing techniques.", "it": "Squilibri significativi rilevati — applicare tecniche di bilanciamento."},
    "categorical_distribution_label": {"en": "**Categorical variable distribution:**", "it": "**Distribuzione variabili categoriche:**"},
    "numeric_stats_label": {"en": "**Numeric variable statistics:**", "it": "**Statistiche variabili numeriche:**"},
    "contextual_analysis_label": {"en": "**Contextual analysis for the selected sector:**", "it": "**Analisi contestuale per il settore selezionato:**"},
    "contextual_focus_info": {
        "en": "For this sector it is important to monitor: **{focus}**\n\n_{reason}_",
        "it": "Per questo settore è importante monitorare: **{focus}**\n\n_{reason}_",
    },
    "contextual_not_found": {
        "en": "I did not find demographic columns relevant to this sector in the dataset.",
        "it": "Non ho trovato colonne demografiche rilevanti per questo settore nel dataset.",
    },
    "contextual_columns_found": {"en": "Relevant columns found: **{cols}**", "it": "Colonne rilevanti trovate: **{cols}**"},
    "representativeness_llm_spinner": {"en": "The LLM is analyzing representativeness...", "it": "L'LLM sta analizzando la rappresentatività..."},
    "expander_col": {"en": "📊 {col} — minimum class: '{cls}' ({pct}%)", "it": "📊 {col} — classe minima: '{cls}' ({pct}%)"},

    "col_column": {"en": "Column", "it": "Colonna"},
    "col_min": {"en": "Min", "it": "Min"},
    "col_max": {"en": "Max", "it": "Max"},
    "col_mean": {"en": "Mean", "it": "Media"},
    "col_median": {"en": "Median", "it": "Mediana"},
    "col_unique_values": {"en": "Unique values", "it": "Valori unici"},
    "col_problem": {"en": "Problem", "it": "Problema"},
    "col_severity": {"en": "Severity", "it": "Gravità"},
    "repr_class_problem": {"en": "Class '{cls}' has only {n} examples ({pct}%)", "it": "Classe '{cls}' ha solo {n} esempi ({pct}%)"},

    "sector_focus_employment": {"en": "gender, age and education level", "it": "genere, età e livello di istruzione"},
    "sector_reason_employment": {
        "en": "Personnel selection systems can discriminate based on gender, age, and background — as in the Amazon case (2018).",
        "it": "I sistemi di selezione del personale possono discriminare in base a genere, età e provenienza — come nel caso Amazon (2018).",
    },
    "sector_focus_essential_services": {"en": "gender, age, ethnicity and income", "it": "genere, età, etnia e reddito"},
    "sector_reason_essential_services": {
        "en": "Credit scoring systems can discriminate based on gender and ethnicity, perpetuating historical inequalities.",
        "it": "I sistemi di valutazione del credito possono discriminare in base a genere ed etnia, perpetuando disuguaglianze storiche.",
    },
    "sector_focus_law_enforcement": {"en": "ethnicity, race and geographic origin", "it": "etnia, razza e provenienza geografica"},
    "sector_reason_law_enforcement": {
        "en": "Systems used in law enforcement show systemic bias against ethnic minorities — as documented in the COMPAS case.",
        "it": "I sistemi usati nelle forze dell'ordine mostrano bias sistematici contro minoranze etniche — come documentato nel caso COMPAS.",
    },
    "sector_focus_education": {"en": "geographic origin and gender", "it": "provenienza geografica e genere"},
    "sector_reason_education": {
        "en": "School assessment systems can reflect geographic and gender inequalities.",
        "it": "I sistemi di valutazione scolastica possono riflettere disuguaglianze geografiche e di genere.",
    },
    "sector_focus_justice": {"en": "ethnicity, race and age", "it": "etnia, razza ed età"},
    "sector_reason_justice": {
        "en": "Decision-support systems in the judicial domain must ensure fairness across different demographic groups.",
        "it": "I sistemi di supporto decisionale in ambito giudiziario devono garantire equità tra gruppi demografici diversi.",
    },
    "sector_focus_migration": {"en": "nationality, religion and geographic origin", "it": "nazionalità, religione e provenienza geografica"},
    "sector_reason_migration": {
        "en": "Asylum application assessment systems must be representative of all nationalities.",
        "it": "I sistemi di valutazione delle domande di asilo devono essere rappresentativi di tutte le nazionalità.",
    },
    "sector_focus_biometrics": {"en": "ethnicity, gender and age", "it": "etnia, genere ed età"},
    "sector_reason_biometrics": {
        "en": "Biometric systems show lower performance on people of color and women.",
        "it": "I sistemi biometrici mostrano performance inferiori su persone di colore e donne.",
    },
    "sector_focus_critical_infrastructure": {"en": "geographic distribution", "it": "distribuzione geografica"},
    "sector_reason_critical_infrastructure": {
        "en": "Systems for critical infrastructure must cover all geographic areas.",
        "it": "I sistemi per infrastrutture critiche devono coprire tutte le aree geografiche.",
    },

    # bias.py
    "col_attribute": {"en": "Attribute", "it": "Attributo"},
    "col_privileged_group": {"en": "Privileged group", "it": "Gruppo privilegiato"},
    "col_disadvantaged_group": {"en": "Disadvantaged group", "it": "Gruppo svantaggiato"},
    "col_spd": {"en": "Statistical Parity Difference", "it": "Statistical Parity Difference"},
    "col_di": {"en": "Disparate Impact", "it": "Disparate Impact"},
    "col_class_imbalance": {"en": "Class Imbalance", "it": "Class Imbalance"},
    "spd_threshold_note": {"en": "(threshold: |SPD| < 0.1)", "it": "(soglia: |SPD| < 0.1)"},
    "di_threshold_note": {"en": "(threshold: 0.8 ≤ DI ≤ 1.25)", "it": "(soglia: 0.8 ≤ DI ≤ 1.25)"},
    "class_imbalance_note": {"en": "{pct}% difference between groups", "it": "{pct}% di differenza tra gruppi"},
    "bias_target_not_binary": {
        "en": "The target column '{target}' is not binary ({n} unique values). Fairness metrics require a binary target.",
        "it": "La colonna target '{target}' non è binaria ({n} valori unici). Le metriche di fairness richiedono un target binario.",
    },
    "bias_cannot_calculate": {
        "en": "It was not possible to calculate the bias metrics. Check that the selected attributes have at least two distinct values.",
        "it": "Non è stato possibile calcolare le metriche di bias. Verifica che gli attributi selezionati abbiano almeno due valori distinti.",
    },

    # analisi.py
    "col_missing_values": {"en": "Missing values", "it": "Valori mancanti"},
    "col_problem_detected": {"en": "Detected problem", "it": "Problema rilevato"},
    "whole_dataset": {"en": "Entire dataset", "it": "Intero dataset"},
    "duplicates_detected": {"en": "{n} duplicate rows ({pct}%)", "it": "{n} righe duplicate ({pct}%)"},
    "outliers_detected": {"en": "{n} outliers detected with IQR ({pct}%)", "it": "{n} outlier rilevati con IQR ({pct}%)"},
    "format_problem_prefix": {"en": "Format: {text}", "it": "Formato: {text}"},

    "col_detail": {"en": "Detail", "it": "Dettaglio"},
    "gov_doc_collection_missing": {"en": "Missing collection documentation", "it": "Documentazione raccolta assente"},
    "gov_doc_collection_missing_detail": {"en": "There is no documentation on the data collection process", "it": "Non esiste documentazione sul processo di raccolta dei dati"},
    "gov_doc_collection_unknown": {"en": "Collection documentation — information not available", "it": "Documentazione raccolta — informazione non disponibile"},
    "gov_doc_collection_unknown_detail": {"en": "It is not known whether documentation on the collection process exists", "it": "Non è noto se esiste documentazione sul processo di raccolta"},
    "gov_consent_missing": {"en": "Missing consent", "it": "Consenso assente"},
    "gov_consent_missing_detail": {"en": "No documentation of consent for the dataset subjects", "it": "Nessuna documentazione del consenso per i soggetti del dataset"},
    "gov_consent_unknown": {"en": "Consent — information not available", "it": "Consenso — informazione non disponibile"},
    "gov_consent_unknown_detail": {"en": "It is not known whether consent was obtained", "it": "Non è noto se il consenso è stato ottenuto"},
    "gov_labeling_criteria_missing": {"en": "Labeling criteria not documented", "it": "Criteri etichettatura non documentati"},
    "gov_labeling_criteria_missing_detail": {"en": "The data is labeled but no documented criteria exist", "it": "I dati sono etichettati ma non esistono criteri documentati"},
    "gov_labeling_criteria_unknown": {"en": "Labeling criteria — information not available", "it": "Criteri etichettatura — informazione non disponibile"},
    "gov_labeling_criteria_unknown_detail": {"en": "It is not known whether documented labeling criteria exist", "it": "Non è noto se esistono criteri documentati per l'etichettatura"},
    "gov_cleaning_undocumented": {"en": "Cleaning not documented", "it": "Pulizia non documentata"},
    "gov_cleaning_undocumented_detail": {"en": "The dataset was cleaned but the operations are not documented", "it": "Il dataset è stato pulito ma le operazioni non sono documentate"},
    "gov_cleaning_unknown": {"en": "Cleaning — information not available", "it": "Pulizia — informazione non disponibile"},
    "gov_cleaning_unknown_detail": {"en": "It is not known whether the cleaning operations were documented", "it": "Non è noto se le operazioni di pulizia sono state documentate"},
    "gov_data_card_missing": {"en": "Missing data card", "it": "Data card assente"},
    "gov_data_card_missing_detail": {"en": "There is no data card or datasheet for this dataset", "it": "Non esiste una data card o datasheet per questo dataset"},
    "gov_data_card_unknown": {"en": "Data card — information not available", "it": "Data card — informazione non disponibile"},
    "gov_data_card_unknown_detail": {"en": "It is not known whether a data card exists for this dataset", "it": "Non è noto se esiste una data card per questo dataset"},

    # rilevanza.py
    "col_description": {"en": "Description", "it": "Descrizione"},
    "col_relevance_score": {"en": "Relevance score", "it": "Score rilevanza"},
    "col_relevance": {"en": "Relevance", "it": "Rilevanza"},
    "col_llm_explanation": {"en": "LLM explanation", "it": "Spiegazione LLM"},
    "no_description_provided": {
        "en": "No use case description provided. Cannot assess relevance.",
        "it": "Nessuna descrizione del caso d'uso fornita. Impossibile valutare la rilevanza.",
    },
    "desc_categorical": {
        "en": "Categorical — {n} unique values, e.g.: {examples}",
        "it": "Categorica — {n} valori unici, es: {examples}",
    },
    "desc_numeric": {
        "en": "Numeric — min: {min}, max: {max}, mean: {mean}",
        "it": "Numerica — min: {min}, max: {max}, media: {mean}",
    },
    "desc_type": {
        "en": "Type: {dtype} — {n} unique values",
        "it": "Tipo: {dtype} — {n} valori unici",
    },

    # LLM settings (sidebar)
    "llm_settings_title": {"en": "🔑 LLM settings", "it": "🔑 Impostazioni LLM"},
    "llm_api_key_label": {"en": "OpenRouter API key", "it": "Chiave API OpenRouter"},
    "llm_api_key_placeholder": {"en": "Uses the server default key if left empty", "it": "Se lasciata vuota usa la chiave predefinita del server"},
    "llm_api_key_help": {
        "en": "Optional — provide your own key from openrouter.ai/keys. If empty, the app's default key is used.",
        "it": "Opzionale — inserisci una tua chiave da openrouter.ai/keys. Se vuota, viene usata la chiave predefinita dell'app.",
    },
    "llm_model_label": {"en": "Model", "it": "Modello"},
    "llm_model_custom_option": {"en": "Custom model ID...", "it": "ID modello personalizzato..."},
    "llm_model_custom_label": {"en": "OpenRouter model ID", "it": "ID modello OpenRouter"},
    "llm_model_custom_help": {
        "en": "Any model ID available on OpenRouter, e.g. provider/model-name.",
        "it": "Un qualsiasi ID modello disponibile su OpenRouter, es. provider/model-name.",
    },
    "llm_settings_caption": {
        "en": "Applies to every LLM-based analysis on this page (target/attribute suggestions, bias, representativeness, relevance, format checks).",
        "it": "Si applica a tutte le analisi basate su LLM in questa pagina (suggerimenti target/attributi, bias, rappresentatività, rilevanza, controlli di formato).",
    },
}


def t(key, **kwargs):
    lang = get_lang()
    entry = STRINGS.get(key)
    if entry is None:
        return key
    text = entry.get(lang, entry.get("en", key))
    return text.format(**kwargs) if kwargs else text


# ── Status (compliance) labels ─────────────────────────────────────────────────
STATUS_COMPLIANT = "compliant"
STATUS_ATTENTION = "attention"
STATUS_NON_COMPLIANT = "non_compliant"

STATUS_LABELS = {
    STATUS_COMPLIANT: {"en": "COMPLIANT", "it": "CONFORME"},
    STATUS_ATTENTION: {"en": "ATTENTION", "it": "ATTENZIONE"},
    STATUS_NON_COMPLIANT: {"en": "NON-COMPLIANT", "it": "NON CONFORME"},
}

STATUS_EMOJI = {
    STATUS_COMPLIANT: "🟢",
    STATUS_ATTENTION: "🟡",
    STATUS_NON_COMPLIANT: "🔴",
}


def t_status(code):
    lang = get_lang()
    return STATUS_LABELS.get(code, {}).get(lang, code)


def status_emoji(code):
    return STATUS_EMOJI.get(code, "")


# ── Severity / level labels (also reused for relevance level: HIGH/MEDIUM/LOW) ─
LEVEL_HIGH = "high"
LEVEL_MEDIUM = "medium"
LEVEL_LOW = "low"

LEVEL_LABELS = {
    LEVEL_HIGH: {"en": "HIGH", "it": "ALTA"},
    LEVEL_MEDIUM: {"en": "MEDIUM", "it": "MEDIA"},
    LEVEL_LOW: {"en": "LOW", "it": "BASSA"},
}


def t_level(code):
    lang = get_lang()
    return LEVEL_LABELS.get(code, {}).get(lang, code)


# t_severity is an alias of t_level, kept for readability at call sites
t_severity = t_level


# ── Sectors ──────────────────────────────────────────────────────────────────
SECTOR_ORDER = [
    "biometrics",
    "critical_infrastructure",
    "education",
    "employment",
    "essential_services",
    "law_enforcement",
    "migration",
    "justice",
]

SECTOR_PLACEHOLDER = "__select__"


def sector_label(code, lang=None):
    if code == SECTOR_PLACEHOLDER or code is None:
        return t("sector_placeholder")
    lang = lang or get_lang()
    entry = STRINGS.get(f"sector_{code}")
    if entry is None:
        return code
    return entry.get(lang, entry.get("en", code))


def sector_label_en(code):
    """Always-English sector label, for LLM prompts."""
    return sector_label(code, lang="en")


def sector_options():
    return [SECTOR_PLACEHOLDER] + SECTOR_ORDER
