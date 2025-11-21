import streamlit as st
import os
import plotly.graph_objects as go
import pandas as pd

def show_page():
    st.title("Duo Page")

    fichiers = os.listdir("./data")
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
        tab1, tab2, tab3, tab4 = st.tabs(["Activity", "Artists", "Albums", "Tracks"])

        with tab1:
                df1 = pd.read_csv(f"./data/{st.session_state.utilisateur_selectionne}.csv")
                df2 = pd.read_csv(f"./data/{st.session_state.user_duo}.csv")
                time_min = max(df1["uts"].min(), df2["uts"].min())
                df1["user"] = st.session_state.utilisateur_selectionne
                df2["user"] = st.session_state.user_duo   

                df = pd.concat([df1, df2], ignore_index=True)
                df= df[df["uts"] > time_min]
                
                # --- Convertir la colonne de temps ---
                df["utc_time"] = pd.to_datetime(df["utc_time"], format="%d %b %Y, %H:%M")

                # --- Colonnes utiles ---
                df["date"] = df["utc_time"].dt.date
                df["year"] = df["utc_time"].dt.year
                df["hour"] = df["utc_time"].dt.hour
                df["weekday"] = df["utc_time"].dt.day_name()
                df["week"] = df["utc_time"].dt.isocalendar().week
            
                # --- Sélecteur d'année ---
                annees_disponibles = sorted(df["year"].unique())
                year_selected = st.selectbox("Année à analyser", annees_disponibles)

                # Filtrer l'année sélectionnée
                df_year = df[df["year"] == year_selected]

                jours_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

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

                # 3. Calcul de qui a le plus écouté
                pivot["compare"] = (
                    pivot[st.session_state.utilisateur_selectionne] -
                    pivot[st.session_state.user_duo]
                )

                # -1 : Gautier gagne / 0 : égalité / +1 : Justin gagne
                pivot["compare_flag"] = pivot["compare"].apply(lambda x:
                    1 if x > 0 else (-1 if x < 0 else 0)
                )

                # 4. Matrice pour la heatmap
                matrix_compare = pivot.pivot(
                    index="weekday",
                    columns="week",
                    values="compare_flag"
                ).reindex(jours_order)

                # 5. Remap des valeurs en [0,1] pour Plotly
                matrix_plot = (matrix_compare + 1) / 2

                # --- Labels axes ---
                semaines = [f"W{w}" for w in matrix_compare.columns]
                jours = matrix_compare.index.tolist()

                fig = go.Figure(go.Heatmap(
                    z=matrix_plot,
                    x=semaines,
                    y=jours,
                    colorscale=[[0, "#8796F5"], [0.5, "grey"], [1, "#76F4BD"]],
                    showscale=False  
                ))

                fig.update_traces(
                    hovertemplate="%{y}, %{x}<extra></extra>"
                )

                fig.update_layout(
                    title=f"Comparaison entre 🟢{st.session_state.utilisateur_selectionne} et 🔵{st.session_state.user_duo} — Année {year_selected}",
                    xaxis_title="Semaine",
                    yaxis_title="Jour de la semaine",
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    margin=dict(t=120)
                )

                st.title("Duo Activity Comparison")
                st.plotly_chart(fig)
                        

