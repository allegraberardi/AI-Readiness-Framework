import streamlit as st

def mostra_governance():
    st.title("Governance del dataset")
    st.write("Compila le informazioni sul tuo dataset. Le risposte verranno usate per valutare la dimensione Governance.")
    st.info("💡 Se non conosci la risposta a una domanda seleziona 'Non lo so' — verrà considerato come un segnale di attenzione nella valutazione.")

    st.divider()
    risposte = {}

    # ── Origine dei dati ─────────────────────────────────────────────────────
    st.subheader("Origine dei dati")

    risposte["origine"] = st.selectbox(
        "1. Da dove provengono i dati?",
        ["Seleziona...", "Raccolti internamente", "Acquistati da fornitore esterno",
         "Open source / pubblici", "Web scraping", "Non lo so", "Altro"]
    )

    risposte["anno"] = st.number_input(
        "2. In che anno sono stati raccolti?",
        min_value=1990, max_value=2025, value=2023
    )

    risposte["dati_personali"] = st.radio(
        "3. I dati contengono dati personali?",
        ["Sì", "No", "Non lo so"]
    )

    st.divider()

    # ── Processo di raccolta ─────────────────────────────────────────────────
    st.subheader("Processo di raccolta")

    risposte["metodo_raccolta"] = st.selectbox(
        "4. Come sono stati raccolti?",
        ["Seleziona...", "Sondaggi o questionari", "Sensori o dispositivi automatici",
         "Log di sistema", "Inserimento manuale", "Processo automatizzato", "Non lo so", "Altro"]
    )

    risposte["doc_raccolta"] = st.radio(
        "5. Esiste documentazione del processo di raccolta?",
        ["Sì", "No", "Non lo so"]
    )

    risposte["consenso"] = st.radio(
        "6. Le persone i cui dati sono stati raccolti erano consapevoli e hanno dato il consenso?",
        ["Sì", "No", "Non lo so", "Non applicabile"]
    )

    st.divider()

    # ── Etichettatura e annotazione ──────────────────────────────────────────
    st.subheader("Etichettatura e annotazione")

    risposte["etichettati"] = st.radio(
        "7. I dati sono etichettati?",
        ["Sì", "No", "Non lo so"]
    )

    if risposte["etichettati"] == "Sì":
        risposte["chi_etichetta"] = st.selectbox(
            "8. Chi ha etichettato i dati?",
            ["Seleziona...", "Esperti del dominio (es. medici, giuristi)",
             "Crowdsourcing", "Processo automatico", "Combinazione di metodi", "Non lo so", "Altro"]
        )
        risposte["doc_etichettatura"] = st.radio(
            "9. Esiste documentazione sui criteri di etichettatura?",
            ["Sì", "No", "Non lo so"]
        )

    st.divider()

    # ── Pulizia e pre-processing ─────────────────────────────────────────────
    st.subheader("Pulizia e pre-processing")

    risposte["pulizia"] = st.radio(
        "10. Il dataset è stato pulito o pre-processato?",
        ["Sì", "No", "Non lo so"]
    )

    if risposte["pulizia"] == "Sì":
        risposte["doc_pulizia"] = st.radio(
            "11. Le operazioni di pulizia sono documentate?",
            ["Sì", "No", "Non lo so"]
        )

    st.divider()

    # ── Data card ────────────────────────────────────────────────────────────
    st.subheader("Data card")

    risposte["data_card"] = st.radio(
        "12. Esiste una data card o datasheet for datasets per questo dataset?",
        ["Sì", "No", "Non lo so"]
    )

    if risposte["data_card"] == "Sì":
        risposte["data_card_aggiornata"] = st.radio(
            "13. La data card è aggiornata?",
            ["Sì", "No", "Non lo so"]
        )
        file_data_card = st.file_uploader(
            "14. Carica la data card",
            type=["pdf", "docx", "txt"],
            help="Opzionale — carica il file se disponibile"
        )
        if file_data_card is not None:
            st.success("✅ Data card caricata!")
            risposte["data_card_file"] = file_data_card.name

    st.divider()

    # ── Navigazione ──────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        if st.button("← Indietro", use_container_width=True):
            st.session_state.pagina = "home"
            st.rerun()

    with col2:
        if st.button("Analizza dataset →", type="primary", use_container_width=True):
            st.session_state.governance = risposte
            st.session_state.pagina = "risultati"
            st.rerun()
