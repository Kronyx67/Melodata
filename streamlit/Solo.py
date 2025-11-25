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
    tab1, tab2 , tab3= st.tabs(["📊 Heatmap", "🏁 Bar Chart Race","Artistes"])
    
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
        col3, col4 = st.columns(2)

        with col3:
            st.markdown("### 🗓️ Artiste favori par mois")
            
            # Calcul du top 1 par mois
            monthly_stats = df.groupby(["month_str", "artist"]).size().reset_index(name="plays")
            # On trie par mois puis par plays pour prendre le dernier (le plus grand)
            monthly_stats = monthly_stats.sort_values(["month_str", "plays"], ascending=[True, False])
            
            # On dédoublonne sur le mois en gardant le premier (donc le plus grand plays)
            top_month = monthly_stats.drop_duplicates(subset=["month_str"], keep="first")
            
            # Mise en forme
            top_month = top_month.rename(columns={"month_str": "Mois", "artist": "Artiste Top 1", "plays": "Écoutes"})
            top_month = top_month.reset_index(drop=True)
            
            st.dataframe(top_month, use_container_width=True, hide_index=True)

        with col4:
            st.markdown("### 🎵 Top Tracks par Artiste")
            
            # Liste des artistes triée alphabétiquement
            liste_artistes = sorted(df["artist"].dropna().unique())
            
            # Sélecteur
            artist_selected = st.selectbox("Choisir un artiste pour voir ses titres phares", liste_artistes)
            
            if artist_selected:
                # Calcul
                top_tracks = df[df["artist"] == artist_selected]["track"].value_counts().head(10).reset_index()
                top_tracks.columns = ["Titre", "Écoutes"]
                top_tracks.index = top_tracks.index + 1
                
                st.dataframe(top_tracks, use_container_width=True)