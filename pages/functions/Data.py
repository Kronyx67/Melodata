import os
import requests
import pandas as pd
import csv
import time
from pprint import pprint
import streamlit as st
from .cache_utils import load_csv_file, load_file_with_cache, load_csv_folder_with_cache
import time

api_key = "ea311d73665c24b237160f90bcb986ff"

def update_data(username, progress_callback=None):
    """
    Met à jour les données d'un utilisateur.
    progress_callback(percent) sera appelé à chaque page si fourni.
    """
    if username is None:
        return "No user selected"
    
    project_root = os.getcwd()
    data_dir = os.path.join(project_root, "data")
    data_temp_dir = os.path.join(project_root, "pages","functions","data_temp")
    
    if not os.path.exists(data_temp_dir):
        os.makedirs(data_temp_dir, exist_ok=True)

    if not os.path.exists(os.path.join(data_dir, f"{username}.csv")):
        user_file = os.path.join(data_dir, f"{username}.csv")
        with open(user_file, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Colonnes obligatoires pour le reste du code
            writer.writerow(["uts", "utc_time", "artist", "artist_mbid",
                             "album", "album_mbid", "track", "track_mbid"])
        max_timestamp = 0
    
    else: 
        df = pd.read_csv(os.path.join(data_dir, f"{username}.csv"))
        max_timestamp = df['uts'].max() + 1

    # Nombre total de tracks
    url_info = f"http://ws.audioscrobbler.com/2.0/?method=user.getInfo&user={username}&api_key={api_key}&format=json"
    response = requests.get(url_info)
    if response.status_code == 200:
        data = response.json()
        playcount = int(data["user"]["playcount"])
    elif response.status_code == 404:
        os.remove(os.path.join(data_dir, f"{username}.csv"))
        return
    else:
        return f"Erreur : {response.status_code}"
   

    method = "user.getrecenttracks"
    limit = 200
    total_pages = int(playcount / limit) + 1
    all_tracks = []
    page = 1

    while page <= total_pages:
        url_page = f"http://ws.audioscrobbler.com/2.0/?method={method}&limit={limit}&user={username}&page={page}&from={max_timestamp}&api_key={api_key}&format=json"
        response = requests.get(url_page)
        if response.status_code == 200:
            data = response.json()
            tracks = data['recenttracks']['track']
            all_tracks.extend(tracks)
            total_pages = int(data['recenttracks']['@attr']['totalPages'])

            # Appel du callback pour la progress bar
            if total_pages > 0 and progress_callback:
                percent = min(int((page / total_pages) * 100), 100)
                progress_callback(percent)

            page += 1
            time.sleep(0.5)
        else:
            return f"Erreur à la page {page} : {response.status_code}"

    # Écriture CSV temporaire
    output_file = os.path.join(data_temp_dir, "data_temp.csv")
    with open(output_file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["uts", "utc_time", "artist", "artist_mbid", "album", "album_mbid", "track", "track_mbid"])
        for track in all_tracks:
            nowplaying = track.get('@attr', {}).get('nowplaying', 'false')
            if nowplaying.lower() == 'true':
                continue
            date_info = track.get("date", {})
            uts = date_info.get("uts", "")
            utc_time = date_info.get("#text", "")
            artist_name = track["artist"].get("#text", "")
            artist_mbid = track["artist"].get("mbid", "")
            album_name = track["album"].get("#text", "")
            album_mbid = track["album"].get("mbid", "")
            track_name = track.get("name", "")
            track_mbid = track.get("mbid", "")
            writer.writerow([uts, utc_time, artist_name, artist_mbid, album_name, album_mbid, track_name, track_mbid])

    # Fusion avec ancien CSV
    new_df = pd.read_csv(output_file)
    old_df = pd.read_csv(os.path.join(data_dir, f"{username}.csv"))
    combined_df = pd.concat([new_df, old_df]).drop_duplicates().reset_index(drop=True)
    combined_df.to_csv(os.path.join(data_dir, f"{username}.csv"), index=False)
    ##Supression du cache pour forcer le rechargement
    updated_df = load_file_with_cache(os.path.join(data_dir, f"{username}.csv"))
    st.session_state["data"][f"{username}.csv"] = updated_df
    return f"Update finished : {len(all_tracks)} Meloz retrieved !"

def update_data_spin(username):
    """
    Affiche le spinner et la barre de progression pendant update_data,
    sans texte additionnel dans le spinner.
    """
    progress_bar = st.progress(0)
    loading_text = st.markdown(
        """
        <div style="display:flex; justify-content:center; align-items:center; height:50px;">
            <p style="font-size:20px; font-weight:bold;">Data updating...</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Callback pour mettre à jour la barre
    def progress_callback(percent):
        progress_bar.progress(percent)

    # Appel de la fonction pure, sans texte dans le spinner
    with st.spinner(" "):  # juste un espace pour ne rien afficher
        result = update_data(username, progress_callback=progress_callback)

    # Nettoyage
    progress_bar.empty()
    loading_text.empty()

    if result is not None:
        st.success(result)
        
    time.sleep(5)
    
    st.session_state.data = load_csv_folder_with_cache("data")
    st.rerun()