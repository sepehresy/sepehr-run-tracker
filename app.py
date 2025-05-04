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

# Chart style toggle
chart_style = st.selectbox(
    "Chart Style",
    ["Bar", "Line", "Dots", "Area", "Line + Dots"],
    index=0
)

# Handle views
if view == "Weekly":
    start = today - timedelta(days=today.weekday())  # Monday
    days = [start + timedelta(days=i) for i in range(7)]
    df_week = df[df["Date"].between(start, start + timedelta(days=6))].copy()
    df_week["Day"] = df_week["Date"].dt.strftime("%a")
    daily_km = df_week.groupby("Day")["Distance (km)"].sum()
    df_agg = pd.DataFrame({"Day": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]})
    df_agg["Distance (km)"] = df_agg["Day"].map(daily_km).fillna(0)
    x_field = "Day:N"
    x_title = "Day"
    bar_width = 60

elif view == "4 Weeks":
    current_week_start = today - timedelta(days=today.weekday())
    start = current_week_start - timedelta(weeks=4)
    weeks = [start + timedelta(weeks=i) for i in range(5)]
    df_4w = df[df["Date"].between(start, current_week_start + timedelta(days=6))].copy()
    df_4w["Week"] = df_4w["Date"].dt.to_period("W").apply(lambda r: r.start_time)
    df_agg = df_4w.groupby("Week")["Distance (km)"].sum().reindex(weeks, fill_value=0).reset_index()
    df_agg.columns = ["Week", "Distance (km)"]
    x_field = "Week:T"
    x_title = "Week"
    bar_width = 40

elif view == "3 Months":
    start = today - relativedelta(months=3)
    df_range = df[df["Date"] >= start].copy()
    df_range["Week"] = df_range["Date"].dt.to_period("W").apply(lambda r: r.start_time)
    df_agg = df_range.groupby("Week")["Distance (km)"].sum().reset_index()
    x_field = "Week:T"
    x_title = "Week"
    bar_width = 10

elif view == "6 Months":
    start = today - relativedelta(months=6)
    df_range = df[df["Date"] >= start].copy()
    df_range["Week"] = df_range["Date"].dt.to_period("W").apply(lambda r: r.start_time)
    df_agg = df_range.groupby("Week")["Distance (km)"].sum().reset_index()
    x_field = "Week:T"
    x_title = "Week"
    bar_width = 8

elif view == "1 Year":
    start = today - relativedelta(years=1)
    df_range = df[df["Date"] >= start].copy()
    df_range["Month"] = df_range["Date"].dt.to_period("M").apply(lambda r: r.start_time)
    df_agg = df_range.groupby("Month")["Distance (km)"].sum().reset_index()
    x_field = "Month:T"
    x_title = "Month"
    bar_width = 20

elif view == "All Months":
    df["Month"] = df["Date"].dt.to_period("M").apply(lambda r: r.start_time)
    df_agg = df.groupby("Month")["Distance (km)"].sum().reset_index()
    x_field = "Month:T"
    x_title = "Month"
    bar_width = 10

else:  # All Yearly
    df["Year"] = df["Date"].dt.to_period("Y").apply(lambda r: r.start_time)
    df_agg = df.groupby("Year")["Distance (km)"].sum().reset_index()
    x_field = "Year:T"
    x_title = "Year"
    bar_width = 30

# Base chart
base = alt.Chart(df_agg).encode(
    x=alt.X(x_field, title=x_title),
    y=alt.Y("Distance (km):Q", title="Distance (km)"),
    tooltip=[df_agg.columns[0], "Distance (km)"]
)

# Chart renderer
if chart_style == "Bar":
    chart = base.mark_bar(size=bar_width)
elif chart_style == "Line":
    chart = base.mark_line(strokeWidth=2)
elif chart_style == "Dots":
    chart = base.mark_point(filled=True, size=80)
elif chart_style == "Area":
    chart = base.mark_area(opacity=0.5)
elif chart_style == "Line + Dots":
    chart = base.mark_line(point=True, strokeWidth=2)

# Show chart
st.altair_chart(chart.properties(height=400), use_container_width=True)
