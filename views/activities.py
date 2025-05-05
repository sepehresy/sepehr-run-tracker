import streamlit as st
import pandas as pd
import re
import altair as alt


def render_activities(df):
    st.title("📋 Activities")

    st.dataframe(df.sort_values("Date", ascending=False))

    if "Lap Details" in df.columns:
        st.subheader("Splits (per run)")

        for _, row in df.sort_values("Date", ascending=False).iterrows():
            if pd.notna(row["Lap Details"]):
                st.markdown(f"**{row['Date'].date()} - {row['Name']}**")
                try:
                    laps_raw = re.findall(r"Lap (\d+):\\s*([^|]+)", row["Lap Details"])
                    lap_data = []
                    for lap_number, details in laps_raw:
                        parts = [x.strip() for x in details.split(",")]
                        lap_info = {"KM": int(lap_number)}
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
                                lap_info["Elev"] = float(p.replace("ElevGain", "").strip())
                        lap_data.append(lap_info)

                    lap_df = pd.DataFrame(lap_data)
                    if not lap_df.empty:
                        lap_df = lap_df.sort_values("KM")

                        # Create base bar chart for pace
                        pace_chart = alt.Chart(lap_df).mark_bar(color="#00BFFF").encode(
                            x=alt.X("KM:O", title="KM"),
                            y=alt.Y("Pace:Q", title="Pace (min/km)"),
                            tooltip=["KM", "Time", "Pace", "HR", "Elev"]
                        )

                        # Add HR and Elev text annotations
                        text_chart = alt.Chart(lap_df).mark_text(align='left', dx=3, dy=5, color='white').encode(
                            x=alt.X("KM:O"),
                            y=alt.Y("Pace:Q"),
                            text=alt.Text("HR:N", format="d")
                        )

                        elev_chart = alt.Chart(lap_df).mark_text(align='left', dx=3, dy=-15, color='white').encode(
                            x=alt.X("KM:O"),
                            y=alt.Y("Pace:Q"),
                            text=alt.Text("Elev:N")
                        )

                        st.altair_chart(
                            (pace_chart + text_chart + elev_chart).properties(height=300),
                            use_container_width=True
                        )

                        st.dataframe(
                            lap_df[["KM", "Time", "Pace", "Elev", "HR"]].set_index("KM"),
                            use_container_width=True
                        )

                except Exception as e:
                    st.warning(f"Could not parse lap details: {e}")
                st.markdown("---")
