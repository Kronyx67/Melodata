import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import bar_chart_race as bcr
import base64

def show_page():
    # --- Configuration de la page ---
    st.set_page_config(page_title="SoloPage", layout="wide")

    st.title("🎧Solo Page")
    
    # Récupération du DataFrame choisi
    df = st.session_state.data[f"{st.session_state.utilisateur_selectionne}.csv"].copy()
    # 1. Conversion indispensable
    df["utc_time"] = pd.to_datetime(df["utc_time"], format="%d %b %Y, %H:%M")
    
    
    # 2. Bornes globales (Min et Max des données)
    min_glob = df["utc_time"].min().date()
    max_glob = df["utc_time"].max().date()
    
    # ====================================================================
    # ÉTAPE 2 : INITIALISER LE STATE (CRÉATION DES VARIABLES)
    # C'est impératif de le faire AVANT de tenter de les lire ou de les corriger
    # ====================================================================
    if 'date_start' not in st.session_state:
        st.session_state.date_start = min_glob
        
    if 'date_end' not in st.session_state:
        st.session_state.date_end = max_glob

    # --- INITIALISATION DU STATE (Mémoire) ---
    # 1. On corrige la date de début si elle est hors limites
    if st.session_state.date_start < min_glob:
        st.session_state.date_start = min_glob
    elif st.session_state.date_start > max_glob:
        st.session_state.date_start = min_glob # Reset au début si incohérent

    # 2. On corrige la date de fin si elle dépasse la date max du fichier
    if st.session_state.date_end > max_glob:
        st.session_state.date_end = max_glob
    elif st.session_state.date_end < min_glob:
        st.session_state.date_end = max_glob

    # 3. Sécurité finale : si Start > End, on réinitialise tout
    if st.session_state.date_start > st.session_state.date_end:
        st.session_state.date_start = min_glob
        st.session_state.date_end = max_glob

    # --- FONCTIONS DE CALLBACK (Ce qui se passe quand on change une option) ---
    
    def update_from_preset():
        """Met à jour les dates selon la période rapide choisie"""
        choix = st.session_state.preset_selector
        if choix == "Tout le temps":
            st.session_state.date_start = min_glob
            st.session_state.date_end = max_glob
        elif "derniers jours" in choix:
            days = int(choix.split()[0]) # Récupère 7, 30 ou 90
            st.session_state.date_end = max_glob
            st.session_state.date_start = max_glob - pd.Timedelta(days=days)
        # On remet l'année sur "Sélectionner" pour éviter la confusion
        st.session_state.year_selector = "Sélectionner"

    def update_from_year():
        """Met à jour les dates selon l'année choisie"""
        annee = st.session_state.year_selector
        if annee != "Sélectionner":
            # Début de l'année (ou min global si données commencent après)
            start = pd.Timestamp(f"{annee}-01-01").date()
            st.session_state.date_start = max(start, min_glob)
            
            # Fin de l'année (ou max global)
            end = pd.Timestamp(f"{annee}-12-31").date()
            st.session_state.date_end = min(end, max_glob)
            
            # On remet le preset sur "Personnalisé"
            st.session_state.preset_selector = "Personnalisé"

    # ====================================================================
    # 📅 ZONE DE FILTRAGE (3 COLONNES)
    # ====================================================================
    with st.container():
        # CSS pour aligner verticalement les widgets (optionnel mais plus joli)
        st.markdown('<style>div.row-widget.stSelectbox {margin-top: -15px;}</style>', unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns([1, 1, 1])

        # --- COL 1 : PÉRIODES RAPIDES ---
        with c1:
            st.selectbox(
                "⚡ Périodes rapides",
                options=["Personnalisé", "Tout le temps", "7 derniers jours", "30 derniers jours", "90 derniers jours", "365 derniers jours"],
                key="preset_selector",
                on_change=update_from_preset # Déclenche la fonction quand on change
            )

        # --- COL 2 : ANNÉE ---
        with c2:
            years_avail = sorted(df["utc_time"].dt.year.unique(), reverse=True)
            st.selectbox(
                "📂 Année",
                options=["Sélectionner"] + years_avail,
                key="year_selector",
                on_change=update_from_year # Déclenche la fonction quand on change
            )

        # --- COL 3 : CALENDRIER (Le maître du jeu) ---
        with c3:
            # Le widget prend ses valeurs par défaut dans le session_state mis à jour par les colonnes 1 et 2
            dates = st.date_input(
                "📅 Sélection des dates",
                value=(st.session_state.date_start, st.session_state.date_end),
                min_value=min_glob,
                max_value=max_glob,
                format="DD/MM/YYYY"
            )

    # ====================================================================
    # APPLICATION DU FILTRE
    # ====================================================================
    
    # Vérification que l'utilisateur a bien sélectionné une date de fin
    if len(dates) == 2:
        start_sel, end_sel = dates
        # Mise à jour du state si l'utilisateur change manuellement le calendrier
        st.session_state.date_start = start_sel
        st.session_state.date_end = end_sel
        
        # Filtre effectif sur le DataFrame
        mask = (df["utc_time"].dt.date >= start_sel) & (df["utc_time"].dt.date <= end_sel)
        
        # Sauvegarde taille avant
        total_rows = len(df)
        df = df.loc[mask].copy()
        
        # Feedback visuel discret
        st.caption(f"✅ **{len(df)}** écoutes affichées (du {start_sel.strftime('%d/%m/%Y')} au {end_sel.strftime('%d/%m/%Y')})")
    else:
        st.warning("Veuillez sélectionner une date de fin dans le calendrier.")
        st.stop() # Arrête l'exécution tant que les dates ne sont pas valides

    st.divider()
    
    # --- Tabs principales ---
    tab1, tab2 , tab3, tab4, tab5= st.tabs(["📊 Heatmap", "🏁 Bar Chart Race","🏆 Artistes","🎵 Meloz", "💿 Albums"])
    
    # ========== TAB 1: HEATMAP ==========
    with tab1:
        st.header("Activité d'écoute par semaine et jour de la semaine")
        
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
        
        # Deuxième fisu heatmap
        
        st.divider()
        st.subheader("☀️ Artistes du Matin vs 🌙 Artistes du Soir")
        
        # --- COMMANDES UTILISATEUR ---
        col_ctrl, col_info = st.columns([1, 2])
        with col_ctrl:
            mode_affichage = st.radio(
                "Mode d'affichage :",
                ["Volume (Écoutes)", "Normalisé (%)"],
                horizontal=True
            )
        with col_info:
            if mode_affichage == "Volume (Écoutes)":
                st.caption("Affiche le nombre réel d'écoutes. Les artistes les plus populaires ressortent davantage.")
            else:
                st.caption("Affiche la concentration horaire. Idéal pour voir les habitudes (ex: artiste du soir) même pour ceux moins écoutés.")

        # --- 1. PRÉPARATION DES DONNÉES (Commune aux deux modes) ---
        # On récupère le Top 20
        top20_artists = df["artist"].value_counts().head(20).index
        df_heat_art = df[df["artist"].isin(top20_artists)].copy()
        
        df_heat_art["hour"] = df_heat_art["utc_time"].dt.hour
        
        # Matrice croisée de base (Volume)
        heat_data = df_heat_art.groupby(["artist", "hour"]).size().reset_index(name="plays")
        matrix_art = heat_data.pivot(index="artist", columns="hour", values="plays").fillna(0)
        
        # On applique l'ordre du Top 20
        matrix_art = matrix_art.reindex(top20_artists)
        
        # Compléter les heures manquantes
        for h in range(24):
            if h not in matrix_art.columns:
                matrix_art[h] = 0
        matrix_art = matrix_art.sort_index(axis=1)

        # --- 2. LOGIQUE D'AFFICHAGE ---
        if mode_affichage == "Normalisé (%)":
            # Calcul du pourcentage par ligne
            matrix_to_plot = matrix_art.div(matrix_art.sum(axis=1), axis=0) * 100
            z_label = "Concentration (%)"
            hover_fmt = ".1f"
            color_scale = "RdBu_r" # Rouge pour les forts pourcentages
        else:
            # Données brutes
            matrix_to_plot = matrix_art
            z_label = "Écoutes"
            hover_fmt = "d" # Entier
            color_scale = "RdBu_r" # Échelle différente pour bien distinguer visuellement

        # --- 3. CRÉATION DU GRAPHIQUE ---
        fig_heat = px.imshow(
            matrix_to_plot,
            labels=dict(x="Heure", y="Artiste", color=z_label),
            color_continuous_scale=color_scale,
            aspect="auto",
            height=600
        )
        
        # Configuration du style
        fig_heat.update_xaxes(side="top", title=None)
        
        # Infobulle dynamique selon le mode
        if mode_affichage == "Normalisé (%)":
            fig_heat.update_traces(
                hovertemplate="<b>%{y}</b><br>Heure: %{x}h<br>Concentration: %{z:.1f}%<extra></extra>"
            )
        else:
             fig_heat.update_traces(
                hovertemplate="<b>%{y}</b><br>Heure: %{x}h<br>Écoutes: %{z}<extra></extra>"
            )

        st.plotly_chart(fig_heat, use_container_width=True)
    
    
    # ========== TAB 3: ARTISTES ==========
    with tab3:
        st.header("🏆 Classements et Analyses")

        # --- Préparation des données ---
        # On s'assure que les dates sont au bon format
        df["utc_time"] = pd.to_datetime(df["utc_time"], format="%d %b %Y, %H:%M", errors="coerce")
        df["month_str"] = df["utc_time"].dt.strftime('%Y-%m') # Format string pour l'affichage
        df["week"] = df["utc_time"].dt.isocalendar().week

        # --- PREMIÈRE LIGNE : LES PODIUMS ---
        st.subheader("🌟 Les Incontournables")
        
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🥇 Top 10 Artistes (Volume)")
            st.caption("Basé sur le nombre total d'écoutes")
            
            # Calcul
            top_artists = df["artist"].value_counts().head(10).reset_index()
            top_artists.columns = ["Artiste", "Écoutes"]
            top_artists.index = top_artists.index + 1 # Commencer le classement à 1
            
            # Affichage tableau
            st.dataframe(top_artists, use_container_width=True)

        with col2:
            st.markdown("### 📅 Top 10 Fidélité")
            st.caption("Artistes écoutés sur le plus grand nombre de semaines distinctes")
            
            # Calcul
            weeks_per_artist = df.groupby("artist")["week"].nunique().sort_values(ascending=False).head(10).reset_index()
            weeks_per_artist.columns = ["Artiste", "Semaines actives"]
            weeks_per_artist.index = weeks_per_artist.index + 1
            
            # Affichage tableau
            st.dataframe(weeks_per_artist, use_container_width=True)

        st.divider()

        # --- DEUXIÈME LIGNE : ÉVOLUTION CUMULÉE ---
        st.subheader("📈 Course aux écoutes (Cumulatif)")
        
        # Sécurité : Si pas de données filtrées, on arrête là
        if df.empty:
            st.warning("⚠️ Aucune donnée disponible sur cette période pour afficher l'évolution.")
        else:
            # 1. Adaptation de la granularité temporelle
            # Si la période est courte (< 30 jours), on regarde par JOUR au lieu de par SEMAINE
            plage_jours = (df["utc_time"].max() - df["utc_time"].min()).days
            
            df_evo = df.copy()
            
            if plage_jours < 30:
                # Mode "Zoom" : Par jour
                df_evo["time_step"] = df_evo["utc_time"].dt.date
                period_label = "Date"
            else:
                # Mode "Large" : Par semaine
                df_evo["time_step"] = df_evo["utc_time"].dt.to_period('W').apply(lambda r: r.start_time)
                period_label = "Semaine"

            # 2. Filtrer sur le Top 10 (Recalculé sur la période filtrée)
            # On prend les artistes affichés dans le tableau juste au-dessus
            top10_list = top_artists["Artiste"].tolist() if "Artiste" in top_artists.columns else []
            df_top10 = df_evo[df_evo["artist"].isin(top10_list)]
            
            if df_top10.empty:
                st.info("Pas assez de données pour le Top 10 sur cette période.")
            else:
                # 3. Compter les écoutes
                counts = df_top10.groupby(["time_step", "artist"]).size().reset_index(name="plays")
                
                # 4. Pivot
                pivot_df = counts.pivot(index="time_step", columns="artist", values="plays").fillna(0)
                
                # 5. Cumul
                cumulative_df = pivot_df.cumsum()
                
                # 6. Format long pour Plotly
                evolution_final = cumulative_df.reset_index().melt(
                    id_vars="time_step", 
                    var_name="artist", 
                    value_name="cumulative_plays"
                )
                
                # 7. Graphique
                fig_evo = px.line(
                    evolution_final,
                    x="time_step",
                    y="cumulative_plays",
                    color="artist",
                    markers=True if plage_jours < 30 else False, # Marqueurs si on a peu de points
                    title=f"Évolution cumulée ({period_label})",
                )
                
                fig_evo.update_layout(
                    hovermode="x unified", 
                    xaxis_title=period_label,
                    yaxis_title="Total Cumulé"
                )
                
                st.plotly_chart(fig_evo, use_container_width=True)

        st.divider()

        # --- TROISIÈME LIGNE : DÉTAILS MENSUELS & TRACKS ---
        
        # 1. ZONE DE TITRES ET CONTRÔLES (Première ligne de colonnes)
        head_col1, head_col2 = st.columns(2)

        with head_col1:
            st.markdown("### 🗓️ Artiste favori par mois")
            # On ne met rien d'autre ici

        with head_col2:
            st.markdown("### 🎵 Top Tracks par Artiste")
            # Liste des artistes
            liste_artistes = sorted(df["artist"].dropna().unique())
            # Le selectbox est ici, au-dessus du futur tableau
            artist_selected = st.selectbox("Choisir un artiste", liste_artistes, label_visibility="collapsed")
            # Note: label_visibility="collapsed" cache le label "Choisir un artiste" pour gagner de la place si le titre suffit

        # 2. ZONE DES DONNÉES (Deuxième ligne de colonnes)
        # Comme c'est une nouvelle rangée de colonnes, elle commencera 
        # sous l'élément le plus bas de la rangée précédente.
        data_col1, data_col2 = st.columns(2)

        with data_col1:
            # --- Calcul pour la gauche ---
            monthly_stats = df.groupby(["month_str", "artist"]).size().reset_index(name="plays")
            
            # Trouver le top 1
            idx = monthly_stats.groupby("month_str")["plays"].idxmax()
            top_month = monthly_stats.loc[idx]
            
            # Tri par date décroissante (le plus récent en haut)
            top_month = top_month.sort_values("month_str", ascending=False)
            
            # === MODIFICATION ICI ===
            # On convertit la chaîne 'YYYY-MM' en objet Date pour la reformater en 'Month Year' (ex: November 2023)
            # %B = Mois complet (January), %Y = Année (2023)
            top_month["formatted_date"] = pd.to_datetime(top_month["month_str"]).dt.strftime('%B %Y')
            
            # On sélectionne les colonnes dans l'ordre voulu et on renomme
            top_month_display = top_month[["formatted_date", "artist", "plays"]].rename(
                columns={"formatted_date": "Mois", "artist": "Artiste Top 1", "plays": "Écoutes"}
            )
            
            # Affichage
            st.dataframe(
                top_month_display, 
                use_container_width=True, 
                hide_index=True,
                height=400
            )

        with data_col2:
            # --- Calcul pour la droite ---
            if artist_selected:
                top_tracks = df[df["artist"] == artist_selected]["track"].value_counts().head(50).reset_index()
                top_tracks.columns = ["Titre", "Écoutes"]
                top_tracks.index = top_tracks.index + 1
                
                # Affichage
                st.dataframe(
                    top_tracks, 
                    use_container_width=True,
                    height=400
                )
        
        st.divider()
        st.subheader("🔍 Profondeur d'exploration (Tracks per Artist)")
        st.caption("Chaque point est un artiste. La ligne représente la tendance moyenne.")

        # 1. Préparation des données
        # On compte le nombre total d'écoutes (scrobbles) ET le nombre de titres uniques par artiste
        artist_scatter = df.groupby("artist").agg(
            scrobbles=('track', 'count'),
            unique_tracks=('track', 'nunique')
        ).reset_index()

        # 2. Filtrage (Comme sur votre image : "50+ scrobbles")
        # On ne garde que les artistes écoutés au moins 50 fois pour éviter le bruit
        artist_scatter_filtered = artist_scatter[artist_scatter["scrobbles"] >= 50]

        # 3. Création du Graphique
        # Note : trendline="ols" nécessite le package 'statsmodels' installé (pip install statsmodels)
        try:
            fig_scatter_art = px.scatter(
                artist_scatter_filtered,
                x="scrobbles",
                y="unique_tracks",
                trendline="ols", # Ajoute la ligne de régression linéaire
                trendline_color_override="#333333", # Couleur de la ligne (Gris foncé)
                hover_name="artist", # Affiche le nom de l'artiste au survol
                title="Tracks per artist (50+ scrobbles)",
                color_discrete_sequence=["#7cb5ec"], # Le bleu clair style Highcharts
                opacity=0.8
            )
        except Exception:
            # Fallback si statsmodels n'est pas installé : on affiche sans la ligne de tendance
            fig_scatter_art = px.scatter(
                artist_scatter_filtered,
                x="scrobbles",
                y="unique_tracks",
                hover_name="artist",
                title="Tracks per artist (50+ scrobbles)",
                color_discrete_sequence=["#7cb5ec"]
            )

        # 4. Style pour imiter Highcharts (Fond blanc, grille grise)
        fig_scatter_art.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            xaxis=dict(
                title="Scrobbles (Total écoutes)",
                showgrid=False, # Pas de grille verticale sur l'image
                linecolor="#ccc",
                tickfont=dict(color="#333")
            ),
            yaxis=dict(
                title="Tracks (Titres uniques)",
                showgrid=True, # Grille horizontale seulement
                gridcolor="#eee",
                gridwidth=1,
                linecolor="#ccc",
                tickfont=dict(color="#333")
            ),
            margin=dict(t=40, l=20, r=20, b=20)
        )

        # Taille des points
        fig_scatter_art.update_traces(marker=dict(size=8, line=dict(width=0)))

        st.plotly_chart(fig_scatter_art, use_container_width=True)
        
    # ========== TAB 4: TRACKS ==========
    with tab4:
        st.header("Analyse des Morceaux (Tracks)")

        # --- PREMIÈRE PARTIE : LES CLASSEMENTS ---
        col_top, col_week = st.columns(2)

        with col_top:
            st.subheader("🥇 Top Tracks (Période)")
            
            # Filtre temporel spécifique à ce tableau
            period_options = ["Tout le temps", "Cette année", "6 derniers mois", "Dernier mois"]
            selected_period = st.selectbox("Période d'analyse", period_options)
            
            # Filtrage des données
            df_tracks = df.copy()
            now = df["utc_time"].max() # On prend la date max des données comme référence
            
            if selected_period == "Cette année":
                df_tracks = df_tracks[df_tracks["utc_time"].dt.year == now.year]
            elif selected_period == "6 derniers mois":
                start_date = now - pd.DateOffset(months=6)
                df_tracks = df_tracks[df_tracks["utc_time"] >= start_date]
            elif selected_period == "Dernier mois":
                start_date = now - pd.DateOffset(months=1)
                df_tracks = df_tracks[df_tracks["utc_time"] >= start_date]
            
            # Calcul du Top 10
            # On groupe par Artiste ET Track pour éviter de mélanger deux chansons du même nom
            top_tracks = df_tracks.groupby(["artist", "track"]).size().reset_index(name="Écoutes")
            top_tracks = top_tracks.sort_values("Écoutes", ascending=False).head(10)
            
            # Mise en forme pour l'affichage
            top_tracks["Morceau"] = top_tracks["artist"] + " - " + top_tracks["track"]
            display_top = top_tracks[["Morceau", "Écoutes"]].reset_index(drop=True)
            display_top.index += 1
            
            st.dataframe(display_top, use_container_width=True, height=400)

        with col_week:
            st.subheader("📅 Les Inusables")
            st.caption("Tracks écoutés sur le plus grand nombre de semaines distinctes")
            
            # Calcul des semaines uniques
            # On utilise df global (pas le filtré) pour voir la longévité réelle
            track_longevity = df.groupby(["artist", "track"])["week"].nunique().reset_index(name="Semaines actives")
            track_longevity = track_longevity.sort_values("Semaines actives", ascending=False).head(10)
            
            # Mise en forme
            track_longevity["Morceau"] = track_longevity["artist"] + " - " + track_longevity["track"]
            display_long = track_longevity[["Morceau", "Semaines actives"]].reset_index(drop=True)
            display_long.index += 1
            
            st.dataframe(display_long, use_container_width=True, height=400)

        st.divider()

        # --- SECONDE PARTIE : LE SCATTER PLOT (ALL SCROBBLES) ---
        st.subheader("🌌 Distribution temporelle des écoutes")

        # Préparation des données pour le scatter plot
        # 1. Axe X : La date (déjà utc_time)
        # 2. Axe Y : L'heure sous forme décimale (ex: 14h30 -> 14.5) pour un placement précis
        df["hour_decimal"] = df["utc_time"].dt.hour + (df["utc_time"].dt.minute / 60)
        
        # Création du graphe
        # render_mode='webgl' est CRUCIAL si vous avez beaucoup de données (>10k points) pour que ça reste fluide
        fig_scatter = px.scatter(
            df, 
            x="utc_time", 
            y="hour_decimal",
            color_discrete_sequence=["#1f77b4"], # Bleu standard, changez le code hex si besoin
            opacity=0.3, # Transparence pour voir la densité (comme sur l'image)
            render_mode="webgl", 
            hover_data={"artist": True, "track": True, "hour_decimal": False}
        )

        # Configuration des axes pour imiter l'image
        fig_scatter.update_layout(
            yaxis=dict(
                title="Heure de la journée",
                range=[24, 0], # INVERSION : 00:00 en haut, 24:00 en bas
                tickmode="array",
                tickvals=[0, 4, 8, 12, 16, 20, 24],
                ticktext=["00:00", "04:00", "08:00", "12:00", "16:00", "20:00", "24:00"]
            ),
            xaxis=dict(
                title="Date"
            ),
            height=500, # Hauteur du graphe
            margin=dict(l=20, r=20, t=20, b=20),
        )
        
        # Petits ajustements des points
        fig_scatter.update_traces(marker=dict(size=3)) # Taille des points
        
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        # --- 3. ANALYSE CYCLIQUE CORRIGÉE ---
        st.subheader("🔄 Cycles d'écoute")

        col1, col2, col3 = st.columns(3)
        chart_color = "#7cb5ec"

        # --- FONCTION D'AIDE POUR LE STYLE ---
        def style_polar_chart(fig, max_value):
            """Applique le style Highcharts et fixe l'échelle pour éviter que ça dépasse"""
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=False,  # Cache les cercles concentriques
                        range=[0, max_value * 1.1]  # AJOUTE 10% DE MARGE pour ne pas toucher le bord
                    ),
                    angularaxis=dict(
                        direction="clockwise",
                        gridcolor="#eee", # Lignes gris clair pour les séparations
                        linecolor="#eee"
                    ),
                    bgcolor="white"
                ),
                margin=dict(t=30, b=30, l=20, r=20),
                height=300,
                showlegend=False,
                paper_bgcolor="white",
            )
            return fig

        # --- 1. HEURES (0h - 23h) ---
        with col1:
            st.markdown("**Scrobbled Hours**")
            
            # Préparation des données
            hours_counts = df["utc_time"].dt.hour.value_counts().reindex(range(24), fill_value=0).reset_index()
            hours_counts.columns = ["hour_num", "count"]
            
            # CRUCIAL : On crée une colonne TEXTE pour l'affichage (0h, 1h...)
            # Cela force Plotly à bien placer les barres comme des catégories
            hours_counts["label"] = hours_counts["hour_num"].astype(str) + "h"
            
            # Calcul du max pour l'échelle
            max_h = hours_counts["count"].max()

            fig_hours = px.bar_polar(
                hours_counts, 
                r="count", 
                theta="label", # On utilise le label texte
                start_angle=90, # 0h en haut (Midi)
                direction="clockwise",
                color_discrete_sequence=[chart_color]
            )
            
            # On applique le style avec la marge de sécurité
            fig_hours = style_polar_chart(fig_hours, max_h)
            st.plotly_chart(fig_hours, use_container_width=True)

        # --- 2. JOURS (Lundi - Dimanche) ---
        with col2:
            st.markdown("**Scrobbled Days**")
            
            days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            # Labels courts pour faire propre sur le cercle
            days_map = {
                'Monday': 'Mon.', 'Tuesday': 'Tue.', 'Wednesday': 'Wed.', 
                'Thursday': 'Thu.', 'Friday': 'Fri.', 'Saturday': 'Sat.', 'Sunday': 'Sun.'
            }
            
            days_data = df["utc_time"].dt.day_name().value_counts().reindex(days_order, fill_value=0).reset_index()
            days_data.columns = ["day_full", "count"]
            days_data["label"] = days_data["day_full"].map(days_map)
            
            max_d = days_data["count"].max()

            fig_days = px.bar_polar(
                days_data, 
                r="count", 
                theta="label",
                start_angle=90, # Lundi en haut (ou changer selon préférence)
                direction="clockwise",
                color_discrete_sequence=[chart_color]
            )
            
            fig_days = style_polar_chart(fig_days, max_d)
            st.plotly_chart(fig_days, use_container_width=True)

        # --- 3. MOIS (Janvier - Décembre) ---
        with col3:
            st.markdown("**Scrobbled Months**")
            
            months_order = range(1, 13)
            months_labels = ['Jan.', 'Feb.', 'Mar.', 'Apr.', 'May', 'Jun.', 'Jul.', 'Aug.', 'Sep.', 'Oct.', 'Nov.', 'Dec.']
            
            months_data = df["utc_time"].dt.month.value_counts().reindex(months_order, fill_value=0).reset_index()
            months_data.columns = ["month_num", "count"]
            months_data["label"] = months_data["month_num"].apply(lambda x: months_labels[x-1])
            
            max_m = months_data["count"].max()
            
            fig_months = px.bar_polar(
                months_data, 
                r="count", 
                theta="label",
                start_angle=90, # Janvier en haut
                direction="clockwise",
                color_discrete_sequence=[chart_color]
            )
            
            fig_months = style_polar_chart(fig_months, max_m)
            st.plotly_chart(fig_months, use_container_width=True)
    
    # ========== TAB 5: ALBUMS ==========
    with tab5:
        st.header("Analyse des Albums")

        col_top_alb, col_week_alb = st.columns(2)

        with col_top_alb:
            st.subheader("🥇 Top Albums (Période)")
            
            # Filtre temporel spécifique
            period_options_alb = ["Tout le temps", "Cette année", "6 derniers mois", "Dernier mois"]
            selected_period_alb = st.selectbox("Période d'analyse", period_options_alb, key="period_alb")
            
            # Filtrage des données
            df_alb = df.copy()
            now = df["utc_time"].max()
            
            if selected_period_alb == "Cette année":
                df_alb = df_alb[df_alb["utc_time"].dt.year == now.year]
            elif selected_period_alb == "6 derniers mois":
                start_date = now - pd.DateOffset(months=6)
                df_alb = df_alb[df_alb["utc_time"] >= start_date]
            elif selected_period_alb == "Dernier mois":
                start_date = now - pd.DateOffset(months=1)
                df_alb = df_alb[df_alb["utc_time"] >= start_date]
            
            # Calcul Top 10
            # GroupBy Artist + Album pour éviter les doublons de noms d'albums (ex: "Greatest Hits")
            top_albums = df_alb.groupby(["artist", "album"]).size().reset_index(name="Écoutes")
            top_albums = top_albums.sort_values("Écoutes", ascending=False).head(10)
            
            # Mise en forme
            top_albums["Album complet"] = top_albums["artist"] + " - " + top_albums["album"]
            display_top_alb = top_albums[["Album complet", "Écoutes"]].reset_index(drop=True)
            display_top_alb.index += 1
            
            st.dataframe(display_top_alb, use_container_width=True, height=500)

        with col_week_alb:
            st.subheader("📅 Albums cultes")
            st.caption("Albums écoutés sur le plus grand nombre de semaines distinctes")
            
            # Calcul longévité
            # On filtre les albums vides ou inconnus si nécessaire
            df_clean = df[df["album"].notna() & (df["album"] != "")]
            
            alb_longevity = df_clean.groupby(["artist", "album"])["week"].nunique().reset_index(name="Semaines actives")
            alb_longevity = alb_longevity.sort_values("Semaines actives", ascending=False).head(10)
            
            # Mise en forme
            alb_longevity["Album complet"] = alb_longevity["artist"] + " - " + alb_longevity["album"]
            display_long_alb = alb_longevity[["Album complet", "Semaines actives"]].reset_index(drop=True)
            display_long_alb.index += 1
            
            st.dataframe(display_long_alb, use_container_width=True, height=500)
            
        st.divider()

        # --- PARTIE 2 : LE TREEMAP (Artiste > Album) ---
        st.subheader("🗺️ Cartographie de votre CD-thèque")
        st.caption("Albums avec au moins 2 titres distincts. La taille représente le volume d'écoutes.")

        # 1. Nettoyage de base
        df_tree = df[df["album"].notna() & (df["album"] != "")].copy()
        
        # 2. CALCUL AVANCÉ : On compte les écoutes ET les pistes uniques par album
        tree_data = df_tree.groupby(["artist", "album"]).agg(
            plays=('track', 'count'),       # Total d'écoutes (taille du carré)
            nb_tracks=('track', 'nunique')  # Nombre de pistes différentes (pour le filtre)
        ).reset_index()
        
        # 3. FILTRE "VRAI ALBUM" : On garde seulement si plus de 1 track unique
        tree_data = tree_data[tree_data["nb_tracks"] > 1]
        
        # 4. FILTRE TOP 50 ARTISTES (Basé sur les albums restants)
        # On recalcule le top 50 APRES avoir enlevé les singles pour que le classement soit pertinent
        top_artists_list = tree_data.groupby("artist")["plays"].sum().nlargest(20).index
        tree_data_final = tree_data[tree_data["artist"].isin(top_artists_list)]

        # Création du Treemap
        fig_tree = px.treemap(
            tree_data_final, 
            path=['artist', 'album'], 
            values='plays',
            color='artist', 
            color_discrete_sequence=px.colors.qualitative.Prism,
        )

        fig_tree.update_layout(
            margin=dict(t=20, l=10, r=10, b=10),
            height=600
        )
        
        # Infobulle améliorée : on affiche aussi le nombre de pistes
        fig_tree.update_traces(
            hovertemplate='<b>%{label}</b><br>Écoutes: %{value}<br>Pistes: %{customdata[0]}<extra></extra>',
            textinfo="label+value",
            customdata=tree_data_final[['nb_tracks']] # On passe la colonne nb_tracks pour l'infobulle
        )
        
        st.plotly_chart(fig_tree, use_container_width=True)
        
        st.divider()
        st.subheader("💿 Singles vs Albums Entiers")
        st.caption("Points à droite = Albums explorés en profondeur. Points à gauche = Singles écoutés en boucle.")

        # Calcul : Pour chaque album, nb d'écoutes total ET nb de titres uniques
        df_integrity = df[df["album"].notna() & (df["album"] != "")]
        album_stats = df_integrity.groupby(["artist", "album"]).agg(
            total_plays=('track', 'count'),
            unique_tracks=('track', 'nunique')
        ).reset_index()

        # On filtre les "petits" albums pour ne pas polluer le graph (min 20 écoutes)
        album_stats = album_stats[album_stats["total_plays"] > 20]

        fig_scat_alb = px.scatter(
            album_stats,
            x="unique_tracks",
            y="total_plays",
            size="total_plays", # La bulle grossit avec les écoutes
            color="unique_tracks", # Couleur selon la profondeur d'exploration
            hover_name="album",
            hover_data=["artist"],
            color_continuous_scale="Viridis",
            labels={"unique_tracks": "Nombre de titres différents écoutés", "total_plays": "Écoutes totales"}
        )
        
        fig_scat_alb.update_layout(height=500)
        st.plotly_chart(fig_scat_alb, use_container_width=True)
    
    # ========== TAB 2: BAR CHART RACE ==========
    with tab2:
        st.header("🏁 Course aux écoutes (Historique complet)")
        
        # Configuration : Seulement le nombre d'artistes en saisie chiffre
        top_n = st.number_input(
            "Nombre d'artistes à afficher", 
            min_value=1, 
            max_value=20, 
            value=10, 
            step=1
        )
        
        # Préparation des données
        # On s'assure que la conversion de date est faite
        # (Si elle a été faite par le filtre global, cette ligne est redondante mais sans danger)
        if not pd.api.types.is_datetime64_any_dtype(df["utc_time"]):
             df["utc_time"] = pd.to_datetime(df["utc_time"], format="%d %b %Y, %H:%M")
        
        # === NETTOYAGE DES CARACTÈRES SPÉCIAUX ===
        def clean_name(name):
            if pd.isna(name):
                return name
            replacements = {
                '$': 'S',
                '_': ' ',
                '^': '',
                '{': '(',
                '}': ')',
                '\\': '',
                '~': '',
                '#': '',
                '%': '',
                '&': 'and'
            }
            cleaned = str(name)
            for old, new in replacements.items():
                cleaned = cleaned.replace(old, new)
            return cleaned
        
        df["artist"] = df["artist"].apply(clean_name)
        
        # === LOGIQUE INTERNE FORCEE ===
        # On force le pas de temps au "Mois" pour que l'animation soit fluide
        # Cela ne filtre pas les données (c'est le filtre en haut de page qui gère ça),
        # Cela définit juste la vitesse de l'animation.
        df["period"] = df["utc_time"].dt.to_period("M")
        
        # Compter les écoutes par artiste et période
        artist_plays = (
            df.groupby(['period', 'artist'])
            .size()
            .reset_index(name='plays')
        )
        
        # Créer le tableau pivot
        pivot_df = artist_plays.pivot(
            index='period',
            columns='artist',
            values='plays'
        ).fillna(0)
        
        # Convertir l'index en datetime pour bar_chart_race
        pivot_df.index = pivot_df.index.to_timestamp()
        
        # Calculer le cumul (Course au total)
        cumulative_df = pivot_df.cumsum()
        
        # Générer la vidéo
        # Cache key simplifiée (plus de variable 'period')
        cache_key = f"{st.session_state.utilisateur_selectionne}_race_{top_n}_{len(df)}"

        if 'video_cache' not in st.session_state:
            st.session_state.video_cache = {}
        
        if cache_key not in st.session_state.video_cache:
            with st.spinner("⏳ Génération de l'animation... (Patience, c'est du lourd !)"):
                try:
                    # Si le dataframe est trop petit (ex: filtre sur 2 jours), on évite le crash
                    if len(cumulative_df) < 2:
                        st.warning("Pas assez de périodes temporelles pour générer une animation. Sélectionnez une plage de dates plus large.")
                        video = None
                    else:
                        html_str = bcr.bar_chart_race(
                            df=cumulative_df,
                            filename=None,
                            n_bars=int(top_n), # Conversion int explicite
                            sort='desc',
                            title='Évolution du Top Artistes (Cumulé)',
                            period_length=1000, # Vitesse (ms par période)
                            steps_per_period=10, # Fluidité
                            figsize=(6, 3.5),
                            cmap='tab20',
                            bar_label_size=10,
                            tick_label_size=10,
                            period_label={'x': .98, 'y': .3, 'ha': 'right', 'va': 'center'},
                            period_fmt='%B %Y', # Format mois
                            filter_column_colors=True
                        ).data
                        
                        # Extraire la vidéo
                        start = html_str.find('base64,') + len('base64,')
                        end = html_str.find('">')
                        video = base64.b64decode(html_str[start:end])
                        
                        # Cache
                        st.session_state.video_cache[cache_key] = video
                        st.success("✅ Animation prête !")
                    
                except Exception as e:
                    st.error(f"❌ Erreur technique : {str(e)}")
                    video = None
        else:
            video = st.session_state.video_cache[cache_key]
        
        # Afficher la vidéo
        if video:
            st.video(video)