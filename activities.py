
import streamlit as st
import pandas as pd

def render_activities(df):
    st.markdown("# 📂 Activities")

    df_sorted = df.sort_values(by="Date", ascending=False).copy()
    df_sorted["DateStr"] = df_sorted["Date"].dt.strftime("%b %d, %Y")
    selected = st.selectbox("Select an activity", df_sorted["DateStr"])

    activity = df_sorted[df_sorted["DateStr"] == selected].iloc[0]

    st.subheader("Overview")
    col1, col2, col3 = st.columns(3)
    col1.metric("Distance", f"{activity['Distance (km)']:.2f} km")
    col2.metric("Avg Pace", f"{activity['Pace (min/km)']}")
    col3.metric("Time", activity['Moving Time'])

    col4, col5, col6 = st.columns(3)
    col4.metric("HR Avg", int(activity['Avg HR']))
    col5.metric("Power Avg", int(activity['Power (W)']))
    col6.metric("Elevation Gain", int(activity['Elevation Gain']))

    st.subheader("Splits (Example Data)")
    split_data = {
        "KM": list(range(1, 9)),
        "Pace": ["5:53", "5:55", "5:36", "6:00", "6:09", "5:45", "6:09", "5:47"],
        "Elev": [8, 1, -1, -2, 8, -4, -1, 0],
        "HR": [122, 133, 178, 173, 172, 178, 178, 181]
    }
    st.dataframe(pd.DataFrame(split_data))
