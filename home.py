import streamlit as st
import pandas as pd

def mostra_home():
    st.title("AI Readiness Framework")
    st.write("Verifica se il tuo dataset rispetta i requisiti dell'AI Act per i sistemi ad alto rischio (Allegato III).")

    st.divider()

    # ── Selezione settore ────────────────────────────────────────────────────
    st.subheader("1. Seleziona il settore di applicazione")
    settore = st.selectbox(
        "A quale settore appartiene il tuo sistema AI?",
        [
            "Seleziona...",
            "Biometria",
            "Infrastrutture critiche",
            "Istruzione e formazione",
            "Occupazione e selezione del personale",
            "Servizi essenziali (credito, welfare, assicurazioni)",
            "Forze dell'ordine",
            "Migrazione e gestione delle frontiere",
            "Giustizia e processi democratici"
        ]
    )

    # ── Descrizione caso d'uso ───────────────────────────────────────────────
    st.subheader("2. Descrivi come utilizzerai questo dataset")
    descrizione = st.text_area(
        "Descrizione del caso d'uso",
        placeholder="Es. Questo dataset verrà usato per addestrare un classificatore che predice...",
        height=120
    )

    # ── Caricamento CSV ──────────────────────────────────────────────────────
    st.subheader("3. Carica il tuo dataset")
    file = st.file_uploader(
        "Trascina qui il tuo file CSV oppure clicca per sfogliare",
        type=["csv"],
        help="Formato supportato: .csv — Max 200 MB"
    )

    if file is not None:
        try:
            df = pd.read_csv(file, sep=None, engine="python")
            st.success(f"✅ File caricato correttamente — {df.shape[0]} righe × {df.shape[1]} colonne")
            st.dataframe(df.head(5), use_container_width=True)
            st.session_state.dataset = df
        except Exception as e:
            st.error(f"Errore nella lettura del file: {e}")

    st.divider()

    # ── Pulsante Avanti ──────────────────────────────────────────────────────
    if st.button("Avanti →", type="primary", use_container_width=True):
        if settore == "Seleziona...":
            st.warning("Seleziona il settore di applicazione prima di continuare.")
        elif not descrizione.strip():
            st.warning("Inserisci una descrizione del caso d'uso prima di continuare.")
        elif st.session_state.dataset is None:
            st.warning("Carica il dataset CSV prima di continuare.")
        else:
            st.session_state.settore = settore
            st.session_state.descrizione = descrizione
            st.session_state.pagina = "governance"
            st.rerun()
