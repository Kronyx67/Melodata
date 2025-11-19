import streamlit as st

def show_page():
    st.title("Bienvenue sur l'Accueil 🏠")
    st.write("Ceci est le contenu de la page d'accueil.")
    
    st.write("Commande pour charger les data :")
    st.code("st.session_state.data['Justin.csv']")
    st.write("Fichiers chargés :", list(st.session_state.data.keys()))
