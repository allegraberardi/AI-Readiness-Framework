import streamlit as st
import pandas as pd
from analisi import (
    analizza_completezza,
    analizza_errori,
    analizza_governance,
    calcola_score_aggregato
)
from rappresentativita import analizza_rappresentativita
from bias import calcola_bias
from rilevanza import calcola_rilevanza

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

        if risultato.get("messaggio"):
            st.info(risultato["messaggio"])

        if risultato.get("dettaglio"):
            df_det = pd.DataFrame(risultato["dettaglio"])
            st.dataframe(df_det, use_container_width=True, hide_index=True)

        st.divider()


def mostra_rappresentativita(risultato):
    """Mostra la rappresentatività con sezione contestuale separata."""
    stato = risultato["stato"]
    emoji = semaforo(stato)

    st.markdown(f"### {emoji} Rappresentatività — {stato}")
    st.caption("📖 Riferimento normativo: Art. 10, par. 3 e par. 4 AI Act — i dati devono essere sufficientemente rappresentativi e tenere conto delle caratteristiche del contesto di utilizzo")

    if stato == "CONFORME":
        st.success("Distribuzione delle classi bilanciata.")
    elif stato == "ATTENZIONE":
        st.warning("Alcune classi sono sottorappresentate. Valutare se applicare tecniche di oversampling (SMOTE) o undersampling.")
    else:
        st.error("Squilibri significativi rilevati. Applicare tecniche di bilanciamento sulle colonne critiche.")

    # Analisi generale
    if risultato.get("dettaglio"):
        st.write("**Analisi generale — classi sottorappresentate:**")
        df_det = pd.DataFrame(risultato["dettaglio"])
        st.dataframe(df_det, use_container_width=True, hide_index=True)

    # Analisi contestuale per settore
    contestuale = risultato.get("contestuale")
    if contestuale:
        st.write("---")
        st.write(f"**Analisi contestuale per il settore selezionato**")
        st.info(f"Per questo settore è importante monitorare: **{contestuale['focus']}**\n\n_{contestuale['motivo']}_")

        if not contestuale.get("trovate"):
            st.warning("Non ho trovato colonne demografiche rilevanti per questo settore nel dataset. Verifica se le variabili sensibili sono presenti con nomi diversi.")
        else:
            st.write(f"Colonne rilevanti trovate: **{', '.join(contestuale.get('colonne_trovate', []))}**")
            if contestuale.get("dettaglio"):
                st.write("Gruppi sottorappresentati per le variabili demografiche del settore:")
                df_cont = pd.DataFrame(contestuale["dettaglio"])
                st.dataframe(df_cont, use_container_width=True, hide_index=True)
            else:
                st.success("Tutte le variabili demografiche rilevanti per questo settore sono adeguatamente rappresentate.")

    st.divider()


def mostra_risultati():
    st.title("Risultati — Report AI Readiness")
    st.write(f"**Settore:** {st.session_state.settore}")

    df = st.session_state.dataset
    governance = st.session_state.governance
    descrizione = st.session_state.descrizione
    settore = st.session_state.settore
    target = st.session_state.get("target")
    attributi_sensibili = st.session_state.get("attributi_sensibili", [])

    # ── Esegui analisi ───────────────────────────────────────────────────────
    with st.spinner("Analisi del dataset in corso..."):
        res_completezza = analizza_completezza(df)
        res_rappresentativita = analizza_rappresentativita(df, settore)
        res_errori = analizza_errori(df)
        res_governance = analizza_governance(governance)
        res_rilevanza = calcola_rilevanza(df, descrizione, settore)

        if target and attributi_sensibili:
            res_bias = calcola_bias(df, target, attributi_sensibili)
        else:
            res_bias = {
                "stato": "ATTENZIONE",
                "dettaglio": [],
                "messaggio": "Dimensione non valutata — target o attributi sensibili non selezionati."
            }

    risultati = {
        "completezza": res_completezza,
        "rappresentativita": res_rappresentativita,
        "errori": res_errori,
        "governance": res_governance,
        "bias": res_bias,
        "rilevanza": res_rilevanza,
    }

    # ── Score aggregato ──────────────────────────────────────────────────────
    score = calcola_score_aggregato(risultati)

    # ── Riepilogo semafori ───────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    col4, col5, col6 = st.columns(3)

    with col1:
        st.metric("Completezza", f"{semaforo(res_completezza['stato'])} {res_completezza['stato']}")
    with col2:
        st.metric("Rappresentatività", f"{semaforo(res_rappresentativita['stato'])} {res_rappresentativita['stato']}")
    with col3:
        st.metric("Assenza di errori", f"{semaforo(res_errori['stato'])} {res_errori['stato']}")
    with col4:
        st.metric("Governance", f"{semaforo(res_governance['stato'])} {res_governance['stato']}")
    with col5:
        st.metric("Assenza di bias", f"{semaforo(res_bias['stato'])} {res_bias['stato']}")
    with col6:
        st.metric("Rilevanza", f"{semaforo(res_rilevanza['stato'])} {res_rilevanza['stato']}")

    st.divider()

    # ── Score finale ─────────────────────────────────────────────────────────
    if score >= 70:
        st.success(f"### AI Readiness Score: {score}/100 — Dataset sufficientemente conforme")
    elif score >= 40:
        st.warning(f"### AI Readiness Score: {score}/100 — Miglioramenti necessari")
    else:
        st.error(f"### AI Readiness Score: {score}/100 — Dataset non conforme all'AI Act")

    st.divider()

    # ── Dettaglio per dimensione ─────────────────────────────────────────────
    mostra_dimensione(
        titolo="Rilevanza",
        riferimento="Art. 10, par. 3 AI Act — i dati devono essere pertinenti rispetto alle finalità previste",
        risultato=res_rilevanza,
        raccomandazione=(
            f"Score medio di rilevanza: {res_rilevanza.get('score_medio', 0)}%. "
            + ("Le colonne del dataset sono pertinenti al caso d'uso descritto." if res_rilevanza["stato"] == "CONFORME"
               else f"Il {res_rilevanza.get('pct_irrilevanti', 0)}% delle colonne sembra poco pertinente al caso d'uso.")
        )
    )

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

    # Rappresentatività con sezione contestuale
    mostra_rappresentativita(res_rappresentativita)

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
        titolo="Assenza di bias",
        riferimento="Art. 10, par. 2(f) e 2(g) AI Act — esaminare le possibili distorsioni e adottare misure adeguate",
        risultato=res_bias,
        raccomandazione=(
            "Nessun bias significativo rilevato." if res_bias["stato"] == "CONFORME"
            else "Applicare tecniche di mitigazione del bias (re-sampling, re-weighting) sugli attributi critici."
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
            st.session_state.target = None
            st.session_state.attributi_sensibili = []
            st.rerun()
    with col2:
        st.button("📄 Scarica Report PDF", use_container_width=True, disabled=True,
                  help="Funzionalità in sviluppo")
