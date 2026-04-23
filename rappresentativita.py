import pandas as pd

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
        "motivo": "I sistemi di valutazione scolastica possono riflettere disuguaglianze geografiche e di genere nell'accesso all'istruzione."
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
        "motivo": "I sistemi di valutazione delle domande di asilo e visto devono essere rappresentativi di tutte le nazionalità e provenienze."
    },
    "Biometria": {
        "keywords": ["race", "razza", "ethnicity", "etnia", "gender", "genere",
                     "age", "età", "eta", "skin", "pelle"],
        "focus": "etnia, genere ed età",
        "motivo": "I sistemi biometrici mostrano performance inferiori su persone di colore e donne — richiedono dataset rappresentativi di tutti i gruppi."
    },
    "Infrastrutture critiche": {
        "keywords": ["region", "regione", "area", "zone", "zona", "location", "posizione"],
        "focus": "distribuzione geografica",
        "motivo": "I sistemi per infrastrutture critiche devono coprire tutte le aree geografiche senza privilegiarne alcune."
    }
}


def analizza_rappresentativita_generale(df):
    """Analisi generale della distribuzione delle variabili categoriche."""
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

    return {"stato": stato, "dettaglio": dettaglio}


def analizza_rappresentativita_contestuale(df, settore):
    """
    Analisi contestuale basata sul settore selezionato.
    Identifica le colonne demograficamente rilevanti per quel settore
    e analizza la loro distribuzione con maggiore attenzione.
    """
    if settore not in VARIABILI_PER_SETTORE:
        return None

    config = VARIABILI_PER_SETTORE[settore]
    keywords = config["keywords"]

    # Trova colonne rilevanti per il settore
    colonne_rilevanti = []
    for col in df.columns:
        col_lower = col.lower().replace(" ", "_")
        for kw in keywords:
            if kw in col_lower:
                colonne_rilevanti.append(col)
                break

    if not colonne_rilevanti:
        return {
            "trovate": False,
            "focus": config["focus"],
            "motivo": config["motivo"],
            "dettaglio": []
        }

    dettaglio = []
    for col in colonne_rilevanti:
        conteggi = df[col].value_counts()
        tot = len(df)

        for classe, count in conteggi.items():
            pct = round(count / tot * 100, 1)
            if pct < 10:
                gravita = "ALTA"
            elif pct < 20:
                gravita = "MEDIA"
            else:
                gravita = "BASSA"

            if gravita != "BASSA":
                dettaglio.append({
                    "Colonna": col,
                    "Gruppo": str(classe),
                    "Esempi": count,
                    "%": f"{pct}%",
                    "Gravità": gravita
                })

    return {
        "trovate": len(colonne_rilevanti) > 0,
        "colonne_trovate": colonne_rilevanti,
        "focus": config["focus"],
        "motivo": config["motivo"],
        "dettaglio": dettaglio
    }


def analizza_rappresentativita(df, settore=None):
    """
    Analisi completa della rappresentatività:
    - Analisi generale su tutte le colonne categoriche
    - Analisi contestuale basata sul settore (se disponibile)
    """
    res_generale = analizza_rappresentativita_generale(df)
    res_contestuale = None

    if settore and settore != "Seleziona...":
        res_contestuale = analizza_rappresentativita_contestuale(df, settore)

    # Stato finale — considera entrambe le analisi
    stato_generale = res_generale["stato"]

    if res_contestuale and res_contestuale.get("dettaglio"):
        if any(d["Gravità"] == "ALTA" for d in res_contestuale["dettaglio"]):
            stato_finale = "NON CONFORME"
        elif any(d["Gravità"] == "MEDIA" for d in res_contestuale["dettaglio"]):
            stato_finale = "ATTENZIONE" if stato_generale == "CONFORME" else stato_generale
        else:
            stato_finale = stato_generale
    else:
        stato_finale = stato_generale

    return {
        "stato": stato_finale,
        "dettaglio": res_generale["dettaglio"],
        "contestuale": res_contestuale
    }
