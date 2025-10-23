import streamlit as st
from streamlit_navigation_bar import st_navbar

import Accueil
import Solo
import Duo

st.set_page_config(page_title="Mon App Multi-Pages", layout="wide")



pages = st_navbar(["Accueil", "Solo", "Duo"])



# Affichage de la page sélectionnée
if pages == "Accueil":
    Accueil.show_page()
elif pages == "Solo":
    Solo.show_page()
elif pages == "Duo":
    Duo.show_page()