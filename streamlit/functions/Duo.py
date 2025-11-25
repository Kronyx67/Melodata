import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

def get_top_artists(df, max_user_share=0.8):
    # Compter le nombre d'écoutes par artiste et par utilisateur
    user_artist_counts = df.groupby(['artist', 'user']).size().unstack(fill_value=0)
    user1 = user_artist_counts.columns[0]
    user2 = user_artist_counts.columns[1]

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
    top_artists.columns = ['Artiste', 'Total écoutes']

    top_artists[f"% des écoutes de {user1}"] = 0.0

    # Calculer le total d'écoutes de user1
    total_user1 = df[df['user'] == user1].shape[0]

    for i, row in top_artists.iterrows():
        artist = row['Artiste']
        total = row['Total écoutes']
        count_user1 = user_artist_counts.loc[artist, user1]
        count_user2 = user_artist_counts.loc[artist, user2]
        top_artists.at[i, f"% des écoutes de {user1}"] = f"{int((count_user1 / total) * 100):.2f}%"

    return top_artists

def get_top_albums(df, max_user_share=0.8):
    # Filtrer les albums qui ont au moins 2 tracks différentes
    album_track_counts = df.groupby('album')['track'].nunique()
    valid_albums_by_tracks = album_track_counts[album_track_counts >= 2].index

    # Filtrer le DataFrame pour ne garder que les albums avec au moins 2 tracks
    filtered_df = df[df['album'].isin(valid_albums_by_tracks)]

    # Compter le nombre d'écoutes par album et par utilisateur
    user_album_counts = filtered_df.groupby(['album', 'user']).size().unstack(fill_value=0)
    user1 = user_album_counts.columns[0]
    user2 = user_album_counts.columns[1]

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
    top_albums.columns = ['Album', 'Total écoutes']

    # Ajouter la colonne pour l'artiste associé à chaque album
    top_albums['Artiste'] = top_albums['Album'].apply(
        lambda album: filtered_df[filtered_df['album'] == album]['artist'].iloc[0]
    )

    # Réorganiser les colonnes
    top_albums = top_albums[['Album', 'Artiste', 'Total écoutes']]

    # Ajouter la colonne pour le pourcentage d'écoutes de user1
    top_albums[f"% des écoutes de {user1}"] = 0.0

    for i, row in top_albums.iterrows():
        album = row['Album']
        total = row['Total écoutes']
        count_user1 = user_album_counts.loc[album, user1]

        # Calculer le pourcentage
        top_albums.at[i, f"% des écoutes de {user1}"] = f"{100 * count_user1 / total:.1f}%"

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
            "Artiste": artist,
            "Total écoutes": int(total),
            f"% {user1}": f"{100 * c1 / total:.1f}%",
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
                hovertemplate=f"%{{x|%d %b %Y}}<br>Total artistes uniques: %{{y}}<extra></extra>"
            )
        )

    # Mise en forme
    fig.update_layout(
        title="Évolution du nombre cumulé d'artistes uniques écoutés par utilisateur",
        xaxis_title="Date",
        yaxis_title="Nombre cumulé d'artistes uniques",
        hovermode="x unified",
        template="plotly_white"
    )

    return fig

import pandas as pd
import plotly.graph_objects as go

def get_total_and_unique_tracks_plot(df):
    # Conversion date
    df['date'] = pd.to_datetime(df['utc_time']).dt.date

    # --- 1) CUMUL TOTAL D'ÉCOUTES ---
    total_counts = (
        df.groupby(['user', 'date'])
        .size()
        .groupby(level='user')
        .cumsum()
        .reset_index(name='cumulative_total_listens')
    )

    # --- 2) CUMUL TRACKS UNIQUES ---
    df_unique = df.drop_duplicates(subset=['user', 'artist', 'track'])
    unique_counts = (
        df_unique.groupby(['user', 'date'])
        .size()
        .groupby(level='user')
        .cumsum()
        .reset_index(name='cumulative_unique_tracks')
    )

    # --- 3) Fusion des deux ---
    merged = pd.merge(
        total_counts,
        unique_counts,
        on=['user', 'date'],
        how='outer'
    ).sort_values(['user', 'date']).fillna(method='ffill')

    # --- 4) Graphique à double axe ---
    fig = go.Figure()

    users = merged['user'].unique()

    # Couleurs cohérentes (1 couleur / user)
    base_colors = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd"]

    for i, user in enumerate(users):
        user_data = merged[merged['user'] == user]

        # Ligne 1 : total listens (axe Y1)
        fig.add_trace(
            go.Scatter(
                x=user_data['date'],
                y=user_data['cumulative_total_listens'],
                mode="lines",
                name=f"{user} - Total écoutes",
                line=dict(color=base_colors[i], width=2),
                hovertemplate="%{x|%d %b %Y}<br>Total écoutes: %{y}<extra></extra>",
                yaxis="y1"
            )
        )

        # Ligne 2 : unique tracks (axe Y2)
        fig.add_trace(
            go.Scatter(
                x=user_data['date'],
                y=user_data['cumulative_unique_tracks'],
                mode="lines",
                name=f"{user} - Tracks uniques",
                line=dict(color=base_colors[i], width=2, dash="dash"),
                hovertemplate="%{x|%d %b %Y}<br>Tracks uniques: %{y}<extra></extra>",
                yaxis="y2"
            )
        )

    # --- 5) Mise en forme ---
    fig.update_layout(
        title="Évolution des écoutes totales vs tracks uniques par utilisateur",
        xaxis_title="Date",
        yaxis=dict(
            title="Total écoutes",
            side="left"
        ),
        yaxis2=dict(
            title="Tracks uniques",
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
        title="Top 10 des artistes les plus écoutés par utilisateur",
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
