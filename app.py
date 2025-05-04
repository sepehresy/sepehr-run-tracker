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

# View selector
view = st.radio(
    "Select View",
    ["Weekly", "Monthly", "3 Months", "6 Months", "1 Year", "All Months", "All Yearly"],
    horizontal=True
)

today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)

if view == "Weekly":
    start = today - timedelta(days=today.weekday())  # Monday of this week
    end = start + timedelta(days=6)
    df_range = df[(df["Date"] >= start) & (df["Date"] <= end)].copy()
    df_range["Period"] = df_range["Date"].dt.strftime("%a")
    group_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    x_title = "Day"
    bar_width = 60

elif view == "Monthly":
    start = today.replace(day=1)
    end = (start + relativedelta(months=1)) - timedelta(days=1)
    df_range = df[(df["Date"] >= start) & (df["Date"] <= end)].copy()
    df_range["Period"] = df_range["Date"].dt.to_period("W").apply(lambda r: r.start_time.strftime("%b %d"))
    x_title = "Week"
    bar_width = 40

elif view in ["3 Months", "6 Months"]:
    months = 3 if view == "3 Months" else 6
    start = (today.replace(day=1) - relativedelta(months=months))
    end = today.replace(day=1) + relativedelta(months=1) - timedelta(days=1)
    df_range = df[(df["Date"] >= start) & (df["Date"] <= end)].copy()
    df_range["Period"] = df_range["Date"].dt.to_period("W").apply(lambda r: r.start_time.strftime("%b %d"))
    x_title = "Week"
    bar_width = 10

elif view == "1 Year":
    start = today.replace(day=1) - relativedelta(years=1)
    end = today.replace(day=1) + relativedelta(months=1) - timedelta(days=1)
    df_range = df[(df["Date"] >= start) & (df["Date"] <= end)].copy()
    df_range["Period"] = df_range["Date"].dt.to_period("M").apply(lambda r: r.start_time.strftime("%b %Y"))
    x_title = "Month"
    bar_width = 20

elif view == "All Months":
    df_range = df.copy()
    df_range["Period"] = df_range["Date"].dt.to_period("M").apply(lambda r: r.start_time.strftime("%b %Y"))
    x_title = "Month"
    bar_width = 10

else:  # All Yearly
    df_range = df.copy()
    df_range["Period"] = df_range["Date"].dt.to_period("Y").apply(lambda r: r.start_time.strftime("%Y"))
    x_title = "Year"
    bar_width = 30

# Group and plot
agg = df_range.groupby("Period")["Distance (km)"].sum().reset_index()

# If it's weekly view, preserve weekday order
if view == "Weekly":
    agg["Period"] = pd.Categorical(agg["Period"], categories=group_order, ordered=True)
    agg = agg.sort_values("Period")

st.subheader(f"📊 Total Distance — {view}")
chart = alt.Chart(agg).mark_bar(size=bar_width).encode(
    x=alt.X("Period:N", title=x_title, sort=None),
    y=alt.Y("Distance (km):Q", title="Distance (km)"),
    tooltip=["Period", "Distance (km)"]
).properties(height=400)

st.altair_chart(chart, use_container_width=True)
