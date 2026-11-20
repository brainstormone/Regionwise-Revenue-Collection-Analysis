"""
Data Loader & SQLite Caching Module
Provides performant database queries cached with st.cache_data.
"""

import os
import sqlite3
import pandas as pd
import streamlit as st
from typing import Optional
from src.data.cleaner import clean_sales_data

# Resolve standard path to app.db
DEFAULT_DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "app.db")
)


def get_db_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Creates a connection to SQLite database with foreign keys enabled."""
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found at expected path: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@st.cache_data(show_spinner=False)
def load_analysis_data(db_path: str = DEFAULT_DB_PATH) -> pd.DataFrame:
    """
    Loads and cleans the 36-column materialized semantic view 'view_sales_analysis'
    with Streamlit caching for sub-100ms multi-page query response.
    
    Args:
        db_path: Absolute or relative path to app.db
        
    Returns:
        Cleaned, deduplicated, and typed pandas DataFrame
    """
    conn = get_db_connection(db_path)
    query = "SELECT * FROM view_sales_analysis;"
    df = pd.read_sql_query(query, conn)
    conn.close()

    # Parse order_date to datetime
    if "order_date" in df.columns:
        df["order_date"] = pd.to_datetime(df["order_date"])

    # Apply data cleaning and deduplication
    cleaned_df = clean_sales_data(df)
    return cleaned_df


@st.cache_data(show_spinner=False)
def load_table(table_name: str, db_path: str = DEFAULT_DB_PATH) -> pd.DataFrame:
    """Loads any specific table or view from SQLite database."""
    conn = get_db_connection(db_path)
    query = f"SELECT * FROM {table_name};"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df
