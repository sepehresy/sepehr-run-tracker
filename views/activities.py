import streamlit as st
import pandas as pd
import re

def render_activities(df):
    st.title("📋 Activities")

    st.dataframe(df.sort_values("Date", ascending=False))

    if "Lap Details" in df.columns:
        st.subheader("Splits (per run)")

        for _, row in df.sort_values("Date", ascending=False).iterrows():
            if pd.notna(row["Lap Details"]):
                st.markdown(f"**{row['Date'].date()} - {row['Name']}**")
                try:
                    laps_raw = re.findall(r"Lap (\d+): ([^\n]+)", row["Lap Details"])
                    lap_data = []
                    for lap_number, details in laps_raw:
                        lap_info = {"Lap": int(lap_number)}
                        for item in details.split(","):
                            if ":" in item:
                                key, val = item.split(":", 1)
                                lap_info[key.strip()] = val.strip()
                        lap_data.append(lap_info)

                    lap_df = pd.DataFrame(lap_data)
                    if not lap_df.empty:
                        lap_df = lap_df.set_index("Lap")
                        columns = [col for col in ["Distance", "Pace", "HR", "Cad", "Elev Gain"] if col in lap_df.columns]
                        st.dataframe(lap_df[columns])
                except Exception as e:
                    st.warning(f"Could not parse lap details: {e}")
                st.markdown("---")
