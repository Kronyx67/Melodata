import streamlit as st
from streamlit_navigation_bar import st_navbar
import os
import pandas as pd
import Home
import Solo
import Duo
from functions.cache_utils import load_csv_folder_with_cache

st.set_page_config(page_title="Mon App Multi-Pages", layout="wide",
    initial_sidebar_state="collapsed")

# Initialisation dans session_state (une seule fois par session)
if "data" not in st.session_state:
    st.session_state.data = load_csv_folder_with_cache("data")

pages = st_navbar(["Home", "Solo", "Duo"])

# Affichage de la page sélectionnée
if pages == "Home":
    Home.show_page()
elif pages == "Solo":
    if  st.session_state.utilisateur_selectionne is None:
        st.warning("Please first select a user on the Home page.")
        st.stop()  
    else:
        Solo.show_page()
elif pages == "Duo":
    if  st.session_state.utilisateur_selectionne is None:
        st.warning("Please first select a user on the Home page.")
        st.stop() 
    else:   
        Duo.show_page()