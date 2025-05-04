import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

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
today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)

# View toggle
view = st.radio(
    "Select View",
    ["Weekly", "4 Weeks", "3 Months", "6 Months", "1 Year", "All Months", "All Yearly"],
    horizontal=True
)

if view == "Weekly":
    start = today - timedelta(days=today.weekday())  # Monday
    days = [start + timedelta(days=i) for i in range(7)]
    df_week = df[df["Date"].between(start, start + timedelta(days=6))].copy()
    df_week["Day"] = df_week["Date"].dt.strftime("%a")
    daily_km = df_week.groupby("Day")["Distance (km)"].sum()
    full_week = pd.DataFrame({"Day": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]})
    full_week["Distance (km)"] = full_week["Day"].map(daily_km).fillna(0)
    chart = alt.Chart(full_week).mark_bar(size=60).encode(
        x=alt.X("Day:N", title="Day", sort=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]),
        y=alt.Y("Distance (km):Q", title="Distance (km)"),
        tooltip=["Day", "Distance (km)"]
    ).properties(height=400)

elif view == "4 Weeks":
    start = today - timedelta(weeks=4)
    df_month = df[df["Date"] >= start].copy()
    df_month["Week"] = df_month["Date"].dt.to_period("W").apply(lambda r: r.start_time)
    weekly_km = df_month.groupby("Week")["Distance (km)"].sum().reset_index()
    chart = alt.Chart(weekly_km).mark_bar(size=40).encode(
        x=alt.X("Week:T", title="Week"),
        y=alt.Y("Distance (km):Q", title="Distance (km)"),
        tooltip=["Week", "Distance (km)"]
    ).properties(height=400)

elif view == "3 Months":
    start = today - relativedelta(months=3)
    df_qtr = df[df["Date"] >= start].copy()
    df_qtr["Week"] = df_qtr["Date"].dt.to_period("W").apply(lambda r: r.start_time)
    weekly_km = df_qtr.groupby("Week")["Distance (km)"].sum().reset_index()
    chart = alt.Chart(weekly_km).mark_bar(size=10).encode(
        x=alt.X("Week:T", title="Week"),
        y=alt.Y("Distance (km):Q", title="Distance (km)"),
        tooltip=["Week", "Distance (km)"]
    ).properties(height=400)

elif view == "6 Months":
    start = today - relativedelta(months=6)
    df_half = df[df["Date"] >= start].copy()
    df_half["Week"] = df_half["Date"].dt.to_period("W").apply(lambda r: r.start_time)
    weekly_km = df_half.groupby("Week")["Distance (km)"].sum().reset_index()
    chart = alt.Chart(weekly_km).mark_bar(size=8).encode(
        x=alt.X("Week:T", title="Week"),
        y=alt.Y("Distance (km):Q", title="Distance (km)"),
        tooltip=["Week", "Distance (km)"]
    ).properties(height=400)

elif view == "1 Year":
    start = today - relativedelta(years=1)
    df_year = df[df["Date"] >= start].copy()
    df_year["Month"] = df_year["Date"].dt.to_period("M").apply(lambda r: r.start_time)
    monthly_km = df_year.groupby("Month")["Distance (km)"].sum().reset_index()
    chart = alt.Chart(monthly_km).mark_bar(size=20).encode(
        x=alt.X("Month:T", title="Month"),
        y=alt.Y("Distance (km):Q", title="Distance (km)"),
        tooltip=["Month", "Distance (km)"]
    ).properties(height=400)

elif view == "All Months":
    df["Month"] = df["Date"].dt.to_period("M").apply(lambda r: r.start_time)
    monthly_km = df.groupby("Month")["Distance (km)"].sum().reset_index()
    chart = alt.Chart(monthly_km).mark_bar(size=10).encode(
        x=alt.X("Month:T", title="Month"),
        y=alt.Y("Distance (km):Q", title="Distance (km)"),
        tooltip=["Month", "Distance (km)"]
    ).properties(height=400)

else:  # All Yearly
    df["Year"] = df["Date"].dt.to_period("Y").apply(lambda r: r.start_time)
    yearly_km = df.groupby("Year")["Distance (km)"].sum().reset_index()
    chart = alt.Chart(yearly_km).mark_bar(size=30).encode(
        x=alt.X("Year:T", title="Year"),
        y=alt.Y("Distance (km):Q", title="Distance (km)"),
        tooltip=["Year", "Distance (km)"]
    ).properties(height=400)

st.altair_chart(chart, use_container_width=True)
