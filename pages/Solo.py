import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import bar_chart_race as bcr
import base64

def show_page():
    # --- Configuration de la page ---
    color_theme = "viridis_r"
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
    # 🧠 GESTION INTELLIGENTE DE LA MÉMOIRE (STATE)
    # On fait tout ici en une seule fois pour éviter les conflits
    # ====================================================================

    # A. Initialisation des clés si elles manquent
    if 'date_start' not in st.session_state: st.session_state.date_start = min_glob
    if 'date_end' not in st.session_state: st.session_state.date_end = max_glob
    if 'current_user_viewed' not in st.session_state: st.session_state.current_user_viewed = None

    # B. RESET : Si on a changé d'utilisateur -> On remet tout à zéro
    if st.session_state.current_user_viewed != st.session_state.utilisateur_selectionne:
        st.session_state.date_start = min_glob
        st.session_state.date_end = max_glob
        # On peut aussi reset les selectbox si besoin, mais le plus important c'est les dates
        st.session_state.current_user_viewed = st.session_state.utilisateur_selectionne
    
    # C. CLAMPING (SÉCURITÉ ANTI-CRASH)
    # On s'assure impérativement que les dates en mémoire sont valides pour CE fichier
    # Sinon st.date_input plantera.
    st.session_state.date_start = max(min_glob, min(st.session_state.date_start, max_glob))
    st.session_state.date_end = min(max_glob, max(st.session_state.date_end, min_glob))
    
    # D. COHÉRENCE (Début <= Fin)
    if st.session_state.date_start > st.session_state.date_end:
        st.session_state.date_start = min_glob
        st.session_state.date_end = max_glob
    # --- FONCTIONS DE CALLBACK (Ce qui se passe quand on change une option) ---
    
    def update_from_preset():
        """Met à jour les dates selon la période rapide choisie"""
        choix = st.session_state.preset_selector
        if choix == "All time":
            st.session_state.date_start = min_glob
            st.session_state.date_end = max_glob
        elif choix.startswith("Last"):
            days = int(choix.split()[1]) # Récupère 7, 30 ou 90
            st.session_state.date_end = max_glob
            st.session_state.date_start = max_glob - pd.Timedelta(days=days)
        # On remet l'année sur "Sélectionner" pour éviter la confusion
        st.session_state.year_selector = "Select"

    def update_from_year():
        """Met à jour les dates selon l'année choisie"""
        annee = st.session_state.year_selector
        if annee != "Select":
            # Début de l'année (ou min global si données commencent après)
            start = pd.Timestamp(f"{annee}-01-01").date()
            st.session_state.date_start = max(start, min_glob)
            
            # Fin de l'année (ou max global)
            end = pd.Timestamp(f"{annee}-12-31").date()
            st.session_state.date_end = min(end, max_glob)
            
            # On remet le preset sur "Personnalisé"
            st.session_state.preset_selector = "Personalized"

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
                "⚡ Rapid periods",
                options=["Personalized", "All time", "Last 7 days", "Last 30 days", "Last 90 days", "Last 365 days"],
                key="preset_selector",
                on_change=update_from_preset # Déclenche la fonction quand on change
            )

        # --- COL 2 : ANNÉE ---
        with c2:
            years_avail = sorted(df["utc_time"].dt.year.unique(), reverse=True)
            st.selectbox(
                "📂 Years",
                options=["Select"] + years_avail,
                key="year_selector",
                on_change=update_from_year # Déclenche la fonction quand on change
            )

        # --- COL 3 : CALENDRIER (Le maître du jeu) ---
        with c3:
            # Le widget prend ses valeurs par défaut dans le session_state mis à jour par les colonnes 1 et 2
            dates = st.date_input(
                "📅 Select dates",
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
        st.caption(f"✅ **{len(df)}** displayed plays (from the {start_sel.strftime('%d/%m/%Y')} to the {end_sel.strftime('%d/%m/%Y')})")
    else:
        st.warning("Veuillez sélectionner une date de fin dans le calendrier.")
        st.stop() # Arrête l'exécution tant que les dates ne sont pas valides

    st.divider()
    
    # --- Tabs principales ---
    tab1, tab3, tab5, tab4, tab2= st.tabs(["📊 Heatmap","🏆 Artists","💿 Albums", "🎵 Meloz", "🏁 Bar Chart Race"])
    
    # ========== TAB 1: HEATMAP ==========
    with tab1:
        st.header("Listening Activity by Week and Day")
        st.caption(
            "This heatmap shows the user's listening activity by week and day for the selected year, "
            "Darker cells indicate more plays, highlighting which days and weeks had the highest engagement."
        )
        
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
        year_selected = st.selectbox("Select Year", annees_disponibles)
        
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
        
        # Remplacer les 0 par NaN pour que ce soit vide (blanc)
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
            color_continuous_scale=color_theme
        )
        
        # --- Options de style ---
        fig.update_traces(
            hovertemplate="%{y}, %{x}: %{z} plays<extra></extra>",
            xgap=1,  # Ajoute une ligne blanche verticale entre les cases
            ygap=1   # Ajoute une ligne blanche horizontale entre les cases
        )
        
        fig.update_layout(
            title=f"Weekly Intensity - Year {year_selected}",
            xaxis_title="Week Number",
            yaxis_title=None, # Pas besoin de titre pour les jours, c'est évident
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis=dict(showgrid=False), # Enlève la grille
            yaxis=dict(showgrid=False)  # Enlève la grille
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Deuxième visu heatmap
        
        st.divider()
        st.header("Hourly Listening Distribution (Top 20 favorite artists)")
        st.caption(
        "This heatmap shows your hourly listening distribution for your 20 favorite artists. "
        "In 'Volume' mode, the colors represent the actual number of plays, highlighting your most-played artists. "
        "In 'Normalized (%)' mode, each row is scaled to show the concentration of listening across hours, making it easier to spot your daily listening habits."
    )
        
        # --- COMMANDES UTILISATEUR ---

        mode_affichage = st.radio(
            "**Display Mode:**",
            ["Volume (Plays)", "Normalized (%)"],
            horizontal=True
        )
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
        if mode_affichage == "Normalized (%)":
            # Calcul du pourcentage par ligne
            matrix_to_plot = matrix_art.div(matrix_art.sum(axis=1), axis=0) * 100
            z_label = "Concentration (%)"
            hover_fmt = ".1f"
            color_scale = "plasma" 
        else:
            # Données brutes
            matrix_to_plot = matrix_art
            z_label = "Plays"
            hover_fmt = "d" 
            color_scale = "plasma"

        # --- 3. CRÉATION DU GRAPHIQUE ---
        fig_heat = px.imshow(
            matrix_to_plot,
            labels=dict(x="Hour", y="Artist", color=z_label),
            color_continuous_scale=color_scale,
            aspect="auto",
            height=600
        )
        
        # Configuration du style
        fig_heat.update_xaxes(side="top", title=None)
        
        # Infobulle dynamique selon le mode
        if mode_affichage == "Normalized (%)":
            fig_heat.update_traces(
                hovertemplate="<b>%{y}</b><br>Hour: %{x}h<br>Concentration: %{z:.1f}%<extra></extra>"
            )
        else:
             fig_heat.update_traces(
                hovertemplate="<b>%{y}</b><br>Hour: %{x}h<br>Plays: %{z}<extra></extra>"
            )
        
        fig_heat.update_layout(
            xaxis=dict(ticksuffix="h"), # Ajoute 'h' après les heures (0h, 1h...)
            plot_bgcolor='white'
        )

        st.plotly_chart(fig_heat, use_container_width=True)
    
    
    # ========== TAB 3: ARTISTS ==========
    with tab3:
        st.header("🏆 Rankings & Analysis")

        # --- Data Preparation ---
        # Ensure dates are in the correct format
        df["utc_time"] = pd.to_datetime(df["utc_time"], format="%d %b %Y, %H:%M", errors="coerce")
        df["month_str"] = df["utc_time"].dt.strftime('%Y-%m') # Format string for display
        df["week"] = df["utc_time"].dt.isocalendar().week

        # --- FIRST ROW: PODIUMS ---
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🥇 Top 10 Artists (Volume)")
            st.caption("Ranked by total play count")
            
            # Calculation
            top_artists = df["artist"].value_counts().head(10).reset_index()
            top_artists.columns = ["Artist", "Plays"]
            top_artists.index = top_artists.index + 1 # Start ranking at 1
            
            # Display Table
            st.dataframe(top_artists, use_container_width=True)

        with col2:
            st.markdown("### 📅 Top 10 Regulars")
            st.caption("Artists listened to across the highest number of distinct weeks")
            
            # Calculation
            weeks_per_artist = df.groupby("artist")["week"].nunique().sort_values(ascending=False).head(10).reset_index()
            weeks_per_artist.columns = ["Artist", "Active Weeks"]
            weeks_per_artist.index = weeks_per_artist.index + 1
            
            # Display Table
            st.dataframe(weeks_per_artist, use_container_width=True)

        st.divider()

        # --- SECOND ROW: CUMULATIVE EVOLUTION ---
        st.subheader("📈 Play Count Race")
        st.caption("This graph shows the race for the number of plays among the top 10 artists, illustrating the evolution of their total number of streams over time.")
        
        # Safety: Stop if no filtered data
        if df.empty:
            st.warning("⚠️ No data available for this period to show evolution.")
        else:
            # 1. Adapt time granularity
            # If period is short (< 30 days), view by DAY instead of WEEK
            days_range = (df["utc_time"].max() - df["utc_time"].min()).days
            
            df_evo = df.copy()
            
            if days_range < 30:
                # "Zoom" Mode: By Day
                df_evo["time_step"] = df_evo["utc_time"].dt.date
            else:
                # "Wide" Mode: By Week
                df_evo["time_step"] = df_evo["utc_time"].dt.to_period('W').apply(lambda r: r.start_time)


            # 2. Filter on Top 10 (Recalculated on the filtered period)
            # Use artists displayed in the table above
            top10_list = top_artists["Artist"].tolist() if "Artist" in top_artists.columns else []
            df_top10 = df_evo[df_evo["artist"].isin(top10_list)]
            
            if df_top10.empty:
                st.info("Not enough data for the Top 10 in this period.")
            else:
                # 3. Count plays
                counts = df_top10.groupby(["time_step", "artist"]).size().reset_index(name="plays")
                
                # 4. Pivot
                pivot_df = counts.pivot(index="time_step", columns="artist", values="plays").fillna(0)
                
                # 5. Cumulative sum
                cumulative_df = pivot_df.cumsum()
                
                # 6. Long format for Plotly
                evolution_final = cumulative_df.reset_index().melt(
                    id_vars="time_step", 
                    var_name="artist", 
                    value_name="cumulative_plays"
                )
                
                # 7. Chart
                fig_evo = px.line(
                    evolution_final,
                    x="time_step",
                    y="cumulative_plays",
                    color="artist",
                    markers=True if days_range < 30 else False, # Markers if few points
                    title=f"Cumulative Evolution",
                )
                
                fig_evo.update_layout(
                    hovermode="x unified", 
                    xaxis_title="Dates",
                    yaxis_title="Cumulative Total"
                )
                
                st.plotly_chart(fig_evo, use_container_width=True)

        st.divider()

        # --- THIRD ROW: MONTHLY DETAILS & TRACKS ---
        
        # 1. HEADERS AND CONTROLS
        head_col1, head_col2 = st.columns(2)

        with head_col1:
            st.markdown("### 🗓️ Top Artist by Month")

        with head_col2:
            st.markdown("### 🎵 Top Tracks per Artist")
            
            # --- FILTER: Keep only artists > 10 plays ---
            # 1. Count occurrences in current filtered DataFrame
            artist_counts = df["artist"].value_counts()
            
            # 2. Keep those above 10
            valid_artists = artist_counts[artist_counts > 10].index.tolist()
            liste_artistes = sorted(valid_artists)
            
            # 3. Display Selectbox
            if not liste_artistes:
                st.warning("No artist with more than 10 plays in this period.")
                artist_selected = None
            else:
                artist_selected = st.selectbox(
                    "Select an artist (10+ plays min.)", 
                    liste_artistes, 
                    label_visibility="collapsed"
                )

        # 2. DATA DISPLAY
        data_col1, data_col2 = st.columns(2)

        with data_col1:
            # --- Left Calculation ---
            monthly_stats = df.groupby(["month_str", "artist"]).size().reset_index(name="plays")
            
            if not monthly_stats.empty:
                # Find top 1
                idx = monthly_stats.groupby("month_str")["plays"].idxmax()
                top_month = monthly_stats.loc[idx]
                
                # Sort by date descending
                top_month = top_month.sort_values("month_str", ascending=False)
                
                # Format date
                top_month["formatted_date"] = pd.to_datetime(top_month["month_str"]).dt.strftime('%B %Y')
                
                # Select and rename
                top_month_display = top_month[["formatted_date", "artist", "plays"]].rename(
                    columns={"formatted_date": "Month", "artist": "Top Artist", "plays": "Plays"}
                )
                
                st.dataframe(
                    top_month_display, 
                    use_container_width=True, 
                    hide_index=True,
                    height=400
                )
            else:
                st.info("Not enough data to display monthly favorites.")

        with data_col2:
            # --- Right Calculation ---
            if artist_selected:
                top_tracks = df[df["artist"] == artist_selected]["track"].value_counts().head(50).reset_index()
                top_tracks.columns = ["Track", "Plays"]
                top_tracks.index = top_tracks.index + 1
                
                st.dataframe(
                    top_tracks, 
                    use_container_width=True,
                    height=400
                )
        
        st.divider()
        st.subheader("🔍 Exploration Depth (Tracks per Artist)")
        st.caption(
        "Each dot represents an artist, showing the total number of plays (Meloz) versus the number of unique tracks,"
        " the line indicates the average trend"
    )

        # 1. Data Preparation
        # Count total plays (scrobbles) AND unique tracks per artist
        artist_scatter = df.groupby("artist").agg(
            scrobbles=('track', 'count'),
            unique_tracks=('track', 'nunique')
        ).reset_index()

        # 2. Filtering ("50+ scrobbles")
        # Keep only artists with at least 50 plays to avoid noise
        artist_scatter_filtered = artist_scatter[artist_scatter["scrobbles"] >= 50]

        # 3. Create Chart

        try:
            fig_scatter_art = px.scatter(
                artist_scatter_filtered,
                x="scrobbles",
                y="unique_tracks",
                trendline="ols", # Adds linear regression line
                trendline_color_override="#333333", # Line color (Dark grey)
                hover_name="artist", # Show artist name on hover
                title="Tracks per artist (50+ scrobbles)",
                color_discrete_sequence=["#7cb5ec"], # Light blue style
                opacity=0.8
            )
        except Exception:
            # Fallback if statsmodels is not installed: display without trendline
            fig_scatter_art = px.scatter(
                artist_scatter_filtered,
                x="scrobbles",
                y="unique_tracks",
                hover_name="artist",
                title="Tracks per artist (50+ scrobbles)",
                color_discrete_sequence=["#7cb5ec"]
            )
            
        # Calcul dynamique de la valeur max pour la borne de fin
        max_x_val = artist_scatter_filtered["scrobbles"].max()
        upper_bound = max_x_val * 1.01

        # 4. Style to mimic Highcharts (White background, grey grid)
        fig_scatter_art.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            xaxis=dict(
                title="Meloz (Total Plays)",
                showgrid=False, 
                linecolor="#ccc",
                tickfont=dict(color="#333"),
                range=[45, upper_bound],
            ),
            yaxis=dict(
                title="Tracks (Unique Titles)",
                showgrid=True, 
                gridcolor="#eee",
                gridwidth=1,
                linecolor="#ccc",
                tickfont=dict(color="#333"),
                rangemode="tozero"
            ),
            margin=dict(t=40, l=20, r=20, b=20)
        )

        # Marker size
        fig_scatter_art.update_traces(marker=dict(size=8, line=dict(width=0)))

        st.plotly_chart(fig_scatter_art, use_container_width=True)
        
    # ========== TAB 4: TRACKS ==========
    with tab4:
        st.header("Track Analysis")

        # --- PART 1: RANKINGS ---
        col_top, col_week = st.columns(2)

        with col_top:
            st.subheader("🥇 Top Tracks")
            st.caption("Most played tracks in the selected period")
            
            
            # Calcul du Top 10
            # On groupe par Artiste ET Track pour distinguer les chansons du même nom
            top_tracks = df.groupby(["artist", "track"]).size().reset_index(name="Plays")
            top_tracks = top_tracks.sort_values("Plays", ascending=False).head(10)
            
            # Mise en forme pour l'affichage
            top_tracks["Track"] = top_tracks["artist"] + " - " + top_tracks["track"]
            display_top = top_tracks[["Track", "Plays"]].reset_index(drop=True)
            display_top.index += 1
            
            st.dataframe(display_top, use_container_width=True)

        with col_week:
            st.subheader("📅 The Timeless Ones")
            st.caption("Tracks listened to across the most distinct weeks")
            
            # Unique Weeks Calculation
            # Use global df (not filtered) to see real longevity
            track_longevity = df.groupby(["artist", "track"])["week"].nunique().reset_index(name="Active Weeks")
            track_longevity = track_longevity.sort_values("Active Weeks", ascending=False).head(10)
            
            # Formatting
            track_longevity["Track"] = track_longevity["artist"] + " - " + track_longevity["track"]
            display_long = track_longevity[["Track", "Active Weeks"]].reset_index(drop=True)
            display_long.index += 1
            
            st.dataframe(display_long, use_container_width=True)

        st.divider()

        # --- PART 2: SCATTER PLOT (ALL SCROBBLES) ---
        st.subheader("🌌 Listening Time Distribution")
        st.caption("Each point represents a listen, the density of points shows your preferred listening times throughout history")

        # Data Preparation
        # 1. X-Axis: Date (already utc_time)
        # 2. Y-Axis: Decimal hour (e.g., 14:30 -> 14.5) for precise placement
        df["hour_decimal"] = df["utc_time"].dt.hour + (df["utc_time"].dt.minute / 60)
        
        # Chart Creation
        # render_mode='webgl' is CRITICAL for performance (>10k points)
        fig_scatter = px.scatter(
            df, 
            x="utc_time", 
            y="hour_decimal",
            color_discrete_sequence=["#1f77b4"], # Standard Blue
            opacity=0.3, # Transparency to show density
            render_mode="webgl", 
            hover_data={"artist": True, "track": True, "hour_decimal": False}
        )

        # Axis Configuration
        fig_scatter.update_layout(
            yaxis=dict(
                title="Time of Day",
                range=[24, 0], # INVERSION: 00:00 at top, 24:00 at bottom
                tickmode="array",
                tickvals=[0, 4, 8, 12, 16, 20, 24],
                ticktext=["00:00", "04:00", "08:00", "12:00", "16:00", "20:00", "24:00"]
            ),
            xaxis=dict(
                title="Date"
            ),
            height=500,
            margin=dict(l=20, r=20, t=20, b=20),
        )
        
        # Point Adjustments
        fig_scatter.update_traces(marker=dict(size=3)) 
        
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        # --- 3. CYCLICAL ANALYSIS ---
        st.subheader("🔄 Listening Cycles")

        col1, col2, col3 = st.columns(3)
        chart_color = "#7cb5ec"

        # --- HELPER FUNCTION FOR STYLE ---
        def style_polar_chart(fig, max_value):
            """Applies Highcharts style and sets scale to avoid clipping"""
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=False,  # Hide concentric circles
                        range=[0, max_value * 1.1]  # ADD 10% MARGIN
                    ),
                    angularaxis=dict(
                        direction="clockwise",
                        gridcolor="#eee", 
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

        # --- 1. HOURS (0h - 23h) ---
        with col1:
            st.markdown("**Meloz Hours**")
            
            # Data Preparation
            hours_counts = df["utc_time"].dt.hour.value_counts().reindex(range(24), fill_value=0).reset_index()
            hours_counts.columns = ["hour_num", "count"]
            
            # CRITICAL: Create TEXT column for display (0h, 1h...)
            hours_counts["label"] = hours_counts["hour_num"].astype(str) + "h"
            
            # Max for scale
            max_h = hours_counts["count"].max()

            fig_hours = px.bar_polar(
                hours_counts, 
                r="count", 
                theta="label", 
                start_angle=90, # 0h at top (Noon position logic in Plotly)
                direction="clockwise",
                color_discrete_sequence=[chart_color]
            )
            
            fig_hours = style_polar_chart(fig_hours, max_h)
            st.plotly_chart(fig_hours, use_container_width=True)

        # --- 2. DAYS (Monday - Sunday) ---
        with col2:
            st.markdown("**Meloz Days**")
            
            days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
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
                start_angle=90, # Monday at top
                direction="clockwise",
                color_discrete_sequence=[chart_color]
            )
            
            fig_days = style_polar_chart(fig_days, max_d)
            st.plotly_chart(fig_days, use_container_width=True)

        # --- 3. MONTHS (January - December) ---
        with col3:
            st.markdown("**Meloz Months**")
            
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
                start_angle=90, # January at top
                direction="clockwise",
                color_discrete_sequence=[chart_color]
            )
            
            fig_months = style_polar_chart(fig_months, max_m)
            st.plotly_chart(fig_months, use_container_width=True)
    
   # ========== TAB 5: ALBUMS ==========
    with tab5:
        st.header("Album Analysis")

        col_top_alb, col_week_alb = st.columns(2)

        with col_top_alb:
            st.subheader("🥇 Top Albums")
            st.caption("Most played albums in the selected period")
            
            # Plus de filtre local ici. On utilise directement 'df' qui est déjà filtré globalement.
            
            # Top 10 Calculation
            # GroupBy Artist + Album to avoid duplicates (e.g., "Greatest Hits" exists for many artists)
            top_albums = df.groupby(["artist", "album"]).size().reset_index(name="Plays")
            top_albums = top_albums.sort_values("Plays", ascending=False).head(10)
            
            # Formatting
            top_albums["Complete Album"] = top_albums["artist"] + " - " + top_albums["album"]
            display_top_alb = top_albums[["Complete Album", "Plays"]].reset_index(drop=True)
            display_top_alb.index += 1
            
            st.dataframe(display_top_alb, use_container_width=True)

        with col_week_alb:
            st.subheader("📅 Cult Albums")
            st.caption("Albums listened to across the most distinct weeks")
            
            # Longevity Calculation
            # Filter empty or unknown albums
            df_clean = df[df["album"].notna() & (df["album"] != "")]
            
            alb_longevity = df_clean.groupby(["artist", "album"])["week"].nunique().reset_index(name="Active Weeks")
            alb_longevity = alb_longevity.sort_values("Active Weeks", ascending=False).head(10)
            
            # Formatting
            alb_longevity["Complete Album"] = alb_longevity["artist"] + " - " + alb_longevity["album"]
            display_long_alb = alb_longevity[["Complete Album", "Active Weeks"]].reset_index(drop=True)
            display_long_alb.index += 1
            
            st.dataframe(display_long_alb, use_container_width=True)
            
        st.divider()

        # --- PART 2: TREEMAP (Artist > Album) ---
        st.subheader("🗺️ Your CD Library Map")
        st.caption("Albums with at least 2 distinct tracks, size represents play volume.")

        # 1. Basic Cleaning
        df_tree = df[df["album"].notna() & (df["album"] != "")].copy()
        
        # 2. ADVANCED CALCULATION: Count plays AND unique tracks per album
        tree_data = df_tree.groupby(["artist", "album"]).agg(
            plays=('track', 'count'),       # Total plays (square size)
            nb_tracks=('track', 'nunique')  # Number of different tracks (for filter)
        ).reset_index()
        
        # 3. "REAL ALBUM" FILTER: Keep only if more than 1 unique track
        tree_data = tree_data[tree_data["nb_tracks"] > 1]
        
        # 4. TOP 50 ARTISTS FILTER (Based on remaining albums)
        # Recalculate top 50 AFTER removing singles for relevant ranking
        top_artists_list = tree_data.groupby("artist")["plays"].sum().nlargest(20).index
        tree_data_final = tree_data[tree_data["artist"].isin(top_artists_list)]

        # Create Treemap
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
        
        # Improved Tooltip: display number of tracks
        fig_tree.update_traces(
            hovertemplate='<b>%{label}</b><br>Plays: %{value}<br>Tracks: %{customdata[0]}<extra></extra>',
            textinfo="label+value",
            customdata=tree_data_final[['nb_tracks']] # Pass nb_tracks column to tooltip
        )
        
        st.plotly_chart(fig_tree, use_container_width=True)
        
        st.divider()
        st.subheader("💿 Singles vs Full Albums")
        st.caption("Points on the right = Albums explored in depth and Points on the left = Singles on repeat.")

        # Calculation: For each album, total plays AND unique tracks
        df_integrity = df[df["album"].notna() & (df["album"] != "")]
        album_stats = df_integrity.groupby(["artist", "album"]).agg(
            total_plays=('track', 'count'),
            unique_tracks=('track', 'nunique')
        ).reset_index()

        # Filter "small" albums to avoid clutter (min 20 plays)
        album_stats = album_stats[album_stats["total_plays"] > 20]

        fig_scat_alb = px.scatter(
            album_stats,
            x="unique_tracks",
            y="total_plays",
            size="total_plays", # Bubble grows with plays
            color="unique_tracks", # Color by exploration depth
            hover_name="album",
            hover_data=["artist"],
            color_continuous_scale="Viridis",
            labels={"unique_tracks": "Unique tracks listened", "total_plays": "Total Plays"}
        )
        
        fig_scat_alb.update_layout(height=500)
        st.plotly_chart(fig_scat_alb, use_container_width=True)
    
    # ========== TAB 2: BAR CHART RACE ==========
    with tab2:
        st.header("🏁 Bar Chart Race")
        
        # Data Preparation
        if not pd.api.types.is_datetime64_any_dtype(df["utc_time"]):
             df["utc_time"] = pd.to_datetime(df["utc_time"], format="%d %b %Y, %H:%M")
        
        # === SPECIAL CHARACTERS CLEANING ===
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
        
        # === FORCED INTERNAL LOGIC ===
        # Force time step to "Month" for fluid animation
        df["period"] = df["utc_time"].dt.to_period("M")
        
        # Count plays by artist and period
        artist_plays = (
            df.groupby(['period', 'artist'])
            .size()
            .reset_index(name='plays')
        )
        
        # Create pivot table
        pivot_df = artist_plays.pivot(
            index='period',
            columns='artist',
            values='plays'
        ).fillna(0)
        
        # Convert index to datetime for bar_chart_race
        pivot_df.index = pivot_df.index.to_timestamp()
        
        # Calculate cumulative sum (Race to total)
        cumulative_df = pivot_df.cumsum()
        
        # Generate video
        cache_key = f"{st.session_state.utilisateur_selectionne}_race_10_{len(df)}"

        if 'video_cache' not in st.session_state:
            st.session_state.video_cache = {}
        
        if cache_key not in st.session_state.video_cache:
            with st.spinner("⏳ Generating animation... (Hold tight, this is heavy!)"):
                try:
                    # Safety check for small datasets
                    if len(cumulative_df) < 2:
                        st.warning("Not enough time periods to generate an animation. Please select a wider date range.")
                        video = None
                    else:
                        html_str = bcr.bar_chart_race(
                            df=cumulative_df,
                            filename=None,
                            n_bars=int(10), 
                            sort='desc',
                            title='Top Artists Evolution (Cumulative)',
                            period_length=1500, # Speed (ms per period)
                            steps_per_period=15, # Smoothness
                            figsize=(6, 3.5),
                            cmap='tab20',
                            bar_label_size=10,
                            tick_label_size=10,
                            period_label={'x': .98, 'y': .3, 'ha': 'right', 'va': 'center'},
                            period_fmt='%B %Y', # Month format
                            filter_column_colors=True
                        ).data
                        
                        # Extract video
                        start = html_str.find('base64,') + len('base64,')
                        end = html_str.find('">')
                        video = base64.b64decode(html_str[start:end])
                        
                        # Cache
                        st.session_state.video_cache[cache_key] = video
                        st.success("✅ Animation ready!")
                    
                except Exception as e:
                    st.error(f"❌ Technical error: {str(e)}")
                    video = None
        else:
            video = st.session_state.video_cache[cache_key]
        
        # Display video
        if video:
            st.video(video)