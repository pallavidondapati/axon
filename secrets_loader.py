# secrets_loader.py
import os

try:
    import streamlit as st
    if hasattr(st, 'secrets') and len(st.secrets) > 0:
        for key, val in st.secrets.items():
            os.environ[key] = str(val)
except Exception:
    pass  # local dev uses .env file