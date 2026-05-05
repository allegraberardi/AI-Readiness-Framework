import pandas as pd
import json
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


def get_client():
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )


def pulisci_testo(testo):
    """Rimuove caratteri speciali che potrebbero rompere il JSON."""
    return str(testo).replace('"', "'").replace('\\', '').replace('\n', ' ').strip()


def descrivi_colonna(df, col):
    """
    Genera una descrizione automatica di una colonna basata
    sul tipo di dato e i valori presenti.
    """
    dtype = df[col].dtype
    n_unici = df[col].nunique()
    n_nulli = df[col].isnull().sum()

    if dtype == "object":
        valori = df[col].dropna().unique()[:5]
        valori_puliti = [pulisci_testo(v) for v in valori]
        return f"Categorica — {n_unici} valori unici, es: {', '.join(valori_puliti)}"
    elif dtype in ["int64", "float64"]:
        min_val = round(df[col].min(), 2)
        max_val = round(df[col].max(), 2)
        media = round(df[col].mean(), 2)
        return f"Numerica — min: {min_val}, max: {max_val}, media: {media}"
    else:
        return f"Tipo: {dtype} — {n_unici} valori unici"


def calcola_rilevanza(df, descrizione, settore):
    """
    Usa l'LLM per valutare la rilevanza di ogni colonna del dataset
    rispetto alla descrizione del caso d'uso e al settore.
    """
    if not descrizione or not descrizione.strip():
        return {
            "stato": "ATTENZIONE",
            "messaggio": "Nessuna descrizione del caso d'uso fornita. Impossibile valutare la rilevanza.",
            "dettaglio": [],
            "score_medio": 0
        }

    # Prepara descrizione delle colonne
    colonne_info = {}
    for col in df.columns:
        colonne_info[col] = descrivi_colonna(df, col)

    colonne_testo = "\n".join([f"- {col}: {desc}" for col, desc in colonne_info.items()])

    prompt = f"""Sei un esperto di AI e del Regolamento Europeo sull'Intelligenza Artificiale (AI Act).

Devi valutare la rilevanza di ogni colonna di un dataset rispetto al caso d'uso descritto dall'utente.

CASO D'USO: {descrizione}
SETTORE AI ACT (Allegato III): {settore}

COLONNE DEL DATASET:
{colonne_testo}

Per ogni colonna assegna:
- uno score da 0 a 100 che indica quanto è rilevante per il caso d'uso (0 = completamente irrilevante, 100 = fondamentale)
- una breve spiegazione del perché

Rispondi SOLO in questo formato JSON, senza testo aggiuntivo:
{{
  "valutazioni": [
    {{
      "colonna": "nome_colonna",
      "score": 85,
      "spiegazione": "Spiegazione breve del perché è rilevante o no"
    }}
  ],
  "commento_generale": "Valutazione complessiva della rilevanza del dataset per il caso d'uso"
}}"""

    try:
        client = get_client()
        response = client.chat.completions.create(
            model="mistralai/mistral-large-2512",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.1
        )

        testo = response.choices[0].message.content.strip()
        testo = testo.replace("```json", "").replace("```", "").strip()
        risultato_llm = json.loads(testo)

        # Costruisci dettaglio per ogni colonna
        dettaglio = []
        scores = []

        for val in risultato_llm.get("valutazioni", []):
            score = val.get("score", 0)
            scores.append(score)

            if score >= 60:
                rilevanza = "ALTA"
                gravita = "BASSA"
            elif score >= 30:
                rilevanza = "MEDIA"
                gravita = "MEDIA"
            else:
                rilevanza = "BASSA"
                gravita = "ALTA"

            dettaglio.append({
                "Colonna": val.get("colonna", ""),
                "Descrizione": colonne_info.get(val.get("colonna", ""), ""),
                "Score rilevanza": f"{score}/100",
                "Rilevanza": rilevanza,
                "Spiegazione LLM": val.get("spiegazione", ""),
                "Gravità": gravita
            })

        # Ordina per score decrescente
        dettaglio = sorted(dettaglio, key=lambda x: int(x["Score rilevanza"].split("/")[0]), reverse=True)

        score_medio = round(sum(scores) / len(scores), 1) if scores else 0
        n_irrilevanti = sum(1 for s in scores if s < 30)
        pct_irrilevanti = round(n_irrilevanti / len(scores) * 100, 1) if scores else 0

        commento = risultato_llm.get("commento_generale", "")

        # Stato finale
        if pct_irrilevanti > 50:
            stato = "NON CONFORME"
        elif pct_irrilevanti > 25 or score_medio < 50:
            stato = "ATTENZIONE"
        else:
            stato = "CONFORME"

        return {
            "stato": stato,
            "score_medio": score_medio,
            "pct_irrilevanti": pct_irrilevanti,
            "commento": commento,
            "dettaglio": dettaglio,
            "messaggio": None
        }

    except Exception as e:
        return {
            "stato": "ATTENZIONE",
            "score_medio": 0,
            "pct_irrilevanti": 0,
            "commento": "",
            "dettaglio": [],
            "messaggio": f"Errore durante l'analisi LLM della rilevanza: {str(e)}"
        }
