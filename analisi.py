import pandas as pd
from rappresentativita import analizza_rappresentativita
from openai import OpenAI
from dotenv import load_dotenv
import os
import json

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


def get_client():
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )


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


def valuta_duplicati_llm(df, descrizione, n_duplicati, pct_duplicati):
    """
    Chiede all'LLM se i duplicati trovati sono legittimi nel contesto del caso d'uso.
    """
    # Prendi un esempio di riga duplicata
    duplicati_df = df[df.duplicated(keep=False)]
    esempio = duplicati_df.head(2).to_dict(orient="records") if len(duplicati_df) > 0 else []

    prompt = f"""Sei un esperto di qualità dei dati per sistemi AI ad alto rischio (AI Act, Art. 10).

Nel dataset sono state trovate {n_duplicati} righe duplicate ({pct_duplicati}% del totale).

CASO D'USO DEL DATASET: {descrizione}

ESEMPIO DI RIGHE DUPLICATE:
{json.dumps(esempio, indent=2, default=str)}

Rispondi a questa domanda: nel contesto di questo caso d'uso, i duplicati sono un problema o possono essere legittimi?

Rispondi in modo conciso (2-3 righe) spiegando se i duplicati vanno rimossi o se possono essere mantenuti e perché."""

    try:
        client = get_client()
        response = client.chat.completions.create(
            model="mistralai/mistral-large-2512",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.2
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Errore durante l'analisi LLM: {str(e)}"


def controlla_formato_llm(df, descrizione):
    """
    Chiede all'LLM di controllare se i formati delle colonne sono coerenti.
    """
    # Prepara campione di ogni colonna
    campioni = {}
    for col in df.columns:
        valori = df[col].dropna().unique()[:8]
        campioni[col] = [str(v) for v in valori]

    prompt = f"""Sei un esperto di qualità dei dati per sistemi AI.

Controlla se i formati dei dati nelle seguenti colonne sono coerenti e corretti.

CASO D'USO: {descrizione}

CAMPIONI DI VALORI PER COLONNA:
{json.dumps(campioni, indent=2)}

Identifica eventuali problemi di formato come:
- Date scritte in formati diversi
- Numeri con formato inconsistente
- Testo con maiuscole/minuscole miste
- Valori che sembrano impossibili o fuori range
- Codici o ID con formati diversi

Rispondi SOLO in questo formato JSON:
{{
  "problemi": [
    {{
      "colonna": "nome_colonna",
      "problema": "descrizione del problema",
      "gravita": "ALTA|MEDIA|BASSA"
    }}
  ]
}}

Se non ci sono problemi di formato rispondi con lista vuota: {{"problemi": []}}"""

    try:
        client = get_client()
        response = client.chat.completions.create(
            model="mistralai/mistral-large-2512",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.1
        )
        testo = response.choices[0].message.content.strip()
        testo = testo.replace("```json", "").replace("```", "").strip()
        risultato = json.loads(testo)
        return risultato.get("problemi", [])
    except Exception as e:
        return []


def analizza_errori(df, descrizione=""):
    dettaglio = []
    commento_duplicati = None

    # ── Duplicati ─────────────────────────────────────────────────────────────
    n_duplicati = df.duplicated().sum()
    pct_duplicati = round(n_duplicati / df.shape[0] * 100, 2)
    if n_duplicati > 0:
        gravita = "ALTA" if pct_duplicati > 10 else "MEDIA" if pct_duplicati > 5 else "BASSA"
        dettaglio.append({
            "Colonna": "Intero dataset",
            "Problema rilevato": f"{n_duplicati} righe duplicate ({pct_duplicati}%)",
            "Gravità": gravita
        })
        # Chiedi all'LLM se i duplicati sono legittimi
        if descrizione:
            commento_duplicati = valuta_duplicati_llm(df, descrizione, n_duplicati, pct_duplicati)

    # ── Outlier con IQR — esclude colonne binarie ─────────────────────────────
    for col in df.select_dtypes(include=["number"]).columns:
        # Salta colonne binarie (solo 2 valori unici es. 0/1)
        if df[col].nunique() <= 2:
            continue
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

    # ── Formato dati con LLM ──────────────────────────────────────────────────
    problemi_formato = []
    if descrizione:
        problemi_formato = controlla_formato_llm(df, descrizione)
        for p in problemi_formato:
            dettaglio.append({
                "Colonna": p.get("colonna", ""),
                "Problema rilevato": f"Formato: {p.get('problema', '')}",
                "Gravità": p.get("gravita", "MEDIA")
            })

    # ── Stato finale ──────────────────────────────────────────────────────────
    has_outliers = any("outlier" in d.get("Problema rilevato", "") for d in dettaglio)

    if any(d["Gravità"] == "ALTA" for d in dettaglio):
        stato = "NON CONFORME"
    elif dettaglio:
        stato = "ATTENZIONE"
    else:
        stato = "CONFORME"

    return {
        "stato": stato,
        "dettaglio": dettaglio,
        "commento_duplicati": commento_duplicati,
        "n_duplicati": n_duplicati,
        "has_outliers": has_outliers
    }


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

    # ── Sezione GDPR ─────────────────────────────────────────────────────────
    if risposte.get("base_giuridica") == "Non lo so":
        problemi.append({"Problema": "Base giuridica GDPR non documentata", "Dettaglio": "Non è nota la base giuridica per il trattamento dei dati (Art. 6 GDPR)", "Gravità": "ALTA"})

    if risposte.get("categorie_speciali") == "Sì":
        if risposte.get("consenso_esplicito") == "No":
            problemi.append({"Problema": "Consenso esplicito assente — categorie speciali", "Dettaglio": "Il dataset contiene categorie speciali (Art. 9 GDPR) ma non è stato ottenuto consenso esplicito", "Gravità": "ALTA"})
        elif risposte.get("consenso_esplicito") == "Non lo so":
            problemi.append({"Problema": "Consenso esplicito — informazione non disponibile", "Dettaglio": "Non è noto se il consenso esplicito per le categorie speciali è stato ottenuto (Art. 9 GDPR)", "Gravità": "MEDIA"})

    if risposte.get("informativa_ai") == "No":
        problemi.append({"Problema": "Informativa sull'uso AI assente", "Dettaglio": "Le persone non sono state informate che i dati sarebbero stati usati per addestrare un sistema AI (Art. 13 GDPR)", "Gravità": "ALTA"})
    elif risposte.get("informativa_ai") == "Non lo so":
        problemi.append({"Problema": "Informativa sull'uso AI — informazione non disponibile", "Dettaglio": "Non è noto se le persone sono state informate dell'uso AI dei loro dati (Art. 13 GDPR)", "Gravità": "MEDIA"})

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
