import pandas as pd
from rappresentativita import analizza_rappresentativita

def analizza_completezza(df):
    totale_celle = df.shape[0] * df.shape[1]
    totale_mancanti = df.isnull().sum().sum()
    pct_totale = round(totale_mancanti / totale_celle * 100, 2)

    dettaglio = []
    for col in df.columns:
        n_mancanti = df[col].isnull().sum()
        pct = round(n_mancanti / df.shape[0] * 100, 2)
        if n_mancanti > 0:
            gravita = "ALTA" if pct > 15 else "MEDIA" if pct > 5 else "BASSA"
            dettaglio.append({
                "Colonna": col,
                "Valori mancanti": n_mancanti,
                "%": f"{pct}%",
                "Gravità": gravita
            })

    if pct_totale < 5:
        stato = "CONFORME"
    elif pct_totale < 15:
        stato = "ATTENZIONE"
    else:
        stato = "NON CONFORME"

    return {"stato": stato, "pct_totale": pct_totale, "dettaglio": dettaglio}


def analizza_errori(df):
    dettaglio = []

    n_duplicati = df.duplicated().sum()
    pct_duplicati = round(n_duplicati / df.shape[0] * 100, 2)
    if n_duplicati > 0:
        gravita = "ALTA" if pct_duplicati > 10 else "MEDIA" if pct_duplicati > 5 else "BASSA"
        dettaglio.append({
            "Colonna": "Intero dataset",
            "Problema rilevato": f"{n_duplicati} righe duplicate ({pct_duplicati}%)",
            "Gravità": gravita
        })

    for col in df.select_dtypes(include=["number"]).columns:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        outliers = df[(df[col] < Q1 - 1.5 * IQR) | (df[col] > Q3 + 1.5 * IQR)]
        n_outlier = len(outliers)
        if n_outlier > 0:
            pct_out = round(n_outlier / df.shape[0] * 100, 2)
            gravita = "ALTA" if pct_out > 5 else "MEDIA" if pct_out > 1 else "BASSA"
            dettaglio.append({
                "Colonna": col,
                "Problema rilevato": f"{n_outlier} outlier rilevati con IQR ({pct_out}%)",
                "Gravità": gravita
            })

    if any(d["Gravità"] == "ALTA" for d in dettaglio):
        stato = "NON CONFORME"
    elif dettaglio:
        stato = "ATTENZIONE"
    else:
        stato = "CONFORME"

    return {"stato": stato, "dettaglio": dettaglio}


def analizza_governance(risposte):
    """
    Calcola lo score di governance dalle risposte del questionario.
    - "No" → problema ALTA gravità (NON CONFORME)
    - "Non lo so" → problema MEDIA gravità (ATTENZIONE)
    - "Sì" → nessun problema
    """
    problemi = []

    # Documentazione raccolta
    if risposte.get("doc_raccolta") == "No":
        problemi.append({"Problema": "Documentazione raccolta assente", "Dettaglio": "Non esiste documentazione sul processo di raccolta dei dati", "Gravità": "ALTA"})
    elif risposte.get("doc_raccolta") == "Non lo so":
        problemi.append({"Problema": "Documentazione raccolta — informazione non disponibile", "Dettaglio": "Non è noto se esiste documentazione sul processo di raccolta", "Gravità": "MEDIA"})

    # Consenso
    if risposte.get("consenso") == "No":
        problemi.append({"Problema": "Consenso assente", "Dettaglio": "Nessuna documentazione del consenso per i soggetti del dataset", "Gravità": "ALTA"})
    elif risposte.get("consenso") == "Non lo so":
        problemi.append({"Problema": "Consenso — informazione non disponibile", "Dettaglio": "Non è noto se il consenso è stato ottenuto", "Gravità": "MEDIA"})

    # Etichettatura
    if risposte.get("etichettati") == "Sì":
        if risposte.get("doc_etichettatura") == "No":
            problemi.append({"Problema": "Criteri etichettatura non documentati", "Dettaglio": "I dati sono etichettati ma non esistono criteri documentati", "Gravità": "ALTA"})
        elif risposte.get("doc_etichettatura") == "Non lo so":
            problemi.append({"Problema": "Criteri etichettatura — informazione non disponibile", "Dettaglio": "Non è noto se esistono criteri documentati per l'etichettatura", "Gravità": "MEDIA"})

    # Pulizia
    if risposte.get("pulizia") == "Sì":
        if risposte.get("doc_pulizia") == "No":
            problemi.append({"Problema": "Pulizia non documentata", "Dettaglio": "Il dataset è stato pulito ma le operazioni non sono documentate", "Gravità": "ALTA"})
        elif risposte.get("doc_pulizia") == "Non lo so":
            problemi.append({"Problema": "Pulizia — informazione non disponibile", "Dettaglio": "Non è noto se le operazioni di pulizia sono state documentate", "Gravità": "MEDIA"})

    # Data card
    if risposte.get("data_card") == "No":
        problemi.append({"Problema": "Data card assente", "Dettaglio": "Non esiste una data card o datasheet per questo dataset", "Gravità": "ALTA"})
    elif risposte.get("data_card") == "Non lo so":
        problemi.append({"Problema": "Data card — informazione non disponibile", "Dettaglio": "Non è noto se esiste una data card per questo dataset", "Gravità": "MEDIA"})

    if any(p["Gravità"] == "ALTA" for p in problemi):
        stato = "NON CONFORME"
    elif problemi:
        stato = "ATTENZIONE"
    else:
        stato = "CONFORME"

    return {"stato": stato, "dettaglio": problemi}


def calcola_score_aggregato(risultati):
    pesi = {
        "bias":              0.25,
        "rappresentativita": 0.20,
        "governance":        0.20,
        "completezza":       0.15,
        "errori":            0.10,
        "rilevanza":         0.10,
    }

    punteggi = {
        "CONFORME":     1.0,
        "ATTENZIONE":   0.5,
        "NON CONFORME": 0.0
    }

    score = 0
    peso_totale = 0
    for dim, peso in pesi.items():
        if dim in risultati:
            score += punteggi.get(risultati[dim]["stato"], 0) * peso
            peso_totale += peso

    if peso_totale > 0:
        score = score / peso_totale

    return round(score * 100, 1)
