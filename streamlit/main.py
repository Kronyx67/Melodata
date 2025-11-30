import streamlit as st
from streamlit_navigation_bar import st_navbar
import os
import pandas as pd
import Accueil
import Solo
import Duo
from functions.cache_utils import load_csv_folder 

st.set_page_config(page_title="Mon App Multi-Pages", layout="wide")

# Initialisation dans session_state (une seule fois par session)
if "data" not in st.session_state:
    st.session_state.data = load_csv_folder("data")

pages = st_navbar(["Accueil", "Solo", "Duo"])

# Affichage de la page sélectionnée
if pages == "Accueil":
    Accueil.show_page()
elif pages == "Solo":
    if  st.session_state.utilisateur_selectionne is None:
        st.warning("Veuillez d'abord sélectionner un utilisateur sur la page Accueil.")
        st.stop()  
    else:
        Solo.show_page()
elif pages == "Duo":
    if  st.session_state.utilisateur_selectionne is None:
        st.warning("Veuillez d'abord sélectionner un utilisateur sur la page Accueil.")
        st.stop() 
    else:   
        Duo.show_page()