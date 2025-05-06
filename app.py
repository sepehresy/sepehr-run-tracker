import streamlit as st
import pandas as pd
from datetime import datetime
from views.summary import render_summary
from views.activities import render_activities
from views.ai_analysis import render_ai_analysis
from views.race_planning import render_race_planning
import requests
import json

# Set Streamlit app config
st.set_page_config(page_title="Sepehr's Running Dashboard", layout="wide")

# Load Google Sheet URL from secrets
sheet_url = st.secrets["gsheet_url"]

@st.cache_data(ttl=3600)
def load_data():
    df = pd.read_csv(sheet_url)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    return df

def load_gist_data():
    gist_id = st.secrets["gist_id"]
    filename = st.secrets["gist_filename"]
    url = f"https://gist.githubusercontent.com/{gist_id}/raw/{filename}"
    response = requests.get(url)
    if response.status_code == 200:
        return json.loads(response.text)
    return {}

def save_gist_data(data):
    gist_id = st.secrets["gist_id"]
    filename = st.secrets["gist_filename"]
    token = st.secrets["github_token"]
    url = f"https://api.github.com/gists/{gist_id}"
    headers = {"Authorization": f"token {token}"}
    payload = {"files": {filename: {"content": json.dumps(data, indent=2)}}}
    response = requests.patch(url, headers=headers, json=payload)
    return response.status_code == 200

# Load data and define reference date
df = load_data()
today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)

# Sidebar navigation
st.sidebar.title("📁 Dashboard View")
view = st.sidebar.radio("Navigate to:", ["📊 Summary", "📂 Activities", "🏁 Race Planning", "🧠 AI Analysis"])

# Render views based on selected section
if view == "📊 Summary":
    render_summary(df, today)

elif view == "📂 Activities":
    render_activities(df)

elif view == "🏁 Race Planning":
    render_race_planning(df, today)

elif view == "🧠 AI Analysis":
    render_ai_analysis(df, today)
