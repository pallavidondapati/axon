# secrets_loader.py
import os
try:
    import streamlit as st
    for key, val in st.secrets.items():
        os.environ[key] = str(val)
except Exception:
    pass