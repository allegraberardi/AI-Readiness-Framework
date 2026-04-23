from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import streamlit as st

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


def get_client():
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )


def identifica_attributi_sensibili(descrizione, settore, colonne):
    """
    Usa un LLM per identificare automaticamente target e attributi sensibili
    a partire dalla descrizione del caso d'uso.
    """
    client = get_client()

    prompt = f"""Sei un esperto di AI fairness e del Regolamento Europeo sull'Intelligenza Artificiale (AI Act).

Ti viene fornito:
1. Una descrizione del caso d'uso di un sistema AI ad alto rischio
2. Il settore di applicazione (Allegato III dell'AI Act)
3. La lista delle colonne presenti nel dataset

Il tuo compito è identificare:
- La colonna TARGET: quella che il modello AI dovrà predire (es. approvato/rifiutato, assunto/non assunto)
- Gli ATTRIBUTI SENSIBILI: colonne che rappresentano caratteristiche demografiche protette come genere, età, etnia, nazionalità, religione, disabilità, o variabili che potrebbero essere proxy di queste caratteristiche

CASO D'USO: {descrizione}
SETTORE: {settore}
COLONNE DEL DATASET: {', '.join(colonne)}

Rispondi SOLO in questo formato JSON, senza testo aggiuntivo:
{{
  "target": "nome_colonna_target",
  "attributi_sensibili": ["colonna1", "colonna2"],
  "spiegazione": "Breve spiegazione delle scelte fatte in riferimento all'Art. 10 dell'AI Act"
}}

Se non riesci a identificare il target o gli attributi sensibili con certezza, metti null per il target e lista vuota per gli attributi sensibili."""

    try:
        response = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.1
        )

        testo = response.choices[0].message.content.strip()
        testo = testo.replace("```json", "").replace("```", "").strip()
        risultato = json.loads(testo)

        # Verifica che le colonne suggerite esistano nel dataset
        if risultato.get("target") not in colonne:
            risultato["target"] = None
        risultato["attributi_sensibili"] = [
            col for col in risultato.get("attributi_sensibili", [])
            if col in colonne
        ]

        return risultato

    except Exception as e:
        return {
            "target": None,
            "attributi_sensibili": [],
            "spiegazione": f"Errore durante l'analisi LLM: {str(e)}"
        }


def mostra_suggerimenti_llm(df, descrizione, settore):
    """
    Mostra i suggerimenti dell'LLM e permette all'utente di confermarli o modificarli.
    """
    st.subheader("🤖 Analisi automatica con LLM")

    with st.spinner("L'LLM sta analizzando il caso d'uso..."):
        suggerimenti = identifica_attributi_sensibili(
            descrizione, settore, list(df.columns)
        )

    if suggerimenti.get("spiegazione"):
        st.info(f"**Analisi LLM:** {suggerimenti['spiegazione']}")

    colonne = ["Nessuna — salta questa dimensione"] + list(df.columns)
    target_suggerito = suggerimenti.get("target")
    target_default = target_suggerito if target_suggerito in df.columns else "Nessuna — salta questa dimensione"

    target = st.selectbox(
        "Colonna target — suggerita dall'LLM (puoi modificarla)",
        colonne,
        index=colonne.index(target_default) if target_default in colonne else 0,
        key="bias_target"
    )

    if target != "Nessuna — salta questa dimensione":
        attributi_suggeriti = suggerimenti.get("attributi_sensibili", [])
        attributi_validi = [col for col in attributi_suggeriti if col in df.columns and col != target]

        attributi = st.multiselect(
            "Attributi sensibili — suggeriti dall'LLM (puoi modificarli)",
            [col for col in df.columns if col != target],
            default=attributi_validi,
            key="bias_attributi"
        )
    else:
        attributi = []

    return (
        target if target != "Nessuna — salta questa dimensione" else None,
        attributi
    )