import pandas as pd
import streamlit as st
import json
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# ── Variabili demografiche rilevanti per settore ──────────────────────────────
VARIABILI_PER_SETTORE = {
    "Occupazione e selezione del personale": {
        "keywords": ["gender", "genere", "sex", "sesso", "age", "età", "eta",
                     "education", "istruzione", "nationality", "nazionalità", "country"],
        "focus": "genere, età e livello di istruzione",
        "motivo": "I sistemi di selezione del personale possono discriminare in base a genere, età e provenienza — come nel caso Amazon (2018)."
    },
    "Servizi essenziali (credito, welfare, assicurazioni)": {
        "keywords": ["gender", "genere", "sex", "sesso", "age", "età", "eta",
                     "income", "reddito", "race", "razza", "ethnicity", "etnia",
                     "education", "istruzione"],
        "focus": "genere, età, etnia e reddito",
        "motivo": "I sistemi di valutazione del credito possono discriminare in base a genere ed etnia, perpetuando disuguaglianze storiche."
    },
    "Forze dell'ordine": {
        "keywords": ["race", "razza", "ethnicity", "etnia", "nationality",
                     "nazionalità", "age", "età", "eta", "gender", "genere"],
        "focus": "etnia, razza e provenienza geografica",
        "motivo": "I sistemi usati nelle forze dell'ordine mostrano bias sistematici contro minoranze etniche — come documentato nel caso COMPAS."
    },
    "Istruzione e formazione": {
        "keywords": ["country", "paese", "nationality", "nazionalità", "gender",
                     "genere", "sex", "sesso", "age", "età", "eta"],
        "focus": "provenienza geografica e genere",
        "motivo": "I sistemi di valutazione scolastica possono riflettere disuguaglianze geografiche e di genere."
    },
    "Giustizia e processi democratici": {
        "keywords": ["race", "razza", "ethnicity", "etnia", "age", "età", "eta",
                     "gender", "genere", "income", "reddito"],
        "focus": "etnia, razza ed età",
        "motivo": "I sistemi di supporto decisionale in ambito giudiziario devono garantire equità tra gruppi demografici diversi."
    },
    "Migrazione e gestione delle frontiere": {
        "keywords": ["nationality", "nazionalità", "country", "paese",
                     "religion", "religione", "age", "età", "eta", "gender", "genere"],
        "focus": "nazionalità, religione e provenienza geografica",
        "motivo": "I sistemi di valutazione delle domande di asilo devono essere rappresentativi di tutte le nazionalità."
    },
    "Biometria": {
        "keywords": ["race", "razza", "ethnicity", "etnia", "gender", "genere",
                     "age", "età", "eta", "skin", "pelle"],
        "focus": "etnia, genere ed età",
        "motivo": "I sistemi biometrici mostrano performance inferiori su persone di colore e donne."
    },
    "Infrastrutture critiche": {
        "keywords": ["region", "regione", "area", "zone", "zona", "location", "posizione"],
        "focus": "distribuzione geografica",
        "motivo": "I sistemi per infrastrutture critiche devono coprire tutte le aree geografiche."
    }
}


def get_client():
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )


def analizza_rappresentativita(df, settore=None):
    """
    Analisi completa della rappresentatività con statistiche per ogni colonna.
    """
    dettaglio_categoriche = []
    dettaglio_numeriche = []
    problemi = []

    # ── Colonne categoriche ──────────────────────────────────────────────────
    for col in df.select_dtypes(include=["object", "category"]).columns:
        conteggi = df[col].value_counts()
        min_classe = conteggi.min()
        classe_min = conteggi.idxmin()
        pct_min = round(min_classe / df.shape[0] * 100, 2)

        if min_classe < 50:
            gravita = "ALTA"
        elif min_classe < 100:
            gravita = "MEDIA"
        else:
            gravita = "BASSA"

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
                "Colonna": col,
                "Problema": f"Classe '{classe_min}' ha solo {min_classe} esempi ({pct_min}%)",
                "Gravità": gravita
            })

    # ── Colonne numeriche ────────────────────────────────────────────────────
    for col in df.select_dtypes(include=["number"]).columns:
        dettaglio_numeriche.append({
            "Colonna": col,
            "Min": round(df[col].min(), 2),
            "Max": round(df[col].max(), 2),
            "Media": round(df[col].mean(), 2),
            "Mediana": round(df[col].median(), 2),
            "Valori unici": df[col].nunique()
        })

    # ── Analisi contestuale per settore ─────────────────────────────────────
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
            "focus": config["focus"],
            "motivo": config["motivo"]
        }

    # ── Stato finale ─────────────────────────────────────────────────────────
    if any(p["Gravità"] == "ALTA" for p in problemi):
        stato = "NON CONFORME"
    elif problemi:
        stato = "ATTENZIONE"
    else:
        stato = "CONFORME"

    return {
        "stato": stato,
        "problemi": problemi,
        "categoriche": dettaglio_categoriche,
        "numeriche": dettaglio_numeriche,
        "contestuale": contestuale
    }


def commento_llm_rappresentativita(df, settore, descrizione, risultato):
    """
    Chiede all'LLM di interpretare i risultati della rappresentatività.
    """
    riassunto = []
    for cat in risultato["categoriche"]:
        top = cat["conteggi"].head(3).to_dict()
        riassunto.append(
            f"{cat['colonna']}: distribuzione {top}, "
            f"classe minima '{cat['classe_min']}' con {cat['min_classe']} esempi ({cat['pct_min']}%)"
        )

    for num in risultato["numeriche"]:
        riassunto.append(
            f"{num['Colonna']}: min={num['Min']}, max={num['Max']}, media={num['Media']}"
        )

    prompt = f"""Sei un esperto di AI fairness e del Regolamento Europeo sull'Intelligenza Artificiale (AI Act).

Analizza la rappresentatività di questo dataset in relazione al caso d'uso descritto.

CASO D'USO: {descrizione}
SETTORE (Allegato III AI Act): {settore}

DISTRIBUZIONE DEI DATI:
{chr(10).join(riassunto)}

Fornisci:
1. Una valutazione della rappresentatività in relazione al caso d'uso
2. Eventuali gruppi sottorappresentati che potrebbero causare problemi
3. Una raccomandazione concreta per migliorare la rappresentatività

Sii conciso (massimo 5 righe) e fai riferimento all'Art. 10 dell'AI Act dove pertinente."""

    try:
        client = get_client()
        response = client.chat.completions.create(
            model="mistralai/mistral-large-2512",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.2
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Errore durante l'analisi LLM: {str(e)}"


def mostra_rappresentativita_con_grafici(risultato, descrizione, settore, df):
    """
    Mostra i risultati della rappresentatività con grafici e commento LLM.
    """
    stato = risultato["stato"]
    emoji = "🟢" if stato == "CONFORME" else "🟡" if stato == "ATTENZIONE" else "🔴"

    st.markdown(f"### {emoji} Rappresentatività — {stato}")
    st.caption("📖 Riferimento normativo: Art. 10, par. 3 e par. 4 AI Act — i dati devono essere sufficientemente rappresentativi")

    if stato == "CONFORME":
        st.success("Distribuzione delle classi bilanciata.")
    elif stato == "ATTENZIONE":
        st.warning("Alcune classi sono sottorappresentate.")
    else:
        st.error("Squilibri significativi rilevati — applicare tecniche di bilanciamento.")

    # ── Grafici colonne categoriche ──────────────────────────────────────────
    if risultato["categoriche"]:
        st.write("**Distribuzione variabili categoriche:**")
        for cat in risultato["categoriche"]:
            with st.expander(f"📊 {cat['colonna']} — classe minima: '{cat['classe_min']}' ({cat['pct_min']}%)"):
                st.bar_chart(cat["conteggi"])

    # ── Statistiche colonne numeriche ────────────────────────────────────────
    if risultato["numeriche"]:
        st.write("**Statistiche variabili numeriche:**")
        df_num = pd.DataFrame(risultato["numeriche"])
        st.dataframe(df_num, use_container_width=True, hide_index=True)

    # ── Analisi contestuale per settore ─────────────────────────────────────
    contestuale = risultato.get("contestuale")
    if contestuale:
        st.write("---")
        st.write("**Analisi contestuale per il settore selezionato:**")
        st.info(f"Per questo settore è importante monitorare: **{contestuale['focus']}**\n\n_{contestuale['motivo']}_")

        if not contestuale.get("trovate"):
            st.warning("Non ho trovato colonne demografiche rilevanti per questo settore nel dataset.")
        else:
            st.write(f"Colonne rilevanti trovate: **{', '.join(contestuale.get('colonne_trovate', []))}**")

    # ── Commento LLM ─────────────────────────────────────────────────────────
    st.write("---")
    st.write("**Interpretazione LLM:**")
    with st.spinner("L'LLM sta analizzando la rappresentatività..."):
        commento = commento_llm_rappresentativita(df, settore, descrizione, risultato)
    st.info(commento)

    # ── Soglie ───────────────────────────────────────────────────────────────
    with st.expander("📏 Soglie utilizzate per questa dimensione"):
        st.write("**🟢 Conforme**: tutte le classi hanno più di 100 esempi")
        st.write("**🟡 Attenzione**: almeno una classe ha tra 50 e 100 esempi")
        st.write("**🔴 Non conforme**: almeno una classe ha meno di 50 esempi")

    st.divider()
