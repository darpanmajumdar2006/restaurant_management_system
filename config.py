import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv


# Try to find and load a .env file by walking upward from this file's folder.
def _load_env_upwards():
    start = Path(__file__).resolve().parent
    for parent in (start,) + tuple(start.parents):
        candidate = parent / '.env'
        if candidate.exists():
            load_dotenv(dotenv_path=str(candidate))
            return str(candidate)
    return None


# Load .env if present (local development)
_load_env_upwards()

# Detect Streamlit Cloud (if deployed there)
IS_CLOUD = os.getenv('STREAMLIT_SERVER_ADDRESS') is not None


def get_secret(name, default=None):
    """Return a secret value preferring Streamlit Cloud secrets when available.

    - On Streamlit Cloud: read from st.secrets (if set) then fallback to env var.
    - Locally: read from environment variables (loaded by python-dotenv if .env exists).
    """
    if IS_CLOUD:
        # st.secrets behaves like a mapping for values set in Streamlit Cloud
        try:
            # prefer st.secrets if present
            if name in st.secrets:
                return st.secrets[name]
        except Exception:
            # When st.secrets isn't available yet (rare), fallback to env
            pass
    return os.getenv(name, default)


# Database configuration: prefer DB_FILE from secrets/env; default to sqlite file locally
DB_FILE = get_secret('DB_FILE', ':memory:' if IS_CLOUD else 'restaurant.db')


def get_db():
    """Get database connection from session state or create new one"""
    if 'db' not in st.session_state:
        st.session_state.db = None
    return st.session_state.db


def set_db(conn):
    """Store database connection in session state"""
    st.session_state.db = conn