import os
import streamlit as st

# Check if we're running on Streamlit Cloud
IS_CLOUD = os.getenv('STREAMLIT_SERVER_ADDRESS') is not None

# Database configuration
DB_FILE = ':memory:' if IS_CLOUD else 'restaurant.db'

def get_db():
    """Get database connection from session state or create new one"""
    if 'db' not in st.session_state:
        st.session_state.db = None
    return st.session_state.db

def set_db(conn):
    """Store database connection in session state"""
    st.session_state.db = conn