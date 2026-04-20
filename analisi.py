import pandas as pd

def analizza_completezza(df):
    """Calcola la percentuale di valori mancanti per colonna e totale."""
    totale_celle = df.shape[0] * df.shape[1]
    totale_mancanti = df.isnull().sum().sum()
    pct_totale = round(totale_mancanti / totale_celle * 100, 2)

    dettaglio = []
    for col in df.columns:
        n_mancanti = df[col].isnull().sum()
        pct = round(n_mancanti / df.shape[0] * 100, 2)
        if n_mancanti > 0:
            if pct > 15:
                gravita = "ALTA"
            elif pct > 5:
                gravita = "MEDIA"
            else:
                gravita = "BASSA"
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

    return {
        "stato": stato,
        "pct_totale": pct_totale,
        "dettaglio": dettaglio
    }


def analizza_rappresentativita(df):
    """Analizza la distribuzione delle variabili categoriche."""
    dettaglio = []

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

        if min_classe < 100:
            dettaglio.append({
                "Colonna": col,
                "Problema rilevato": f"Classe '{classe_min}' ha solo {min_classe} esempi ({pct_min}%)",
                "Gravità": gravita
            })

    if any(d["Gravità"] == "ALTA" for d in dettaglio):
        stato = "NON CONFORME"
    elif dettaglio:
        stato = "ATTENZIONE"
    else:
        stato = "CONFORME"

    return {
        "stato": stato,
        "dettaglio": dettaglio
    }


def analizza_errori(df):
    """Rileva duplicati e outlier numerici con IQR."""
    dettaglio = []

    # Duplicati
    n_duplicati = df.duplicated().sum()
    pct_duplicati = round(n_duplicati / df.shape[0] * 100, 2)
    if n_duplicati > 0:
        if pct_duplicati > 10:
            gravita = "ALTA"
        elif pct_duplicati > 5:
            gravita = "MEDIA"
        else:
            gravita = "BASSA"
        dettaglio.append({
            "Colonna": "Intero dataset",
            "Problema rilevato": f"{n_duplicati} righe duplicate ({pct_duplicati}%)",
            "Gravità": gravita
        })

    # Outlier con IQR per colonne numeriche
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

    return {
        "stato": stato,
        "dettaglio": dettaglio
    }


def analizza_governance(risposte):
    """Calcola lo score di governance dalle risposte del questionario."""
    problemi = []

    if risposte.get("doc_raccolta") == "No":
        problemi.append({
            "Problema": "Documentazione raccolta assente",
            "Dettaglio": "Non esiste documentazione sul processo di raccolta dei dati",
            "Gravità": "ALTA"
        })

    if risposte.get("consenso") == "No":
        problemi.append({
            "Problema": "Consenso assente",
            "Dettaglio": "Nessuna documentazione del consenso per i soggetti del dataset",
            "Gravità": "ALTA"
        })

    if risposte.get("etichettati") == "Sì" and risposte.get("doc_etichettatura") == "No":
        problemi.append({
            "Problema": "Criteri etichettatura non documentati",
            "Dettaglio": "I dati sono etichettati ma non esistono criteri documentati",
            "Gravità": "MEDIA"
        })

    if risposte.get("pulizia") == "Sì" and risposte.get("doc_pulizia") == "No":
        problemi.append({
            "Problema": "Pulizia non documentata",
            "Dettaglio": "Il dataset è stato pulito ma le operazioni non sono documentate",
            "Gravità": "MEDIA"
        })

    if risposte.get("data_card") == "No":
        problemi.append({
            "Problema": "Data card assente",
            "Dettaglio": "Non esiste una data card o datasheet per questo dataset",
            "Gravità": "ALTA"
        })

    if any(p["Gravità"] == "ALTA" for p in problemi):
        stato = "NON CONFORME"
    elif problemi:
        stato = "ATTENZIONE"
    else:
        stato = "CONFORME"

    return {
        "stato": stato,
        "dettaglio": problemi
    }


def calcola_score_aggregato(risultati):
    """
    Calcola lo score aggregato pesato secondo la classifica delle dimensioni.
    Pesi basati sull'importanza nell'Art. 10 (da definire con la prof):
    - Assenza di bias: 30%
    - Rappresentatività: 25%
    - Governance: 20%
    - Completezza: 15%
    - Assenza di errori: 10%
    """
    pesi = {
        "completezza": 0.15,
        "rappresentativita": 0.25,
        "errori": 0.10,
        "governance": 0.20,
    }

    punteggi = {
        "CONFORME": 1.0,
        "ATTENZIONE": 0.5,
        "NON CONFORME": 0.0
    }

    score = 0
    for dim, peso in pesi.items():
        if dim in risultati:
            score += punteggi.get(risultati[dim]["stato"], 0) * peso

    return round(score * 100, 1)
