import streamlit as st
import os
import plotly.graph_objects as go
import pandas as pd
from functions.Duo import get_top_artists, get_cumulative_unique_artists_plot, get_top_artists_treemap
from functions.Duo import get_top_albums
from functions.Duo import get_top_tracks, get_total_and_unique_tracks_plot
import numpy as np

def show_page():
    st.title("Duo Page")

    fichiers = [
        f for f in os.listdir("./data")
        if f.endswith(".csv") and os.path.isfile(os.path.join("./data", f))
    ]
    fichiers = [f for f in fichiers if os.path.isfile(os.path.join("./data", f))]
    users = [f.replace(".csv", "") for f in fichiers]
    users.remove(st.session_state.utilisateur_selectionne)

    # Champ de recherche
    recherche = st.text_input("Choisissez un utilisateur à comparer :", value="")

    if not recherche:
        st.session_state.suggestions = users
    else :
        st.session_state.suggestions = [u for u in users if recherche.lower() in u.lower()]
    if st.session_state.suggestions:
        st.write("**Suggestions :**")
        cols = st.columns(len(st.session_state.suggestions))
        for i, suggestion in enumerate(st.session_state.suggestions):
            with cols[i]:
                if st.button(suggestion, use_container_width=True, key=f"btn_{i}"):
                    st.session_state.user_duo = suggestion
                    st.session_state.suggestions = []

    if "user_duo" in st.session_state:
        df1 = pd.read_csv(f"./data/{st.session_state.utilisateur_selectionne}.csv")
        df2 = pd.read_csv(f"./data/{st.session_state.user_duo}.csv")
        time_min = max(df1["uts"].min(), df2["uts"].min())
        df1["user"] = st.session_state.utilisateur_selectionne
        df2["user"] = st.session_state.user_duo   

        df = pd.concat([df1, df2], ignore_index=True)
        df= df[df["uts"] > time_min]

        tab1, tab2, tab3, tab4 = st.tabs(["Activity", "Artists", "Albums", "Tracks"])

        with tab1:
            st.header("Weekly Duo Comparison")
            
            # --- Convertir la colonne de temps ---
            df["utc_time"] = pd.to_datetime(df["utc_time"], format="%d %b %Y, %H:%M")

            # --- Colonnes utiles ---
            df["year"] = df["utc_time"].dt.year
            df["weekday"] = df["utc_time"].dt.day_name()
            df["week"] = df["utc_time"].dt.isocalendar().week
        
            # --- Sélecteur d'année ---
            annees_disponibles = sorted(df["year"].unique())
            year_selected = st.selectbox("Select Year", annees_disponibles)

            # Filtrer l'année sélectionnée
            df_year = df[df["year"] == year_selected]

            jours_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            
            # Variables pour les noms (plus court à écrire)
            u1 = st.session_state.utilisateur_selectionne
            u2 = st.session_state.user_duo

            # 1. Regrouper par semaine / jour / utilisateur
            comp = (
                df_year.groupby(["week", "weekday", "user"])
                    .size()
                    .reset_index(name="plays")
            )

            # 2. Pivot table → weekday × week × user
            pivot = comp.pivot_table(
                index=["weekday", "week"],
                columns="user",
                values="plays",
                fill_value=0
            ).reset_index()

            # --- SÉCURITÉ : Si un user n'a rien écouté, sa colonne manque ---
            if u1 not in pivot.columns: pivot[u1] = 0
            if u2 not in pivot.columns: pivot[u2] = 0

            # 3. NOUVELLE LOGIQUE (Pour avoir les blancs)
            def calculate_score(row):
                val1 = row[u1]
                val2 = row[u2]
                
                # Si personne n'a écouté : NaN (Blanc)
                if val1 == 0 and val2 == 0:
                    return np.nan
                # Si User 1 > User 2 : 1 (Vert)
                elif val1 > val2:
                    return 1
                # Si User 2 > User 1 : 0 (Bleu)
                elif val2 > val1:
                    return 0
                # Égalité active : 0.5 (Gris)
                else:
                    return 0.5

            pivot["score"] = pivot.apply(calculate_score, axis=1)

            # 4. Matrice pour la heatmap
            matrix_compare = pivot.pivot(
                index="weekday",
                columns="week",
                values="score"
            ).reindex(jours_order)

            # --- LÉGENDE PERSONNALISÉE ---
            st.markdown(f"""
            <div style="display: flex; gap: 20px; margin-bottom: 15px; font-family: sans-serif; font-size: 14px;">
                <div style="display: flex; align-items: center;">
                    <div style="width: 15px; height: 15px; background-color: #76F4BD; margin-right: 5px; border-radius: 3px;"></div>
                    <span><b>{u1}</b></span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 15px; height: 15px; background-color: #8796F5; margin-right: 5px; border-radius: 3px;"></div>
                    <span><b>{u2}</b></span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 15px; height: 15px; background-color: grey; margin-right: 5px; border-radius: 3px;"></div>
                    <span>Tie</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 15px; height: 15px; background-color: white; border: 1px solid #ddd; margin-right: 5px; border-radius: 3px;"></div>
                    <span>No data</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # --- Labels axes ---
            semaines = [f"W{w}" for w in matrix_compare.columns]
            jours = matrix_compare.index.tolist()

            fig = go.Figure(go.Heatmap(
                z=matrix_compare,
                x=semaines,
                y=jours,
                # 0=Bleu, 0.5=Gris, 1=Vert. Les NaN seront transparents (blancs)
                colorscale=[
                    [0.0, "#8796F5"], 
                    [0.49, "#8796F5"],
                    [0.5, "grey"], 
                    [0.51, "grey"],
                    [1.0, "#76F4BD"]
                ],
                showscale=False,
                xgap=1, # Espace entre les cases
                ygap=1
            ))

            fig.update_traces(
                hovertemplate="Week: %{x}<br>Day: %{y}<extra></extra>"
            )

            fig.update_layout(
                title=f"Activity Map — {year_selected}",
                xaxis_title=None, # Plus propre sans titre "Semaine"
                yaxis_title=None,
                plot_bgcolor='white',
                paper_bgcolor='white',
                margin=dict(t=40, l=40, b=40, r=20),
                # AXE Y : Lundi en haut
                yaxis=dict(
                    autorange="reversed",
                    showgrid=False,
                    zeroline=False
                ),
                # AXE X : Semaines en bas
                xaxis=dict(
                    side="bottom",
                    showgrid=False,
                    zeroline=False
                )
            )

            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            col1, col2 = st.columns(2)
            with col1:
                st.write("""
                Ce tableau affiche les 5 artistes les plus écoutés en commun,
                avec la condition qu'un seul utilisateur ne représente pas plus de 80% des écoutes d'un artiste.
                """)

                top_artists = get_top_artists(df)
                st.subheader("Top 5 des artistes")
                st.dataframe(top_artists)

            with col2:
                # Génération et affichage du graphique
                fig = get_cumulative_unique_artists_plot(df)
                st.plotly_chart(fig, use_container_width=True)


            # 2. Treemap du top 10 des artistes
            fig2 = get_top_artists_treemap(df)
            st.plotly_chart(fig2, use_container_width=True)

        with tab3:
            top_albums = get_top_albums(df)
            st.subheader("Top 5 des albums les plus écoutés en commun")
            st.dataframe(top_albums)

        with tab4:
            col1, col2 = st.columns(2)

            with col1:
                top_tracks = get_top_tracks(df)
                st.subheader("Top 5 des titres les plus écoutés en commun")
                st.dataframe(top_tracks)

            with col2:
                fig = get_total_and_unique_tracks_plot(df)
                st.plotly_chart(fig, use_container_width=True)