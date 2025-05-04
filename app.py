import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime

st.set_page_config(page_title="Running Dashboard", layout="wide")
st.title("🏃 Summary Statistics")

# Load data
sheet_url = st.secrets["gsheet_url"]
@st.cache_data(ttl=3600)
def load_data():
    df = pd.read_csv(sheet_url)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    return df

df = load_data()

# Total Distance (Grouped Weekly)
df['Week'] = df['Date'].dt.to_period("W").apply(lambda r: r.start_time)
weekly_km = df.groupby('Week')["Distance (km)"].sum().reset_index()

st.subheader("📊 Total Distance per Week")
chart = alt.Chart(weekly_km).mark_bar().encode(
    x=alt.X('Week:T', title='Week'),
    y=alt.Y('Distance (km):Q', title='Total Distance (km)'),
    tooltip=["Week", "Distance (km)"]
).properties(height=400)

st.altair_chart(chart, use_container_width=True)
