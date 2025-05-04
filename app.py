import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
import numpy as np

st.set_page_config(page_title="Sepehr's Running Dashboard", layout="wide")
st.title("🏃 Sepehr's Running Dashboard")

# Load data
sheet_url = st.secrets["gsheet_url"]
@st.cache_data(ttl=3600)
def load_data():
    return pd.read_csv(sheet_url)

df = load_data()
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

# Sidebar filters
st.sidebar.subheader("🗓️ Filter by Time Range")
time_range = st.sidebar.selectbox(
    "Select time range",
    ["All", "2 Years", "1 Year", "6 Months", "3 Months", "1 Month", "1 Week"]
)

st.sidebar.subheader("🗂️ Group distance by")
group_by = st.sidebar.selectbox(
    "Group by",
    ["Daily", "Weekly", "Monthly", "Yearly"]
)

# Apply time filter
now = pd.to_datetime(datetime.now())
range_mapping = {
    "1 Week": now - timedelta(weeks=1),
    "1 Month": now - timedelta(weeks=4),
    "3 Months": now - timedelta(weeks=13),
    "6 Months": now - timedelta(weeks=26),
    "1 Year": now - timedelta(weeks=52),
    "2 Years": now - timedelta(weeks=104),
    "All": pd.to_datetime("2000-01-01")
}
cutoff = range_mapping[time_range]
df_filtered = df[df["Date"] >= cutoff].copy()

# Summary Stats
st.subheader("📈 Summary Statistics")
col1, col2, col3 = st.columns(3)
col1.metric("Total Distance", f"{df_filtered['Distance (km)'].sum():.1f} km")
col2.metric("Avg Pace", f"{df_filtered['Pace (min/km)'].mean():.2f} min/km")
col3.metric("Avg Heart Rate", f"{df_filtered['Avg HR'].mean():.0f} bpm")

# Garmin-style total distance chart
st.subheader("📊 Total Distance")
distance_view = st.radio(
    "Select Time Range",
    ["7 Days", "4 Weeks", "6 Months", "1 Year", "All"],
    horizontal=True
)

today = pd.to_datetime("today").normalize()

if distance_view == "7 Days":
    start = today - pd.Timedelta(days=6)
    df_range = df[df["Date"] >= start]
    df_range["Day"] = df_range["Date"].dt.day_name()
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    total_by = df_range.groupby("Day")["Distance (km)"].sum().reindex(order, fill_value=0).reset_index()
    x_field = "Day"
    chart_title = "Distance This Week"

elif distance_view == "4 Weeks":
    start = today - pd.Timedelta(weeks=4)
    df_range = df[df["Date"] >= start]
    df_range["Week"] = df_range["Date"].dt.to_period("W").apply(lambda r: r.start_time)
    total_by = df_range.groupby("Week")["Distance (km)"].sum().reset_index()
    x_field = "Week"
    chart_title = "Distance (Last 4 Weeks)"

elif distance_view in ["6 Months", "1 Year"]:
    months_back = 6 if distance_view == "6 Months" else 12
    start = today - pd.DateOffset(months=months_back)
    df_range = df[df["Date"] >= start]
    df_range["Month"] = df_range["Date"].dt.to_period("M").apply(lambda r: r.start_time)
    total_by = df_range.groupby("Month")["Distance (km)"].sum().reset_index()
    x_field = "Month"
    chart_title = f"Distance (Last {months_back} Months)"

else:  # All
    if (df["Date"].max() - df["Date"].min()).days < 700:
        df["Month"] = df["Date"].dt.to_period("M").apply(lambda r: r.start_time)
        total_by = df.groupby("Month")["Distance (km)"].sum().reset_index()
        x_field = "Month"
        chart_title = "Distance by Month"
    else:
        df["Year"] = df["Date"].dt.to_period("Y").apply(lambda r: r.start_time)
        total_by = df.groupby("Year")["Distance (km)"].sum().reset_index()
        x_field = "Year"
        chart_title = "Distance by Year"

chart = alt.Chart(total_by).mark_bar(cornerRadiusTop=3).encode(
    x=alt.X(f"{x_field}:T", title=None),
    y=alt.Y("Distance (km):Q", title="Kilometers"),
    tooltip=[x_field, "Distance (km)"]
).properties(
    height=400,
    title=chart_title
)

st.altair_chart(chart, use_container_width=True)

# Aggregation logic for classic distance chart
if group_by == "Daily":
    df_filtered["Period"] = df_filtered["Date"].dt.date
elif group_by == "Weekly":
    df_filtered["Period"] = df_filtered["Date"].dt.to_period("W").apply(lambda r: r.start_time)
elif group_by == "Monthly":
    df_filtered["Period"] = df_filtered["Date"].dt.to_period("M").apply(lambda r: r.start_time)
else:
    df_filtered["Period"] = df_filtered["Date"].dt.to_period("Y").apply(lambda r: r.start_time)

agg_km = df_filtered.groupby("Period")["Distance (km)"].sum().reset_index()
bar_size = {"Daily": 20, "Weekly": 10, "Monthly": 5, "Yearly": 2}.get(group_by, 10)

# Distance Chart (classic)
st.subheader(f"📊 Total Distance ({group_by}) — {time_range}")
chart = alt.Chart(agg_km).mark_bar(size=bar_size).encode(
    x=alt.X('Period:T', title=group_by),
    y=alt.Y('Distance (km):Q', title='Distance (km)')
).properties(height=400)
st.altair_chart(chart, use_container_width=True)

# Per-run Viewer
st.subheader("📋 Per-Run Analysis")
run_names = df_filtered['Name'].tolist()
if run_names:
    selected = st.selectbox("Select a run", run_names)
    run = df_filtered[df_filtered['Name'] == selected].iloc[0]
    st.write(f"**Date**: {run['Date'].date()}")
    st.write(f"**Distance**: {run['Distance (km)']} km")
    st.write(f"**Pace**: {run['Pace (min/km)']} min/km")
    st.write(f"**Heart Rate**: {run['Avg HR']} bpm")

# Countdown
race_day = datetime(2025, 5, 24)
days_left = (race_day - datetime.today()).days
st.markdown(f"### 🗓️ {days_left} days left until race day (May 24, 2025)")

# --- Race Training Plan Section ---
st.header("Race Training Plan")
start_week = df['Date'].min().to_period("W").start_time
end_week = race_day
weeks = pd.date_range(start=start_week, end=end_week, freq="W-MON")

df['Week'] = df['Date'].dt.to_period("W").apply(lambda r: r.start_time)
actual_km = df.groupby('Week')['Distance (km)'].sum().reindex(weeks, fill_value=0).reset_index()
actual_km.columns = ['Week', 'Actual']

if 'plan_df' not in st.session_state:
    st.session_state.plan_df = pd.DataFrame({
        'Week': weeks,
        'Planned': [np.nan] * len(weeks)
    })

plan_df = st.session_state.plan_df.copy()
merged = pd.merge(plan_df, actual_km, on='Week', how='left')
merged['Planned'] = merged['Planned'].fillna(0)
merged['Delta'] = merged['Actual'] - merged['Planned']
merged['Status'] = np.where(merged['Week'] < datetime.today(), "✅ Done", "⏳ Upcoming")

st.subheader("📋 Weekly Plan (editable)")
edited = st.data_editor(
    merged[['Week', 'Planned']],
    num_rows="dynamic",
    use_container_width=True,
    key="training_plan"
)
st.session_state.plan_df['Planned'] = edited['Planned']

# Plot: Planned vs Actual
st.subheader("📊 Planned vs Actual Distance per Week")
melted = pd.melt(merged, id_vars=["Week"], value_vars=["Planned", "Actual"], var_name="Type", value_name="KM")

highlight = alt.Chart(pd.DataFrame({"x": [pd.to_datetime("2025-05-24")]})).mark_rule(color="red").encode(x='x:T')

bar_chart = alt.Chart(melted).mark_bar().encode(
    x=alt.X('Week:T', title='Week'),
    y=alt.Y('KM:Q', title='Distance (km)'),
    color='Type:N',
    tooltip=['Week', 'Type', 'KM']
).properties(height=400)

done_points = merged[merged['Week'] < datetime.today()]
done_text = alt.Chart(done_points).mark_text(
    align='center', dy=-10, fontSize=10
).encode(
    x='Week:T',
    y='Actual:Q',
    text=alt.Text('Delta:Q', format=".1f")
)

st.altair_chart((bar_chart + done_text + highlight), use_container_width=True)
