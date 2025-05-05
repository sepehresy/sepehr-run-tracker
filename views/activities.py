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
                            lap_lines = lap.strip().split(",")
                            lap_info = {}
                            for item in lap_lines:
                                if ":" in item:
                                    key, val = item.split(":", 1)
                                    lap_info[key.strip()] = val.strip()
                            if 'Lap' in lap_info:
                                lap_number = lap_info.pop('Lap')
                            else:
                                lap_number = lap.strip().split()[0].replace(":", "")
                            lap_info["Lap"] = int(lap_number)
                            lap_data.append(lap_info)

                    lap_df = pd.DataFrame(lap_data)
                    if not lap_df.empty:
                        lap_df = lap_df.set_index("Lap")
                        columns = [col for col in ["Distance", "Pace", "HR", "Cad", "Elev Gain"] if col in lap_df.columns]
                        st.dataframe(lap_df[columns])
                except Exception as e:
                    st.warning(f"Could not parse lap details: {e}")
                st.markdown("---")
