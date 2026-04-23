import streamlit as st

st.set_page_config(
    page_title="AI Readiness Framework",
    page_icon="🤖",
    layout="wide"
)

# ── Inizializza lo stato della sessione ──────────────────────────────────────
if "pagina" not in st.session_state:
    st.session_state.pagina = "home"
if "dataset" not in st.session_state:
    st.session_state.dataset = None
if "settore" not in st.session_state:
    st.session_state.settore = None
if "descrizione" not in st.session_state:
    st.session_state.descrizione = None
if "governance" not in st.session_state:
    st.session_state.governance = {}
if "target" not in st.session_state:
    st.session_state.target = None
if "attributi_sensibili" not in st.session_state:
    st.session_state.attributi_sensibili = []

# ── Importa le pagine ────────────────────────────────────────────────────────
from home import mostra_home
from governance import mostra_governance
from risultati import mostra_risultati

# ── Barra di progresso in cima ───────────────────────────────────────────────
pagine = ["home", "governance", "risultati"]
nomi = ["1. Informazioni", "2. Governance", "3. Risultati"]
idx = pagine.index(st.session_state.pagina)

col1, col2, col3 = st.columns(3)
for i, (col, nome) in enumerate(zip([col1, col2, col3], nomi)):
    with col:
        if i < idx:
            st.markdown(f"✅ **{nome}**")
        elif i == idx:
            st.markdown(f"🔵 **{nome}**")
        else:
            st.markdown(f"⚪ {nome}")

st.divider()

# ── Routing ──────────────────────────────────────────────────────────────────
if st.session_state.pagina == "home":
    mostra_home()
elif st.session_state.pagina == "governance":
    mostra_governance()
elif st.session_state.pagina == "risultati":
    mostra_risultati()
