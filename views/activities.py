import streamlit as st
import pandas as pd

def render_activities(df):
    st.title("📋 Activities")

    st.dataframe(df.sort_values("Date", ascending=False))

    if "Lap Details" in df.columns:
        st.subheader("Splits (per run)")

        for _, row in df.sort_values("Date", ascending=False).iterrows():
            if pd.notna(row["Lap Details"]):
                st.markdown(f"**{row['Date'].date()} - {row['Name']}**")
                try:
                    laps_raw = row["Lap Details"].split("Lap ")
                    lap_data = []
                    for lap in laps_raw:
                        if lap.strip():
                            lap_number = lap.strip().split()[0].replace(":", "")
                            parts = [p.strip() for p in lap.strip().split(",") if ":" in p]
                            lap_info = {"Lap": int(lap_number)}
                            for kv in parts:
                                k, v = kv.split(":", 1)
                                lap_info[k.strip()] = v.strip()
                            lap_data.append(lap_info)
                    lap_df = pd.DataFrame(lap_data)
                    st.dataframe(lap_df[[col for col in ["Lap", "Distance", "pace", "HR", "Cad", "Elev Gain"] if col in lap_df.columns]])
                except Exception as e:
                    st.warning(f"Could not parse lap details: {e}")
                st.markdown("---")
