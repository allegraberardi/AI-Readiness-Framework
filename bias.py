import pandas as pd
import streamlit as st

# ── Keyword per identificare automaticamente attributi sensibili ──────────────
KEYWORD_SENSIBILI = [
    "gender", "genere", "sex", "sesso",
    "age", "età", "eta", "age_group",
    "race", "razza", "ethnicity", "etnia",
    "nationality", "nazionalità", "country", "paese",
    "religion", "religione",
    "disability", "disabilità",
    "income", "reddito", "salary", "stipendio",
    "marital", "stato_civile",
    "education", "istruzione"
]

def trova_attributi_sensibili(df):
    """Cerca colonne con nomi simili a keyword sensibili."""
    trovati = []
    for col in df.columns:
        col_lower = col.lower().replace(" ", "_")
        for keyword in KEYWORD_SENSIBILI:
            if keyword in col_lower:
                trovati.append(col)
                break
    return trovati


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
            "SPD": f"{spd} (soglia: |SPD| < 0.1)",
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
