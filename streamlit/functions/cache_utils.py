import streamlit as st
import os
import pandas as pd

@st.cache_data
def load_csv_folder(folder):
    dfs = {}
    for file in os.listdir(folder):
        if file.endswith(".csv"):
            dfs[file] = pd.read_csv(os.path.join(folder, file))
    return dfs
