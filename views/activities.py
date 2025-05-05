import streamlit as st
import pandas as pd
import re
import matplotlib.pyplot as plt


def render_activities(df):
    st.title("📋 Activities")

    st.dataframe(df.sort_values("Date", ascending=False))

    if "Lap Details" in df.columns:
        st.subheader("Splits (per run)")

        for _, row in df.sort_values("Date", ascending=False).iterrows():
            if pd.notna(row["Lap Details"]):
                st.markdown(f"**{row['Date'].date()} - {row['Name']}**")
                try:
                    laps_raw = re.findall(r"Lap (\d+):\s*([^|]+)", row["Lap Details"].replace("\\n", " "))
                    lap_data = []
                    for lap_number, details in laps_raw:
                        parts = [x.strip() for x in details.split(",")]
                        lap_info = {"Lap": int(lap_number)}
                        for p in parts:
                            if p.endswith("km"):
                                lap_info["Distance"] = float(p.replace("km", ""))
                            elif re.match(r"\d+:\d+", p):
                                lap_info["Time"] = p
                            elif p.startswith("pace"):
                                lap_info["Pace"] = float(p.replace("pace", "").strip())
                            elif p.startswith("HR"):
                                lap_info["HR"] = int(float(p.replace("HR", "").strip()))
                            elif p.startswith("Cad"):
                                lap_info["Cad"] = int(float(p.replace("Cad", "").strip()))
                            elif p.startswith("ElevGain"):
                                lap_info["ElevGain"] = float(p.replace("ElevGain", "").strip())
                        lap_data.append(lap_info)

                    lap_df = pd.DataFrame(lap_data)
                    if not lap_df.empty:
                        st.dataframe(lap_df.set_index("Lap"), use_container_width=True)

                        # Create strava-like table chart with bars
                        fig, ax = plt.subplots(figsize=(10, 0.4 * len(lap_df)))
                        bars = ax.barh(lap_df.index, lap_df["Pace"], color="#1EBEFF")

                        for i, (dist, pace, elev, hr) in enumerate(zip(lap_df["Distance"], lap_df["Pace"], lap_df["ElevGain"], lap_df["HR"])):
                            ax.text(0.01, i, f"{int(dist)}", va='center', ha='left', color='black', fontweight='bold')
                            ax.text(pace + 0.1, i, f"{elev:.0f} | {hr}", va='center', ha='left', color='black')

                        ax.set_yticks(lap_df.index)
                        ax.set_yticklabels([f"{lap_df.loc[i, 'Time']}" for i in lap_df.index])
                        ax.set_xlabel("Pace (min/km)")
                        ax.set_ylabel("Lap")
                        ax.invert_yaxis()
                        ax.grid(True, axis='x', linestyle='--', alpha=0.5)
                        ax.set_xlim(0, max(lap_df["Pace"]) + 2)
                        st.pyplot(fig)

                except Exception as e:
                    st.warning(f"Could not parse lap details: {e}")
                st.markdown("---")
