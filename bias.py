import pandas as pd
import streamlit as st

# ── Keyword per identificare automaticamente attributi sensibili ──────────────
# Basate sulle categorie speciali dell'Art. 9 GDPR e attributi protetti AI Act
KEYWORD_SENSIBILI = {
    # Genere e sesso
    "genere_sesso": ["gender", "genere", "sex", "sesso"],

    # Età
    "eta": ["age", "età", "eta", "age_group", "birth", "nascita", "dob", "born"],

    # Origine razziale ed etnica (Art. 9 GDPR)
    "etnia": ["race", "razza", "ethnicity", "etnia", "ethnic", "origin", "origine"],

    # Nazionalità e provenienza
    "nazionalita": ["nationality", "nazionalità", "country", "paese", "nation", "nazione"],

    # Credenze religiose e filosofiche (Art. 9 GDPR)
    "religione": ["religion", "religione", "faith", "credo", "church", "chiesa",
                  "belief", "credenza", "confession", "confessione"],

    # Opinioni politiche (Art. 9 GDPR)
    "politica": ["political", "politico", "party", "partito", "vote", "voto",
                 "ideology", "ideologia", "opinion", "opinione"],

    # Orientamento sessuale e vita sessuale (Art. 9 GDPR)
    "orientamento": ["sexual", "sessuale", "orientation", "orientamento",
                     "lgbt", "gay", "lesbian", "bisexual"],

    # Dati sulla salute (Art. 9 GDPR)
    "salute": ["health", "salute", "medical", "medico", "disease", "malattia",
               "diagnosis", "diagnosi", "illness", "disorder", "condition",
               "patient", "paziente", "hospital", "ospedale", "clinical"],

    # Disabilità (Art. 9 GDPR)
    "disabilita": ["disability", "disabilità", "disabled", "disabile",
                   "handicap", "impairment", "special_needs"],

    # Dati genetici (Art. 9 GDPR)
    "genetica": ["genetic", "genetico", "dna", "gene", "genome", "genoma",
                 "hereditary", "ereditario"],

    # Dati biometrici (Art. 9 GDPR)
    "biometria": ["biometric", "biometrico", "fingerprint", "impronta",
                  "facial", "facciale", "iris", "retina", "voice", "voce"],

    # Appartenenza sindacale (Art. 9 GDPR)
    "sindacato": ["union", "sindacato", "trade_union", "labor", "labour",
                  "sindacale", "membership"],

    # Reddito e situazione economica
    "reddito": ["income", "reddito", "salary", "stipendio", "wage", "earning",
                "wealth", "ricchezza", "poverty", "povertà"],

    # Stato civile e famiglia
    "stato_civile": ["marital", "stato_civile", "married", "sposato",
                     "divorced", "divorziato", "family", "famiglia"],

    # Istruzione
    "istruzione": ["education", "istruzione", "degree", "laurea",
                   "school", "scuola", "qualification"],
}

# Lista piatta per ricerca rapida
KEYWORD_LISTA = [kw for gruppo in KEYWORD_SENSIBILI.values() for kw in gruppo]


def trova_attributi_sensibili(df):
    """Cerca colonne con nomi simili a keyword sensibili GDPR/AI Act."""
    trovati = []
    for col in df.columns:
        col_lower = col.lower().replace(" ", "_")
        for keyword in KEYWORD_LISTA:
            if keyword in col_lower:
                trovati.append(col)
                break
    return trovati


def categoria_gdpr(col):
    """Restituisce la categoria GDPR di una colonna se è sensibile."""
    col_lower = col.lower().replace(" ", "_")
    for categoria, keywords in KEYWORD_SENSIBILI.items():
        for kw in keywords:
            if kw in col_lower:
                return categoria
    return None



def calcola_bias(df, target, attributi_sensibili):
    """
    Calcola Statistical Parity Difference, Disparate Impact e Class Imbalance
    per ogni attributo sensibile rispetto alla colonna target.
    Allineato al metodo di AIF360.
    """
    risultati_dettaglio = []
    stati = []

    # Verifica che il target sia binario
    valori_target = df[target].dropna().unique()
    if len(valori_target) != 2:
        return {
            "stato": "ATTENZIONE",
            "messaggio": f"La colonna target '{target}' non è binaria ({len(valori_target)} valori unici). Le metriche di fairness richiedono un target binario.",
            "dettaglio": []
        }

    # Valore positivo = 1 se presente, altrimenti il valore massimo
    valore_positivo = 1 if 1 in valori_target else max(valori_target)

    for attr in attributi_sensibili:
        gruppi = df[attr].dropna().unique()

        if len(gruppi) < 2:
            continue

        # ── Class Imbalance ──────────────────────────────────────────────────
        conteggi = df[attr].value_counts()
        gruppo_min = conteggi.idxmin()
        gruppo_max = conteggi.idxmax()
        pct_min = round(conteggi.min() / len(df) * 100, 1)
        pct_max = round(conteggi.max() / len(df) * 100, 1)
        imbalance = round(pct_max - pct_min, 1)

        if imbalance > 40:
            ci_gravita = "ALTA"
        elif imbalance > 20:
            ci_gravita = "MEDIA"
        else:
            ci_gravita = "BASSA"

        # ── Proporzione decisioni positive per ogni gruppo ───────────────────
        proporzioni = {}
        for gruppo in gruppi:
            subset = df[df[attr] == gruppo]
            if len(subset) == 0:
                continue
            prop = len(subset[subset[target] == valore_positivo]) / len(subset)
            proporzioni[gruppo] = round(prop, 4)

        if len(proporzioni) < 2:
            continue

        # Gruppo privilegiato = quello con proporzione più alta
        # Gruppo svantaggiato = quello con proporzione più bassa
        gruppo_privilegiato = max(proporzioni, key=proporzioni.get)
        gruppo_svantaggiato = min(proporzioni, key=proporzioni.get)
        prop_privilegiato = proporzioni[gruppo_privilegiato]
        prop_svantaggiato = proporzioni[gruppo_svantaggiato]

        # ── Statistical Parity Difference ────────────────────────────────────
        # Formula: P(positivo | svantaggiato) - P(positivo | privilegiato)
        # Valore ideale = 0, negativo = discriminazione
        spd = round(prop_svantaggiato - prop_privilegiato, 4)
        spd_abs = abs(spd)

        if spd_abs > 0.2:
            spd_gravita = "ALTA"
        elif spd_abs > 0.1:
            spd_gravita = "MEDIA"
        else:
            spd_gravita = "BASSA"

        # ── Disparate Impact ─────────────────────────────────────────────────
        # Formula: P(positivo | svantaggiato) / P(positivo | privilegiato)
        # Valore ideale = 1.0, fair se >= 0.8 e <= 1.25
        if prop_privilegiato > 0:
            di = round(prop_svantaggiato / prop_privilegiato, 4)
        else:
            di = 0

        if di < 0.6 or di > 1.4:
            di_gravita = "ALTA"
        elif di < 0.8 or di > 1.25:
            di_gravita = "MEDIA"
        else:
            di_gravita = "BASSA"

        # ── Gravità complessiva ───────────────────────────────────────────────
        gravita_valori = {"ALTA": 3, "MEDIA": 2, "BASSA": 1}
        gravita_max = max(
            gravita_valori[spd_gravita],
            gravita_valori[di_gravita],
            gravita_valori[ci_gravita]
        )
        gravita_complessiva = {3: "ALTA", 2: "MEDIA", 1: "BASSA"}[gravita_max]

        risultati_dettaglio.append({
            "Attributo": attr,
            "Gruppo privilegiato": f"{gruppo_privilegiato} ({round(prop_privilegiato*100,2)}%)",
            "Gruppo svantaggiato": f"{gruppo_svantaggiato} ({round(prop_svantaggiato*100,2)}%)",
            "Statistical Parity Difference": f"{spd} (soglia: |SPD| < 0.1)",
            "Disparate Impact": f"{di} (soglia: 0.8 ≤ DI ≤ 1.25)",
            "Class Imbalance": f"{imbalance}% di differenza tra gruppi",
            "Gravità": gravita_complessiva
        })

        stati.append(gravita_complessiva)

    # ── Stato finale ─────────────────────────────────────────────────────────
    if not stati:
        return {
            "stato": "ATTENZIONE",
            "messaggio": "Non è stato possibile calcolare le metriche di bias. Verifica che gli attributi selezionati abbiano almeno due valori distinti.",
            "dettaglio": []
        }

    if "ALTA" in stati:
        stato = "NON CONFORME"
    elif "MEDIA" in stati:
        stato = "ATTENZIONE"
    else:
        stato = "CONFORME"

    return {
        "stato": stato,
        "dettaglio": risultati_dettaglio
    }


def commento_llm_bias(risultati_dettaglio, descrizione, settore, target):
    """
    Chiede all'LLM di interpretare i risultati del bias nel contesto del caso d'uso.
    """
    from openai import OpenAI
    from dotenv import load_dotenv
    import os
    import json

    load_dotenv()
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )

    riassunto = []
    for r in risultati_dettaglio:
        riassunto.append(
            f"Attributo: {r['Attributo']} — "
            f"Gruppo privilegiato: {r['Gruppo privilegiato']} — "
            f"Gruppo svantaggiato: {r['Gruppo svantaggiato']} — "
            f"Statistical Parity Difference: {r['Statistical Parity Difference']} — "
            f"Disparate Impact: {r['Disparate Impact']} — "
            f"Class Imbalance: {r['Class Imbalance']} — "
            f"Gravità: {r['Gravità']}"
        )

    prompt = f"""Sei un esperto di AI fairness e del Regolamento Europeo sull'Intelligenza Artificiale (AI Act).

Analizza i risultati del bias per questo dataset e fornisci una valutazione contestualizzata.

CASO D'USO: {descrizione}
SETTORE (Allegato III AI Act): {settore}
VARIABILE TARGET: {target}

RISULTATI ANALISI BIAS:
{chr(10).join(riassunto)}

Fornisci:
1. Una valutazione complessiva del bias nel dataset in relazione al caso d'uso
2. I gruppi più a rischio di discriminazione
3. Una raccomandazione concreta per mitigare il bias in riferimento all'Art. 10(2)(f) e (g) dell'AI Act

Sii conciso (massimo 5 righe) e preciso."""

    try:
        response = client.chat.completions.create(
            model="mistralai/mistral-large-2512",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.2
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Errore durante l'analisi LLM: {str(e)}"
