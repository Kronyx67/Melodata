import streamlit as st
import os
import pandas as pd
import time

def compute_folder_signature(folder):
    sig = []
    for file in os.listdir(folder):
        if file.endswith(".csv"):
            filepath = os.path.join(folder, file)
            sig.append((file, os.path.getmtime(filepath)))
    return tuple(sig)

@st.cache_data
def load_csv_folder(folder, signature):
    dfs = {}
    for file in os.listdir(folder):
        if file.endswith(".csv"):
            dfs[file] = pd.read_csv(os.path.join(folder, file))
    return dfs

def load_csv_folder_with_cache(folder):
    signature = compute_folder_signature(folder)
    return load_csv_folder(folder, signature)

@st.cache_data
def load_csv_file(filepath, cache_bust):
    return pd.read_csv(filepath)

def load_file_with_cache(filepath):
    cache_bust = time.time()  # Force instantanément l’invalidation
    return load_csv_file(filepath, cache_bust)
