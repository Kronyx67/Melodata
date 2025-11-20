import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os


def show_page():
    #st.dataframe(st.session_state.data["Justin.csv"])

    # --- Configuration de la page ---
    st.set_page_config(page_title="Heatmap des écoutes", layout="wide")

    st.title("🎧 Activité d’écoute par semaine et jour de la semaine")

    # --- Sélecteur de fichier parmi ceux chargés en session ---
    fichier_selectionne = st.selectbox(
        "Choisissez un fichier à analyser",
        list(st.session_state.data.keys())
    )

    # Récupération du DataFrame choisi
    df = st.session_state.data[fichier_selectionne]
    
    tab1, tab2, tab3 = st.tabs(["Heatmap", "Histogramme", "Courbe"])
    
    with tab1:
        
        # --- Convertir la colonne de temps ---
        df["utc_time"] = pd.to_datetime(df["utc_time"], format="%d %b %Y, %H:%M")

        # --- Colonnes utiles ---
        df["date"] = df["utc_time"].dt.date
        df["year"] = df["utc_time"].dt.year
        df["hour"] = df["utc_time"].dt.hour
        df["weekday"] = df["utc_time"].dt.day_name()
        df["week"] = df["utc_time"].dt.isocalendar().week

        # --- Sélecteur d'année dynamique ---
        annees_disponibles = sorted(df["year"].unique())
        year_selected = st.selectbox("Année à analyser", annees_disponibles)

        # Filtrer
        df_year = df[df["year"] == year_selected]

        jours_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        # --- Regrouper par semaine et jour ---
        heatmap_data = df_year.groupby(['week', 'weekday']).size().reset_index(name='plays')

        # Pivot pour créer la matrice
        matrix = (
            heatmap_data
            .pivot(index='weekday', columns='week', values='plays')
            .reindex(jours_order)
        )

        # Remplacer les 0 par NaN
        matrix = matrix.replace(0, np.nan)

        # --- Étiquettes axes ---
        semaines = [f"W{w}" for w in matrix.columns]
        jours = matrix.index.tolist()

        # --- Création de la heatmap ---
        fig = px.imshow(
            matrix.values,
            x=semaines,
            y=jours,
            text_auto=True,
            color_continuous_scale='Turbo'
        )

        # --- Options de style ---
        fig.update_traces(
            hovertemplate="%{y}, %{x}: %{z}<extra></extra>",
            zmin=0
        )

        fig.update_layout(
            title=f"Weekly activity per week - Year {year_selected}",
            xaxis_title="Week of the year",
            yaxis_title="Day of the week",
            plot_bgcolor='white',
            paper_bgcolor='white'
        )

        st.plotly_chart(fig, use_container_width=True)
    
