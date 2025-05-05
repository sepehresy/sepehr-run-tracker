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
                            parts = lap.split(",")
                            lap_info = {kv.split(":")[0].strip(): kv.split(":")[1].strip() for kv in parts if ":" in kv}
                            lap_info["Lap"] = lap.split(":")[0].strip().split()[0]
                            lap_data.append(lap_info)
                    lap_df = pd.DataFrame(lap_data)
                    lap_df.set_index("Lap", inplace=True)
                    st.dataframe(lap_df)
                except Exception as e:
                    st.warning(f"Could not parse lap details: {e}")
                st.markdown("---")
