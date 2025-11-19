import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os

DATA_FOLDER = "data"

def load_csv_folder(folder):
    dataframes = {}
    for filename in os.listdir(folder):
        if filename.endswith(".csv"):
            path = os.path.join(folder, filename)
            dataframes[filename] = pd.read_csv(path)
    return dataframes

# Chargement unique dans session_state
if "data" not in st.session_state:
    st.session_state.data = load_csv_folder(DATA_FOLDER)




def show_page():
    
    st.write("Fichiers chargés :", list(st.session_state.data.keys()))
    #st.dataframe(st.session_state.data["Justin.csv"])

    # --- Configuration de la page ---
    st.set_page_config(page_title="Heatmap des écoutes", layout="wide")

    st.title("🎧 Activité d’écoute par semaine et jour de la semaine")

    # --- Chargement des données ---
    uploaded_file = st.file_uploader("📂 Importez votre fichier CSV (avec utc_time, artist, track...)", type=["csv"])

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)

        # --- Préparation des données ---
        df["utc_time"] = pd.to_datetime(df["utc_time"], format="%d %b %Y, %H:%M")
        df["year"] = df["utc_time"].dt.year
        df["week"] = df["utc_time"].dt.isocalendar().week
        df["weekday"] = df["utc_time"].dt.day_name()

        # --- Sélecteur d'année ---
        years = sorted(df["year"].unique())
        year_selected = st.selectbox("📅 Choisissez une année :", years, index=len(years)-1)

        df_year = df[df["year"] == year_selected]
        jours_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        # --- Regrouper par semaine et jour ---
        heatmap_data = df_year.groupby(['week', 'weekday']).size().reset_index(name='plays')

        # --- Matrice jours × semaines ---
        matrix = heatmap_data.pivot(index='weekday', columns='week', values='plays').reindex(jours_order)
        matrix = matrix.replace(0, np.nan)

        semaines = [f"W{w}" for w in matrix.columns]
        jours = matrix.index.tolist()

        # --- Choix de la palette de couleurs ---
        palette = st.selectbox(
            "🎨 Choisissez un style de couleurs :",
            ["Viridis", "Magma", "Blues", "Cividis", "IceFire", "Turbo", "Greens"]
        )

        # --- Création de la heatmap Plotly ---
        fig = px.imshow(
            matrix.values,
            x=semaines,
            y=jours,
            color_continuous_scale=palette,
            aspect="auto"
        )

        fig.update_layout(
            title=f"🔥 Activité d’écoute hebdomadaire ({year_selected})",
            xaxis_title="Semaine de l'année",
            yaxis_title="Jour de la semaine",
            plot_bgcolor='white',
            paper_bgcolor='white'
        )

        # --- Affichage dans Streamlit ---
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("⬆️ Importez un fichier CSV pour commencer.")

        
        