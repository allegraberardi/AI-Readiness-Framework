import pandas as pd
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def prepara_testo_colonne(df):
    """
    Prepara una rappresentazione testuale delle colonne del dataset
    combinando nome colonna, tipo di dato e valori unici (per categoriche).
    """
    testi = []
    for col in df.columns:
        testo = col.replace("_", " ").lower()
        # Aggiungi i valori unici per colonne categoriche
        if df[col].dtype == "object":
            valori = df[col].dropna().unique()[:10]  # max 10 valori
            testo += " " + " ".join([str(v).lower() for v in valori])
        testi.append(testo)
    return testi


def calcola_rilevanza(df, descrizione, settore):
    """
    Calcola la rilevanza del dataset rispetto alla descrizione del caso d'uso
    usando TF-IDF e cosine similarity.
    """
    if not descrizione or not descrizione.strip():
        return {
            "stato": "ATTENZIONE",
            "messaggio": "Nessuna descrizione del caso d'uso fornita. Impossibile valutare la rilevanza.",
            "dettaglio": [],
            "score_medio": 0
        }

    # Prepara i testi delle colonne
    testi_colonne = prepara_testo_colonne(df)

    # Combina descrizione e settore per arricchire il contesto
    testo_query = descrizione.lower() + " " + settore.lower()

    # Calcola TF-IDF e cosine similarity
    try:
        vectorizer = TfidfVectorizer()
        tutti_testi = [testo_query] + testi_colonne
        tfidf_matrix = vectorizer.fit_transform(tutti_testi)

        # Similarità tra query e ogni colonna
        similarita = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

    except Exception:
        # Se TF-IDF fallisce (es. testo troppo corto) usa keyword matching
        similarita = []
        parole_query = set(testo_query.lower().split())
        for testo_col in testi_colonne:
            parole_col = set(testo_col.lower().split())
            if len(parole_col) == 0:
                similarita.append(0)
            else:
                overlap = len(parole_query & parole_col) / len(parole_col)
                similarita.append(overlap)
        similarita = np.array(similarita)

    # Costruisci dettaglio per ogni colonna
    dettaglio = []
    for col, score in zip(df.columns, similarita):
        score_pct = round(score * 100, 1)
        if score_pct >= 20:
            rilevanza = "ALTA"
            gravita = "BASSA"
        elif score_pct >= 5:
            rilevanza = "MEDIA"
            gravita = "MEDIA"
        else:
            rilevanza = "BASSA"
            gravita = "ALTA"

        dettaglio.append({
            "Colonna": col,
            "Score di rilevanza": f"{score_pct}%",
            "Rilevanza": rilevanza,
            "Gravità": gravita
        })

    # Ordina per score decrescente
    dettaglio = sorted(dettaglio, key=lambda x: float(x["Score di rilevanza"].replace("%", "")), reverse=True)

    # Score medio
    score_medio = round(np.mean(similarita) * 100, 1)

    # Colonne irrilevanti (score < 5%)
    n_irrilevanti = sum(1 for d in dettaglio if d["Rilevanza"] == "BASSA")
    pct_irrilevanti = round(n_irrilevanti / len(df.columns) * 100, 1)

    # Stato finale
    if pct_irrilevanti > 50:
        stato = "NON CONFORME"
    elif pct_irrilevanti > 25:
        stato = "ATTENZIONE"
    else:
        stato = "CONFORME"

    return {
        "stato": stato,
        "score_medio": score_medio,
        "pct_irrilevanti": pct_irrilevanti,
        "dettaglio": dettaglio,
        "messaggio": None
    }
