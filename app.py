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
    ["Weekly", "4 Weeks", "3 Months", "6 Months", "1 Year", "All (monthly)", "All Yearly"],
    horizontal=True
)

# Chart style toggle
chart_style = st.selectbox(
    "Chart Style",
    ["Bar", "Bar + Line", "Line + Dots", "Area + Dots"],
    index=0
)

# Handle each view
if view == "Weekly":
    start = today - timedelta(days=today.weekday())
    days = [start + timedelta(days=i) for i in range(7)]
    df["Day"] = df["Date"].dt.strftime("%a")
    daily_km = df[df["Date"].between(start, start + timedelta(days=6))].groupby("Day")["Distance (km)"].sum()
    df_agg = pd.DataFrame({"Day": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]})
    df_agg["Distance (km)"] = df_agg["Day"].map(daily_km).fillna(0)
    x_field = "Day:N"
    x_title = "Day"
    bar_width = 60
    x_axis = alt.Axis(title=x_title)

elif view == "4 Weeks":
    current_week_start = today - timedelta(days=today.weekday())
    start = current_week_start - timedelta(weeks=4)
    weeks = [start + timedelta(weeks=i) for i in range(5)]
    df["Week"] = df["Date"].dt.to_period("W").apply(lambda r: r.start_time)
    weekly_km = df.groupby("Week")["Distance (km)"].sum().reset_index()
    df_agg = pd.DataFrame({"Week": weeks}).merge(weekly_km, on="Week", how="left").fillna(0)
    x_field = "Week:T"
    x_title = "Week"
    bar_width = 40
    x_axis = alt.Axis(title=x_title)

elif view == "3 Months":
    start = today - relativedelta(months=3)
    week_range = pd.date_range(start=start, end=today, freq="W-MON")
    df["Week"] = df["Date"].dt.to_period("W").apply(lambda r: r.start_time)
    weekly_km = df.groupby("Week")["Distance (km)"].sum().reset_index()
    df_agg = pd.DataFrame({"Week": week_range}).merge(weekly_km, on="Week", how="left").fillna(0)
    x_field = "Week:T"
    x_title = "Week"
    bar_width = 10
    x_axis = alt.Axis(title=x_title)

elif view == "6 Months":
    start = today - relativedelta(months=6)
    week_range = pd.date_range(start=start, end=today, freq="W-MON")
    df["Week"] = df["Date"].dt.to_period("W").apply(lambda r: r.start_time)
    weekly_km = df.groupby("Week")["Distance (km)"].sum().reset_index()
    df_agg = pd.DataFrame({"Week": week_range}).merge(weekly_km, on="Week", how="left").fillna(0)
    x_field = "Week:T"
    x_title = "Week"
    bar_width = 8
    x_axis = alt.Axis(title=x_title)

elif view == "1 Year":
    months = [(today.replace(day=1) - relativedelta(months=12 - i)) for i in range(13)]
    df["Month"] = df["Date"].dt.to_period("M").apply(lambda r: r.start_time)
    monthly_km = df.groupby("Month")["Distance (km)"].sum().reset_index()
    df_months = pd.DataFrame({"Month": months}).merge(monthly_km, on="Month", how="left").fillna(0)
    df_months["Month Label"] = df_months["Month"].dt.strftime("%b %Y")
    month_label_order = df_months["Month Label"].tolist()
    df_agg = df_months
    x_field = "Month Label:N"
    x_title = "Month"
    bar_width = 20
    x_axis = alt.Axis(title=x_title, labelAngle=-45)

elif view == "All (monthly)":
    df["MonthStart"] = df["Date"].dt.to_period("M").apply(lambda r: r.start_time)
    monthly_km = df.groupby("MonthStart")["Distance (km)"].sum().reset_index()
    monthly_km["Year"] = monthly_km["MonthStart"].dt.year
    monthly_km["Quarter"] = monthly_km["MonthStart"].dt.quarter
    monthly_km["MonthName"] = monthly_km["MonthStart"].dt.strftime("%b")
    monthly_km["MultiLabel"] = monthly_km["Year"].astype(str) + " | Q" + monthly_km["Quarter"].astype(str) + " | " + monthly_km["MonthName"]
    
    df_agg = monthly_km
    x_field = "MultiLabel:N"
    x_title = "Year | Quarter | Month"
    bar_width = 10
    x_axis = alt.Axis(title=x_title, labelAngle=-45, labelFontSize=10)

elif view == "All Yearly":
    df["Year"] = df["Date"].dt.to_period("Y").apply(lambda r: r.start_time)
    df_agg = df.groupby("Year")["Distance (km)"].sum().reset_index()
    x_field = "Year:T"
    x_title = "Year"
    bar_width = 30
    x_axis = alt.Axis(title=x_title)

# Base chart
base = alt.Chart(df_agg).encode(
    x=alt.X(x_field, title=x_title, axis=x_axis, sort=df_agg[x_field].tolist() if x_field.endswith(":N") else None),
    y=alt.Y("Distance (km):Q", title="Distance (km)"),
    tooltip=[df_agg.columns[0], "Distance (km)"]
)

# Render chart
if chart_style == "Bar":
    chart = base.mark_bar(size=bar_width)
elif chart_style == "Bar + Line":
    chart = base.mark_bar(size=bar_width) + base.mark_line(strokeWidth=2, color="orange")
elif chart_style == "Line + Dots":
    chart = base.mark_line(strokeWidth=2) + base.mark_point(filled=True, size=70)
elif chart_style == "Area + Dots":
    chart = base.mark_area(opacity=0.5, interpolate="monotone") + base.mark_point(filled=True, size=70)

st.altair_chart(chart.properties(height=400), use_container_width=True)
