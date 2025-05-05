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

                        st.dataframe(lap_df.set_index("KM"))

                        chart_data = lap_df.copy()
                        chart_data["Pace_min"] = chart_data["Pace"]

                        bars = alt.Chart(chart_data).mark_bar(color="#00BFFF").encode(
                            x=alt.X("KM:O", title="KM"),
                            y=alt.Y("Pace_min:Q", title="Pace (min/km)"),
                            tooltip=["KM", "Time", "Pace", "HR", "Elev"]
                        )

                        pace_labels = alt.Chart(chart_data).mark_text(
                            align="left",
                            baseline="middle",
                            dx=5,
                            color="black",
                            fontSize=12
                        ).encode(
                            x=alt.X("KM:O"),
                            y=alt.Y("Pace_min:Q"),
                            text=alt.Text("Pace_min:Q", format=".2f")
                        )

                        st.altair_chart((bars + pace_labels).properties(height=400), use_container_width=True)

                except Exception as e:
                    st.warning(f"Could not parse lap details: {e}")
                st.markdown("---")
