import streamlit as st
import os
import Solo

def show_page():
    st.title("🎶 Melodata 🎶")
    fichiers = os.listdir("./data")
    fichiers = [f for f in fichiers if os.path.isfile(os.path.join("./data", f))]
    utilisateurs = [f.replace(".csv", "") for f in fichiers]

    if "utilisateur_selectionne" not in st.session_state:
        st.session_state.utilisateur_selectionne = None

    # Champ de recherche
    recherche = st.text_input("Tapez le nom d'un utilisateur :", key="recherche")

    # Suggestions
    if recherche:
        suggestions = [u for u in utilisateurs if recherche.lower() in u.lower()]
        if suggestions:
            st.write("**Suggestions :**")
            cols = st.columns(len(suggestions))
            for i, suggestion in enumerate(suggestions):
                with cols[i]:
                    if st.button(suggestion, use_container_width=True, key=f"btn_{i}"):
                        st.session_state.utilisateur_selectionne = suggestion
                        ### ne fonctionne pas
                        #st.switch_page("Solo.py")


    # Affichage du choix
    if st.session_state.utilisateur_selectionne:
        st.success(f"Bienvenue sur Melodata **{st.session_state.utilisateur_selectionne}** !")
