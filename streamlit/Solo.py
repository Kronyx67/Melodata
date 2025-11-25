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
    
    # --- Tabs principales ---
    tab1, tab2 , tab3, tab4= st.tabs(["📊 Heatmap", "🏁 Bar Chart Race","🏆 Artistes","🎵 Meloz" ])
    
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
    
    # # ========== TAB 2: BAR CHART RACE ==========
    # with tab2:
    #     st.header("Top Artistes les plus écoutés")
        
    #     # Configuration simple
    #     col1, col2 = st.columns(2)
        
    #     with col1:
    #         top_n = st.slider("Nombre d'artistes", 5, 20, 10)
        
    #     with col2:
    #         period = st.selectbox("Période", ["Semaine", "Mois", "Trimestre"], index=1)
        
    #     # Préparation des données
    #     df["utc_time"] = pd.to_datetime(df["utc_time"], format="%d %b %Y, %H:%M")
        
    #     # === NETTOYAGE DES CARACTÈRES SPÉCIAUX ===
    #     def clean_name(name):
    #         if pd.isna(name):
    #             return name
    #         replacements = {
    #             '$': 'S',
    #             '_': ' ',
    #             '^': '',
    #             '{': '(',
    #             '}': ')',
    #             '\\': '',
    #             '~': '',
    #             '#': '',
    #             '%': '',
    #             '&': 'and'
    #         }
    #         cleaned = str(name)
    #         for old, new in replacements.items():
    #             cleaned = cleaned.replace(old, new)
    #         return cleaned
        
    #     df["artist"] = df["artist"].apply(clean_name)
        
    #     # Mapping des périodes
    #     period_map = {
    #         "Semaine": "W",
    #         "Mois": "M",
    #         "Trimestre": "Q"
    #     }
        
    #     # Créer la colonne de période
    #     df["period"] = df["utc_time"].dt.to_period(period_map[period])
        
    #     # Compter les écoutes par artiste et période
    #     artist_plays = (
    #         df.groupby(['period', 'artist'])
    #         .size()
    #         .reset_index(name='plays')
    #     )
        
    #     # Créer le tableau pivot avec périodes en index et artistes en colonnes
    #     pivot_df = artist_plays.pivot(
    #         index='period',
    #         columns='artist',
    #         values='plays'
    #     ).fillna(0)
        
    #     # Convertir l'index en datetime pour bar_chart_race
    #     pivot_df.index = pivot_df.index.to_timestamp()
        
    #     # Calculer le cumul au fil du temps
    #     cumulative_df = pivot_df.cumsum()
        
    #     # Générer automatiquement la vidéo
    #     # Utiliser un cache basé sur le fichier et les paramètres
    #     cache_key = f"{st.session_state.utilisateur_selectionne}.csv_{period}_{top_n}"

    #     if 'video_cache' not in st.session_state:
    #         st.session_state.video_cache = {}
        
    #     if cache_key not in st.session_state.video_cache:
    #         with st.spinner("⏳ Génération du Bar Chart Race en cours... (cela peut prendre quelques instants)"):
    #             try:
    #                 html_str = bcr.bar_chart_race(
    #                     df=cumulative_df,
    #                     filename=None,
    #                     n_bars=top_n,
    #                     sort='desc',
    #                     title='Top Artistes les plus écoutés',
    #                     period_length=1500,
    #                     steps_per_period=20,
    #                     figsize=(6, 4),
    #                     cmap='tab20',
    #                     bar_label_size=10,
    #                     tick_label_size=10,
    #                     period_label={'x': .98, 'y': .3, 'ha': 'right', 'va': 'center'},
    #                     period_fmt='%B %Y' if period_map[period] == 'M' else '%Y-W%U',
    #                     filter_column_colors=True
    #                 ).data
                    
    #                 # Extraire la vidéo encodée en base64
    #                 start = html_str.find('base64,') + len('base64,')
    #                 end = html_str.find('">')
    #                 video = base64.b64decode(html_str[start:end])
                    
    #                 # Stocker dans le cache
    #                 st.session_state.video_cache[cache_key] = video
                    
    #                 st.success("✅ Animation générée avec succès !")
                    
    #             except Exception as e:
    #                 st.error(f"❌ Erreur lors de la génération : {str(e)}")
    #                 st.info("💡 Essayez de réduire le nombre d'artistes")
    #                 video = None
    #     else:
    #         video = st.session_state.video_cache[cache_key]
    #         #st.info("📼 Vidéo chargée depuis le cache")
        
    #     # Afficher la vidéo
    #     if video:
    #         st.video(video)
            
    #         # Statistiques
    #         st.divider()
    #         st.subheader("📊 Statistiques")
    #         col1, col2, col3 = st.columns(3)
            
    #         final_top = cumulative_df.iloc[-1].nlargest(5)
            
    #         with col1:
    #             st.metric("Total périodes", len(cumulative_df))
            
    #         with col2:
    #             st.metric("Artiste #1", final_top.index[0])
            
    #         with col3:
    #             st.metric("Écoutes top artiste", int(final_top.values[0]))
            
    #         # Top 5 final
    #         st.subheader("🏆 Top 5 Final")
    #         top5_df = pd.DataFrame({
    #             'Artiste': final_top.index,
    #             'Écoutes totales': final_top.values.astype(int)
    #         }).reset_index(drop=True)
    #         top5_df.index += 1
    #         st.dataframe(top5_df, width=True)
    
    
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
        
        # 1. On prépare une colonne temporelle triable (Début de semaine)
        # Cela évite les soucis si vos données couvrent plusieurs années
        df["week_start"] = df["utc_time"].dt.to_period('W').apply(lambda r: r.start_time)
        
        # 2. Filtrer sur le Top 10 actuel
        top10_list = top_artists["Artiste"].tolist()
        df_top10 = df[df["artist"].isin(top10_list)]
        
        # 3. Compter les écoutes par semaine et par artiste
        weekly_counts = df_top10.groupby(["week_start", "artist"]).size().reset_index(name="plays")
        
        # 4. Pivot pour avoir une colonne par artiste et remplir les trous par 0
        # C'est CRUCIAL pour que la ligne reste plate quand on n'écoute pas l'artiste, 
        # au lieu de relier deux points éloignés.
        pivot_df = weekly_counts.pivot(index="week_start", columns="artist", values="plays").fillna(0)
        
        # 5. Calcul du cumul (cumsum)
        cumulative_df = pivot_df.cumsum()
        
        # 6. On remet en format long pour Plotly
        evolution_final = cumulative_df.reset_index().melt(
            id_vars="week_start", 
            var_name="artist", 
            value_name="cumulative_plays"
        )
        
        # 7. Création du graphique
        fig_evo = px.line(
            evolution_final,
            x="week_start",
            y="cumulative_plays",
            color="artist",
            markers=False, # On enlève les marqueurs pour alléger visuellement le cumul
            title="Évolution cumulée des écoutes du Top 10",
            labels={"week_start": "Date", "cumulative_plays": "Total écoutes cumulées", "artist": "Artiste"}
        )
        
        # Amélioration du style
        fig_evo.update_layout(
            hovermode="x unified", 
            xaxis_title="Temps",
            yaxis_title="Écoutes totales"
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