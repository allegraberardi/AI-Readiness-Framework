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

def semaforo(stato):
    if stato == "CONFORME":
        return "🟢"
    elif stato == "ATTENZIONE":
        return "🟡"
    else:
        return "🔴"

# Soglie per ogni dimensione
SOGLIE = {
    "Completezza": [
        ("🟢 Conforme", "Valori mancanti < 5%"),
        ("🟡 Attenzione", "Valori mancanti tra 5% e 15%"),
        ("🔴 Non conforme", "Valori mancanti > 15%"),
    ],
    "Rappresentatività": [
        ("🟢 Conforme", "Tutte le classi hanno più di 100 esempi"),
        ("🟡 Attenzione", "Almeno una classe ha tra 50 e 100 esempi"),
        ("🔴 Non conforme", "Almeno una classe ha meno di 50 esempi"),
    ],
    "Assenza di errori": [
        ("🟢 Conforme", "Nessun duplicato o outlier significativo"),
        ("🟡 Attenzione", "Duplicati tra 5% e 10% oppure outlier tra 1% e 5%"),
        ("🔴 Non conforme", "Duplicati > 10% oppure outlier > 5%"),
    ],
    "Assenza di bias": [
        ("🟢 Conforme", "Statistical Parity Difference < 0.1 e Disparate Impact tra 0.8 e 1.25 e Class Imbalance < 20%"),
        ("🟡 Attenzione", "Statistical Parity Difference tra 0.1 e 0.2 oppure Disparate Impact tra 0.6 e 0.8 oppure Class Imbalance tra 20% e 40%"),
        ("🔴 Non conforme", "Statistical Parity Difference > 0.2 oppure Disparate Impact < 0.6 oppure Class Imbalance > 40%"),
    ],
    "Rilevanza": [
        ("🟢 Conforme", "Score medio LLM > 60/100 e colonne irrilevanti < 25%"),
        ("🟡 Attenzione", "Score medio LLM tra 30 e 60 oppure colonne irrilevanti tra 25% e 50%"),
        ("🔴 Non conforme", "Score medio LLM < 30 oppure colonne irrilevanti > 50%"),
    ],
    "Governance e Consenso": [
        ("🟢 Conforme", "Tutte le informazioni documentate"),
        ("🟡 Attenzione", "Alcune informazioni non disponibili (Non lo so)"),
        ("🔴 Non conforme", "Informazioni chiave assenti (consenso, data card, documentazione raccolta)"),
    ],
}


def mostra_dimensione(titolo, riferimento, risultato, raccomandazione, commento_extra=None):
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

        if commento_extra:
            st.info(f"**Valutazione LLM sui duplicati:** {commento_extra}")

        if risultato.get("dettaglio"):
            df_det = pd.DataFrame(risultato["dettaglio"])
            st.dataframe(df_det, use_container_width=True, hide_index=True)

        # Soglie espandibili
        if titolo in SOGLIE:
            with st.expander("📏 Soglie utilizzate per questa dimensione"):
                for label, desc in SOGLIE[titolo]:
                    st.write(f"**{label}**: {desc}")

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
        res_errori = analizza_errori(df, descrizione)
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
    # Rilevanza con commento LLM
    with st.container():
        stato_rile = res_rilevanza["stato"]
        emoji_rile = semaforo(stato_rile)
        st.markdown(f"### {emoji_rile} Rilevanza — {stato_rile}")
        st.caption("📖 Riferimento normativo: Art. 10, par. 3 AI Act — i dati devono essere pertinenti rispetto alle finalità previste")

        raccomandazione_rile = (
            f"Score medio di rilevanza: {res_rilevanza.get('score_medio', 0)}/100. "
            + ("Le colonne del dataset sono pertinenti al caso d'uso descritto." if stato_rile == "CONFORME"
               else f"Il {res_rilevanza.get('pct_irrilevanti', 0)}% delle colonne risulta poco pertinente al caso d'uso.")
        )

        if stato_rile == "CONFORME":
            st.success(raccomandazione_rile)
        elif stato_rile == "ATTENZIONE":
            st.warning(raccomandazione_rile)
        else:
            st.error(raccomandazione_rile)

        if res_rilevanza.get("messaggio"):
            st.info(res_rilevanza["messaggio"])

        if res_rilevanza.get("commento"):
            st.info(f"**Commento LLM:** {res_rilevanza['commento']}")

        if res_rilevanza.get("dettaglio"):
            st.write("**Dettaglio per colonna:**")
            df_rile = pd.DataFrame(res_rilevanza["dettaglio"])
            st.dataframe(df_rile, use_container_width=True, hide_index=True)

        with st.expander("📏 Soglie utilizzate per questa dimensione"):
            for label, desc in SOGLIE["Rilevanza"]:
                st.write(f"**{label}**: {desc}")

        st.divider()

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

    # Rappresentatività con grafici e LLM
    mostra_rappresentativita_con_grafici(res_rappresentativita, descrizione, settore, df)

    # Raccomandazione specifica in base al tipo di problema
    n_dup = res_errori.get("n_duplicati", 0)
    has_out = res_errori.get("has_outliers", False)
    if n_dup > 0 and has_out:
        raccomandazione_errori = f"Rilevati {n_dup} duplicati e valori anomali nelle colonne indicate — verificare e correggere prima di procedere."
    elif n_dup > 0:
        raccomandazione_errori = f"Rilevati {n_dup} duplicati nel dataset — valutare se rimuoverli in base al caso d'uso."
    elif has_out:
        raccomandazione_errori = "Rilevati valori anomali nelle colonne indicate — verificare se sono errori o valori legittimi."
    else:
        raccomandazione_errori = "Nessun errore significativo rilevato."

    mostra_dimensione(
        titolo="Assenza di errori",
        riferimento="Art. 10, par. 3 AI Act — i dati devono essere esenti da errori nella misura del possibile",
        risultato=res_errori,
        raccomandazione=raccomandazione_errori,
        commento_extra=res_errori.get("commento_duplicati")
    )

    # Boxplot per colonne numeriche con outlier
    colonne_outlier = [
        d["Colonna"] for d in res_errori.get("dettaglio", [])
        if "outlier" in d.get("Problema rilevato", "") and d["Colonna"] != "Intero dataset"
    ]
    if colonne_outlier:
        try:
            import plotly.express as px
            st.write("**Visualizzazione outlier — Boxplot:**")
            st.caption("Le boxplot mostrano la distribuzione dei valori per ogni colonna con outlier rilevati. I punti fuori dai baffi (whisker) sono i valori anomali identificati dal metodo IQR.")
            for col in colonne_outlier:
                if col in df.columns:
                    gravita = next(
                        (d["Gravità"] for d in res_errori.get("dettaglio", [])
                         if d["Colonna"] == col), "")
                    with st.expander(f"📊 {col} — Gravità: {gravita}"):
                        fig = px.box(
                            df, y=col,
                            title=f"Distribuzione e outlier — {col}",
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
            st.warning("Installa plotly per visualizzare le boxplot: pip install plotly")

    # Messaggio se nessun duplicato
    if n_dup == 0 and res_errori["stato"] != "CONFORME":
        pass  # già gestito dalla raccomandazione

    # Assenza di bias con commento LLM
    with st.container():
        stato_bias = res_bias["stato"]
        emoji_bias = semaforo(stato_bias)
        st.markdown(f"### {emoji_bias} Assenza di bias — {stato_bias}")
        st.caption("📖 Riferimento normativo: Art. 10, par. 2(f) e 2(g) AI Act — esaminare le possibili distorsioni e adottare misure adeguate")

        if stato_bias == "CONFORME":
            st.success("Nessun bias significativo rilevato.")
        elif stato_bias == "ATTENZIONE":
            st.warning("Bias moderato rilevato — applicare tecniche di mitigazione sugli attributi critici.")
        else:
            st.error("Applicare tecniche di mitigazione del bias (re-sampling, re-weighting) sugli attributi critici.")

        if res_bias.get("messaggio"):
            st.info(res_bias["messaggio"])

        if res_bias.get("dettaglio"):
            df_bias = pd.DataFrame(res_bias["dettaglio"])
            st.dataframe(df_bias, use_container_width=True, hide_index=True)

            # Commento LLM
            st.write("**Interpretazione LLM:**")
            with st.spinner("L'LLM sta analizzando il bias..."):
                commento_bias = commento_llm_bias(
                    res_bias["dettaglio"], descrizione, settore, target or "non specificato"
                )
            st.info(commento_bias)

        with st.expander("📏 Soglie utilizzate per questa dimensione"):
            for label, desc in SOGLIE["Assenza di bias"]:
                st.write(f"**{label}**: {desc}")

        st.divider()

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
    if st.button("← Torna all'inizio", use_container_width=True):
    st.session_state.pagina = "home"
    st.session_state.dataset = None
    st.session_state.governance = {}
    st.session_state.target = None
    st.session_state.attributi_sensibili = []
    st.rerun()
