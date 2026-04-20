import streamlit as st
import pandas as pd
from analisi import (
    analizza_completezza,
    analizza_rappresentativita,
    analizza_errori,
    analizza_governance,
    calcola_score_aggregato
)

def semaforo(stato):
    if stato == "CONFORME":
        return "🟢"
    elif stato == "ATTENZIONE":
        return "🟡"
    else:
        return "🔴"

def mostra_dimensione(titolo, riferimento, risultato, raccomandazione):
    stato = risultato["stato"]
    emoji = semaforo(stato)

    with st.container():
        st.markdown(f"### {emoji} {titolo} — {stato}")
        st.caption(f"📖 Riferimento normativo: {riferimento}")

        if stato == "CONFORME":
            st.success(raccomandazione)
        elif stato == "ATTENZIONE":
            st.warning(raccomandazione)
        else:
            st.error(raccomandazione)

        if risultato.get("dettaglio"):
            df_det = pd.DataFrame(risultato["dettaglio"])
            st.dataframe(df_det, use_container_width=True, hide_index=True)

        st.divider()


def mostra_risultati():
    st.title("Risultati — Report AI Readiness")
    st.write(f"**Settore:** {st.session_state.settore}")

    df = st.session_state.dataset
    governance = st.session_state.governance

    # ── Esegui analisi ───────────────────────────────────────────────────────
    with st.spinner("Analisi del dataset in corso..."):
        res_completezza = analizza_completezza(df)
        res_rappresentativita = analizza_rappresentativita(df)
        res_errori = analizza_errori(df)
        res_governance = analizza_governance(governance)

    risultati = {
        "completezza": res_completezza,
        "rappresentativita": res_rappresentativita,
        "errori": res_errori,
        "governance": res_governance,
    }

    # ── Score aggregato ──────────────────────────────────────────────────────
    score = calcola_score_aggregato(risultati)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Completezza", f"{semaforo(res_completezza['stato'])} {res_completezza['stato']}")
    with col2:
        st.metric("Rappresentatività", f"{semaforo(res_rappresentativita['stato'])} {res_rappresentativita['stato']}")
    with col3:
        st.metric("Assenza di errori", f"{semaforo(res_errori['stato'])} {res_errori['stato']}")
    with col4:
        st.metric("Governance", f"{semaforo(res_governance['stato'])} {res_governance['stato']}")

    st.divider()

    # ── Score finale ─────────────────────────────────────────────────────────
    if score >= 70:
        st.success(f"### 🏆 AI Readiness Score: {score}/100 — Dataset sufficientemente conforme")
    elif score >= 40:
        st.warning(f"### ⚠️ AI Readiness Score: {score}/100 — Miglioramenti necessari")
    else:
        st.error(f"### ❌ AI Readiness Score: {score}/100 — Dataset non conforme all'AI Act")

    st.divider()

    # ── Dettaglio per dimensione ─────────────────────────────────────────────
    mostra_dimensione(
        titolo="Completezza",
        riferimento="Art. 10, par. 3 AI Act — i dati devono essere completi nella misura del possibile",
        risultato=res_completezza,
        raccomandazione=(
            f"Il dataset presenta il {res_completezza['pct_totale']}% di valori mancanti. "
            + ("Nessuna azione correttiva richiesta." if res_completezza["stato"] == "CONFORME"
               else "Si raccomanda di verificare e integrare i valori mancanti nelle colonne critiche.")
        )
    )

    mostra_dimensione(
        titolo="Rappresentatività",
        riferimento="Art. 10, par. 3 AI Act — i dati devono essere sufficientemente rappresentativi",
        risultato=res_rappresentativita,
        raccomandazione=(
            "Distribuzione delle classi bilanciata." if res_rappresentativita["stato"] == "CONFORME"
            else "Applicare tecniche di oversampling (SMOTE) o undersampling sulle colonne critiche."
        )
    )

    mostra_dimensione(
        titolo="Assenza di errori",
        riferimento="Art. 10, par. 3 AI Act — i dati devono essere esenti da errori nella misura del possibile",
        risultato=res_errori,
        raccomandazione=(
            "Nessun errore significativo rilevato." if res_errori["stato"] == "CONFORME"
            else "Rimuovere i duplicati e verificare i valori anomali nelle colonne indicate."
        )
    )

    mostra_dimensione(
        titolo="Governance e Consenso",
        riferimento="Art. 10, par. 2 AI Act — i dati devono essere soggetti a pratiche di governance adeguate",
        risultato=res_governance,
        raccomandazione=(
            "La governance del dataset è adeguata." if res_governance["stato"] == "CONFORME"
            else "Documentare le informazioni mancanti e aggiornare la data card del dataset."
        )
    )

    st.divider()

    # ── Navigazione ──────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Torna all'inizio", use_container_width=True):
            st.session_state.pagina = "home"
            st.session_state.dataset = None
            st.session_state.governance = {}
            st.rerun()
    with col2:
        st.button("📄 Scarica Report PDF", use_container_width=True, disabled=True,
                  help="Funzionalità in sviluppo")
