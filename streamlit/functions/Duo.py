import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

def get_top_artists(df, max_user_share=0.8):
    # Compter le nombre d'écoutes par artiste et par utilisateur
    user_artist_counts = df.groupby(['artist', 'user']).size().unstack(fill_value=0)
    user1, user2 = df['user'].unique()

    # Calculer le nombre total d'écoutes par artiste
    artist_totals = user_artist_counts.sum(axis=1)

    # Filtrer les artistes où un seul utilisateur a plus de 80% des écoutes
    valid_artists = []
    for artist in user_artist_counts.index:
        user_shares = user_artist_counts.loc[artist] / artist_totals[artist]
        if (user_shares <= max_user_share).all():
            valid_artists.append(artist)

    # Filtrer le DataFrame pour ne garder que les artistes valides
    filtered_df = df[df['artist'].isin(valid_artists)]

    # Compter le nombre total d'écoutes par artiste (valides)
    artist_counts = filtered_df['artist'].value_counts()

    # Préparer un DataFrame pour le Top 5 avec les proportions
    top_artists = artist_counts.head(5).reset_index()
    top_artists.index = top_artists.index + 1  
    top_artists.columns = ['Artist', 'Total Meloz']

    top_artists[f"% of {user1}'s Meloz"] = 0.0

    # Calculer le total d'écoutes de user1
    total_user1 = df[df['user'] == user1].shape[0]

    for i, row in top_artists.iterrows():
        artist = row['Artist']
        total = row['Total Meloz']
        count_user1 = user_artist_counts.loc[artist, user1]
        count_user2 = user_artist_counts.loc[artist, user2]
        top_artists.at[i, f"% of {user1}'s Meloz"] = f"{int((count_user1 / total) * 100)}%"
    return top_artists

def get_top_albums(df, max_user_share=0.8):
    # Filtrer les albums qui ont au moins 2 tracks différentes
    album_track_counts = df.groupby('album')['track'].nunique()
    valid_albums_by_tracks = album_track_counts[album_track_counts >= 2].index

    # Filtrer le DataFrame pour ne garder que les albums avec au moins 2 tracks
    filtered_df = df[df['album'].isin(valid_albums_by_tracks)]

    # Compter le nombre d'écoutes par album et par utilisateur
    user_album_counts = filtered_df.groupby(['album', 'user']).size().unstack(fill_value=0)
    user1, user2 = df['user'].unique()

    # Calculer le nombre total d'écoutes par album
    album_totals = user_album_counts.sum(axis=1)

    # Filtrer les albums où un seul utilisateur a plus de max_user_share des écoutes
    valid_albums = []
    for album in user_album_counts.index:
        user_shares = user_album_counts.loc[album] / album_totals[album]
        if (user_shares <= max_user_share).all():
            valid_albums.append(album)

    # Filtrer le DataFrame pour ne garder que les albums valides
    filtered_df = filtered_df[filtered_df['album'].isin(valid_albums)]

    # Compter le nombre total d'écoutes par album (valides)
    album_counts = filtered_df['album'].value_counts()

    # Préparer un DataFrame pour le Top 5 avec les proportions
    top_albums = album_counts.head(5).reset_index()
    top_albums.index = top_albums.index + 1
    top_albums.columns = ['Album', 'Total Meloz']

    # Ajouter la colonne pour l'artiste associé à chaque album
    top_albums['Artist'] = top_albums['Album'].apply(
        lambda album: filtered_df[filtered_df['album'] == album]['artist'].iloc[0]
    )

    # Réorganiser les colonnes
    top_albums = top_albums[['Album', 'Artist', 'Total Meloz']]

    # Ajouter la colonne pour le pourcentage d'écoutes de user1
    top_albums[f"% of {user1}'s Meloz"] = 0.0

    for i, row in top_albums.iterrows():
        album = row['Album']
        total = row['Total Meloz']
        count_user1 = user_album_counts.loc[album, user1]

        # Calculer le pourcentage
        top_albums.at[i, f"% of {user1}'s Meloz"] = f"{int((count_user1 / total) * 100)}%"
    return top_albums

def get_top_tracks(df, max_user_share=0.8, top_n=5):
    user1, user2 = df['user'].unique()

    # Combinaison unique : (artist, track)
    df['track_key'] = df['artist'] + " — " + df['track']

    # Compter écoutes par track_key et par user
    user_track = df.groupby(['track_key', 'user']).size().unstack(fill_value=0)

    # Totaux par track_key
    totals = user_track.sum(axis=1)

    # Tracks communes
    mask_common = (user_track[user1] > 0) & (user_track[user2] > 0)

    # Pourcentages
    shares = user_track.div(totals, axis=0)

    # Filtre 80%
    mask_share = (shares[user1] <= max_user_share) & (shares[user2] <= max_user_share)

    # Tracks valides
    valid = user_track.index[mask_common & mask_share]

    # Top N
    top = totals.loc[valid].sort_values(ascending=False).head(top_n)

    # Construction du résultat
    rows = []
    for key, total in top.items():
        artist, track = key.split(" — ", 1)
        c1 = user_track.loc[key, user1]

        rows.append({
            "Track": track,
            "Artist": artist,
            "Total Meloz": int(total),
            f"% of {user1}'s Meloz": f"{int((c1 / total) * 100)}%"
        })

    result = pd.DataFrame(rows)
    result.index = range(1, len(result) + 1)
    return result


def get_cumulative_unique_artists_plot(df):
    # Conversion de la colonne utc_time en date
    df['date'] = pd.to_datetime(df['utc_time']).dt.date

    # On garde uniquement la première occurrence de chaque artiste par utilisateur (pour éviter les doublons)
    df_unique = df.drop_duplicates(subset=['user', 'artist'])

    # On trie par utilisateur et par date
    df_unique = df_unique.sort_values(by=['user', 'date'])

    # On calcule le nombre cumulé d'artistes uniques par utilisateur et par date
    cumulative_counts = (
        df_unique.groupby(['user', 'date'])
        .size()
        .groupby(level='user')
        .cumsum()
        .reset_index(name='cumulative_unique_artists')
    )

    # Création du graphique Plotly
    fig = go.Figure()
    for user in cumulative_counts['user'].unique():
        user_data = cumulative_counts[cumulative_counts['user'] == user]
        fig.add_trace(
            go.Scatter(
                x=user_data['date'],
                y=user_data['cumulative_unique_artists'],
                mode='lines+markers',
                name=user,
                hovertemplate=f"%{{x|%d %b %Y}}<br>Total unique artists: %{{y}}<extra></extra>"
            )
        )

    # Mise en forme
    fig.update_layout(
        title="Unique Artists Listened Over Time by User",
        xaxis_title="Date",
        yaxis_title="Cumulative Number of Unique Artists",
        hovermode="x unified",
        template="plotly_white"
    )

    return fig

def get_total_and_unique_tracks_plot(df):
    # --- 0) Préparer la colonne date ---
    df['date'] = pd.to_datetime(df['utc_time']).dt.date

    users = df['user'].unique()
    all_dates = sorted(df['date'].unique())

    # --- 1) Total d'écoutes cumulées ---
    total_counts = (
        df.groupby(['user', 'date'])
        .size()
        .reset_index(name='cumulative_total_listens')
    )

    # Créer full index user x date pour total écoutes
    full_index_total = pd.MultiIndex.from_product([users, all_dates], names=['user', 'date'])
    total_counts = pd.DataFrame(index=full_index_total).reset_index().merge(
        total_counts, on=['user', 'date'], how='left'
    ).fillna(0)
    total_counts['cumulative_total_listens'] = total_counts.groupby('user')['cumulative_total_listens'].cumsum()

    # --- 2) Tracks uniques cumulées ---
    df_unique = df.drop_duplicates(subset=['user', 'artist', 'track'])
    unique_counts = (
        df_unique.groupby(['user', 'date'])
        .size()
        .reset_index(name='cumulative_unique_tracks')
    )

    # Créer full index user x date pour unique tracks
    full_index_unique = pd.MultiIndex.from_product([users, all_dates], names=['user', 'date'])
    cumulative_unique = pd.DataFrame(index=full_index_unique).reset_index().merge(
        unique_counts, on=['user', 'date'], how='left'
    ).fillna(0)
    cumulative_unique['cumulative_unique_tracks'] = cumulative_unique.groupby('user')['cumulative_unique_tracks'].cumsum()

    # --- 3) Fusionner total et unique tracks ---
    merged = pd.merge(
        total_counts,
        cumulative_unique,
        on=['user', 'date'],
        how='outer'
    ).sort_values(['user', 'date'])

    # --- 4) Création du graphique ---
    fig = go.Figure()
    base_colors = ["#d62728","#1f77b4", "#2ca02c", "#9467bd"]

    for i, user in enumerate(users):
        user_data = merged[merged['user'] == user]

        # Ligne 1 : total listens (axe Y1)
        fig.add_trace(
            go.Scatter(
                x=user_data['date'],
                y=user_data['cumulative_total_listens'],
                mode="lines",
                name=f"{user} - Total Meloz",
                line=dict(color=base_colors[i], width=2),
                hovertemplate="%{x|%d %b %Y}<br>Total Meloz: %{y}<extra></extra>",
                yaxis="y1"
            )
        )

        # Ligne 2 : unique tracks (axe Y2)
        fig.add_trace(
            go.Scatter(
                x=user_data['date'],
                y=user_data['cumulative_unique_tracks'],
                mode="lines",
                name=f"{user} - Unique Tracks",
                line=dict(color=base_colors[i], width=2, dash="dash"),
                hovertemplate="%{x|%d %b %Y}<br>Unique Tracks: %{y}<extra></extra>",
                yaxis="y2"
            )
        )

    # --- 5) Mise en forme ---
    fig.update_layout(
        title="Evolution of Total Listens and Unique Tracks Over Time",
        xaxis_title="Date",
        yaxis=dict(
            title="Total Meloz",
            side="left"
        ),
        yaxis2=dict(
            title="Unique Tracks",
            overlaying="y",
            side="right"
        ),
        hovermode="x unified",
        template="plotly_white",
        legend=dict(x=0.01, y=0.99)
    )

    return fig


def get_top_artists_treemap(df):
    # Compter le nombre d'écoutes par artiste et par utilisateur
    artist_counts = df.groupby(['user', 'artist']).size().reset_index(name='counts')

    # Garder uniquement le top 10 pour chaque utilisateur
    top_artists = (
        artist_counts.sort_values(['user', 'counts'], ascending=[True, False])
        .groupby('user')
        .head(10)
    )

    # Création du treemap
    fig = px.treemap(
        top_artists,
        path=['user', 'artist'],
        values='counts',
        title="Top 10 Most Played Artists by User",
        color='counts',
        color_continuous_scale='Viridis',
    )

    fig.update_traces(
        marker=dict(line=dict(width=0.5, color='white')),  # Bordures des feuilles en blanc
        texttemplate="%{label}<br>%{value} écoutes",
        hovertemplate="%{label}<br>%{value} écoutes<extra></extra>",
    )

    # Personnalisation du layout
    fig.update_layout(
        uniformtext=dict(minsize=10),
        margin=dict(t=50, l=0, r=0, b=0),
        plot_bgcolor='white',
        paper_bgcolor='white',
    )

    return fig

def display_album_comparison(df, max_user_share=0.8):
    """
    Affiche les graphiques de comparaison d'albums pour 2 utilisateurs.
    Filtres appliqués :
    1. Albums avec au moins 2 titres différents (pas de singles).
    2. Intersection stricte (écouté par les deux).
    3. Équilibre des écoutes (max_user_share) : Personne ne doit "posséder" l'album à plus de 80%.
    """
    
    # Vérification : on a besoin de 2 utilisateurs
    users = df['user'].unique()
    if len(users) != 2:
        st.warning("⚠️ Please select exactly 2 users to compare albums.")
        return

    user1, user2 = users[0], users[1]
    
    # --- 1. PRÉPARATION DES DONNÉES ---
    
    # A. Filtre "Vrais Albums" (Au moins 2 titres différents)
    alb_track_counts = df.groupby('album')['track'].nunique()
    valid_albs_indices = alb_track_counts[alb_track_counts >= 2].index
    
    df_duo = df[df['album'].isin(valid_albs_indices)].copy()

    # B. Pivot : Matrice [Album x User]
    pivot_albums = df_duo.groupby(['album', 'artist', 'user']).size().unstack(fill_value=0).reset_index()
    
    # Sécurité colonnes
    if user1 not in pivot_albums.columns: pivot_albums[user1] = 0
    if user2 not in pivot_albums.columns: pivot_albums[user2] = 0

    # C. FILTRE INTERSECTION STRICTE
    # On ne garde que si les deux ont écouté au moins une fois
    pivot_albums = pivot_albums[
        (pivot_albums[user1] > 0) & 
        (pivot_albums[user2] > 0)
    ]

    # D. Calcul du Total
    pivot_albums['total'] = pivot_albums[user1] + pivot_albums[user2]
    
    # E. FILTRE DE PARTAGE (max_user_share)
    # On vérifie que personne n'a plus de X% des écoutes totales
    # Ex: Si User1=90 et User2=10 (Total 100), Share1 = 0.9. Si max=0.8, on exclut.
    pivot_albums['share_u1'] = pivot_albums[user1] / pivot_albums['total']
    pivot_albums['share_u2'] = pivot_albums[user2] / pivot_albums['total']
    
    pivot_albums = pivot_albums[
        (pivot_albums['share_u1'] <= max_user_share) & 
        (pivot_albums['share_u2'] <= max_user_share)
    ]
    
    if pivot_albums.empty:
        st.info(f"No truly shared albums found (where both users contribute > {int((1-max_user_share)*100)}%).")
        return

    # --- 2. GRAPHIQUE 1 : SCATTER PLOT (Common Ground) ---
    st.subheader("🗺️ Common Ground Landscape")
    st.caption(f"Strictly shared albums (Balance < {int(max_user_share*100)}%), diagonal = Perfect match.")

    # On utilise share_u2 comme ratio pour la couleur (0=User1 dominant, 1=User2 dominant)
    # Puisqu'on a filtré, le ratio sera forcément entre 0.2 et 0.8 (pour max=0.8)
    
    fig_scatter = px.scatter(
        pivot_albums,
        x=user1,
        y=user2,
        hover_name="album",
        hover_data={"artist": True, "total": True, "share_u1": False, "share_u2": False},
        color="share_u2",
        color_continuous_scale="RdBu", # Rouge (User1) <-> Bleu (User2)
        size="total", 
        size_max=40,
        title=f"Shared Albums: {user1} vs {user2}"
    )

    # Ligne diagonale
    max_val = pivot_albums[['total']].max().max()
    fig_scatter.add_shape(
        type="line", line=dict(dash="dash", color="gray", width=1),
        x0=0, y0=0, x1=max_val, y1=max_val
    )

    fig_scatter.update_layout(
        xaxis_title=f"{user1} Meloz",
        yaxis_title=f"{user2} Meloz",
        coloraxis_showscale=False,
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=500
    )
    
    st.plotly_chart(fig_scatter, use_container_width=True)

    st.divider()

    # --- 3. GRAPHIQUE 2 : TUG OF WAR (Top Shared Albums) ---
    st.subheader(f"⚔️ Tug of War (Top Shared)")
    st.caption(
            "This chart compares the listening volume of your two top users on the most shared albums, "
            "bars to the left show plays for one user, bars to the right show plays for the other, "
            "highlighting who dominates each album."
        )

    # On prend les 15 plus gros albums communs restants après filtrage
    top_shared = pivot_albums.sort_values('total', ascending=False).head(15)
    top_shared = top_shared.iloc[::-1]
    
    fig_tug = go.Figure()

    # Barres User 1 (Vers la gauche)
    fig_tug.add_trace(go.Bar(
        y=top_shared["album"] + " - " + top_shared["artist"],
        x=-top_shared[user1], 
        name=user1,
        orientation='h',
        marker_color='#FF4B4B',
        customdata=top_shared[user1],
        hovertemplate=f"<b>{user1}</b>: %{{customdata}} meloz<extra></extra>"
    ))

    # Barres User 2 (Vers la droite)
    fig_tug.add_trace(go.Bar(
        y=top_shared["album"] + " - " + top_shared["artist"],
        x=top_shared[user2],
        name=user2,
        orientation='h',
        marker_color='#4B4BFF',
        hovertemplate=f"<b>{user2}</b>: %{{x}} meloz<extra></extra>"
    ))

    # Bornes dynamiques
    max_x = max(top_shared[user1].max(), top_shared[user2].max()) * 1.1

    fig_tug.update_layout(
        barmode='overlay',
        title="Listening Balance",
        xaxis=dict(
            title="Volume of Meloz",
            range=[-max_x, max_x],
            tickmode='array',
            tickvals=[-100, -50, 0, 50, 100], 
            ticktext=['100', '50', '0', '50', '100'],
            showgrid=False
        ),
        yaxis=dict(showgrid=False),
        plot_bgcolor='white',
        paper_bgcolor="white",
        legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"),
        height=600
    )
    
    st.plotly_chart(fig_tug, use_container_width=True)