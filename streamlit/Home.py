import streamlit as st
import os
import Solo
import pandas as pd
from functions.Data import update_data_spin


def show_page():
    st.title("🎶 Melodata 🎶")
    fichiers = os.listdir("./data")
    fichiers = [
        f for f in os.listdir("./data")
        if f.endswith(".csv") and os.path.isfile(os.path.join("./data", f))
    ]
    utilisateurs = [f.replace(".csv", "") for f in fichiers]

    if "utilisateur_selectionne" not in st.session_state:
        st.session_state.utilisateur_selectionne = None

    # Champ de recherche
    recherche = st.text_input("Type a username:", key="recherche")

    # Suggestions
    if recherche:
        suggestions = [u for u in utilisateurs if recherche.lower() in u.lower()] + [recherche]
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
        user = st.session_state.utilisateur_selectionne
        user_path = os.path.join("data", f"{user}.csv")
        if not os.path.exists(user_path):
            update_data_spin(user)
        
        # 1. Chargement rapide des données pour la preview
        try:
            # On charge le CSV
            df = st.session_state.data[f"{user}.csv"]
            
            # Si tu stockes déjà tout dans st.session_state.data dans le main, 
            # tu peux utiliser ça à la place de pd.read_csv pour aller plus vite.
            # Exemple : df = st.session_state.data[f"{user}.csv"]

            # Nettoyage minimal pour les stats
            df["utc_time"] = pd.to_datetime(df["utc_time"], format="%d %b %Y, %H:%M", errors='coerce')
            
            # 2. Calcul des KPIs (Indicateurs Clés)
            total_plays = len(df)
            top_artist = df['artist'].mode()[0] if not df.empty else "Inconnu"
            total_artists = df['artist'].nunique()
            first_listen = df['utc_time'].min().strftime('%d %b %Y') if not df.empty else "-"
            last_listen = df['utc_time'].max().strftime('%d %b %Y') if not df.empty else "-"
            
            # Calcul jours actifs (optionnel)
            active_days = df['utc_time'].dt.date.nunique()

            # 3. Affichage "Carte d'identité"
            st.markdown(f"## 👋 Hi, **{user}** !")
            
            # Bloc de statistiques visuelles
            with st.container(border=True):
                # On met un fond légèrement coloré ou une mise en page aérée
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Meloz", f"{total_plays:,}".replace(",", " "))
                    st.metric("Favorite Artist", top_artist)
                
                with col2:
                    st.metric("Number of different artists", total_artists)
                    st.metric("Active Days", active_days)

                with col3:
                    st.metric("First Meloz", first_listen)
                    st.metric("Last Meloz", last_listen)

            st.button("Update your Data", key="go_solo", on_click=lambda: update_data_spin(st.session_state.utilisateur_selectionne))
              
        except Exception as e:
            st.error(f"{user} doesn't exist on Last.fm")
