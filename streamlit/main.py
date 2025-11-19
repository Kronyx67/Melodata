import streamlit as st
from streamlit_navigation_bar import st_navbar
import os
import pandas as pd

import Accueil
import Solo
import Duo

st.set_page_config(page_title="Mon App Multi-Pages", layout="wide")

# --- 1. Chargement optimisé des CSV une seule fois ---
@st.cache_data
def load_csv_folder(folder):
    dfs = {}
    for file in os.listdir(folder):
        if file.endswith(".csv"):
            dfs[file] = pd.read_csv(os.path.join(folder, file))
    return dfs

# Initialisation dans session_state (une seule fois par session)
if "data" not in st.session_state:
    st.session_state.data = load_csv_folder("data")

pages = st_navbar(["Accueil", "Solo", "Duo"])




# Affichage de la page sélectionnée
if pages == "Accueil":
    Accueil.show_page()
elif pages == "Solo":
    Solo.show_page()
elif pages == "Duo":
    Duo.show_page()