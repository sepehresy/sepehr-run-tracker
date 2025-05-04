import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Sepehr's Running Dashboard", layout="wide")
st.title("🏃 Sepehr's Running Dashboard")

# Load Google Sheet data
sheet_url = st.secrets["gsheet_url"]
@st.cache_data(ttl=3600)
def load_data():
    return pd.read_csv(sheet_url)

df = load_data()

# Summary Stats
st.subheader("📈 Summary Statistics")
col1, col2, col3 = st.columns(3)
col1.metric("Total Distance", f"{df['Distance (km)'].sum():.1f} km")
col2.metric("Avg Pace", f"{df['Pace (min/km)'].mean():.2f} min/km")
col3.metric("Avg Heart Rate", f"{df['Avg HR'].mean():.0f} bpm")

# Weekly KM Chart
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
df['Week'] = df['Date'].dt.to_period('W').apply(lambda r: r.start_time)
weekly_km = df.groupby('Week')['Distance (km)'].sum().reset_index()
chart = alt.Chart(weekly_km).mark_bar().encode(
    x='Week:T',
    y='Distance (km):Q'
).properties(title="Weekly Kilometers")
st.altair_chart(chart, use_container_width=True)

# Per-run Selector
st.subheader("📋 Per-Run Analysis")
run_names = df['Name'].tolist()
selected = st.selectbox("Select a run", run_names)
run = df[df['Name'] == selected].iloc[0]
st.write(f"**Date**: {run['Date']}")
st.write(f"**Distance**: {run['Distance (km)']} km")
st.write(f"**Pace**: {run['Pace (min/km)']} min/km")
st.write(f"**Heart Rate**: {run['Avg HR']} bpm")

# Countdown to race
from datetime import datetime
race_day = datetime(2025, 5, 24)
today = datetime.today()
days_left = (race_day - today).days
st.markdown(f"### 🗓️ {days_left} days left until race day (May 24, 2025)")
# Streamlit app placeholder
