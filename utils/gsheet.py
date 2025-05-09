import pandas as pd
import streamlit as st
import requests

def fetch_gsheet_plan(url):
    try:
        df = pd.read_csv(url)
        # Expect columns: Week, Start Date, Status, Monday, ..., Sunday, Comment
        required_cols = {"Week", "Start Date", "Status", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "Comment"}
        if not required_cols.issubset(set(df.columns)):
            st.error("Google Sheet is missing required columns. Please use the provided template.")
            return None
        return df
    except Exception as e:
        st.error(f"Failed to fetch or parse Google Sheet: {e}")
        return None
